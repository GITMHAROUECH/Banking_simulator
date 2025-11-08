"""
Service de génération et gestion des expositions - I11.
Gère la génération, persistance et chargement des expositions par run_id.
"""
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.base import SessionLocal

def get_session():
    """Retourne une nouvelle session DB."""
    return SessionLocal()
from db.models import BalanceSheetSnapshot, Exposure, SimulationRun
from src.domain.simulation.exposure_generator import generate_all_exposures, get_default_config
from src.services.persistence_service import compute_params_hash


def generate_exposures(
    run_id: str | None = None,
    config: dict | None = None,
    seed: int = 42,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, bool]:
    """
    Génère les expositions pour un run_id.
    
    Args:
        run_id: Identifiant unique du run (généré si None)
        config: Configuration de génération (utilise default si None)
        seed: Seed pour reproductibilité
        use_cache: Si True, vérifie le cache avant génération
    
    Returns:
        (DataFrame exposures, cache_hit)
    """
    # Générer run_id si non fourni
    if run_id is None:
        run_id = str(uuid.uuid4())
    
    # Utiliser config par défaut si non fournie
    if config is None:
        config = get_default_config()
    
    # Calculer params_hash pour le cache
    params_hash = compute_params_hash({'config': config, 'seed': seed})
    
    # Vérifier le cache
    if use_cache:
        cached_df = _load_exposures_from_db(run_id)
        if cached_df is not None and len(cached_df) > 0:
            return (cached_df, True)  # Cache hit
    
    # Générer les expositions (domain layer)
    df = generate_all_exposures(run_id, config, seed)
    
    # Sauvegarder en DB
    _save_exposures_to_db(run_id, df, params_hash, config)
    
    return (df, False)  # Cache miss


def load_exposures(run_id: str) -> pd.DataFrame:
    """
    Charge les expositions depuis la DB pour un run_id.
    
    Args:
        run_id: Identifiant du run
    
    Returns:
        DataFrame exposures
    """
    df = _load_exposures_from_db(run_id)
    if df is None:
        raise ValueError(f"Aucune exposition trouvée pour run_id={run_id}")
    return df


def snapshot_balance_sheet(run_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Crée un snapshot du bilan (assets, liabilities) à partir des expositions.

    Args:
        run_id: Identifiant du run

    Returns:
        (df_assets, df_liabilities)
    """
    # Charger les expositions
    df = load_exposures(run_id)

    # Assets : Loans, Bonds, Derivatives (MTM > 0), Equities
    asset_products = ['Loan', 'Bond', 'Equity']
    df_assets_base = df[df['product_type'].isin(asset_products)].copy()

    # Derivatives avec MTM > 0
    df_deriv_assets = df[(df['product_type'] == 'Derivative') & (df['mtm'] > 0)].copy()

    # Off-BS (EAD seulement)
    df_offbs = df[df['product_type'].isin(['Commitment', 'Guarantee'])].copy()

    # Combiner
    df_assets_all = pd.concat([df_assets_base, df_deriv_assets, df_offbs], ignore_index=True)

    # Agréger par catégorie, entity, currency
    df_assets = df_assets_all.groupby(['product_type', 'entity', 'currency']).agg({
        'notional': 'sum',
        'ead': 'sum',
        'mtm': 'sum',
    }).reset_index()

    df_assets['item_type'] = 'asset'
    df_assets.rename(columns={'product_type': 'category', 'notional': 'amount'}, inplace=True)

    # Liabilities : Deposits, Derivatives (MTM < 0)
    df_liab_deposits = df[df['product_type'] == 'Deposit'].copy()
    df_deriv_liab = df[(df['product_type'] == 'Derivative') & (df['mtm'] < 0)].copy()

    df_liabilities_all = pd.concat([df_liab_deposits, df_deriv_liab], ignore_index=True)

    df_liabilities = df_liabilities_all.groupby(['product_type', 'entity', 'currency']).agg({
        'notional': 'sum',
        'ead': 'sum',
        'mtm': 'sum',
    }).reset_index()

    df_liabilities['item_type'] = 'liability'
    df_liabilities.rename(columns={'product_type': 'category', 'notional': 'amount'}, inplace=True)

    # Sauvegarder en DB
    _save_balance_sheet_snapshots(run_id, df_assets, df_liabilities)

    return (df_assets, df_liabilities)


def list_runs(limit: int = 50) -> pd.DataFrame:
    """
    Liste les runs de simulation disponibles.

    Args:
        limit: Nombre maximum de runs à retourner

    Returns:
        DataFrame avec colonnes: run_id, run_date, status, total_exposures, total_notional
    """
    session: Session = get_session()

    try:
        stmt = select(SimulationRun).order_by(SimulationRun.run_date.desc()).limit(limit)
        results = session.execute(stmt).scalars().all()

        if not results:
            return pd.DataFrame(columns=['run_id', 'run_date', 'status', 'total_exposures', 'total_notional'])

        # Convertir en DataFrame
        data = [
            {
                'run_id': r.run_id,
                'run_date': r.run_date,
                'status': r.status,
                'total_exposures': r.total_exposures,
                'total_notional': float(r.total_notional) if r.total_notional else 0.0,
            }
            for r in results
        ]

        return pd.DataFrame(data)
    finally:
        session.close()


# ============================================================================
# Fonctions privées de persistance
# ============================================================================

def _save_exposures_to_db(run_id: str, df: pd.DataFrame, params_hash: str, config: dict) -> None:
    """Sauvegarde les exposures en DB."""
    session: Session = get_session()
    
    try:
        # Créer le SimulationRun
        sim_run = SimulationRun(
            run_id=run_id,
            params_hash=params_hash,
            run_date=datetime.utcnow(),
            status='completed',
            total_exposures=len(df),
            total_notional=float(df['notional'].sum()),
            config_json=json.dumps(config),
        )
        session.merge(sim_run)
        
        # Sauvegarder les exposures (bulk insert)
        exposures = df.to_dict('records')
        for exp in exposures:
            # Convertir les dates en datetime.date si nécessaire
            if pd.notna(exp.get('booking_date')):
                if isinstance(exp['booking_date'], pd.Timestamp):
                    exp['booking_date'] = exp['booking_date'].date()
            if pd.notna(exp.get('maturity_date')):
                if isinstance(exp['maturity_date'], pd.Timestamp):
                    exp['maturity_date'] = exp['maturity_date'].date()
            
            # Remplacer NaN par None
            for key, value in exp.items():
                if pd.isna(value):
                    exp[key] = None
        
        session.bulk_insert_mappings(Exposure, exposures)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def _load_exposures_from_db(run_id: str) -> pd.DataFrame | None:
    """Charge les exposures depuis la DB."""
    session: Session = get_session()
    
    try:
        stmt = select(Exposure).where(Exposure.run_id == run_id)
        results = session.execute(stmt).scalars().all()
        
        if not results:
            return None
        
        # Convertir en DataFrame
        data = [
            {
                'id': r.id,
                'run_id': r.run_id,
                'product_type': r.product_type,
                'counterparty_id': r.counterparty_id,
                'booking_date': r.booking_date,
                'maturity_date': r.maturity_date,
                'currency': r.currency,
                'notional': float(r.notional) if r.notional else None,
                'ead': float(r.ead) if r.ead else None,
                'pd': float(r.pd) if r.pd else None,
                'lgd': float(r.lgd) if r.lgd else None,
                'ccf': float(r.ccf) if r.ccf else None,
                'maturity_years': float(r.maturity_years) if r.maturity_years else None,
                'mtm': float(r.mtm) if r.mtm else None,
                'desk': r.desk,
                'entity': r.entity,
                'is_retail': r.is_retail,
                'exposure_class': r.exposure_class,
                'netting_set_id': r.netting_set_id,
                'collateral_value': float(r.collateral_value) if r.collateral_value else None,
            }
            for r in results
        ]
        
        return pd.DataFrame(data)
    finally:
        session.close()


def _save_balance_sheet_snapshots(run_id: str, df_assets: pd.DataFrame, df_liabilities: pd.DataFrame) -> None:
    """Sauvegarde les balance sheet snapshots en DB."""
    session: Session = get_session()
    
    try:
        # Combiner assets et liabilities
        df_all = pd.concat([df_assets, df_liabilities], ignore_index=True)
        
        # Ajouter IDs
        df_all['id'] = [str(uuid.uuid4()) for _ in range(len(df_all))]
        df_all['run_id'] = run_id
        
        # Sélectionner les colonnes
        df_all = df_all[['id', 'run_id', 'item_type', 'category', 'entity', 'currency', 'amount']]
        
        # Bulk insert
        snapshots = df_all.to_dict('records')
        for snap in snapshots:
            # Remplacer NaN par None
            for key, value in snap.items():
                if pd.isna(value):
                    snap[key] = None
        
        session.bulk_insert_mappings(BalanceSheetSnapshot, snapshots)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

