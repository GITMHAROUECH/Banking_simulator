"""
Module IFRS 9 ECL (Expected Credit Loss) - I12.
Implémente le calcul ECL avec staging S1/S2/S3, PD term structures, LGD downturn.
"""
import numpy as np
import pandas as pd


# ============================================================================
# 1. Staging (S1/S2/S3)
# ============================================================================

def determine_stage(
    pd_current: float,
    pd_origination: float,
    dpd: int = 0,
    forbearance: bool = False,
    sicr_threshold_abs: float = 1.0,  # 100 bps
    sicr_threshold_rel: float = 1.0,  # 100% relatif
    backstop_days: int = 30,
) -> str:
    """
    Détermine le stage IFRS 9 d'une exposition.
    
    Args:
        pd_current: PD actuelle (%)
        pd_origination: PD à l'origination (%)
        dpd: Days Past Due
        forbearance: Flag forbearance
        sicr_threshold_abs: Seuil SICR absolu (bps)
        sicr_threshold_rel: Seuil SICR relatif (%)
        backstop_days: Backstop jours (défaut 30)
    
    Returns:
        'S1', 'S2', ou 'S3'
    """
    # Stage 3 : Default (DPD > 90 jours)
    if dpd >= 90:
        return 'S3'
    
    # Stage 2 : SICR détecté
    # Critère 1 : Backstop 30 jours
    if dpd >= backstop_days:
        return 'S2'
    
    # Critère 2 : Forbearance
    if forbearance:
        return 'S2'
    
    # Critère 3 : Augmentation significative PD
    delta_pd_abs = (pd_current - pd_origination) * 100  # en bps
    delta_pd_rel = (pd_current / pd_origination - 1) if pd_origination > 0 else 0
    
    if delta_pd_abs >= sicr_threshold_abs or delta_pd_rel >= sicr_threshold_rel:
        return 'S2'
    
    # Stage 1 : Performing
    return 'S1'


# ============================================================================
# 2. PD Term Structure
# ============================================================================

def compute_pd_curve(
    pd_1y: float,
    horizon_months: int,
    method: str = 'simple',
    scenario_overlay: dict | None = None,
) -> np.ndarray:
    """
    Calcule la courbe PD sur l'horizon.
    
    Args:
        pd_1y: PD 1 an (%)
        horizon_months: Horizon en mois
        method: 'simple', 'beta', 'overlay'
        scenario_overlay: Dict avec pd_shift (bps)
    
    Returns:
        Array de PD_t pour t=1..horizon_months (en %)
    """
    if method == 'simple':
        # Approximation simple : PD_t = 1 - (1 - PD_1y)^(t/12)
        t_years = np.arange(1, horizon_months + 1) / 12.0
        pd_curve = 1 - (1 - pd_1y / 100) ** t_years
        pd_curve *= 100  # Retour en %
    
    elif method == 'beta':
        # Beta distribution (proxy rating)
        # Paramètres simplifiés : α=2, β=10 (forme typique)
        t_norm = np.arange(1, horizon_months + 1) / horizon_months
        from scipy.stats import beta
        pd_curve = beta.cdf(t_norm, a=2, b=10) * pd_1y
    
    elif method == 'overlay':
        # Overlay : PD_t = PD_base_t × (1 + shift)
        t_years = np.arange(1, horizon_months + 1) / 12.0
        pd_curve = 1 - (1 - pd_1y / 100) ** t_years
        pd_curve *= 100
        
        if scenario_overlay and 'pd_shift' in scenario_overlay:
            shift_bps = scenario_overlay['pd_shift']
            pd_curve += shift_bps / 100  # Shift en %
    
    else:
        raise ValueError(f"Méthode inconnue : {method}")
    
    return pd_curve


# ============================================================================
# 3. LGD Downturn
# ============================================================================

def compute_lgd_downturn(
    lgd_base: float,
    asset_class: str,
    lgd_floors: dict[str, float] | None = None,
    haircut_stress: float = 0.0,
) -> float:
    """
    Calcule LGD downturn avec floor.
    
    Args:
        lgd_base: LGD de base (%)
        asset_class: Classe d'actif
        lgd_floors: Dict {asset_class: floor_%}
        haircut_stress: Haircut additionnel (%)
    
    Returns:
        LGD ajustée (%)
    """
    # Floors par défaut
    default_floors = {
        'Sovereign': 20.0,
        'Corporate': 30.0,
        'Retail': 40.0,
        'SME': 45.0,
        'Real Estate': 25.0,
    }
    
    floors = lgd_floors or default_floors
    floor = floors.get(asset_class, 30.0)  # Défaut 30%
    
    # Appliquer floor + haircut
    lgd_downturn = max(lgd_base, floor) * (1 + haircut_stress / 100)
    
    return min(lgd_downturn, 100.0)  # Cap à 100%


# ============================================================================
# 4. EAD Projection
# ============================================================================

def project_ead(
    notional: float,
    product_type: str,
    maturity_months: int,
    horizon_months: int,
    ccf: float = 1.0,
    amortization_rate: float = 0.0,
) -> np.ndarray:
    """
    Projette EAD sur l'horizon.
    
    Args:
        notional: Notional initial
        product_type: Type de produit (Loan, Bond, Off-BS, etc.)
        maturity_months: Maturité en mois
        horizon_months: Horizon projection en mois
        ccf: Credit Conversion Factor (pour off-BS)
        amortization_rate: Taux d'amortissement annuel (%)
    
    Returns:
        Array de EAD_t pour t=1..horizon_months
    """
    t = np.arange(1, min(horizon_months, maturity_months) + 1)
    
    if product_type in ['Loan', 'Bond']:
        # Amortizing : EAD_t = Notional × (1 - amort_rate)^(t/12)
        ead_curve = notional * (1 - amortization_rate / 100) ** (t / 12.0)
    
    elif product_type in ['Off-BS', 'Commitment', 'Guarantee']:
        # Off-BS : EAD_t = Notional × CCF (constant)
        ead_curve = np.full(len(t), notional * ccf)
    
    elif product_type == 'Revolving':
        # Revolving : EAD constant (simplifié)
        ead_curve = np.full(len(t), notional)
    
    else:
        # Défaut : EAD constant
        ead_curve = np.full(len(t), notional)
    
    # Padding si horizon > maturity
    if horizon_months > maturity_months:
        padding = np.zeros(horizon_months - maturity_months)
        ead_curve = np.concatenate([ead_curve, padding])
    
    return ead_curve


# ============================================================================
# 5. Discount Factor
# ============================================================================

def compute_discount_factors(
    horizon_months: int,
    discount_rate: float,
    mode: str = 'EIR',
) -> np.ndarray:
    """
    Calcule les facteurs de discount.
    
    Args:
        horizon_months: Horizon en mois
        discount_rate: Taux de discount annuel (%)
        mode: 'EIR', 'RFR', 'Market'
    
    Returns:
        Array de DF_t pour t=1..horizon_months
    """
    t_years = np.arange(1, horizon_months + 1) / 12.0
    df_curve = 1 / (1 + discount_rate / 100) ** t_years
    
    return df_curve


# ============================================================================
# 6. ECL Calculation
# ============================================================================

def compute_ecl_single_exposure(
    notional: float,
    pd_curve: np.ndarray,
    lgd: float,
    ead_curve: np.ndarray,
    discount_factors: np.ndarray,
    stage: str,
) -> dict:
    """
    Calcule ECL pour une exposition.
    
    Args:
        notional: Notional
        pd_curve: Courbe PD (%)
        lgd: LGD (%)
        ead_curve: Courbe EAD
        discount_factors: Facteurs de discount
        stage: 'S1', 'S2', 'S3'
    
    Returns:
        {
            'ecl_amount': float,
            'ecl_12m': float,
            'ecl_lifetime': float,
            'stage': str,
        }
    """
    # Convertir PD et LGD en décimales
    pd_decimal = pd_curve / 100.0
    lgd_decimal = lgd / 100.0
    
    # ECL lifetime (tous les horizons)
    ecl_by_period = ead_curve * pd_decimal * lgd_decimal * discount_factors
    ecl_lifetime = ecl_by_period.sum()
    
    # ECL 12 mois (premiers 12 mois)
    ecl_12m = ecl_by_period[:12].sum() if len(ecl_by_period) >= 12 else ecl_by_period.sum()
    
    # ECL final selon stage
    if stage == 'S1':
        ecl_amount = ecl_12m
    else:  # S2 ou S3
        ecl_amount = ecl_lifetime
    
    return {
        'ecl_amount': float(ecl_amount),
        'ecl_12m': float(ecl_12m),
        'ecl_lifetime': float(ecl_lifetime),
        'stage': stage,
    }


# ============================================================================
# 7. Batch ECL Calculation
# ============================================================================

def compute_ecl_batch(
    exposures_df: pd.DataFrame,
    scenario_overlay: dict | None = None,
    horizon_months: int = 12,
    discount_rate: float = 5.0,
) -> pd.DataFrame:
    """
    Calcule ECL pour un batch d'expositions.
    
    Args:
        exposures_df: DataFrame avec colonnes:
            - id, notional, pd, lgd, product_type, maturity_years,
              exposure_class, ccf, dpd, forbearance, pd_origination
        scenario_overlay: Dict avec overlays (pd_shift, lgd_floors, etc.)
        horizon_months: Horizon projection (mois)
        discount_rate: Taux de discount annuel (%)
    
    Returns:
        DataFrame avec colonnes:
            - exposure_id, stage, pd_12m, pd_lifetime, lgd, ead,
              ecl_amount, ecl_12m, ecl_lifetime
    """
    results = []
    
    # Paramètres SICR depuis overlay
    sicr_abs = scenario_overlay.get('sicr_threshold_abs', 1.0) if scenario_overlay else 1.0
    sicr_rel = scenario_overlay.get('sicr_threshold_rel', 1.0) if scenario_overlay else 1.0
    backstop = scenario_overlay.get('backstop_days', 30) if scenario_overlay else 30
    
    # LGD floors depuis overlay
    lgd_floors = None
    if scenario_overlay and 'lgd_floor_by_class' in scenario_overlay:
        import json
        lgd_floors = json.loads(scenario_overlay['lgd_floor_by_class'])
    
    # Discount factors (communs à toutes les expositions)
    df_curve = compute_discount_factors(horizon_months, discount_rate)
    
    for _, exp in exposures_df.iterrows():
        # 1. Staging
        stage = determine_stage(
            pd_current=exp.get('pd', 1.0),
            pd_origination=exp.get('pd_origination', exp.get('pd', 1.0)),
            dpd=exp.get('dpd', 0),
            forbearance=exp.get('forbearance', False),
            sicr_threshold_abs=sicr_abs,
            sicr_threshold_rel=sicr_rel,
            backstop_days=backstop,
        )
        
        # 2. PD curve
        pd_curve = compute_pd_curve(
            pd_1y=exp.get('pd', 1.0),
            horizon_months=horizon_months,
            method='overlay' if scenario_overlay else 'simple',
            scenario_overlay=scenario_overlay,
        )
        
        # 3. LGD downturn
        lgd = compute_lgd_downturn(
            lgd_base=exp.get('lgd', 45.0),
            asset_class=exp.get('exposure_class', 'Corporate'),
            lgd_floors=lgd_floors,
        )
        
        # 4. EAD projection
        ead_curve = project_ead(
            notional=exp.get('notional', 0),
            product_type=exp.get('product_type', 'Loan'),
            maturity_months=int(5 * 12) if pd.isna(exp.get('maturity_years')) else int(float(exp.get('maturity_years', 5)) * 12),
            horizon_months=horizon_months,
            ccf=exp.get('ccf', 1.0),
        )
        
        # 5. ECL calculation
        ecl_result = compute_ecl_single_exposure(
            notional=exp.get('notional', 0),
            pd_curve=pd_curve,
            lgd=lgd,
            ead_curve=ead_curve,
            discount_factors=df_curve,
            stage=stage,
        )
        
        # 6. Stocker résultat
        results.append({
            'exposure_id': exp.get('id'),
            'stage': stage,
            'pd_12m': pd_curve[0] if len(pd_curve) > 0 else 0,
            'pd_lifetime': pd_curve[-1] if len(pd_curve) > 0 else 0,
            'lgd': lgd,
            'ead': ead_curve[0] if len(ead_curve) > 0 else 0,
            'ecl_amount': ecl_result['ecl_amount'],
            'ecl_12m': ecl_result['ecl_12m'],
            'ecl_lifetime': ecl_result['ecl_lifetime'],
        })
    
    return pd.DataFrame(results)

