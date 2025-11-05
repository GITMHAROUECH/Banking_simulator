"""
Service IFRS 9 ECL - I12.
Orchestration du calcul ECL avec persistance et cache.
"""
import hashlib
import json
import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from db.base import SessionLocal

def get_session():
    """Retourne une nouvelle session DB."""
    return SessionLocal()
from db.models import ECLResult, ScenarioOverlay
from src.domain.ifrs9.ecl import compute_ecl_batch
from src.services.exposure_service import load_exposures


def compute_ecl_advanced(
    run_id: str,
    scenario_id: str,
    *,
    horizon_months: int = 12,
    discount_rate: float = 5.0,
    use_cache: bool = True,
) -> tuple[dict, bool]:
    """
    Calcule ECL avancé pour un run_id + scenario_id.
    
    Args:
        run_id: Identifiant du run
        scenario_id: Identifiant du scénario overlay
        horizon_months: Horizon projection (mois)
        discount_rate: Taux de discount annuel (%)
        use_cache: Si True, utilise le cache
    
    Returns:
        ({
            'by_exposure': DataFrame,
            'by_segment': DataFrame,
            'totals': DataFrame,
            'stage_mix': dict,
        }, cache_hit)
    """
    cache_hit = False
    
    # 1. Vérifier le cache
    if use_cache:
        cached_result = _load_ecl_from_cache(run_id, scenario_id)
        if cached_result is not None:
            return (cached_result, True)
    
    # 2. Charger les exposures
    df_exp = load_exposures(run_id)
    
    if len(df_exp) == 0:
        return ({
            'by_exposure': pd.DataFrame(),
            'by_segment': pd.DataFrame(),
            'totals': pd.DataFrame(),
            'stage_mix': {},
        }, False)
    
    # 3. Charger le scénario overlay
    scenario_overlay = _load_scenario_overlay(scenario_id)
    
    # Utiliser horizon_months depuis scenario si disponible
    if scenario_overlay and 'horizon_months' in scenario_overlay:
        horizon_months = scenario_overlay['horizon_months']
    
    # Utiliser discount_rate depuis scenario si disponible
    if scenario_overlay and 'discount_rate_value' in scenario_overlay:
        discount_rate = scenario_overlay['discount_rate_value']
    
    # 4. Calculer ECL (Domain)
    df_ecl = compute_ecl_batch(
        exposures_df=df_exp,
        scenario_overlay=scenario_overlay,
        horizon_months=horizon_months,
        discount_rate=discount_rate,
    )
    
    # 5. Enrichir avec metadata
    df_ecl['run_id'] = run_id
    df_ecl['scenario_id'] = scenario_id
    df_ecl['ecl_currency'] = df_exp['currency'].iloc[0] if 'currency' in df_exp.columns else 'EUR'
    
    # Ajouter segment_id (depuis exposure_class)
    df_ecl = df_ecl.merge(
        df_exp[['id', 'exposure_class']].rename(columns={'id': 'exposure_id'}),
        on='exposure_id',
        how='left'
    )
    df_ecl['segment_id'] = df_ecl['exposure_class']
    
    # 6. Agréger par segment
    df_by_segment = df_ecl.groupby(['segment_id', 'stage']).agg({
        'ecl_amount': 'sum',
        'ead': 'sum',
    }).reset_index()
    
    df_by_segment['ecl_rate'] = (
        df_by_segment['ecl_amount'] / df_by_segment['ead'] * 100
    ).fillna(0)
    
    # 7. Totaux
    total_ecl = df_ecl['ecl_amount'].sum()
    total_ead = df_ecl['ead'].sum()
    
    df_totals = pd.DataFrame([{
        'Total ECL': total_ecl,
        'Total EAD': total_ead,
        'ECL Rate (%)': (total_ecl / total_ead * 100) if total_ead > 0 else 0,
    }])
    
    # 8. Stage mix
    stage_counts = df_ecl['stage'].value_counts().to_dict()
    total_count = len(df_ecl)
    stage_mix = {
        stage: {
            'count': count,
            'percentage': count / total_count * 100,
            'ecl_amount': float(df_ecl[df_ecl['stage'] == stage]['ecl_amount'].sum()),
        }
        for stage, count in stage_counts.items()
    }
    
    # 9. Persister les résultats
    _persist_ecl_results(df_ecl, run_id, scenario_id)
    
    # 10. Préparer le résultat
    result = {
        'by_exposure': df_ecl,
        'by_segment': df_by_segment,
        'totals': df_totals,
        'stage_mix': stage_mix,
    }
    
    return (result, cache_hit)


def _load_scenario_overlay(scenario_id: str) -> dict | None:
    """
    Charge un scénario overlay depuis la DB.
    
    Args:
        scenario_id: Identifiant du scénario
    
    Returns:
        Dict avec les paramètres du scénario, ou None si non trouvé
    """
    session: Session = get_session()
    try:
        scenario = session.query(ScenarioOverlay).filter_by(scenario_id=scenario_id).first()
        
        if scenario is None:
            return None
        
        overlay = {
            'scenario_id': scenario.scenario_id,
            'name': scenario.name,
            'description': scenario.description,
            'pd_shift': float(scenario.pd_shift) if scenario.pd_shift else 0.0,
            'sicr_threshold_abs': float(scenario.sicr_threshold_abs) if scenario.sicr_threshold_abs else 1.0,
            'sicr_threshold_rel': float(scenario.sicr_threshold_rel) if scenario.sicr_threshold_rel else 1.0,
            'backstop_days': scenario.backstop_days or 30,
            'discount_rate_mode': scenario.discount_rate_mode or 'EIR',
            'discount_rate_value': float(scenario.discount_rate_value) if scenario.discount_rate_value else 5.0,
            'horizon_months': scenario.horizon_months or 12,
        }
        
        # Parser lgd_floor_by_class si présent
        if scenario.lgd_floor_by_class:
            overlay['lgd_floor_by_class'] = scenario.lgd_floor_by_class
        
        return overlay
    
    finally:
        session.close()


def _persist_ecl_results(df_ecl: pd.DataFrame, run_id: str, scenario_id: str) -> None:
    """
    Persiste les résultats ECL dans la DB.
    
    Args:
        df_ecl: DataFrame avec résultats ECL
        run_id: Identifiant du run
        scenario_id: Identifiant du scénario
    """
    session: Session = get_session()
    try:
        # Nettoyer les NaN avant persistance
        df_ecl = df_ecl.fillna({
            'ecl_amount': 0.0,
            'pd_12m': 0.0,
            'pd_lifetime': 0.0,
            'lgd': 0.0,
            'ead': 0.0,
        })
        
        # Supprimer les résultats existants pour ce run_id + scenario_id
        session.query(ECLResult).filter_by(run_id=run_id, scenario_id=scenario_id).delete()
        
        # Insérer les nouveaux résultats
        for _, row in df_ecl.iterrows():
            ecl_result = ECLResult(
                id=str(uuid.uuid4()),
                run_id=run_id,
                scenario_id=scenario_id,
                exposure_id=str(row['exposure_id']),
                stage=row['stage'],
                pd_12m=float(row['pd_12m']),
                pd_lifetime=float(row['pd_lifetime']),
                lgd=float(row['lgd']),
                ead=float(row['ead']),
                ecl_amount=float(row['ecl_amount']),
                ecl_currency=row.get('ecl_currency', 'EUR'),
                segment_id=row.get('segment_id'),
                calculation_date=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            session.add(ecl_result)
        
        session.commit()
    
    except Exception as e:
        session.rollback()
        raise e
    
    finally:
        session.close()


def _load_ecl_from_cache(run_id: str, scenario_id: str) -> dict | None:
    """
    Charge les résultats ECL depuis le cache (DB).
    
    Args:
        run_id: Identifiant du run
        scenario_id: Identifiant du scénario
    
    Returns:
        Dict avec résultats ECL, ou None si non trouvé
    """
    session: Session = get_session()
    try:
        results = session.query(ECLResult).filter_by(
            run_id=run_id,
            scenario_id=scenario_id
        ).all()
        
        if not results:
            return None
        
        # Convertir en DataFrame
        df_ecl = pd.DataFrame([{
            'exposure_id': r.exposure_id,
            'stage': r.stage,
            'pd_12m': float(r.pd_12m) if r.pd_12m else 0,
            'pd_lifetime': float(r.pd_lifetime) if r.pd_lifetime else 0,
            'lgd': float(r.lgd),
            'ead': float(r.ead),
            'ecl_amount': float(r.ecl_amount),
            'ecl_currency': r.ecl_currency,
            'segment_id': r.segment_id,
        } for r in results])
        
        # Agréger par segment
        df_by_segment = df_ecl.groupby(['segment_id', 'stage']).agg({
            'ecl_amount': 'sum',
            'ead': 'sum',
        }).reset_index()
        
        df_by_segment['ecl_rate'] = (
            df_by_segment['ecl_amount'] / df_by_segment['ead'] * 100
        ).fillna(0)
        
        # Totaux
        total_ecl = df_ecl['ecl_amount'].sum()
        total_ead = df_ecl['ead'].sum()
        
        df_totals = pd.DataFrame([{
            'Total ECL': total_ecl,
            'Total EAD': total_ead,
            'ECL Rate (%)': (total_ecl / total_ead * 100) if total_ead > 0 else 0,
        }])
        
        # Stage mix
        stage_counts = df_ecl['stage'].value_counts().to_dict()
        total_count = len(df_ecl)
        stage_mix = {
            stage: {
                'count': count,
                'percentage': count / total_count * 100,
                'ecl_amount': float(df_ecl[df_ecl['stage'] == stage]['ecl_amount'].sum()),
            }
            for stage, count in stage_counts.items()
        }
        
        return {
            'by_exposure': df_ecl,
            'by_segment': df_by_segment,
            'totals': df_totals,
            'stage_mix': stage_mix,
        }
    
    finally:
        session.close()


def create_scenario_overlay(
    scenario_id: str,
    name: str,
    description: str = '',
    pd_shift: float = 0.0,
    lgd_floors: dict[str, float] | None = None,
    sicr_threshold_abs: float = 1.0,
    sicr_threshold_rel: float = 1.0,
    backstop_days: int = 30,
    discount_rate_mode: str = 'EIR',
    discount_rate_value: float = 5.0,
    horizon_months: int = 12,
) -> str:
    """
    Crée un scénario overlay dans la DB.
    
    Args:
        scenario_id: Identifiant unique du scénario
        name: Nom du scénario
        description: Description
        pd_shift: Shift PD (bps)
        lgd_floors: Dict {asset_class: floor_%}
        sicr_threshold_abs: Seuil SICR absolu (bps)
        sicr_threshold_rel: Seuil SICR relatif (%)
        backstop_days: Backstop jours
        discount_rate_mode: 'EIR', 'RFR', 'Market'
        discount_rate_value: Taux de discount (%)
        horizon_months: Horizon lifetime (mois)
    
    Returns:
        scenario_id
    """
    session: Session = get_session()
    try:
        # Vérifier si existe déjà
        existing = session.query(ScenarioOverlay).filter_by(scenario_id=scenario_id).first()
        if existing:
            session.delete(existing)
        
        # Créer le scénario
        scenario = ScenarioOverlay(
            id=str(uuid.uuid4()),
            scenario_id=scenario_id,
            name=name,
            description=description,
            pd_shift=pd_shift,
            lgd_floor_by_class=json.dumps(lgd_floors) if lgd_floors else None,
            sicr_threshold_abs=sicr_threshold_abs,
            sicr_threshold_rel=sicr_threshold_rel,
            backstop_days=backstop_days,
            discount_rate_mode=discount_rate_mode,
            discount_rate_value=discount_rate_value,
            horizon_months=horizon_months,
            created_at=datetime.utcnow(),
        )
        
        session.add(scenario)
        session.commit()
        
        return scenario_id
    
    except Exception as e:
        session.rollback()
        raise e
    
    finally:
        session.close()


def list_scenario_overlays() -> pd.DataFrame:
    """
    Liste tous les scénarios overlays.
    
    Returns:
        DataFrame avec colonnes: scenario_id, name, description, created_at
    """
    session: Session = get_session()
    try:
        scenarios = session.query(ScenarioOverlay).all()
        
        if not scenarios:
            return pd.DataFrame(columns=['scenario_id', 'name', 'description', 'created_at'])
        
        df = pd.DataFrame([{
            'scenario_id': s.scenario_id,
            'name': s.name,
            'description': s.description,
            'pd_shift': float(s.pd_shift) if s.pd_shift else 0.0,
            'horizon_months': s.horizon_months,
            'created_at': s.created_at,
        } for s in scenarios])
        
        return df
    
    finally:
        session.close()

