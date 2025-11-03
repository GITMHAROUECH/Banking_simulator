"""
Banking Simulation & CRR3 Reporting - Version Complète V2
Basée sur la version ultra-simple qui fonctionne + toutes les fonctionnalités
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import random
import json
import base64
import io
import math
import logging
# Import de la page d'accueil mise à jour
try:
    from home_page import show_updated_home
except ImportError:
    def show_updated_home():
        st.error("Page d'accueil mise à jour non disponible")


# Import des fonctions de consolidation
try:
    from consolidation_complete import show_consolidation_advanced
except ImportError:
    # Fallback si le fichier n'est pas trouvé
    def show_consolidation_advanced():
        st.error("Module de consolidation non disponible")

# Import des fonctions de réconciliation
try:
    from reconciliation_complete import show_reconciliation_advanced
except ImportError:
    # Fallback si le fichier n'est pas trouvé
    def show_reconciliation_advanced():
        st.error("Module de réconciliation non disponible")

# Import des fonctions de risque de contrepartie
try:
    from counterparty_risk_functions import show_counterparty_risk_advanced
    from counterparty_risk_functions import show_counterparty_risk_advanced
    from derivatives_integration import generate_derivatives_for_simulation
except ImportError:
    # Fallback si le fichier n'est pas trouvé
    def show_counterparty_risk_advanced():
        st.error("Module de risque de contrepartie non disponible")

# Configuration de la page
st.set_page_config(
    page_title="Banking Simulation & CRR3 Reporting",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f4e79;
        padding-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4e79;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def safe_dataframe_creation(data_list, columns=None):
    """Créer un DataFrame de manière sécurisée"""
    try:
        if isinstance(data_list, list) and len(data_list) > 0:
            if isinstance(data_list[0], dict):
                # Liste de dictionnaires
                df = pd.DataFrame(data_list)
            else:
                # Liste de listes avec colonnes
                df = pd.DataFrame(data_list, columns=columns)
            return df
        else:
            # DataFrame vide avec colonnes par défaut
            default_cols = columns if columns else ['id', 'value']
            return pd.DataFrame(columns=default_cols)
    except Exception as e:
        st.error(f"Erreur création DataFrame: {e}")
        # Retourner un DataFrame minimal
        return pd.DataFrame({'id': [1], 'value': [0]})

def generate_positions_advanced(num_positions=1000, seed=42, config=None):
    """Générer des positions avancées - Version sécurisée"""
    
    random.seed(seed)
    
    # Configuration par défaut
    if config is None:
        config = {
            'base_currency': 'EUR',
            'stress_scenario': 'Baseline',
            'include_derivatives': False,
            'retail_pd_base': 0.02,
            'corporate_pd_base': 0.03
        }
    
    # Données de référence
    entities = ['EU_SUB', 'US_SUB', 'CN_SUB']
    products = [
        'Retail_Mortgages', 'Retail_Consumer', 'Retail_Credit_Cards',
        'Corporate_Loans', 'SME_Loans', 'Retail_Deposits',
        'Corporate_Deposits', 'Government_Bonds', 'Corporate_Bonds',
        'Credit_Facilities', 'Revolving_Credit_Lines', 'Overdraft_Facilities'
    ]
    
    exposure_classes = [
        'Retail_Mortgages', 'Retail_Other', 'Corporate', 'SME', 
        'Sovereign', 'Bank', 'Equity', 'Other_Items'
    ]
    
    currencies = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CNY']
    
    # Générer les positions sous forme de liste
    positions_list = []
    
    for i in range(num_positions):
        # Sélections équilibrées
        entity = entities[i % len(entities)]
        product = products[i % len(products)]
        exposure_class = exposure_classes[i % len(exposure_classes)]
        currency = currencies[i % len(currencies)]
        
        # Générer EAD avec variabilité réaliste et CCF pour facilities
        if 'Mortgage' in product:
            base_ead = 150000 + random.randint(-50000, 300000)
            ccf = 0.0  # Pas de CCF pour les prêts tirés
            commitment_amount = 0
        elif 'Corporate' in product:
            base_ead = 500000 + random.randint(-200000, 2000000)
            ccf = 0.0  # Pas de CCF pour les prêts tirés
            commitment_amount = 0
        elif 'Deposit' in product:
            base_ead = 50000 + random.randint(-30000, 200000)
            ccf = 0.0  # Pas de CCF pour les dépôts
            commitment_amount = 0
        elif 'Facilities' in product or 'Credit_Lines' in product or 'Overdraft' in product:
            # Pour les facilities : montant tiré + CCF * montant non tiré
            drawn_amount = random.randint(10000, 200000)
            commitment_amount = random.randint(50000, 500000)
            undrawn_amount = max(0, commitment_amount - drawn_amount)
            
            # CCF selon le type de facility
            if 'Credit_Facilities' in product:
                ccf = random.uniform(0.20, 0.50)  # CCF 20-50% pour facilities corporate
            elif 'Revolving' in product:
                ccf = random.uniform(0.75, 1.0)   # CCF 75-100% pour revolving
            elif 'Overdraft' in product:
                ccf = random.uniform(0.50, 0.75)  # CCF 50-75% pour overdrafts
            else:
                ccf = 0.35  # CCF par défaut
            
            base_ead = drawn_amount + (ccf * undrawn_amount)
        else:
            base_ead = 100000 + random.randint(-50000, 500000)
            ccf = 0.0
            commitment_amount = 0
        
        ead = max(1000, base_ead)
        
        # Générer PD selon le type et le stress
        if 'Retail' in exposure_class:
            base_pd = config.get('retail_pd_base', 0.02)
            pd_variation = random.uniform(-0.005, 0.015)
        elif exposure_class == 'Corporate':
            base_pd = config.get('corporate_pd_base', 0.03)
            pd_variation = random.uniform(-0.01, 0.02)
        elif exposure_class == 'SME':
            base_pd = 0.025
            pd_variation = random.uniform(-0.005, 0.02)
        elif exposure_class == 'Sovereign':
            base_pd = 0.001
            pd_variation = random.uniform(0, 0.005)
        else:
            base_pd = 0.015
            pd_variation = random.uniform(-0.005, 0.01)
        
        # Ajustement selon le scénario de stress
        if config['stress_scenario'] == 'Adverse':
            stress_multiplier = 1.5
        elif config['stress_scenario'] == 'Severely Adverse':
            stress_multiplier = 2.0
        else:
            stress_multiplier = 1.0
        
        pd = max(0.0001, (base_pd + pd_variation) * stress_multiplier)
        
        # Générer LGD selon le type de garantie
        if 'Mortgage' in product:
            lgd = 0.20 + random.uniform(0, 0.25)  # 20-45%
        elif 'Deposit' in product:
            lgd = 0.0  # Dépôts non risqués
        elif exposure_class == 'Sovereign':
            lgd = 0.45 + random.uniform(0, 0.10)  # 45-55%
        else:
            lgd = 0.35 + random.uniform(0, 0.30)  # 35-65%
        
        # Générer maturité
        if 'Mortgage' in product:
            maturity = 15 + random.uniform(0, 15)  # 15-30 ans
        elif 'Deposit' in product:
            maturity = random.uniform(0.1, 2)  # 1 mois - 2 ans
        elif 'Corporate' in product:
            maturity = 1 + random.uniform(0, 7)  # 1-8 ans
        else:
            maturity = 0.5 + random.uniform(0, 5)  # 6 mois - 5.5 ans
        
        # Classification IFRS 9
        if pd <= 0.005:
            stage = 1
        elif pd <= 0.03:
            stage = 2
        else:
            stage = 3
        
        # Calcul ECL (Expected Credit Loss)
        if stage == 1:
            # 12 mois ECL
            ecl = ead * pd * lgd
        else:
            # Lifetime ECL
            ecl = ead * pd * lgd * min(maturity, 1.0)
        
        # Taux d'intérêt
        base_rate = 0.02  # 2% de base
        if currency == 'EUR':
            currency_spread = 0.0
        elif currency == 'USD':
            currency_spread = 0.005
        elif currency == 'GBP':
            currency_spread = 0.003
        else:
            currency_spread = 0.01
        
        risk_spread = pd * 100  # Spread basé sur le risque
        interest_rate = base_rate + currency_spread + risk_spread
        
        # Revenus d'intérêts annuels
        interest_income = ead * interest_rate
        
        # Créer la position
        position = {
            'position_id': f'POS_{i+1:06d}',
            'entity_id': entity,
            'product_id': product,
            'exposure_class': exposure_class,
            'currency': currency,
            'ead': round(ead, 2),
            'pd': round(pd, 6),
            'lgd': round(lgd, 4),
            'maturity': round(maturity, 2),
            'stage': stage,
            'ecl_provision': round(ecl, 2),
            'interest_rate': round(interest_rate, 4),
            'interest_income': round(interest_income, 2),
            'booking_date': datetime.now().strftime('%Y-%m-%d'),
            'country_risk': entity.split('_')[0],
            'sector': 'Financial' if 'Bank' in exposure_class else 'Non-Financial',
            'ccf': round(ccf, 4),
            'commitment_amount': round(commitment_amount, 2),
            'drawn_amount': round(ead - (ccf * max(0, commitment_amount - ead)), 2) if ccf > 0 else round(ead, 2)
        }
        
        positions_list.append(position)
    
    # Ajouter les dérivés si demandé
    if config.get("include_derivatives", False):
        num_derivatives = config.get("num_derivatives", 500)
        derivatives_data = generate_derivatives_for_simulation(num_derivatives, entities, config)
        positions_list.extend(derivatives_data)
    # Créer le DataFrame de manière sécurisée
    return safe_dataframe_creation(positions_list)

def calculate_rwa_advanced(positions_df):
    """Calculer les RWA selon CRR3 - Version avancée"""
    
    rwa_list = []
    
    for index, row in positions_df.iterrows():
        pos_id = row['position_id']
        entity = row['entity_id']
        exposure_class = row['exposure_class']
        ead = row['ead']
        pd = row['pd']
        lgd = row['lgd']
        maturity = row['maturity']
        
        # Calcul selon l'approche CRR3
        if exposure_class in ['Retail_Mortgages', 'Retail_Other']:
            # Approche IRB Foundation pour Retail
            
            # Corrélation selon CRR3
            if exposure_class == 'Retail_Mortgages':
                correlation = 0.15
            else:
                correlation = 0.04
            
            # Calcul du capital réglementaire K
            # Formule CRR3 simplifiée
            confidence_level = 0.999  # 99.9%
            
            # Approximation de la fonction inverse normale
            z_score = 3.09  # Approximation pour 99.9%
            
            # Formule IRB
            sqrt_correlation = math.sqrt(correlation)
            sqrt_one_minus_corr = math.sqrt(1 - correlation)
            
            # Calcul simplifié du facteur de risque
            risk_factor = lgd * (pd + sqrt_correlation * z_score * math.sqrt(pd * (1 - pd)))
            
            # Ajustement maturité (si > 1 an)
            if maturity > 1:
                maturity_adjustment = (1 + (maturity - 2.5) * 0.11) / (1 + 1.5 * 0.11)
                maturity_adjustment = max(1.0, min(maturity_adjustment, 5.0))
            else:
                maturity_adjustment = 1.0
            
            # Capital requis
            k = max(0, risk_factor - pd * lgd) * maturity_adjustment
            
            # RWA = K * 12.5 * EAD
            rwa = k * 12.5 * ead
            approach = 'IRB_Foundation'
            
        elif exposure_class == 'Corporate':
            # Approche IRB Foundation pour Corporate
            
            # Corrélation selon la taille (approximation)
            firm_size_factor = min(max((ead / 1000000 - 5) / 45, 0), 1)  # 0 à 1
            correlation = 0.12 * (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)) + \
                         0.24 * (1 - (1 - math.exp(-50 * pd)) / (1 - math.exp(-50))) - \
                         0.04 * (1 - firm_size_factor)
            
            correlation = max(0.12, min(correlation, 0.24))
            
            # Calcul similaire au retail mais avec ajustements corporate
            z_score = 3.09
            sqrt_correlation = math.sqrt(correlation)
            
            risk_factor = lgd * (pd + sqrt_correlation * z_score * math.sqrt(pd * (1 - pd)))
            
            # Ajustement maturité plus complexe pour corporate
            if maturity > 1:
                b_factor = (0.11852 - 0.05478 * math.log(pd)) ** 2
                maturity_adjustment = (1 + (maturity - 2.5) * b_factor) / (1 + 1.5 * b_factor)
                maturity_adjustment = max(1.0, min(maturity_adjustment, 5.0))
            else:
                maturity_adjustment = 1.0
            
            k = max(0, risk_factor - pd * lgd) * maturity_adjustment
            rwa = k * 12.5 * ead
            approach = 'IRB_Foundation'
            
        elif exposure_class == 'SME':
            # Traitement spécial SME avec réduction de 23.81%
            # Utiliser la formule corporate puis appliquer la réduction
            correlation = 0.12 * (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)) + \
                         0.24 * (1 - (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)))
            
            z_score = 3.09
            sqrt_correlation = math.sqrt(correlation)
            risk_factor = lgd * (pd + sqrt_correlation * z_score * math.sqrt(pd * (1 - pd)))
            
            k = max(0, risk_factor - pd * lgd)
            rwa = k * 12.5 * ead * 0.7619  # Réduction de 23.81%
            approach = 'IRB_SME'
            
        elif exposure_class == 'Sovereign':
            # Approche standardisée pour souverains
            # Pondération selon la notation (simulée)
            if pd <= 0.001:
                risk_weight = 0.0  # AAA à AA-
            elif pd <= 0.005:
                risk_weight = 0.20  # A+ à A-
            elif pd <= 0.01:
                risk_weight = 0.50  # BBB+ à BBB-
            elif pd <= 0.03:
                risk_weight = 1.00  # BB+ à B-
            else:
                risk_weight = 1.50  # En dessous de B-
            
            rwa = ead * risk_weight
            approach = 'Standardised'
            
        elif exposure_class == 'Bank':
            # Approche standardisée pour banques
            if pd <= 0.002:
                risk_weight = 0.20
            elif pd <= 0.01:
                risk_weight = 0.50
            elif pd <= 0.02:
                risk_weight = 1.00
            else:
                risk_weight = 1.50
            
            rwa = ead * risk_weight
            approach = 'Standardised'
            
        else:
            # Autres expositions - approche standardisée
            risk_weight = 1.00  # 100% par défaut
            rwa = ead * risk_weight
            approach = 'Standardised'
        
        # Calculer la densité RWA
        rwa_density = (rwa / ead * 100) if ead > 0 else 0
        
        # Ajouter aux résultats
        rwa_result = {
            'position_id': pos_id,
            'entity_id': entity,
            'exposure_class': exposure_class,
            'ead': ead,
            'rwa_amount': round(rwa, 2),
            'rwa_density': round(rwa_density, 2),
            'approach': approach,
            'pd': pd,
            'lgd': lgd,
            'maturity': maturity
        }
        
        rwa_list.append(rwa_result)
    
    return safe_dataframe_creation(rwa_list)

def calculate_capital_ratios(rwa_df):
    """Calculer les ratios de capital"""
    
    total_rwa = rwa_df['rwa_amount'].sum()
    
    # Capital simulé (en millions d'EUR)
    cet1_capital = total_rwa * 0.12  # 12% CET1
    tier1_capital = total_rwa * 0.135  # 13.5% Tier 1
    total_capital = total_rwa * 0.15  # 15% Total Capital
    
    # Ratios
    cet1_ratio = (cet1_capital / total_rwa * 100) if total_rwa > 0 else 0
    tier1_ratio = (tier1_capital / total_rwa * 100) if total_rwa > 0 else 0
    total_capital_ratio = (total_capital / total_rwa * 100) if total_rwa > 0 else 0
    
    # Exigences réglementaires
    cet1_requirement = 4.5  # Pilier 1
    cet1_buffer = 2.5  # Conservation buffer
    cet1_total_requirement = cet1_requirement + cet1_buffer
    
    tier1_requirement = 6.0
    tier1_buffer = 2.5
    tier1_total_requirement = tier1_requirement + tier1_buffer
    
    total_requirement = 8.0
    total_buffer = 2.5
    total_total_requirement = total_requirement + total_buffer
    
    capital_ratios = {
        'total_rwa': total_rwa,
        'cet1_capital': cet1_capital,
        'tier1_capital': tier1_capital,
        'total_capital': total_capital,
        'cet1_ratio': cet1_ratio,
        'tier1_ratio': tier1_ratio,
        'total_capital_ratio': total_capital_ratio,
        'cet1_requirement': cet1_total_requirement,
        'tier1_requirement': tier1_total_requirement,
        'total_requirement': total_total_requirement,
        'cet1_surplus': cet1_ratio - cet1_total_requirement,
        'tier1_surplus': tier1_ratio - tier1_total_requirement,
        'total_surplus': total_capital_ratio - total_total_requirement
    }
    
    return capital_ratios

def calculate_liquidity_advanced(positions_df):
    """Calculer les ratios de liquidité avancés"""
    
    entities = positions_df['entity_id'].unique()
    
    lcr_results = []
    nsfr_results = []
    almm_results = []
    
    for entity in entities:
        entity_positions = positions_df[positions_df['entity_id'] == entity]
        
        if len(entity_positions) == 0:
            continue
        
        # === LCR (Liquidity Coverage Ratio) ===
        
        # HQLA (High Quality Liquid Assets)
        total_assets = entity_positions['ead'].sum()
        
        # Level 1 HQLA (100% eligible)
        level1_hqla = total_assets * 0.10  # 10% en obligations souveraines
        
        # Level 2A HQLA (85% eligible)
        level2a_hqla = total_assets * 0.05 * 0.85  # 5% en obligations corporate AA
        
        # Level 2B HQLA (50% eligible, max 15% du total)
        level2b_hqla = min(total_assets * 0.03 * 0.50, (level1_hqla + level2a_hqla) * 0.15)
        
        total_hqla = level1_hqla + level2a_hqla + level2b_hqla
        
        # Sorties de trésorerie (30 jours)
        retail_deposits = entity_positions[entity_positions['product_id'].str.contains('Retail_Deposit', na=False)]['ead'].sum()
        corporate_deposits = entity_positions[entity_positions['product_id'].str.contains('Corporate_Deposit', na=False)]['ead'].sum()
        
        # Taux de sortie selon CRR
        retail_outflow = retail_deposits * 0.05  # 5% pour dépôts retail stables
        corporate_outflow = corporate_deposits * 0.25  # 25% pour dépôts corporate
        
        # Autres sorties (lignes de crédit, dérivés, etc.)
        other_outflows = total_assets * 0.03  # 3% autres engagements
        
        total_outflows = retail_outflow + corporate_outflow + other_outflows
        
        # Entrées de trésorerie (plafonnées à 75% des sorties)
        loan_repayments = entity_positions[entity_positions['product_id'].str.contains('Loan', na=False)]['ead'].sum() * 0.02  # 2% remboursements mensuels
        total_inflows = min(loan_repayments, total_outflows * 0.75)
        
        net_cash_outflows = max(total_outflows - total_inflows, total_assets * 0.05)  # Minimum 5%
        
        lcr_ratio = (total_hqla / net_cash_outflows * 100) if net_cash_outflows > 0 else 200
        
        lcr_result = {
            'entity_id': entity,
            'total_hqla': round(total_hqla, 2),
            'level1_hqla': round(level1_hqla, 2),
            'level2a_hqla': round(level2a_hqla, 2),
            'level2b_hqla': round(level2b_hqla, 2),
            'total_outflows': round(total_outflows, 2),
            'total_inflows': round(total_inflows, 2),
            'net_cash_outflows': round(net_cash_outflows, 2),
            'lcr_ratio': round(lcr_ratio, 1),
            'lcr_surplus': round(lcr_ratio - 100, 1)
        }
        
        lcr_results.append(lcr_result)
        
        # === NSFR (Net Stable Funding Ratio) ===
        
        # Available Stable Funding (ASF)
        
        # Capital et instruments de capital
        regulatory_capital = total_assets * 0.12  # 12% capital réglementaire
        asf_capital = regulatory_capital * 1.0  # 100% ASF
        
        # Dépôts retail
        asf_retail_deposits = retail_deposits * 0.95  # 95% ASF pour dépôts retail stables
        
        # Dépôts corporate
        asf_corporate_deposits = corporate_deposits * 0.50  # 50% ASF pour dépôts corporate
        
        # Financement wholesale > 1 an
        wholesale_funding = total_assets * 0.20  # 20% financement wholesale
        asf_wholesale = wholesale_funding * 0.100  # 100% ASF si > 1 an
        
        total_asf = asf_capital + asf_retail_deposits + asf_corporate_deposits + asf_wholesale
        
        # Required Stable Funding (RSF)
        
        # HQLA
        rsf_hqla = total_hqla * 0.05  # 5% RSF pour HQLA
        
        # Prêts hypothécaires
        mortgages = entity_positions[entity_positions['product_id'].str.contains('Mortgage', na=False)]['ead'].sum()
        rsf_mortgages = mortgages * 0.65  # 65% RSF
        
        # Prêts retail autres
        retail_loans = entity_positions[
            (entity_positions['product_id'].str.contains('Retail', na=False)) & 
            (~entity_positions['product_id'].str.contains('Mortgage', na=False)) &
            (~entity_positions['product_id'].str.contains('Deposit', na=False))
        ]['ead'].sum()
        rsf_retail_loans = retail_loans * 0.85  # 85% RSF
        
        # Prêts corporate
        corporate_loans = entity_positions[entity_positions['product_id'].str.contains('Corporate_Loan', na=False)]['ead'].sum()
        rsf_corporate_loans = corporate_loans * 1.00  # 100% RSF
        
        # Autres actifs
        other_assets = total_assets - total_hqla - mortgages - retail_loans - corporate_loans
        rsf_other = other_assets * 1.00  # 100% RSF par défaut
        
        total_rsf = rsf_hqla + rsf_mortgages + rsf_retail_loans + rsf_corporate_loans + rsf_other
        
        nsfr_ratio = (total_asf / total_rsf * 100) if total_rsf > 0 else 150
        
        nsfr_result = {
            'entity_id': entity,
            'total_asf': round(total_asf, 2),
            'asf_capital': round(asf_capital, 2),
            'asf_retail_deposits': round(asf_retail_deposits, 2),
            'asf_corporate_deposits': round(asf_corporate_deposits, 2),
            'asf_wholesale': round(asf_wholesale, 2),
            'total_rsf': round(total_rsf, 2),
            'rsf_hqla': round(rsf_hqla, 2),
            'rsf_mortgages': round(rsf_mortgages, 2),
            'rsf_retail_loans': round(rsf_retail_loans, 2),
            'rsf_corporate_loans': round(rsf_corporate_loans, 2),
            'nsfr_ratio': round(nsfr_ratio, 1),
            'nsfr_surplus': round(nsfr_ratio - 100, 1)
        }
        
        nsfr_results.append(nsfr_result)
        
        # === ALMM (Asset Liability Maturity Mismatch) ===
        
        # Gaps de maturité par buckets
        maturity_buckets = {
            '0-1M': (0, 1/12),
            '1-3M': (1/12, 3/12),
            '3-6M': (3/12, 6/12),
            '6-12M': (6/12, 1),
            '1-2Y': (1, 2),
            '2-5Y': (2, 5),
            '5Y+': (5, float('inf'))
        }
        
        almm_gaps = {}
        
        for bucket_name, (min_mat, max_mat) in maturity_buckets.items():
            # Actifs dans ce bucket
            assets_in_bucket = entity_positions[
                (entity_positions['maturity'] >= min_mat) & 
                (entity_positions['maturity'] < max_mat)
            ]['ead'].sum()
            
            # Passifs dans ce bucket (approximation)
            # Les dépôts sont généralement court terme
            if bucket_name in ['0-1M', '1-3M']:
                liabilities_in_bucket = (retail_deposits + corporate_deposits) * 0.4
            elif bucket_name in ['3-6M', '6-12M']:
                liabilities_in_bucket = (retail_deposits + corporate_deposits) * 0.3
            else:
                liabilities_in_bucket = (retail_deposits + corporate_deposits) * 0.1
            
            gap = assets_in_bucket - liabilities_in_bucket
            almm_gaps[bucket_name] = round(gap, 2)
        
        # Gap cumulé
        cumulative_gap = 0
        almm_cumulative = {}
        for bucket_name in maturity_buckets.keys():
            cumulative_gap += almm_gaps[bucket_name]
            almm_cumulative[bucket_name] = round(cumulative_gap, 2)
        
        almm_result = {
            'entity_id': entity,
            'gaps': almm_gaps,
            'cumulative_gaps': almm_cumulative,
            'total_assets': round(total_assets, 2),
            'total_liabilities': round(retail_deposits + corporate_deposits, 2)
        }
        
        almm_results.append(almm_result)
    
    return (safe_dataframe_creation(lcr_results), 
            safe_dataframe_creation(nsfr_results), 
            almm_results)

def create_excel_export_advanced(positions_df, rwa_df, lcr_df, nsfr_df, capital_ratios):
    """Créer un export Excel avancé avec plusieurs feuilles"""
    
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Feuille de synthèse
            summary_data = {
                'Métrique': [
                    'Nombre de positions',
                    'EAD totale (EUR)',
                    'RWA total (EUR)',
                    'Ratio CET1 (%)',
                    'Ratio Tier 1 (%)',
                    'Ratio Total Capital (%)',
                    'LCR moyen (%)',
                    'NSFR moyen (%)'
                ],
                'Valeur': [
                    f"{len(positions_df):,}",
                    f"{positions_df['ead'].sum():,.0f}",
                    f"{rwa_df['rwa_amount'].sum():,.0f}",
                    f"{capital_ratios['cet1_ratio']:.1f}",
                    f"{capital_ratios['tier1_ratio']:.1f}",
                    f"{capital_ratios['total_capital_ratio']:.1f}",
                    f"{lcr_df['lcr_ratio'].mean():.1f}" if len(lcr_df) > 0 else "N/A",
                    f"{nsfr_df['nsfr_ratio'].mean():.1f}" if len(nsfr_df) > 0 else "N/A"
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Synthese', index=False)
            
            # Positions détaillées
            positions_df.to_excel(writer, sheet_name='Positions', index=False)
            
            # RWA détaillés
            rwa_df.to_excel(writer, sheet_name='RWA', index=False)
            
            # Ratios de capital
            capital_df = pd.DataFrame([capital_ratios])
            capital_df.to_excel(writer, sheet_name='Capital_Ratios', index=False)
            
            # LCR
            if len(lcr_df) > 0:
                lcr_df.to_excel(writer, sheet_name='LCR', index=False)
            
            # NSFR
            if len(nsfr_df) > 0:
                nsfr_df.to_excel(writer, sheet_name='NSFR', index=False)
            
            # Résumé par entité
            entity_summary = positions_df.groupby('entity_id').agg({
                'ead': 'sum',
                'ecl_provision': 'sum',
                'interest_income': 'sum'
            }).reset_index()
            
            entity_summary.columns = ['Entité', 'EAD Total', 'Provisions ECL', 'Revenus Intérêts']
            entity_summary.to_excel(writer, sheet_name='Resume_Entites', index=False)
            
            # Résumé par produit
            product_summary = positions_df.groupby('product_id').agg({
                'ead': 'sum',
                'pd': 'mean',
                'lgd': 'mean'
            }).reset_index()
            
            product_summary.columns = ['Produit', 'EAD Total', 'PD Moyenne', 'LGD Moyenne']
            product_summary.to_excel(writer, sheet_name='Resume_Produits', index=False)
        
        excel_data = output.getvalue()
        return excel_data
        
    except Exception as e:
        st.error(f"Erreur création Excel: {e}")
        return None

def create_download_link(data, filename, link_text):
    """Créer un lien de téléchargement"""
    if data is not None:
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{link_text}</a>'
        return href
    return "Erreur de génération"

def main():
    """Fonction principale de l'application"""
    
    # En-tête principal
    st.markdown('<h1 class="main-header">🏦 Banking Simulation & CRR3 Reporting - Version Complète</h1>', unsafe_allow_html=True)
    
    # Sidebar pour la navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choisir une section",
        [
            "🏠 Accueil",
            "⚙️ Configuration Avancée",
            "📊 Simulation Monte Carlo",
            "🔄 Consolidation IFRS",
            "🔍 Réconciliation Compta-Risque",
            "⚠️ Risque de Crédit CRR3",
            "💧 Liquidité (LCR/NSFR/ALMM)",
            "🏛️ Ratios de Capital",
            "📈 Reporting Réglementaire",
            "📥 Export Excel Avancé",
            "📋 Templates & Import",
            "ℹ️ Documentation CRR3"
        ]
    )
    
    # Routage des pages
    if page == "🏠 Accueil":
        show_updated_home()
    elif page == "⚙️ Configuration Avancée":
        show_configuration_advanced()
    elif page == "📊 Simulation Monte Carlo":
        show_simulation_advanced()
    elif page == "🔄 Consolidation IFRS":
        show_consolidation_advanced()
    elif page == "🔍 Réconciliation Compta-Risque":
        show_reconciliation_advanced()
    elif page == "⚠️ Risque de Crédit CRR3":
        show_credit_risk_advanced()
    elif page == "💧 Liquidité (LCR/NSFR/ALMM)":
        show_liquidity_advanced()
    elif page == "🏛️ Ratios de Capital":
        show_capital_ratios()
    elif page == "📈 Reporting Réglementaire":
        show_reporting_advanced()
    elif page == "📥 Export Excel Avancé":
        show_export_advanced()
    elif page == "📋 Templates & Import":
        show_templates_import()
    elif page == "ℹ️ Documentation CRR3":
        show_documentation_advanced()

def show_home_advanced():
    """Page d'accueil avancée"""
    st.markdown("## Bienvenue dans l'application de simulation bancaire CRR3")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Fonctionnalités Avancées
        
        Cette application implémente les dernières réglementations bancaires européennes :
        
        - **🔬 Simulation Monte Carlo** : Génération de milliers de positions réalistes
        - **⚖️ Calculs RWA CRR3** : Approches IRB et standardisée conformes
        - **💧 Ratios de liquidité** : LCR, NSFR et ALMM selon Bâle III
        - **🏛️ Ratios de capital** : CET1, Tier 1, Total Capital avec buffers
        - **📊 Comptabilité IFRS 9** : Classification par stages et provisions ECL
        - **🌍 Multi-devises** : Support EUR, USD, GBP, JPY, CHF, CNY
        - **📈 Reporting réglementaire** : Templates FINREP, COREP, RUBA
        - **📥 Export Excel** : Fichiers multi-feuilles détaillés
        """)
    
    with col2:
        st.markdown("""
        ### 📋 Workflow Réglementaire
        
        **Phase 1 : Configuration**
        - Paramètres de simulation (nombre, graine, scénarios)
        - Facteurs de risque par classe d'exposition
        - Scénarios de stress (Baseline, Adverse, Severely Adverse)
        
        **Phase 2 : Simulation**
        - Génération des positions bancaires
        - Attribution des paramètres de risque (PD, LGD, EAD)
        - Classification IFRS 9 (Stages 1, 2, 3)
        
        **Phase 3 : Consolidation**
        - Élimination des opérations intragroupes
        - Génération du bilan consolidé
        - Calcul des intérêts minoritaires
        
        **Phase 4 : Réconciliation**
        - **🔍 Contrôle qualité comptabilité-risque**
        - Détection et analyse des écarts
        - Investigation des différences matérielles
        - Plan d'action correctif
        
        **Phase 5 : Calculs Réglementaires**
        - RWA selon approches CRR3
        - Ratios de capital avec buffers
        - Ratios de liquidité LCR/NSFR
        
        **Phase 6 : Reporting**
        - Génération des rapports réglementaires
        - Export Excel multi-feuilles
        - Analyse de conformité
        """)
    
    # Métriques de démonstration avancées
    st.markdown("### 📊 Capacités de l'application")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Entités simulées", "3", "EU, US, CN")
        st.metric("Classes d'exposition", "8", "Retail, Corporate, SME, etc.")
    
    with col2:
        st.metric("Produits financiers", "9", "Prêts, Dépôts, Obligations")
        st.metric("Devises supportées", "6", "EUR, USD, GBP, JPY, CHF, CNY")
    
    with col3:
        st.metric("Positions max", "5,000", "Simulation Monte Carlo")
        st.metric("Approches RWA", "3", "IRB Foundation, IRB SME, Standardisée")
    
    with col4:
        st.metric("Ratios calculés", "10+", "Capital, Liquidité, Levier")
        st.metric("Conformité", "CRR3 2024", "Dernière réglementation")
    
    # Guide de démarrage avancé
    st.markdown("### 🚀 Guide de démarrage avancé")
    
    with st.expander("📖 Étapes détaillées"):
        st.markdown("""
        #### 1. Configuration Avancée
        - **Scénario de base** : Définir le nom, la graine aléatoire, le nombre de positions
        - **Paramètres de risque** : Ajuster les PD de base par classe d'exposition
        - **Scénario de stress** : Choisir Baseline, Adverse ou Severely Adverse
        - **Options avancées** : Inclure les dérivés, ajuster les facteurs de liquidité
        
        #### 2. Simulation Monte Carlo
        - **Génération** : Créer les positions avec paramètres réalistes
        - **Diversification** : Répartition équilibrée par entité, produit, devise
        - **Cohérence** : Corrélations entre PD, LGD et maturité
        - **IFRS 9** : Classification automatique par stages
        
        #### 3. Calculs RWA CRR3
        - **IRB Foundation** : Retail et Corporate avec corrélations réglementaires
        - **IRB SME** : Réduction de 23.81% pour les PME
        - **Standardisée** : Souverains et banques selon pondérations CRR
        - **Ajustements** : Maturité, taille d'entreprise, garanties
        
        #### 4. Ratios de Liquidité
        - **LCR** : HQLA Level 1/2A/2B, sorties/entrées 30 jours
        - **NSFR** : ASF/RSF par catégorie d'actifs et passifs
        - **ALMM** : Gaps de maturité par buckets temporels
        
        #### 5. Ratios de Capital
        - **CET1** : Capital de base avec exigences Pilier 1 + buffers
        - **Tier 1** : Capital de première catégorie
        - **Total Capital** : Capital total réglementaire
        - **Ratio de levier** : Exposition totale vs Tier 1
        
        #### 6. Reporting Réglementaire
        - **Synthèse exécutive** : KPI et conformité
        - **Détails par entité** : Ventilation géographique
        - **Analyse de sensibilité** : Impact des scénarios de stress
        - **Recommandations** : Actions correctives si nécessaire
        
        #### 7. Export et Documentation
        - **Excel multi-feuilles** : Données détaillées et synthèses
        - **Templates d'import** : Fichiers pour données réelles
        - **Documentation** : Références réglementaires et formules
        """)
    
    # Avertissements réglementaires
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Application de démonstration réglementaire :</strong><br>
    Cette application implémente les formules CRR3 à des fins éducatives et de formation. 
    Elle ne constitue pas un système de calcul réglementaire certifié et ne doit pas être utilisée 
    pour des déclarations officielles aux autorités de supervision sans validation appropriée par des experts.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>ℹ️ Conformité CRR3 :</strong><br>
    Les calculs sont basés sur le Règlement (UE) 2024/1623 (CRR3) et les Guidelines EBA. 
    Les formules IRB, les pondérations standardisées et les ratios de liquidité suivent les spécifications officielles.
    </div>
    """, unsafe_allow_html=True)

def show_configuration_advanced():
    """Page de configuration avancée"""
    st.markdown("## ⚙️ Configuration Avancée de la Simulation")
    
    st.markdown("### 🎛️ Paramètres de Base")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scenario_name = st.text_input("Nom du scénario", value="CRR3_Simulation_2024")
        scenario_seed = st.number_input("Graine aléatoire", value=42, min_value=1, max_value=9999)
        num_positions = st.number_input("Nombre de positions", value=2000, min_value=100, max_value=5000)
    
    with col2:
        base_currency = st.selectbox("Devise de base", ["EUR", "USD", "GBP"], index=0)
        stress_scenario = st.selectbox(
            "Scénario de stress", 
            ["Baseline", "Adverse", "Severely Adverse"], 
            index=0,
            help="Baseline: conditions normales, Adverse: récession modérée, Severely Adverse: crise majeure"
        )
        include_derivatives = st.checkbox("Inclure les dérivés", value=False)
        if include_derivatives:
            num_derivatives = st.number_input("Nombre de dérivés", value=500, min_value=50, max_value=2000)
    
    with col3:
        reporting_date = st.date_input("Date de reporting", value=date.today())
        consolidation_level = st.selectbox("Niveau de consolidation", ["Individual", "Consolidated"], index=1)
        use_ifrs9 = st.checkbox("Appliquer IFRS 9", value=True)
    
    # Paramètres de risque avancés
    st.markdown("### ⚠️ Paramètres de Risque par Classe d'Exposition")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Retail**")
        retail_mortgage_pd = st.slider("PD Retail Mortgages (%)", 0.1, 5.0, 1.5) / 100
        retail_other_pd = st.slider("PD Retail Other (%)", 0.5, 8.0, 3.0) / 100
        retail_lgd = st.slider("LGD Retail (%)", 20, 60, 35) / 100
        
        st.markdown("**Corporate**")
        corporate_pd = st.slider("PD Corporate (%)", 0.2, 10.0, 2.5) / 100
        corporate_lgd = st.slider("LGD Corporate (%)", 30, 70, 45) / 100
    
    with col2:
        st.markdown("**SME**")
        sme_pd = st.slider("PD SME (%)", 0.5, 12.0, 4.0) / 100
        sme_lgd = st.slider("LGD SME (%)", 35, 65, 50) / 100
        
        st.markdown("**Sovereign/Bank**")
        sovereign_pd = st.slider("PD Sovereign (%)", 0.01, 2.0, 0.1) / 100
        bank_pd = st.slider("PD Bank (%)", 0.1, 5.0, 1.0) / 100
    
    # Paramètres de liquidité avancés
    st.markdown("### 💧 Paramètres de Liquidité")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**HQLA**")
        level1_hqla_ratio = st.slider("Ratio Level 1 HQLA (%)", 5, 20, 10) / 100
        level2a_hqla_ratio = st.slider("Ratio Level 2A HQLA (%)", 2, 10, 5) / 100
        level2b_hqla_ratio = st.slider("Ratio Level 2B HQLA (%)", 1, 5, 3) / 100
    
    with col2:
        st.markdown("**Taux de Sortie LCR**")
        retail_deposit_outflow = st.slider("Sortie Dépôts Retail (%)", 3, 10, 5) / 100
        corporate_deposit_outflow = st.slider("Sortie Dépôts Corporate (%)", 15, 40, 25) / 100
        wholesale_outflow = st.slider("Sortie Wholesale (%)", 50, 100, 75) / 100
    
    with col3:
        st.markdown("**Facteurs NSFR**")
        retail_deposit_asf = st.slider("ASF Dépôts Retail (%)", 85, 100, 95) / 100
        corporate_deposit_asf = st.slider("ASF Dépôts Corporate (%)", 40, 70, 50) / 100
        mortgage_rsf = st.slider("RSF Mortgages (%)", 50, 85, 65) / 100
    
    # Paramètres de capital avancés
    st.markdown("### 🏛️ Paramètres de Capital")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Ratios Cibles**")
        target_cet1 = st.slider("CET1 Ratio Cible (%)", 8, 16, 12) / 100
        target_tier1 = st.slider("Tier 1 Ratio Cible (%)", 10, 18, 14) / 100
        target_total = st.slider("Total Capital Ratio Cible (%)", 12, 20, 15) / 100
    
    with col2:
        st.markdown("**Buffers Additionnels**")
        conservation_buffer = st.slider("Conservation Buffer (%)", 2.0, 3.0, 2.5) / 100
        countercyclical_buffer = st.slider("Countercyclical Buffer (%)", 0.0, 2.5, 0.0) / 100
        systemic_buffer = st.slider("Systemic Buffer (%)", 0.0, 3.5, 1.0) / 100
    
    with col3:
        st.markdown("**Autres Ratios**")
        leverage_ratio_target = st.slider("Leverage Ratio Cible (%)", 3.0, 5.0, 3.5) / 100
        mrel_target = st.slider("MREL Cible (%)", 16, 24, 18) / 100
    
    # Scénarios de stress avancés
    st.markdown("### 📈 Scénarios de Stress Avancés")
    
    with st.expander("⚙️ Paramètres de stress personnalisés"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Multipliers PD par Scénario**")
            baseline_pd_mult = st.number_input("Baseline PD Multiplier", value=1.0, min_value=0.5, max_value=2.0)
            adverse_pd_mult = st.number_input("Adverse PD Multiplier", value=1.5, min_value=1.0, max_value=3.0)
            severe_pd_mult = st.number_input("Severely Adverse PD Multiplier", value=2.5, min_value=1.5, max_value=5.0)
        
        with col2:
            st.markdown("**Chocs de Liquidité**")
            adverse_lcr_shock = st.slider("Choc LCR Adverse (%)", -30, 0, -15) / 100
            severe_lcr_shock = st.slider("Choc LCR Severely Adverse (%)", -50, -20, -30) / 100
            deposit_flight_shock = st.slider("Choc Fuite Dépôts (%)", 0, 50, 20) / 100
    
    # Sauvegarde de la configuration
    if st.button("💾 Sauvegarder la Configuration Avancée", type="primary"):
        config = {
            # Base
            'scenario_name': scenario_name,
            'scenario_seed': scenario_seed,
            'num_positions': num_positions,
            'base_currency': base_currency,
            'stress_scenario': stress_scenario,
            'include_derivatives': include_derivatives,
            'reporting_date': reporting_date.isoformat(),
            'consolidation_level': consolidation_level,
            'use_ifrs9': use_ifrs9,
            
            # Risque
            'retail_mortgage_pd': retail_mortgage_pd,
            'retail_other_pd': retail_other_pd,
            'retail_lgd': retail_lgd,
            'corporate_pd': corporate_pd,
            'corporate_lgd': corporate_lgd,
            'sme_pd': sme_pd,
            'sme_lgd': sme_lgd,
            'sovereign_pd': sovereign_pd,
            'bank_pd': bank_pd,
            
            # Liquidité
            'level1_hqla_ratio': level1_hqla_ratio,
            'level2a_hqla_ratio': level2a_hqla_ratio,
            'level2b_hqla_ratio': level2b_hqla_ratio,
            'retail_deposit_outflow': retail_deposit_outflow,
            'corporate_deposit_outflow': corporate_deposit_outflow,
            'wholesale_outflow': wholesale_outflow,
            'retail_deposit_asf': retail_deposit_asf,
            'corporate_deposit_asf': corporate_deposit_asf,
            'mortgage_rsf': mortgage_rsf,
            
            # Capital
            'target_cet1': target_cet1,
            'target_tier1': target_tier1,
            'target_total': target_total,
            'conservation_buffer': conservation_buffer,
            'countercyclical_buffer': countercyclical_buffer,
            'systemic_buffer': systemic_buffer,
            'leverage_ratio_target': leverage_ratio_target,
            'mrel_target': mrel_target,
            
            # Stress
            'baseline_pd_mult': baseline_pd_mult,
            'adverse_pd_mult': adverse_pd_mult,
            'severe_pd_mult': severe_pd_mult,
            'adverse_lcr_shock': adverse_lcr_shock,
            'severe_lcr_shock': severe_lcr_shock,
            'deposit_flight_shock': deposit_flight_shock
        }
        
        st.session_state['advanced_config'] = config
        st.success("✅ Configuration avancée sauvegardée avec succès!")
        
        with st.expander("Voir la configuration complète"):
            st.json(config)
    
    # Configuration par défaut
    if st.button("🔄 Charger Configuration par Défaut"):
        default_config = {
            'scenario_name': 'CRR3_Simulation_2024',
            'scenario_seed': 42,
            'num_positions': 2000,
            'base_currency': 'EUR',
            'stress_scenario': 'Baseline',
            'include_derivatives': False,
            'retail_mortgage_pd': 0.015,
            'corporate_pd': 0.025,
            'target_cet1': 0.12,
            'target_tier1': 0.135,
            'target_total': 0.15
        }
        
        st.session_state['advanced_config'] = default_config
        st.info("ℹ️ Configuration par défaut chargée. Actualisez la page pour voir les valeurs.")

def show_simulation_advanced():
    """Page de simulation avancée"""
    st.markdown("## 📊 Simulation Monte Carlo Avancée")
    
    # Configuration par défaut si pas encore définie
    if 'advanced_config' not in st.session_state:
        st.session_state['advanced_config'] = {
            'scenario_name': 'Scénario par Défaut',
            'num_positions': 1000,
            'scenario_seed': 42,
            'base_currency': 'EUR',
            'stress_scenario': 'Baseline',
            'include_derivatives': False,
            'retail_pd_base': 0.02,
            'corporate_pd_base': 0.03,
            'retail_mortgage_pd': 0.015,
            'retail_other_pd': 0.03,
            'corporate_pd': 0.025,
            'sme_pd': 0.04,
            'sovereign_pd': 0.001,
            'bank_pd': 0.01
        }
    config = st.session_state['advanced_config']
    
    # Afficher les paramètres de simulation
    st.markdown("### 🎛️ Paramètres de Simulation")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Scénario", config['scenario_name'])
        st.metric("Positions", f"{config['num_positions']:,}")
    
    with col2:
        st.metric("Devise Base", config['base_currency'])
        st.metric("Stress", config['stress_scenario'])
    
    with col3:
        st.metric("Graine", config['scenario_seed'])
        st.metric("Dérivés", "Oui" if config.get('include_derivatives', False) else "Non")
    
    with col4:
        st.metric("PD Retail", f"{config.get('retail_mortgage_pd', 0.015):.2%}")
        st.metric("PD Corporate", f"{config.get('corporate_pd', 0.025):.2%}")
    
    # Simulation avancée
    if st.button("🚀 Lancer la Simulation Monte Carlo", type="primary"):
        with st.spinner("Simulation Monte Carlo en cours..."):
            try:
                # Générer les positions avec la configuration avancée
                positions = generate_positions_advanced(
                    num_positions=config['num_positions'],
                    seed=config['scenario_seed'],
                    config=config
                )
                
                st.session_state['advanced_positions'] = positions
                st.success(f"🎉 Simulation terminée ! {len(positions)} positions générées avec succès.")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la simulation: {str(e)}")
                st.error("Détails de l'erreur pour le débogage:")
                st.code(str(e))
                return
    
    # Afficher les résultats avancés
    if 'advanced_positions' in st.session_state:
        positions = st.session_state['advanced_positions']
        
        st.markdown("### 📊 Résultats de la Simulation Monte Carlo")
        
        # Métriques avancées
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_ead = positions['ead'].sum()
            st.metric("EAD Total", f"{total_ead:,.0f} {config['base_currency']}")
        
        with col2:
            avg_pd = positions['pd'].mean()
            st.metric("PD Moyenne", f"{avg_pd:.3%}")
        
        with col3:
            total_ecl = positions['ecl_provision'].sum()
            st.metric("Provisions ECL", f"{total_ecl:,.0f} {config['base_currency']}")
        
        with col4:
            total_interest = positions['interest_income'].sum()
            st.metric("Revenus Intérêts", f"{total_interest:,.0f} {config['base_currency']}")
        
        with col5:
            num_positions = len(positions)
            st.metric("Positions", f"{num_positions:,}")
        
        # Analyses avancées
        st.markdown("### 📈 Analyses Détaillées")
        
        # Répartition par entité et devise
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Répartition par Entité")
            entity_summary = positions.groupby('entity_id').agg({
                'ead': 'sum',
                'ecl_provision': 'sum',
                'interest_income': 'sum'
            }).reset_index()
            
            fig = px.pie(entity_summary, values='ead', names='entity_id', 
                       title="EAD par Entité")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Répartition par Devise")
            currency_summary = positions.groupby('currency').agg({
                'ead': 'sum'
            }).reset_index()
            
            fig = px.bar(currency_summary, x='currency', y='ead',
                       title="EAD par Devise", color='currency')
            st.plotly_chart(fig, use_container_width=True)
        
        # Répartition par classe d'exposition et produit
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### EAD par Classe d'Exposition")
            exposure_summary = positions.groupby('exposure_class')['ead'].sum().reset_index()
            
            fig = px.bar(exposure_summary, x='exposure_class', y='ead',
                       title="EAD par Classe d'Exposition", color='exposure_class')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### EAD par Produit")
            product_summary = positions.groupby('product_id')['ead'].sum().reset_index()
            
            fig = px.bar(product_summary, x='product_id', y='ead',
                       title="EAD par Produit", color='product_id')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Distribution des paramètres de risque
        st.markdown("#### 📊 Distribution des Paramètres de Risque")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig = px.histogram(positions, x='pd', nbins=50, 
                             title="Distribution des PD")
            fig.update_layout(xaxis_title="Probability of Default")
            fig.update_layout(yaxis_title="Nombre de Positions")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(positions, x='lgd', nbins=50,
                             title="Distribution des LGD")
            fig.update_layout(xaxis_title="Loss Given Default")
            fig.update_layout(yaxis_title="Nombre de Positions")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            fig = px.histogram(positions, x='maturity', nbins=50,
                             title="Distribution des Maturités")
            fig.update_layout(xaxis_title="Maturité (années)")
            fig.update_layout(yaxis_title="Nombre de Positions")
            st.plotly_chart(fig, use_container_width=True)
        
        # Analyse spécifique des dérivés si inclus
        derivatives_positions = positions[positions["product_id"].str.contains("Derivative", na=False)]
        if not derivatives_positions.empty:
            st.markdown("#### ⚡ Analyse des Produits Dérivés")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_notional = derivatives_positions["commitment_amount"].sum()
                st.metric("Notionnel Total", f"{total_notional:,.0f} EUR")
            
            with col2:
                total_mtm = derivatives_positions.get("mtm_value", pd.Series([0])).sum()
                st.metric("MTM Total", f"{total_mtm:,.0f} EUR")
            
            with col3:
                total_cva = derivatives_positions.get("cva_charge", pd.Series([0])).sum()
                st.metric("Charge CVA", f"{total_mtm:,.0f} EUR")
            
            with col4:
                num_derivatives = len(derivatives_positions)
                st.metric("Nombre Dérivés", f"{num_derivatives:,}")
            
            # Graphiques spécifiques aux dérivés
            col1, col2 = st.columns(2)
            
            with col1:
                if "derivative_type" in derivatives_positions.columns:
                    derivative_summary = derivatives_positions.groupby("derivative_type")["commitment_amount"].sum().reset_index()
                    fig = px.pie(derivative_summary, values="commitment_amount", names="derivative_type",
                               title="Répartition du Notionnel par Type de Dérivé")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if "counterparty_rating" in derivatives_positions.columns:
                    rating_summary = derivatives_positions.groupby("counterparty_rating")["ead"].sum().reset_index()
                    fig = px.bar(rating_summary, x="counterparty_rating", y="ead",
                               title="EAD par Rating de Contrepartie", color="counterparty_rating")
                    st.plotly_chart(fig, use_container_width=True)

        # Classification IFRS 9
        st.markdown("#### 🏷️ Classification IFRS 9")
        
        stage_summary = positions.groupby('stage').agg({
            'ead': ['count', 'sum'],
            'ecl_provision': 'sum'
        }).round(2)
        
        stage_summary.columns = ['Nombre', 'EAD Total', 'Provisions ECL']
        stage_summary = stage_summary.reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(stage_summary, values='Nombre', names='stage',
                       title="Répartition par Stage IFRS 9 (Nombre)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(stage_summary, x='stage', y='EAD Total',
                       title="EAD par Stage IFRS 9", color='stage')
            st.plotly_chart(fig, use_container_width=True)
        
        # Tableau de synthèse par stage
        st.markdown("#### 📋 Synthèse par Stage IFRS 9")
        
        stage_summary['Pourcentage'] = (stage_summary['Nombre'] / stage_summary['Nombre'].sum() * 100).round(1)
        stage_summary['Taux de Provision'] = (stage_summary['Provisions ECL'] / stage_summary['EAD Total'] * 100).round(2)
        
        st.dataframe(stage_summary, use_container_width=True)
        
        # Analyse des Facilities et CCF
        st.markdown("#### 🏦 Analyse des Facilities et CCF")
        
        # Filtrer les facilities
        facilities = positions[positions['ccf'] > 0]
        
        if len(facilities) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Nombre de Facilities", len(facilities))
                st.metric("CCF Moyen", f"{facilities['ccf'].mean():.2%}")
            
            with col2:
                total_commitment = facilities['commitment_amount'].sum()
                st.metric("Engagements Totaux", f"{total_commitment:,.0f} EUR")
                total_drawn = facilities['drawn_amount'].sum()
                st.metric("Montants Tirés", f"{total_drawn:,.0f} EUR")
            
            with col3:
                utilization_rate = total_drawn / total_commitment if total_commitment > 0 else 0
                st.metric("Taux d'Utilisation", f"{utilization_rate:.1%}")
                potential_ead = facilities['ccf'].sum() * (total_commitment - total_drawn)
                st.metric("EAD Potentielle", f"{potential_ead:,.0f} EUR")
            
            # Graphiques des facilities
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution des CCF
                fig = px.histogram(facilities, x='ccf', nbins=20,
                                 title="Distribution des CCF")
                fig.update_layout(xaxis_title="Credit Conversion Factor")
                fig.update_layout(yaxis_title="Nombre de Facilities")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # CCF par type de produit
                ccf_by_product = facilities.groupby('product_id')['ccf'].mean().reset_index()
                fig = px.bar(ccf_by_product, x='product_id', y='ccf',
                           title="CCF Moyen par Type de Facility")
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé des facilities
            with st.expander("📋 Détail des Facilities"):
                facilities_display = facilities[['position_id', 'entity_id', 'product_id', 
                                               'commitment_amount', 'drawn_amount', 'ccf', 'ead']].copy()
                facilities_display['Taux Utilisation'] = (facilities_display['drawn_amount'] / 
                                                         facilities_display['commitment_amount'] * 100).round(1)
                st.dataframe(facilities_display, use_container_width=True)
        else:
            st.info("Aucune facility avec CCF détectée dans cette simulation.")
        
        # Corrélations et analyses statistiques
        st.markdown("#### 🔍 Analyses Statistiques")
        
        with st.expander("Voir les corrélations entre paramètres"):
            # Matrice de corrélation
            corr_data = positions[['ead', 'pd', 'lgd', 'maturity', 'interest_rate']].corr()
            
            fig = px.imshow(corr_data, 
                          title="Matrice de Corrélation des Paramètres",
                          color_continuous_scale='RdBu_r',
                          aspect="auto")
            st.plotly_chart(fig, use_container_width=True)
        
        # Aperçu des données détaillées
        st.markdown("### 👀 Aperçu des Positions Générées")
        
        # Filtres pour l'aperçu
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_entity = st.selectbox("Filtrer par Entité", 
                                         ['Toutes'] + list(positions['entity_id'].unique()))
        
        with col2:
            selected_product = st.selectbox("Filtrer par Produit",
                                          ['Tous'] + list(positions['product_id'].unique()))
        
        with col3:
            selected_stage = st.selectbox("Filtrer par Stage IFRS 9",
                                        ['Tous'] + [1, 2, 3])
        
        # Appliquer les filtres
        filtered_positions = positions.copy()
        
        if selected_entity != 'Toutes':
            filtered_positions = filtered_positions[filtered_positions['entity_id'] == selected_entity]
        
        if selected_product != 'Tous':
            filtered_positions = filtered_positions[filtered_positions['product_id'] == selected_product]
        
        if selected_stage != 'Tous':
            filtered_positions = filtered_positions[filtered_positions['stage'] == selected_stage]
        
        st.write(f"**{len(filtered_positions):,} positions** correspondent aux filtres sélectionnés")
        
        # Afficher les données filtrées
        if len(filtered_positions) > 0:
            st.dataframe(filtered_positions.head(100), use_container_width=True)
        else:
            st.warning("Aucune position ne correspond aux filtres sélectionnés.")

def show_credit_risk_advanced():
    """Page de risque de crédit avancée"""
    st.markdown("## ⚠️ Risque de Crédit et RWA selon CRR3")
    
    if 'advanced_positions' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation Monte Carlo.")
        return
    
    positions = st.session_state['advanced_positions']
    
    st.markdown("### 📊 Calculs RWA selon les Approches CRR3")
    
    # Informations sur les approches
    with st.expander("ℹ️ Approches de Calcul CRR3"):
        st.markdown("""
        **IRB Foundation (Internal Ratings Based)**
        - Utilisée pour les expositions Retail et Corporate
        - Formules de corrélation selon CRR3
        - Ajustements de maturité pour Corporate
        - Réduction de 23.81% pour les SME
        
        **Approche Standardisée**
        - Utilisée pour Souverains, Banques et autres expositions
        - Pondérations de risque fixes selon la notation
        - Pas d'ajustement de maturité
        
        **Paramètres Clés**
        - PD : Probability of Default (probabilité de défaut)
        - LGD : Loss Given Default (perte en cas de défaut)
        - EAD : Exposure at Default (exposition au moment du défaut)
        - M : Maturity (maturité effective)
        """)
    
    if st.button("⚠️ Calculer les RWA selon CRR3", type="primary"):
        with st.spinner("Calcul des RWA en cours..."):
            try:
                rwa_results = calculate_rwa_advanced(positions)
                capital_ratios = calculate_capital_ratios(rwa_results)
                
                st.session_state['advanced_rwa'] = rwa_results
                st.session_state['capital_ratios'] = capital_ratios
                
                st.success("🎉 RWA calculés avec succès selon CRR3!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul des RWA: {str(e)}")
                return
    
    if 'advanced_rwa' in st.session_state and 'capital_ratios' in st.session_state:
        rwa_results = st.session_state['advanced_rwa']
        capital_ratios = st.session_state['capital_ratios']
        
        st.markdown("### 📊 Résultats des RWA")
        
        # Métriques principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_rwa = capital_ratios['total_rwa']
            st.metric("RWA Total", f"{total_rwa:,.0f} EUR")
        
        with col2:
            total_ead = rwa_results['ead'].sum()
            avg_density = (total_rwa / total_ead * 100) if total_ead > 0 else 0
            st.metric("Densité RWA", f"{avg_density:.1f}%")
        
        with col3:
            capital_required = total_rwa * 0.08
            st.metric("Capital Requis (8%)", f"{capital_required:,.0f} EUR")
        
        with col4:
            cet1_capital = capital_ratios['cet1_capital']
            st.metric("Capital CET1", f"{cet1_capital:,.0f} EUR")
        
        with col5:
            cet1_ratio = capital_ratios['cet1_ratio']
            st.metric("Ratio CET1", f"{cet1_ratio:.1f}%")
        
        # Ratios de capital détaillés
        st.markdown("#### 🏛️ Ratios de Capital Réglementaires")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cet1_req = capital_ratios['cet1_requirement']
            cet1_surplus = capital_ratios['cet1_surplus']
            color = "normal" if cet1_surplus > 0 else "inverse"
            st.metric("CET1 Ratio", f"{cet1_ratio:.1f}%", 
                     delta=f"{cet1_surplus:.1f}% vs exigence ({cet1_req:.1f}%)",
                     delta_color=color)
        
        with col2:
            tier1_ratio = capital_ratios['tier1_ratio']
            tier1_req = capital_ratios['tier1_requirement']
            tier1_surplus = capital_ratios['tier1_surplus']
            color = "normal" if tier1_surplus > 0 else "inverse"
            st.metric("Tier 1 Ratio", f"{tier1_ratio:.1f}%",
                     delta=f"{tier1_surplus:.1f}% vs exigence ({tier1_req:.1f}%)",
                     delta_color=color)
        
        with col3:
            total_ratio = capital_ratios['total_capital_ratio']
            total_req = capital_ratios['total_requirement']
            total_surplus = capital_ratios['total_surplus']
            color = "normal" if total_surplus > 0 else "inverse"
            st.metric("Total Capital Ratio", f"{total_ratio:.1f}%",
                     delta=f"{total_surplus:.1f}% vs exigence ({total_req:.1f}%)",
                     delta_color=color)
        
        # Graphiques d'analyse RWA
        st.markdown("#### 📈 Analyse des RWA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # RWA par classe d'exposition
            rwa_by_class = rwa_results.groupby('exposure_class')['rwa_amount'].sum().reset_index()
            
            fig = px.bar(rwa_by_class, x='exposure_class', y='rwa_amount',
                       title="RWA par Classe d'Exposition", color='exposure_class')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # RWA par approche
            rwa_by_approach = rwa_results.groupby('approach')['rwa_amount'].sum().reset_index()
            
            fig = px.pie(rwa_by_approach, values='rwa_amount', names='approach',
                       title="Répartition RWA par Approche")
            st.plotly_chart(fig, use_container_width=True)
        
        # Densité RWA par entité et classe
        col1, col2 = st.columns(2)
        
        with col1:
            # RWA par entité
            rwa_by_entity = rwa_results.groupby('entity_id').agg({
                'rwa_amount': 'sum',
                'ead': 'sum'
            }).reset_index()
            rwa_by_entity['rwa_density'] = (rwa_by_entity['rwa_amount'] / rwa_by_entity['ead'] * 100).round(1)
            
            fig = px.bar(rwa_by_entity, x='entity_id', y='rwa_amount',
                       title="RWA par Entité", color='entity_id')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Densité RWA par classe
            density_by_class = rwa_results.groupby('exposure_class')['rwa_density'].mean().reset_index()
            
            fig = px.bar(density_by_class, x='exposure_class', y='rwa_density',
                       title="Densité RWA Moyenne par Classe", color='exposure_class')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Analyse spécifique des dérivés dans les RWA
        derivatives_rwa = rwa_results[rwa_results["product_id"].str.contains("Derivative", na=False)]
        if not derivatives_rwa.empty:
            st.markdown("#### ⚡ RWA des Produits Dérivés")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                derivatives_total_rwa = derivatives_rwa["rwa_amount"].sum()
                derivatives_pct = (derivatives_total_rwa / total_rwa * 100) if total_rwa > 0 else 0
                st.metric("RWA Dérivés", f"{derivatives_total_rwa:,.0f} EUR", f"{derivatives_pct:.1f}% du total")
            
            with col2:
                avg_rwa_density_derivatives = derivatives_rwa["rwa_density"].mean()
                st.metric("Densité RWA Moyenne", f"{avg_rwa_density_derivatives:.1%}")
            
            with col3:
                num_derivatives_rwa = len(derivatives_rwa)
                st.metric("Positions Dérivés", f"{num_derivatives_rwa:,}")
            
            # Graphique RWA par type de dérivé
            if "derivative_type" in derivatives_rwa.columns:
                derivative_rwa_summary = derivatives_rwa.groupby("derivative_type")["rwa_amount"].sum().reset_index()
                fig = px.bar(derivative_rwa_summary, x="derivative_type", y="rwa_amount",
                           title="RWA par Type de Dérivé", color="derivative_type")
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        # Analyse de sensibilité
        st.markdown("#### 🎯 Analyse de Sensibilité")
        
        with st.expander("Voir l'impact des variations de paramètres"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Impact d'une augmentation de PD de +50%**")
                
                # Simulation rapide
                pd_shock = 1.5
                shocked_rwa = total_rwa * pd_shock
                rwa_impact = shocked_rwa - total_rwa
                
                st.write(f"• RWA après choc: {shocked_rwa:,.0f} EUR")
                st.write(f"• Impact: +{rwa_impact:,.0f} EUR (+{(rwa_impact/total_rwa*100):.1f}%)")
                
                # Impact sur les ratios
                new_cet1 = (cet1_capital / shocked_rwa * 100)
                cet1_impact = new_cet1 - cet1_ratio
                st.write(f"• Nouveau CET1: {new_cet1:.1f}% ({cet1_impact:+.1f}%)")
            
            with col2:
                st.markdown("**Impact d'une augmentation de LGD de +25%**")
                
                lgd_shock = 1.25
                shocked_rwa_lgd = total_rwa * lgd_shock
                rwa_impact_lgd = shocked_rwa_lgd - total_rwa
                
                st.write(f"• RWA après choc: {shocked_rwa_lgd:,.0f} EUR")
                st.write(f"• Impact: +{rwa_impact_lgd:,.0f} EUR (+{(rwa_impact_lgd/total_rwa*100):.1f}%)")
                
                new_cet1_lgd = (cet1_capital / shocked_rwa_lgd * 100)
                cet1_impact_lgd = new_cet1_lgd - cet1_ratio
                st.write(f"• Nouveau CET1: {new_cet1_lgd:.1f}% ({cet1_impact_lgd:+.1f}%)")
        
        # Détail des RWA par entité
        st.markdown("#### 🏢 Détail par Entité")
        
        entity_detail = rwa_results.groupby(['entity_id', 'exposure_class']).agg({
            'rwa_amount': 'sum',
            'ead': 'sum',
            'rwa_density': 'mean'
        }).reset_index()
        
        entity_pivot = entity_detail.pivot(index='entity_id', 
                                         columns='exposure_class', 
                                         values='rwa_amount').fillna(0)
        
        st.dataframe(entity_pivot, use_container_width=True)
        
        # Aperçu des RWA détaillés
        st.markdown("### 🔍 Détail des RWA (100 premières positions)")
        
        display_columns = ['position_id', 'entity_id', 'exposure_class', 'ead', 
                          'rwa_amount', 'rwa_density', 'approach', 'pd', 'lgd']
        
        st.dataframe(rwa_results[display_columns].head(100), use_container_width=True)

def show_liquidity_advanced():
    """Page de liquidité avancée"""
    st.markdown("## 💧 Liquidité : LCR, NSFR et ALMM")
    
    if 'advanced_positions' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation Monte Carlo.")
        return
    
    positions = st.session_state['advanced_positions']
    
    # Informations sur les ratios de liquidité
    with st.expander("ℹ️ Ratios de Liquidité selon Bâle III"):
        st.markdown("""
        **LCR (Liquidity Coverage Ratio)**
        - Horizon : 30 jours de stress
        - Formule : HQLA / Sorties nettes ≥ 100%
        - HQLA Level 1 (100%), Level 2A (85%), Level 2B (50%)
        - Taux de sortie différenciés par type de passif
        
        **NSFR (Net Stable Funding Ratio)**
        - Horizon : 1 an
        - Formule : ASF / RSF ≥ 100%
        - ASF : Available Stable Funding (financement stable disponible)
        - RSF : Required Stable Funding (financement stable requis)
        
        **ALMM (Asset Liability Maturity Mismatch)**
        - Analyse des gaps de maturité par buckets temporels
        - Identification des déséquilibres actif/passif
        - Gestion du risque de transformation de maturité
        """)
    
    if st.button("💧 Calculer les Ratios de Liquidité", type="primary"):
        with st.spinner("Calcul des ratios de liquidité..."):
            try:
                lcr_results, nsfr_results, almm_results = calculate_liquidity_advanced(positions)
                
                st.session_state['advanced_lcr'] = lcr_results
                st.session_state['advanced_nsfr'] = nsfr_results
                st.session_state['advanced_almm'] = almm_results
                
                st.success("🎉 Ratios de liquidité calculés avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul de liquidité: {str(e)}")
                return
    
    if ('advanced_lcr' in st.session_state and 
        'advanced_nsfr' in st.session_state and 
        'advanced_almm' in st.session_state):
        
        lcr_results = st.session_state['advanced_lcr']
        nsfr_results = st.session_state['advanced_nsfr']
        almm_results = st.session_state['advanced_almm']
        
        st.markdown("### 📊 Résultats des Ratios de Liquidité")
        
        # === LCR (Liquidity Coverage Ratio) ===
        st.markdown("#### 🌊 Liquidity Coverage Ratio (LCR)")
        
        col1, col2, col3 = st.columns(3)
        
        entities = ['EU_SUB', 'US_SUB', 'CN_SUB']
        for i, entity in enumerate(entities):
            entity_lcr = lcr_results[lcr_results['entity_id'] == entity]
            if not entity_lcr.empty:
                with [col1, col2, col3][i]:
                    lcr_ratio = entity_lcr['lcr_ratio'].iloc[0]
                    lcr_surplus = entity_lcr['lcr_surplus'].iloc[0]
                    color = "normal" if lcr_ratio >= 100 else "inverse"
                    st.metric(
                        f"LCR {entity}",
                        f"{lcr_ratio:.1f}%",
                        delta=f"{lcr_surplus:+.1f}% vs min (100%)",
                        delta_color=color
                    )
        
        # Détail LCR
        with st.expander("🔍 Détail des Calculs LCR"):
            st.dataframe(lcr_results, use_container_width=True)
            
            # Graphique de composition HQLA
            if len(lcr_results) > 0:
                hqla_composition = []
                for _, row in lcr_results.iterrows():
                    hqla_composition.extend([
                        {'Entity': row['entity_id'], 'Type': 'Level 1', 'Amount': row['level1_hqla']},
                        {'Entity': row['entity_id'], 'Type': 'Level 2A', 'Amount': row['level2a_hqla']},
                        {'Entity': row['entity_id'], 'Type': 'Level 2B', 'Amount': row['level2b_hqla']}
                    ])
                
                hqla_df = safe_dataframe_creation(hqla_composition)
                
                fig = px.bar(hqla_df, x='Entity', y='Amount', color='Type',
                           title="Composition des HQLA par Entité")
                st.plotly_chart(fig, use_container_width=True)
        
        # === NSFR (Net Stable Funding Ratio) ===
        st.markdown("#### 🏗️ Net Stable Funding Ratio (NSFR)")
        
        col1, col2, col3 = st.columns(3)
        
        for i, entity in enumerate(entities):
            entity_nsfr = nsfr_results[nsfr_results['entity_id'] == entity]
            if not entity_nsfr.empty:
                with [col1, col2, col3][i]:
                    nsfr_ratio = entity_nsfr['nsfr_ratio'].iloc[0]
                    nsfr_surplus = entity_nsfr['nsfr_surplus'].iloc[0]
                    color = "normal" if nsfr_ratio >= 100 else "inverse"
                    st.metric(
                        f"NSFR {entity}",
                        f"{nsfr_ratio:.1f}%",
                        delta=f"{nsfr_surplus:+.1f}% vs min (100%)",
                        delta_color=color
                    )
        
        # Détail NSFR
        with st.expander("🔍 Détail des Calculs NSFR"):
            st.dataframe(nsfr_results, use_container_width=True)
            
            # Graphiques ASF vs RSF
            if len(nsfr_results) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(nsfr_results, x='entity_id', y='total_asf',
                               title="Available Stable Funding (ASF)", color='entity_id')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(nsfr_results, x='entity_id', y='total_rsf',
                               title="Required Stable Funding (RSF)", color='entity_id')
                    st.plotly_chart(fig, use_container_width=True)
        
        # === ALMM (Asset Liability Maturity Mismatch) ===
        st.markdown("#### ⏰ Asset Liability Maturity Mismatch (ALMM)")
        
        if almm_results:
            # Sélecteur d'entité pour ALMM
            selected_entity_almm = st.selectbox("Choisir une entité pour l'analyse ALMM", 
                                               [result['entity_id'] for result in almm_results])
            
            entity_almm = next((result for result in almm_results 
                              if result['entity_id'] == selected_entity_almm), None)
            
            if entity_almm:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Gaps de Maturité - {selected_entity_almm}**")
                    
                    gaps_data = []
                    for bucket, gap in entity_almm['gaps'].items():
                        gaps_data.append({'Bucket': bucket, 'Gap': gap})
                    
                    gaps_df = safe_dataframe_creation(gaps_data)
                    
                    fig = px.bar(gaps_df, x='Bucket', y='Gap',
                               title=f"Gaps de Maturité - {selected_entity_almm}",
                               color='Gap', color_continuous_scale='RdYlBu_r')
                    fig.add_hline(y=0, line_dash="dash", line_color="black")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown(f"**Gaps Cumulés - {selected_entity_almm}**")
                    
                    cumul_data = []
                    for bucket, cumul_gap in entity_almm['cumulative_gaps'].items():
                        cumul_data.append({'Bucket': bucket, 'Cumulative_Gap': cumul_gap})
                    
                    cumul_df = safe_dataframe_creation(cumul_data)
                    
                    fig = px.line(cumul_df, x='Bucket', y='Cumulative_Gap',
                                title=f"Gaps Cumulés - {selected_entity_almm}",
                                markers=True)
                    fig.add_hline(y=0, line_dash="dash", line_color="black")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tableau détaillé ALMM
                st.markdown(f"**Détail ALMM - {selected_entity_almm}**")
                
                almm_detail = []
                for bucket in entity_almm['gaps'].keys():
                    almm_detail.append({
                        'Bucket de Maturité': bucket,
                        'Gap (EUR)': f"{entity_almm['gaps'][bucket]:,.0f}",
                        'Gap Cumulé (EUR)': f"{entity_almm['cumulative_gaps'][bucket]:,.0f}"
                    })
                
                almm_detail_df = safe_dataframe_creation(almm_detail)
                st.dataframe(almm_detail_df, use_container_width=True)
        
        # === Synthèse de Liquidité ===
        st.markdown("#### 📋 Synthèse de Liquidité")
        
        # Statut de conformité global
        lcr_compliant = all(row['lcr_ratio'] >= 100 for _, row in lcr_results.iterrows()) if len(lcr_results) > 0 else False
        nsfr_compliant = all(row['nsfr_ratio'] >= 100 for _, row in nsfr_results.iterrows()) if len(nsfr_results) > 0 else False
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Conforme" if lcr_compliant else "❌ Non conforme"
            st.metric("Statut LCR Global", status)
        
        with col2:
            status = "✅ Conforme" if nsfr_compliant else "❌ Non conforme"
            st.metric("Statut NSFR Global", status)
        
        with col3:
            overall_status = "✅ Conforme" if (lcr_compliant and nsfr_compliant) else "❌ Non conforme"
            st.metric("Statut Liquidité Global", overall_status)
        
        # Graphiques de synthèse
        col1, col2 = st.columns(2)
        
        with col1:
            if len(lcr_results) > 0:
                fig = px.bar(lcr_results, x='entity_id', y='lcr_ratio',
                           title="LCR par Entité", color='entity_id')
                fig.add_hline(y=100, line_dash="dash", line_color="red", 
                             annotation_text="Minimum réglementaire (100%)")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if len(nsfr_results) > 0:
                fig = px.bar(nsfr_results, x='entity_id', y='nsfr_ratio',
                           title="NSFR par Entité", color='entity_id')
                fig.add_hline(y=100, line_dash="dash", line_color="red",
                             annotation_text="Minimum réglementaire (100%)")
                st.plotly_chart(fig, use_container_width=True)

def show_capital_ratios():
    """Page des ratios de capital"""
    st.markdown("## 🏛️ Ratios de Capital Réglementaires")
    
    if 'capital_ratios' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord calculer les RWA dans la section Risque de Crédit.")
        return
    
    capital_ratios = st.session_state['capital_ratios']
    
    st.markdown("### 📊 Vue d'Ensemble des Ratios de Capital")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("RWA Total", f"{capital_ratios['total_rwa']:,.0f} EUR")
        st.metric("Capital CET1", f"{capital_ratios['cet1_capital']:,.0f} EUR")
    
    with col2:
        cet1_ratio = capital_ratios['cet1_ratio']
        cet1_req = capital_ratios['cet1_requirement']
        cet1_surplus = capital_ratios['cet1_surplus']
        color = "normal" if cet1_surplus > 0 else "inverse"
        st.metric("CET1 Ratio", f"{cet1_ratio:.1f}%", 
                 delta=f"{cet1_surplus:+.1f}% vs exigence",
                 delta_color=color)
    
    with col3:
        tier1_ratio = capital_ratios['tier1_ratio']
        tier1_surplus = capital_ratios['tier1_surplus']
        color = "normal" if tier1_surplus > 0 else "inverse"
        st.metric("Tier 1 Ratio", f"{tier1_ratio:.1f}%",
                 delta=f"{tier1_surplus:+.1f}% vs exigence",
                 delta_color=color)
    
    with col4:
        total_ratio = capital_ratios['total_capital_ratio']
        total_surplus = capital_ratios['total_surplus']
        color = "normal" if total_surplus > 0 else "inverse"
        st.metric("Total Capital Ratio", f"{total_ratio:.1f}%",
                 delta=f"{total_surplus:+.1f}% vs exigence",
                 delta_color=color)
    
    # Graphique en cascade des exigences
    st.markdown("#### 📊 Exigences de Capital en Cascade")
    
    # Données pour le graphique en cascade
    cascade_data = {
        'Composant': [
            'Pilier 1 (CET1)',
            'Conservation Buffer',
            'Countercyclical Buffer',
            'Systemic Buffer',
            'Total CET1 Requirement',
            'Additional Tier 1',
            'Tier 2 Capital'
        ],
        'Pourcentage': [
            4.5,  # Pilier 1 CET1
            2.5,  # Conservation buffer
            0.0,  # Countercyclical (simulé à 0)
            1.0,  # Systemic buffer (simulé)
            capital_ratios['cet1_requirement'],  # Total CET1
            capital_ratios['tier1_requirement'] - capital_ratios['cet1_requirement'],  # AT1
            capital_ratios['total_requirement'] - capital_ratios['tier1_requirement']   # Tier 2
        ],
        'Type': [
            'CET1', 'CET1', 'CET1', 'CET1', 'CET1', 'AT1', 'Tier2'
        ]
    }
    
    cascade_df = safe_dataframe_creation(cascade_data)
    
    fig = px.bar(cascade_df, x='Composant', y='Pourcentage', color='Type',
               title="Composition des Exigences de Capital")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison avec les ratios actuels
    st.markdown("#### 📈 Comparaison Ratios Actuels vs Exigences")
    
    comparison_data = {
        'Ratio': ['CET1', 'Tier 1', 'Total Capital'],
        'Actuel': [
            capital_ratios['cet1_ratio'],
            capital_ratios['tier1_ratio'],
            capital_ratios['total_capital_ratio']
        ],
        'Exigence': [
            capital_ratios['cet1_requirement'],
            capital_ratios['tier1_requirement'],
            capital_ratios['total_requirement']
        ],
        'Surplus': [
            capital_ratios['cet1_surplus'],
            capital_ratios['tier1_surplus'],
            capital_ratios['total_surplus']
        ]
    }
    
    comparison_df = safe_dataframe_creation(comparison_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Ratio Actuel',
            x=comparison_df['Ratio'],
            y=comparison_df['Actuel'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Exigence Réglementaire',
            x=comparison_df['Ratio'],
            y=comparison_df['Exigence'],
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Ratios Actuels vs Exigences",
            yaxis_title="Pourcentage (%)",
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Graphique des surplus/déficits
        colors = ['green' if x > 0 else 'red' for x in comparison_df['Surplus']]
        
        fig = px.bar(comparison_df, x='Ratio', y='Surplus',
                   title="Surplus/Déficit de Capital",
                   color='Surplus',
                   color_continuous_scale='RdYlGn')
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig, use_container_width=True)
    
    # Tableau détaillé
    st.markdown("#### 📋 Détail des Ratios de Capital")
    
    detail_data = {
        'Métrique': [
            'RWA Total (EUR)',
            'Capital CET1 (EUR)',
            'Capital Tier 1 (EUR)',
            'Capital Total (EUR)',
            'CET1 Ratio (%)',
            'Tier 1 Ratio (%)',
            'Total Capital Ratio (%)',
            'CET1 Exigence (%)',
            'Tier 1 Exigence (%)',
            'Total Capital Exigence (%)',
            'CET1 Surplus/Déficit (%)',
            'Tier 1 Surplus/Déficit (%)',
            'Total Capital Surplus/Déficit (%)'
        ],
        'Valeur': [
            f"{capital_ratios['total_rwa']:,.0f}",
            f"{capital_ratios['cet1_capital']:,.0f}",
            f"{capital_ratios['tier1_capital']:,.0f}",
            f"{capital_ratios['total_capital']:,.0f}",
            f"{capital_ratios['cet1_ratio']:.2f}",
            f"{capital_ratios['tier1_ratio']:.2f}",
            f"{capital_ratios['total_capital_ratio']:.2f}",
            f"{capital_ratios['cet1_requirement']:.2f}",
            f"{capital_ratios['tier1_requirement']:.2f}",
            f"{capital_ratios['total_requirement']:.2f}",
            f"{capital_ratios['cet1_surplus']:+.2f}",
            f"{capital_ratios['tier1_surplus']:+.2f}",
            f"{capital_ratios['total_surplus']:+.2f}"
        ]
    }
    
    detail_df = safe_dataframe_creation(detail_data)
    st.dataframe(detail_df, use_container_width=True)
    
    # Analyse spécifique des dérivés dans les RWA
    derivatives_rwa = rwa_results[rwa_results["product_id"].str.contains("Derivative", na=False)]
    if not derivatives_rwa.empty:
        st.markdown("#### ⚡ RWA des Produits Dérivés")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            derivatives_total_rwa = derivatives_rwa["rwa_amount"].sum()
            derivatives_pct = (derivatives_total_rwa / total_rwa * 100) if total_rwa > 0 else 0
            st.metric("RWA Dérivés", f"{derivatives_total_rwa:,.0f} EUR", f"{derivatives_pct:.1f}% du total")
        
        with col2:
            avg_rwa_density_derivatives = derivatives_rwa["rwa_density"].mean()
            st.metric("Densité RWA Moyenne", f"{avg_rwa_density_derivatives:.1%}")
        
        with col3:
            num_derivatives_rwa = len(derivatives_rwa)
            st.metric("Positions Dérivés", f"{num_derivatives_rwa:,}")
        
        # Graphique RWA par type de dérivé
        if "derivative_type" in derivatives_rwa.columns:
            derivative_rwa_summary = derivatives_rwa.groupby("derivative_type")["rwa_amount"].sum().reset_index()
            fig = px.bar(derivative_rwa_summary, x="derivative_type", y="rwa_amount",
                       title="RWA par Type de Dérivé", color="derivative_type")
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # Analyse de sensibilité du capital
    st.markdown("#### 🎯 Analyse de Sensibilité du Capital")
    
    with st.expander("Voir l'impact des variations de RWA"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Impact d'une augmentation des RWA**")
            
            rwa_increases = [10, 25, 50, 100]  # Pourcentages
            
            sensitivity_data = []
            for increase in rwa_increases:
                new_rwa = capital_ratios['total_rwa'] * (1 + increase/100)
                new_cet1_ratio = (capital_ratios['cet1_capital'] / new_rwa * 100)
                
                sensitivity_data.append({
                    'Augmentation RWA (%)': f"+{increase}%",
                    'Nouveau RWA (EUR)': f"{new_rwa:,.0f}",
                    'Nouveau CET1 (%)': f"{new_cet1_ratio:.1f}",
                    'Impact CET1 (pp)': f"{new_cet1_ratio - capital_ratios['cet1_ratio']:+.1f}"
                })
            
            sensitivity_df = safe_dataframe_creation(sensitivity_data)
            st.dataframe(sensitivity_df, use_container_width=True)
        
        with col2:
            st.markdown("**Capital additionnel requis**")
            
            # Calculer le capital additionnel pour maintenir les ratios cibles
            target_cet1 = capital_ratios['cet1_requirement']
            
            additional_capital_data = []
            for increase in rwa_increases:
                new_rwa = capital_ratios['total_rwa'] * (1 + increase/100)
                required_capital = new_rwa * (target_cet1 / 100)
                additional_capital = required_capital - capital_ratios['cet1_capital']
                
                additional_capital_data.append({
                    'Augmentation RWA (%)': f"+{increase}%",
                    'Capital Requis (EUR)': f"{required_capital:,.0f}",
                    'Capital Additionnel (EUR)': f"{additional_capital:,.0f}",
                    'Coût Opportunité (%)': f"{(additional_capital / capital_ratios['cet1_capital'] * 100):+.1f}"
                })
            
            additional_df = safe_dataframe_creation(additional_capital_data)
            st.dataframe(additional_df, use_container_width=True)
    
    # Recommandations
    st.markdown("#### 💡 Recommandations")
    
    recommendations = []
    
    if capital_ratios['cet1_surplus'] < 1.0:
        recommendations.append("⚠️ **CET1 Ratio proche de l'exigence** : Envisager une augmentation de capital ou une réduction des RWA")
    
    if capital_ratios['tier1_surplus'] < 1.0:
        recommendations.append("⚠️ **Tier 1 Ratio faible** : Surveiller de près et préparer des mesures correctives")
    
    if capital_ratios['total_surplus'] < 2.0:
        recommendations.append("⚠️ **Total Capital Ratio serré** : Maintenir une surveillance renforcée")
    
    if capital_ratios['cet1_surplus'] > 5.0:
        recommendations.append("✅ **Excès de capital CET1** : Opportunité de croissance ou de distribution")
    
    if not recommendations:
        recommendations.append("✅ **Ratios de capital satisfaisants** : Situation conforme aux exigences réglementaires")
    
    for rec in recommendations:
        st.markdown(rec)

def show_reporting_advanced():
    """Page de reporting avancée"""
    st.markdown("## 📈 Reporting Réglementaire Avancé")
    
    # Vérifier les données disponibles
    available_data = []
    if 'advanced_positions' in st.session_state:
        available_data.append("Positions")
    if 'advanced_rwa' in st.session_state:
        available_data.append("RWA")
    if 'capital_ratios' in st.session_state:
        available_data.append("Capital")
    if 'advanced_lcr' in st.session_state:
        available_data.append("LCR")
    if 'advanced_nsfr' in st.session_state:
        available_data.append("NSFR")
    
    if not available_data:
        st.warning("⚠️ Aucune donnée disponible. Veuillez effectuer les calculs précédents.")
        return
    
    st.markdown("### 📊 Données Disponibles pour le Reporting")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    data_icons = {
        "Positions": "📊",
        "RWA": "⚠️", 
        "Capital": "🏛️",
        "LCR": "🌊",
        "NSFR": "🏗️"
    }
    
    for i, data_type in enumerate(["Positions", "RWA", "Capital", "LCR", "NSFR"]):
        with [col1, col2, col3, col4, col5][i]:
            if data_type in available_data:
                st.success(f"{data_icons[data_type]} {data_type}")
            else:
                st.error(f"❌ {data_type}")
    
    if st.button("📈 Générer le Rapport Réglementaire Complet", type="primary"):
        with st.spinner("Génération du rapport réglementaire..."):
            
            # En-tête du rapport
            st.markdown("### 📋 Rapport de Supervision Bancaire")
            
            report_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            st.markdown(f"**Date de génération** : {report_date}")
            
            config = st.session_state.get('advanced_config', {})
            st.markdown(f"**Scénario** : {config.get('scenario_name', 'N/A')}")
            st.markdown(f"**Niveau de stress** : {config.get('stress_scenario', 'N/A')}")
            
            # === 1. RÉSUMÉ EXÉCUTIF ===
            st.markdown("#### 1. 📊 Résumé Exécutif")
            
            if 'advanced_positions' in st.session_state:
                positions = st.session_state['advanced_positions']
                
                exec_summary = {
                    'Nombre total de positions': f"{len(positions):,}",
                    'EAD totale': f"{positions['ead'].sum():,.0f} EUR",
                    'Provisions ECL totales': f"{positions['ecl_provision'].sum():,.0f} EUR",
                    'Revenus d\'intérêts annuels': f"{positions['interest_income'].sum():,.0f} EUR"
                }
                
                if 'advanced_rwa' in st.session_state and 'capital_ratios' in st.session_state:
                    capital_ratios = st.session_state['capital_ratios']
                    exec_summary.update({
                        'RWA total': f"{capital_ratios['total_rwa']:,.0f} EUR",
                        'Ratio CET1': f"{capital_ratios['cet1_ratio']:.1f}%",
                        'Ratio Tier 1': f"{capital_ratios['tier1_ratio']:.1f}%",
                        'Ratio Total Capital': f"{capital_ratios['total_capital_ratio']:.1f}%"
                    })
                
                if 'advanced_lcr' in st.session_state:
                    lcr_results = st.session_state['advanced_lcr']
                    avg_lcr = lcr_results['lcr_ratio'].mean() if len(lcr_results) > 0 else 0
                    exec_summary['LCR moyen'] = f"{avg_lcr:.1f}%"
                
                if 'advanced_nsfr' in st.session_state:
                    nsfr_results = st.session_state['advanced_nsfr']
                    avg_nsfr = nsfr_results['nsfr_ratio'].mean() if len(nsfr_results) > 0 else 0
                    exec_summary['NSFR moyen'] = f"{avg_nsfr:.1f}%"
                
                # Afficher le résumé exécutif
                col1, col2 = st.columns(2)
                
                items = list(exec_summary.items())
                mid_point = len(items) // 2
                
                with col1:
                    for key, value in items[:mid_point]:
                        st.write(f"• **{key}** : {value}")
                
                with col2:
                    for key, value in items[mid_point:]:
                        st.write(f"• **{key}** : {value}")
            
            # === 2. ANALYSE DES EXPOSITIONS ===
            st.markdown("#### 2. 🏦 Analyse des Expositions")
            
            if 'advanced_positions' in st.session_state:
                positions = st.session_state['advanced_positions']
                
                # Synthèse par entité
                entity_analysis = positions.groupby('entity_id').agg({
                    'ead': ['count', 'sum'],
                    'pd': 'mean',
                    'lgd': 'mean',
                    'ecl_provision': 'sum',
                    'interest_income': 'sum'
                }).round(2)
                
                entity_analysis.columns = ['Nb Positions', 'EAD Total (EUR)', 'PD Moyenne', 
                                         'LGD Moyenne', 'Provisions ECL (EUR)', 'Revenus Intérêts (EUR)']
                entity_analysis = entity_analysis.reset_index()
                
                st.markdown("**Synthèse par Entité**")
                st.dataframe(entity_analysis, use_container_width=True)
                
                # Graphique des expositions par entité
                fig = px.bar(entity_analysis, x='entity_id', y='EAD Total (EUR)',
                           title="Expositions par Entité", color='entity_id')
                st.plotly_chart(fig, use_container_width=True)
                
                # Analyse par classe d'exposition
                exposure_analysis = positions.groupby('exposure_class').agg({
                    'ead': ['count', 'sum'],
                    'pd': 'mean',
                    'lgd': 'mean'
                }).round(4)
                
                exposure_analysis.columns = ['Nb Positions', 'EAD Total (EUR)', 'PD Moyenne', 'LGD Moyenne']
                exposure_analysis = exposure_analysis.reset_index()
                
                st.markdown("**Synthèse par Classe d'Exposition**")
                st.dataframe(exposure_analysis, use_container_width=True)
            
            # === 3. ANALYSE DES RISQUES DE CRÉDIT ===
            st.markdown("#### 3. ⚠️ Analyse des Risques de Crédit")
            
            if 'advanced_rwa' in st.session_state and 'capital_ratios' in st.session_state:
                rwa_results = st.session_state['advanced_rwa']
                capital_ratios = st.session_state['capital_ratios']
                
                # RWA par approche
                rwa_by_approach = rwa_results.groupby('approach').agg({
                    'rwa_amount': 'sum',
                    'ead': 'sum'
                }).reset_index()
                rwa_by_approach['rwa_density'] = (rwa_by_approach['rwa_amount'] / rwa_by_approach['ead'] * 100).round(1)
                
                st.markdown("**RWA par Approche de Calcul**")
                st.dataframe(rwa_by_approach, use_container_width=True)
                
                # Graphique RWA par approche
                fig = px.pie(rwa_by_approach, values='rwa_amount', names='approach',
                           title="Répartition des RWA par Approche")
                st.plotly_chart(fig, use_container_width=True)
                
                # Ratios de capital avec seuils réglementaires
                st.markdown("**Conformité des Ratios de Capital**")
                
                capital_compliance = {
                    'Ratio': ['CET1', 'Tier 1', 'Total Capital'],
                    'Valeur Actuelle (%)': [
                        f"{capital_ratios['cet1_ratio']:.1f}",
                        f"{capital_ratios['tier1_ratio']:.1f}",
                        f"{capital_ratios['total_capital_ratio']:.1f}"
                    ],
                    'Exigence Réglementaire (%)': [
                        f"{capital_ratios['cet1_requirement']:.1f}",
                        f"{capital_ratios['tier1_requirement']:.1f}",
                        f"{capital_ratios['total_requirement']:.1f}"
                    ],
                    'Surplus/Déficit (pp)': [
                        f"{capital_ratios['cet1_surplus']:+.1f}",
                        f"{capital_ratios['tier1_surplus']:+.1f}",
                        f"{capital_ratios['total_surplus']:+.1f}"
                    ],
                    'Statut': [
                        "✅ Conforme" if capital_ratios['cet1_surplus'] > 0 else "❌ Non conforme",
                        "✅ Conforme" if capital_ratios['tier1_surplus'] > 0 else "❌ Non conforme",
                        "✅ Conforme" if capital_ratios['total_surplus'] > 0 else "❌ Non conforme"
                    ]
                }
                
                capital_compliance_df = safe_dataframe_creation(capital_compliance)
                st.dataframe(capital_compliance_df, use_container_width=True)
            
            # === 4. ANALYSE DES FACILITIES ET CCF ===
            st.markdown("#### 4. 🏦 Analyse des Facilities et CCF")
            
            if 'advanced_positions' in st.session_state:
                positions = st.session_state['advanced_positions']
                facilities = positions[positions['ccf'] > 0]
                
                if len(facilities) > 0:
                    # Synthèse des facilities par entité
                    facilities_summary = facilities.groupby('entity_id').agg({
                        'commitment_amount': 'sum',
                        'drawn_amount': 'sum',
                        'ccf': 'mean',
                        'ead': 'sum'
                    }).round(2)
                    
                    facilities_summary['Taux_Utilisation'] = (
                        facilities_summary['drawn_amount'] / facilities_summary['commitment_amount'] * 100
                    ).round(1)
                    
                    facilities_summary['EAD_Potentielle'] = (
                        facilities_summary['ccf'] * 
                        (facilities_summary['commitment_amount'] - facilities_summary['drawn_amount'])
                    ).round(0)
                    
                    facilities_summary = facilities_summary.reset_index()
                    facilities_summary.columns = [
                        'Entité', 'Engagements (EUR)', 'Montants Tirés (EUR)', 
                        'CCF Moyen', 'EAD Actuelle (EUR)', 'Taux Utilisation (%)', 'EAD Potentielle (EUR)'
                    ]
                    
                    st.dataframe(facilities_summary, use_container_width=True)
                    
                    # Métriques globales des facilities
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_commitments = facilities['commitment_amount'].sum()
                        st.metric("Engagements Totaux", f"{total_commitments:,.0f} EUR")
                    
                    with col2:
                        total_drawn = facilities['drawn_amount'].sum()
                        utilization_rate = total_drawn / total_commitments if total_commitments > 0 else 0
                        st.metric("Taux d'Utilisation Global", f"{utilization_rate:.1%}")
                    
                    with col3:
                        avg_ccf = facilities['ccf'].mean()
                        st.metric("CCF Moyen", f"{avg_ccf:.2%}")
                    
                    with col4:
                        potential_ead = (facilities['ccf'] * (facilities['commitment_amount'] - facilities['drawn_amount'])).sum()
                        st.metric("EAD Potentielle Totale", f"{potential_ead:,.0f} EUR")
                    
                    # Analyse par type de facility
                    facility_types = facilities.groupby('product_id').agg({
                        'commitment_amount': 'sum',
                        'ccf': 'mean',
                        'ead': 'sum'
                    }).round(2)
                    
                    facility_types = facility_types.reset_index()
                    facility_types.columns = ['Type de Facility', 'Engagements (EUR)', 'CCF Moyen', 'EAD (EUR)']
                    
                    st.markdown("**Répartition par Type de Facility :**")
                    st.dataframe(facility_types, use_container_width=True)
                else:
                    st.info("Aucune facility avec CCF détectée dans le portefeuille.")
            
            # === 5. ANALYSE DE LIQUIDITÉ ===
            st.markdown("#### 5. 💧 Analyse de Liquidité")
            
            if 'advanced_lcr' in st.session_state and 'advanced_nsfr' in st.session_state:
                lcr_results = st.session_state['advanced_lcr']
                nsfr_results = st.session_state['advanced_nsfr']
                
                # Synthèse de liquidité par entité
                liquidity_summary = []
                
                for entity in ['EU_SUB', 'US_SUB', 'CN_SUB']:
                    entity_lcr = lcr_results[lcr_results['entity_id'] == entity]
                    entity_nsfr = nsfr_results[nsfr_results['entity_id'] == entity]
                    
                    if not entity_lcr.empty and not entity_nsfr.empty:
                        lcr_ratio = entity_lcr['lcr_ratio'].iloc[0]
                        nsfr_ratio = entity_nsfr['nsfr_ratio'].iloc[0]
                        
                        liquidity_summary.append({
                            'Entité': entity,
                            'LCR (%)': f"{lcr_ratio:.1f}",
                            'NSFR (%)': f"{nsfr_ratio:.1f}",
                            'Statut LCR': "✅ Conforme" if lcr_ratio >= 100 else "❌ Non conforme",
                            'Statut NSFR': "✅ Conforme" if nsfr_ratio >= 100 else "❌ Non conforme",
                            'HQLA (EUR)': f"{entity_lcr['total_hqla'].iloc[0]:,.0f}",
                            'Sorties Nettes (EUR)': f"{entity_lcr['net_cash_outflows'].iloc[0]:,.0f}"
                        })
                
                if liquidity_summary:
                    liquidity_df = safe_dataframe_creation(liquidity_summary)
                    st.dataframe(liquidity_df, use_container_width=True)
                    
                    # Graphiques de conformité liquidité
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(lcr_results, x='entity_id', y='lcr_ratio',
                                   title="LCR par Entité", color='entity_id')
                        fig.add_hline(y=100, line_dash="dash", line_color="red",
                                     annotation_text="Minimum (100%)")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.bar(nsfr_results, x='entity_id', y='nsfr_ratio',
                                   title="NSFR par Entité", color='entity_id')
                        fig.add_hline(y=100, line_dash="dash", line_color="red",
                                     annotation_text="Minimum (100%)")
                        st.plotly_chart(fig, use_container_width=True)
            
            # === 5. CLASSIFICATION IFRS 9 ===
            st.markdown("#### 5. 🏷️ Classification IFRS 9 et Provisions")
            
            if 'advanced_positions' in st.session_state:
                positions = st.session_state['advanced_positions']
                
                # Analyse par stage IFRS 9
                ifrs9_analysis = positions.groupby(['entity_id', 'stage']).agg({
                    'ead': ['count', 'sum'],
                    'ecl_provision': 'sum'
                }).round(2)
                
                ifrs9_analysis.columns = ['Nb Positions', 'EAD (EUR)', 'Provisions ECL (EUR)']
                ifrs9_analysis = ifrs9_analysis.reset_index()
                
                # Calculer les taux de provision
                ifrs9_analysis['Taux de Provision (%)'] = (
                    ifrs9_analysis['Provisions ECL (EUR)'] / ifrs9_analysis['EAD (EUR)'] * 100
                ).round(2)
                
                st.markdown("**Analyse par Stage IFRS 9 et Entité**")
                st.dataframe(ifrs9_analysis, use_container_width=True)
                
                # Graphique des provisions par stage
                stage_provisions = positions.groupby('stage')['ecl_provision'].sum().reset_index()
                
                fig = px.bar(stage_provisions, x='stage', y='ecl_provision',
                           title="Provisions ECL par Stage IFRS 9", color='stage')
                st.plotly_chart(fig, use_container_width=True)
            
            # === 6. RECOMMANDATIONS ET ACTIONS ===
            st.markdown("#### 6. 💡 Recommandations et Plan d'Actions")
            
            recommendations = []
            
            # Recommandations sur le capital
            if 'capital_ratios' in st.session_state:
                capital_ratios = st.session_state['capital_ratios']
                
                if capital_ratios['cet1_surplus'] < 1.0:
                    recommendations.append({
                        'Priorité': '🔴 Haute',
                        'Domaine': 'Capital',
                        'Recommandation': 'CET1 ratio proche de l\'exigence réglementaire',
                        'Action': 'Envisager une augmentation de capital ou une optimisation des RWA'
                    })
                elif capital_ratios['cet1_surplus'] > 5.0:
                    recommendations.append({
                        'Priorité': '🟢 Faible',
                        'Domaine': 'Capital',
                        'Recommandation': 'Excès de capital CET1 identifié',
                        'Action': 'Opportunité de croissance ou de distribution aux actionnaires'
                    })
            
            # Recommandations sur la liquidité
            if 'advanced_lcr' in st.session_state:
                lcr_results = st.session_state['advanced_lcr']
                
                for _, row in lcr_results.iterrows():
                    if row['lcr_ratio'] < 110:  # Marge de sécurité de 10%
                        recommendations.append({
                            'Priorité': '🟡 Moyenne',
                            'Domaine': 'Liquidité',
                            'Recommandation': f'LCR de {row["entity_id"]} proche du minimum ({row["lcr_ratio"]:.1f}%)',
                            'Action': 'Augmenter les HQLA ou réduire les sorties de trésorerie'
                        })
            
            # Recommandations sur les provisions
            if 'advanced_positions' in st.session_state:
                positions = st.session_state['advanced_positions']
                
                stage3_ratio = len(positions[positions['stage'] == 3]) / len(positions) * 100
                if stage3_ratio > 5:  # Plus de 5% en stage 3
                    recommendations.append({
                        'Priorité': '🟡 Moyenne',
                        'Domaine': 'Crédit',
                        'Recommandation': f'Proportion élevée de positions en Stage 3 ({stage3_ratio:.1f}%)',
                        'Action': 'Renforcer les procédures de recouvrement et de provisionnement'
                    })
            
            # Recommandations générales
            if not recommendations:
                recommendations.append({
                    'Priorité': '🟢 Faible',
                    'Domaine': 'Général',
                    'Recommandation': 'Situation réglementaire satisfaisante',
                    'Action': 'Maintenir la surveillance et les contrôles en place'
                })
            
            if recommendations:
                recommendations_df = safe_dataframe_creation(recommendations)
                st.dataframe(recommendations_df, use_container_width=True)
            
            # === 7. CONCLUSION ===
            st.markdown("#### 7. 📝 Conclusion")
            
            st.markdown(f"""
            **Synthèse de l'évaluation réglementaire au {report_date} :**
            
            L'analyse des données de simulation révèle la situation prudentielle de l'établissement. 
            Les calculs ont été effectués selon les méthodologies CRR3 et les standards Bâle III.
            
            **Points clés :**
            - Simulation Monte Carlo de {config.get('num_positions', 'N/A')} positions
            - Scénario de stress : {config.get('stress_scenario', 'N/A')}
            - Approches de calcul RWA : IRB Foundation et Standardisée
            - Ratios de liquidité LCR et NSFR évalués
            - Classification IFRS 9 appliquée
            
            **Conformité réglementaire :**
            Les résultats doivent être interprétés dans le contexte d'une simulation à des fins 
            éducatives. Pour une utilisation réglementaire réelle, une validation par des experts 
            et une certification des modèles seraient nécessaires.
            """)
            
            st.success("🎉 Rapport réglementaire généré avec succès!")

def show_export_advanced():
    """Page d'export Excel avancée"""
    st.markdown("## 📥 Export Excel Avancé")
    
    # Vérifier les données disponibles
    available_exports = []
    
    if 'advanced_positions' in st.session_state:
        available_exports.append(("Positions", st.session_state['advanced_positions']))
    
    if 'advanced_rwa' in st.session_state:
        available_exports.append(("RWA", st.session_state['advanced_rwa']))
    
    if 'capital_ratios' in st.session_state:
        available_exports.append(("Capital_Ratios", st.session_state['capital_ratios']))
    
    if 'advanced_lcr' in st.session_state:
        available_exports.append(("LCR", st.session_state['advanced_lcr']))
    
    if 'advanced_nsfr' in st.session_state:
        available_exports.append(("NSFR", st.session_state['advanced_nsfr']))
    
    if not available_exports:
        st.warning("⚠️ Aucune donnée disponible pour l'export. Veuillez effectuer les calculs précédents.")
        return
    
    st.markdown("### 📊 Données Disponibles pour l'Export")
    
    for export_name, export_data in available_exports:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if isinstance(export_data, dict):
                st.write(f"**{export_name}** (Dictionnaire)")
                st.write(f"Clés: {len(export_data)}")
            else:
                st.write(f"**{export_name}**")
                st.write(f"Lignes: {len(export_data):,}, Colonnes: {len(export_data.columns)}")
        
        with col2:
            # Aperçu
            if st.button(f"👀 Aperçu", key=f"preview_adv_{export_name}"):
                if isinstance(export_data, dict):
                    st.json(export_data)
                else:
                    st.dataframe(export_data.head(10), use_container_width=True)
        
        with col3:
            # Téléchargement individuel
            if not isinstance(export_data, dict):
                filename = f"{export_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        export_data.to_excel(writer, index=False)
                    
                    excel_data = output.getvalue()
                    download_link = create_download_link(excel_data, filename, f"📥 {export_name}")
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Erreur export {export_name}: {e}")
    
    # Export combiné avancé
    st.markdown("### 📦 Export Excel Combiné Avancé")
    
    if st.button("📥 Créer Fichier Excel Réglementaire Complet", type="primary"):
        with st.spinner("Création du fichier Excel réglementaire..."):
            try:
                # Préparer les données pour l'export
                positions_df = st.session_state.get('advanced_positions', pd.DataFrame())
                rwa_df = st.session_state.get('advanced_rwa', pd.DataFrame())
                lcr_df = st.session_state.get('advanced_lcr', pd.DataFrame())
                nsfr_df = st.session_state.get('advanced_nsfr', pd.DataFrame())
                capital_ratios = st.session_state.get('capital_ratios', {})
                
                excel_data = create_excel_export_advanced(positions_df, rwa_df, lcr_df, nsfr_df, capital_ratios)
                
                if excel_data:
                    filename = f"banking_regulatory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    download_link = create_download_link(excel_data, filename, f"📥 Télécharger {filename}")
                    
                    st.markdown("#### ✅ Fichier Excel Réglementaire Créé !")
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    st.info(f"""
                    **Contenu du fichier Excel :**
                    - 📊 Feuille de synthèse avec KPI principaux
                    - 🏦 Positions détaillées avec paramètres IFRS 9
                    - ⚠️ RWA par position avec approches CRR3
                    - 🏛️ Ratios de capital avec exigences réglementaires
                    - 💧 Ratios de liquidité LCR et NSFR
                    - 📈 Résumés par entité et par produit
                    """)
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la création du fichier Excel: {str(e)}")

def show_templates_import():
    """Page des templates et import"""
    st.markdown("## 📋 Templates Excel et Import de Données")
    
    st.markdown("""
    Cette section permet de générer des templates Excel pour importer vos propres données 
    et de charger des fichiers de données réelles dans l'application.
    """)
    
    # Génération de templates
    st.markdown("### 📄 Génération de Templates Excel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Templates Disponibles")
        
        templates = {
            "input_positions": "Template pour les positions bancaires",
            "input_fx_rates": "Template pour les taux de change",
            "input_market_data": "Template pour les données de marché",
            "input_capital_data": "Template pour les données de capital",
            "input_liquidity_data": "Template pour les données de liquidité"
        }
        
        for template_name, description in templates.items():
            st.write(f"• **{template_name}.xlsx** : {description}")
    
    with col2:
        st.markdown("#### Génération")
        
        if st.button("📄 Générer tous les Templates", type="primary"):
            with st.spinner("Génération des templates..."):
                try:
                    # Template positions
                    positions_template = {
                        'position_id': ['POS_000001', 'POS_000002', 'POS_000003'],
                        'entity_id': ['EU_SUB', 'US_SUB', 'CN_SUB'],
                        'product_id': ['Retail_Mortgages', 'Corporate_Loans', 'SME_Loans'],
                        'exposure_class': ['Retail_Mortgages', 'Corporate', 'SME'],
                        'currency': ['EUR', 'USD', 'EUR'],
                        'ead': [150000.00, 500000.00, 75000.00],
                        'pd': [0.015, 0.025, 0.040],
                        'lgd': [0.35, 0.45, 0.50],
                        'maturity': [20.0, 5.0, 3.0],
                        'interest_rate': [0.025, 0.035, 0.045],
                        'booking_date': ['2024-01-01', '2024-01-01', '2024-01-01']
                    }
                    
                    positions_template_df = safe_dataframe_creation(positions_template)
                    
                    # Créer le fichier Excel template
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        positions_template_df.to_excel(writer, sheet_name='Positions', index=False)
                        
                        # Ajouter une feuille d'instructions
                        instructions = {
                            'Champ': list(positions_template.keys()),
                            'Description': [
                                'Identifiant unique de la position',
                                'Identifiant de l\'entité (EU_SUB, US_SUB, CN_SUB)',
                                'Type de produit financier',
                                'Classe d\'exposition pour calcul RWA',
                                'Devise de la position',
                                'Exposition au moment du défaut (EUR)',
                                'Probabilité de défaut (décimal, ex: 0.02 = 2%)',
                                'Perte en cas de défaut (décimal, ex: 0.45 = 45%)',
                                'Maturité en années',
                                'Taux d\'intérêt annuel (décimal)',
                                'Date de comptabilisation (YYYY-MM-DD)'
                            ],
                            'Format': [
                                'Texte (POS_XXXXXX)',
                                'Texte',
                                'Texte',
                                'Texte',
                                'Texte (EUR, USD, GBP, etc.)',
                                'Nombre décimal',
                                'Nombre décimal (0-1)',
                                'Nombre décimal (0-1)',
                                'Nombre décimal',
                                'Nombre décimal (0-1)',
                                'Date (YYYY-MM-DD)'
                            ]
                        }
                        
                        instructions_df = safe_dataframe_creation(instructions)
                        instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
                    
                    excel_data = output.getvalue()
                    
                    filename = f"template_positions_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    download_link = create_download_link(excel_data, filename, f"📥 Télécharger {filename}")
                    
                    st.success("✅ Template généré avec succès !")
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Erreur génération template: {str(e)}")
    
    # Import de données
    st.markdown("### 📤 Import de Données Réelles")
    
    st.markdown("""
    **Instructions d'import :**
    1. Téléchargez le template Excel ci-dessus
    2. Remplissez-le avec vos données réelles
    3. Uploadez le fichier complété ci-dessous
    4. L'application utilisera vos données pour les calculs
    """)
    
    uploaded_file = st.file_uploader(
        "Choisir un fichier Excel de positions",
        type=['xlsx', 'xls'],
        help="Fichier Excel contenant les positions bancaires selon le template"
    )
    
    if uploaded_file is not None:
        try:
            # Lire le fichier Excel
            imported_positions = pd.read_excel(uploaded_file, sheet_name='Positions')
            
            st.success(f"✅ Fichier importé avec succès ! {len(imported_positions)} positions chargées.")
            
            # Validation des données
            required_columns = ['position_id', 'entity_id', 'product_id', 'ead', 'pd', 'lgd']
            missing_columns = [col for col in required_columns if col not in imported_positions.columns]
            
            if missing_columns:
                st.error(f"❌ Colonnes manquantes: {', '.join(missing_columns)}")
            else:
                # Validation des valeurs
                validation_errors = []
                
                if imported_positions['ead'].min() <= 0:
                    validation_errors.append("EAD doit être > 0")
                
                if (imported_positions['pd'] < 0).any() or (imported_positions['pd'] > 1).any():
                    validation_errors.append("PD doit être entre 0 et 1")
                
                if (imported_positions['lgd'] < 0).any() or (imported_positions['lgd'] > 1).any():
                    validation_errors.append("LGD doit être entre 0 et 1")
                
                if validation_errors:
                    st.error("❌ Erreurs de validation:")
                    for error in validation_errors:
                        st.write(f"• {error}")
                else:
                    # Ajouter les colonnes manquantes avec des valeurs par défaut
                    if 'exposure_class' not in imported_positions.columns:
                        imported_positions['exposure_class'] = imported_positions['product_id'].apply(
                            lambda x: 'Retail_Mortgages' if 'Mortgage' in x else 
                                     'Retail_Other' if 'Retail' in x else 'Corporate'
                        )
                    
                    if 'currency' not in imported_positions.columns:
                        imported_positions['currency'] = 'EUR'
                    
                    if 'maturity' not in imported_positions.columns:
                        imported_positions['maturity'] = 5.0
                    
                    if 'stage' not in imported_positions.columns:
                        imported_positions['stage'] = imported_positions['pd'].apply(
                            lambda pd: 1 if pd <= 0.01 else (2 if pd <= 0.03 else 3)
                        )
                    
                    if 'ecl_provision' not in imported_positions.columns:
                        imported_positions['ecl_provision'] = (
                            imported_positions['ead'] * 
                            imported_positions['pd'] * 
                            imported_positions['lgd']
                        ).round(2)
                    
                    if 'interest_rate' not in imported_positions.columns:
                        imported_positions['interest_rate'] = 0.03
                    
                    if 'interest_income' not in imported_positions.columns:
                        imported_positions['interest_income'] = (
                            imported_positions['ead'] * imported_positions['interest_rate']
                        ).round(2)
                    
                    if 'booking_date' not in imported_positions.columns:
                        imported_positions['booking_date'] = datetime.now().strftime('%Y-%m-%d')
                    
                    if 'country_risk' not in imported_positions.columns:
                        imported_positions['country_risk'] = imported_positions['entity_id'].apply(
                            lambda x: x.split('_')[0] if '_' in x else 'EU'
                        )
                    
                    if 'sector' not in imported_positions.columns:
                        imported_positions['sector'] = 'Non-Financial'
                    
                    # Sauvegarder les données importées
                    st.session_state['advanced_positions'] = imported_positions
                    st.session_state['data_source'] = 'imported'
                    
                    st.success("🎉 Données importées et validées avec succès !")
                    
                    # Afficher un aperçu
                    st.markdown("#### 👀 Aperçu des Données Importées")
                    st.dataframe(imported_positions.head(10), use_container_width=True)
                    
                    # Statistiques
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Positions", f"{len(imported_positions):,}")
                    
                    with col2:
                        st.metric("EAD Total", f"{imported_positions['ead'].sum():,.0f} EUR")
                    
                    with col3:
                        st.metric("PD Moyenne", f"{imported_positions['pd'].mean():.2%}")
                    
                    with col4:
                        st.metric("Provisions", f"{imported_positions['ecl_provision'].sum():,.0f} EUR")
        
        except Exception as e:
            st.error(f"❌ Erreur lors de l'import: {str(e)}")
    
    # Gestion des données
    st.markdown("### 🔄 Gestion des Données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Revenir aux Données Simulées"):
            if 'advanced_positions' in st.session_state:
                del st.session_state['advanced_positions']
            if 'data_source' in st.session_state:
                del st.session_state['data_source']
            st.success("✅ Données simulées restaurées. Relancez une simulation.")
    
    with col2:
        data_source = st.session_state.get('data_source', 'simulated')
        if data_source == 'imported':
            st.info("📊 Utilisation de données importées")
        else:
            st.info("🎲 Utilisation de données simulées")

def show_documentation_advanced():
    """Page de documentation avancée"""
    st.markdown("## ℹ️ Documentation CRR3 et Bâle III")
    
    # Navigation dans la documentation
    doc_section = st.selectbox(
        "Choisir une section de documentation",
        [
            "📖 Vue d'ensemble",
            "⚖️ Réglementation CRR3",
            "🔬 Méthodologies de Calcul",
            "💧 Ratios de Liquidité",
            "🏛️ Ratios de Capital",
            "📊 Classification IFRS 9",
            "🔧 Guide Technique",
            "📚 Références et Sources"
        ]
    )
    
    if doc_section == "📖 Vue d'ensemble":
        st.markdown("""
        ### 📖 Vue d'Ensemble de l'Application
        
        Cette application implémente une simulation complète des calculs bancaires réglementaires 
        selon les dernières normes européennes et internationales.
        
        #### 🎯 Objectifs Pédagogiques
        
        **Formation aux Réglementations Bancaires**
        - Comprendre les mécanismes de calcul des RWA selon CRR3
        - Maîtriser les ratios de liquidité Bâle III (LCR, NSFR)
        - Appliquer la classification IFRS 9 pour les provisions
        - Analyser les ratios de capital réglementaires
        
        **Simulation Réaliste**
        - Génération Monte Carlo de milliers de positions
        - Paramètres de risque cohérents et réalistes
        - Diversification par entités, produits et devises
        - Scénarios de stress intégrés
        
        **Reporting Professionnel**
        - Templates conformes aux standards EBA
        - Export Excel multi-feuilles détaillé
        - Visualisations interactives avancées
        - Analyse de conformité automatisée
        
        #### 🏗️ Architecture de l'Application
        
        **Couche de Données**
        - Génération de positions synthétiques
        - Import de données réelles via Excel
        - Validation et contrôles de cohérence
        
        **Moteurs de Calcul**
        - Moteur RWA (IRB Foundation, IRB SME, Standardisé)
        - Moteur de liquidité (LCR, NSFR, ALMM)
        - Moteur de capital (CET1, Tier 1, Total)
        - Moteur IFRS 9 (stages et provisions ECL)
        
        **Interface Utilisateur**
        - Navigation intuitive par sections
        - Configuration avancée des paramètres
        - Visualisations Plotly interactives
        - Export et téléchargement intégrés
        
          **Workflow Recommandé :**
        1. **⚙️ Configuration** → Définir les paramètres de simulation
        2. **📊 Simulation** → Générer les positions bancaires
        3. **🔄 Consolidation** → Éliminer les opérations intragroupes et créer le bilan consolidé
        4. **⚠️ Risque de Crédit** → Calculer les RWA selon CRR3
        5. **💧 Liquidité** → Analyser LCR, NSFR et ALMM
        6. **🏛️ Capital** → Évaluer les ratios de capital
        7. **📈 Reporting** → Générer les rapports réglementaires
        8. **📥 Export** → Télécharger les résultats Excel
        """)
    
    elif doc_section == "⚖️ Réglementation CRR3":
        st.markdown("""
        ### ⚖️ Réglementation CRR3 (Capital Requirements Regulation)
        
        #### 📜 Contexte Réglementaire
        
        **CRR3 - Règlement (UE) 2024/1623**
        - Entrée en vigueur : 1er janvier 2025
        - Transposition finale de Bâle III en Europe
        - Renforcement des exigences de capital et de liquidité
        - Nouvelles méthodologies de calcul des RWA
        
        **Objectifs Principaux**
        - Renforcer la résilience du système bancaire européen
        - Harmoniser les pratiques de supervision
        - Améliorer la comparabilité des ratios entre banques
        - Intégrer les leçons de la crise COVID-19
        
        #### 🏛️ Piliers de la Réglementation
        
        **Pilier 1 : Exigences Minimales de Capital**
        - CET1 : 4.5% des RWA (minimum absolu)
        - Tier 1 : 6.0% des RWA
        - Total Capital : 8.0% des RWA
        - Ratio de levier : 3.0% minimum
        
        **Pilier 2 : Processus de Supervision**
        - SREP (Supervisory Review and Evaluation Process)
        - Exigences additionnelles spécifiques (P2R)
        - Orientations de supervision (P2G)
        - Tests de résistance réguliers
        
        **Pilier 3 : Discipline de Marché**
        - Publication d'informations réglementaires
        - Transparence sur les risques et le capital
        - Rapports FINREP et COREP
        - Communication aux parties prenantes
        
        #### 🔄 Nouveautés CRR3
        
        **Révisions des Approches IRB**
        - Nouvelles corrélations pour les expositions corporate
        - Ajustements des facteurs de maturité
        - Réduction SME maintenue à 23.81%
        - Planchers de sortie (output floors) à 72.5%
        
        **Renforcement de l'Approche Standardisée**
        - Nouvelles pondérations de risque
        - Prise en compte des garanties immobilières
        - Traitement spécifique des expositions retail
        - Méthodes alternatives pour les PME
        
        **Ratios de Liquidité Renforcés**
        - LCR : maintien à 100% minimum
        - NSFR : 100% minimum (pleinement applicable)
        - ALMM : surveillance renforcée des gaps de maturité
        - Nouveaux facteurs de pondération HQLA
        
        #### 📊 Impact sur les Banques
        
        **Augmentation des Exigences**
        - Hausse moyenne des RWA de 10-15%
        - Pression sur les ratios de capital
        - Besoin de capital additionnel estimé à 65 Md€
        - Adaptation des modèles internes
        
        **Opportunités d'Optimisation**
        - Révision des portefeuilles de crédit
        - Optimisation de la gestion actif-passif
        - Amélioration des processus de provisionnement
        - Digitalisation des contrôles réglementaires
        """)
    
    elif doc_section == "🔬 Méthodologies de Calcul":
        st.markdown("""
        ### 🔬 Méthodologies de Calcul des RWA
        
        #### 🎯 Approche IRB Foundation
        
        **Formule Générale**
        ```
        RWA = K × 12.5 × EAD × MA
        
        Où :
        K = Capital réglementaire
        MA = Ajustement de maturité (si applicable)
        ```
        
        **Calcul du Capital K**
        ```
        K = [LGD × N((1-R)^(-0.5) × G(PD) + (R/(1-R))^0.5 × G(0.999)) - PD × LGD]
        
        Où :
        N(x) = Fonction de répartition normale standard
        G(x) = Fonction inverse de N(x)
        R = Corrélation
        ```
        
        **Corrélations par Classe d'Exposition**
        
        *Retail Mortgages :*
        ```
        R = 0.15
        ```
        
        *Retail Other :*
        ```
        R = 0.04
        ```
        
        *Corporate :*
        ```
        R = 0.12 × (1 - exp(-50×PD))/(1 - exp(-50)) + 
            0.24 × [1 - (1 - exp(-50×PD))/(1 - exp(-50))] - 
            0.04 × [1 - (S-5)/45]
        
        Où S = Chiffre d'affaires en M€ (plafonné à 50)
        ```
        
        **Ajustement de Maturité (Corporate uniquement)**
        ```
        MA = (1 + (M - 2.5) × b) / (1 + 1.5 × b)
        
        Où :
        b = (0.11852 - 0.05478 × ln(PD))²
        M = Maturité effective (plafonnée à 5 ans)
        ```
        
        #### 📏 Approche Standardisée
        
        **Pondérations de Risque par Classe**
        
        *Expositions Souveraines :*
        - AAA à AA- : 0%
        - A+ à A- : 20%
        - BBB+ à BBB- : 50%
        - BB+ à B- : 100%
        - Inférieur à B- : 150%
        
        *Expositions Bancaires :*
        - Méthode 1 (basée sur la notation externe)
        - Méthode 2 (basée sur la notation souveraine)
        - Pondération minimale : 20%
        
        *Expositions Corporate :*
        - Standard : 100%
        - PME : 75%
        - Spécialisées : 100% à 150%
        
        *Expositions Retail :*
        - Garanties immobilières : 35%
        - Autres retail : 75%
        - Crédit revolving : 75%
        
        #### 🏢 Traitement Spécial SME
        
        **Réduction de 23.81%**
        ```
        RWA_SME = RWA_Corporate × 0.7619
        ```
        
        **Critères d'Éligibilité**
        - Chiffre d'affaires < 50 M€
        - Exposition < 1.5 M€ par contrepartie
        - Portefeuille diversifié
        
        #### 🔄 Planchers de Sortie (Output Floors)
        
        **Application Progressive**
        - 2025 : 50%
        - 2026 : 55%
        - 2027 : 60%
        - 2028 : 65%
        - 2029+ : 72.5%
        
        **Formule**
        ```
        RWA_Final = max(RWA_IRB, RWA_Standardisé × Plancher)
        ```
        """)
    
    elif doc_section == "💧 Ratios de Liquidité":
        st.markdown("""
        ### 💧 Ratios de Liquidité Bâle III
        
        #### 🌊 LCR (Liquidity Coverage Ratio)
        
        **Objectif**
        Assurer que la banque dispose d'actifs liquides suffisants pour survivre 
        à un stress de liquidité de 30 jours.
        
        **Formule**
        ```
        LCR = HQLA / Sorties Nettes ≥ 100%
        
        Sorties Nettes = max(Sorties - Entrées, 25% × Sorties)
        ```
        
        **HQLA (High Quality Liquid Assets)**
        
        *Level 1 (100% éligible) :*
        - Réserves de banque centrale
        - Titres souverains AAA à AA-
        - Obligations garanties par l'État
        
        *Level 2A (85% éligible) :*
        - Titres souverains A+ à BBB-
        - Obligations sécurisées AAA à AA-
        - Obligations d'entreprises AAA à AA-
        
        *Level 2B (50% éligible, max 15% du total) :*
        - Actions d'indices boursiers majeurs
        - Obligations d'entreprises BBB+ à BBB-
        - RMBS AAA notés
        
        **Taux de Sortie par Type de Passif**
        
        *Dépôts Retail :*
        - Stables assurés : 3%
        - Stables non assurés : 5%
        - Moins stables : 10%
        
        *Dépôts Corporate :*
        - Opérationnels : 25%
        - Non opérationnels : 40%
        - Wholesale : 100%
        
        *Financements Sécurisés :*
        - Collatéral Level 1 : 0%
        - Collatéral Level 2A : 15%
        - Collatéral Level 2B : 50%
        
        #### 🏗️ NSFR (Net Stable Funding Ratio)
        
        **Objectif**
        Promouvoir la stabilité du financement à moyen et long terme 
        (horizon 1 an).
        
        **Formule**
        ```
        NSFR = ASF / RSF ≥ 100%
        
        ASF = Available Stable Funding
        RSF = Required Stable Funding
        ```
        
        **Facteurs ASF (Available Stable Funding)**
        
        *Capital et Instruments de Capital :*
        - Capital réglementaire : 100%
        - Autres instruments > 1 an : 100%
        
        *Dépôts Retail :*
        - Stables < 100k€ : 95%
        - Moins stables < 100k€ : 90%
        - Terme > 1 an : 100%
        
        *Dépôts Wholesale :*
        - Opérationnels : 50%
        - Autres < 1 an : 0%
        - Terme > 1 an : 100%
        
        **Facteurs RSF (Required Stable Funding)**
        
        *Actifs Liquides :*
        - HQLA Level 1 : 5%
        - HQLA Level 2A : 15%
        - HQLA Level 2B : 50%
        
        *Prêts et Avances :*
        - Hypothèques < 35% LTV : 65%
        - Autres prêts retail : 85%
        - Prêts corporate : 85%
        - Prêts > 1 an : 100%
        
        #### ⏰ ALMM (Asset Liability Maturity Mismatch)
        
        **Objectif**
        Surveiller les déséquilibres de maturité entre actifs et passifs 
        pour identifier les risques de transformation.
        
        **Buckets de Maturité**
        - 0-1 mois
        - 1-3 mois  
        - 3-6 mois
        - 6-12 mois
        - 1-2 ans
        - 2-5 ans
        - 5+ ans
        
        **Calcul des Gaps**
        ```
        Gap(i) = Actifs(i) - Passifs(i)
        Gap_Cumulé(i) = Σ Gap(j) pour j ≤ i
        ```
        
        **Indicateurs de Surveillance**
        - Gaps négatifs importants court terme
        - Concentration excessive sur certaines maturités
        - Évolution des gaps dans le temps
        - Sensibilité aux variations de taux
        """)
    
    elif doc_section == "🏛️ Ratios de Capital":
        st.markdown("""
        ### 🏛️ Ratios de Capital Réglementaires
        
        #### 📊 Composition du Capital Réglementaire
        
        **CET1 (Common Equity Tier 1)**
        - Actions ordinaires émises et libérées
        - Primes d'émission liées aux actions CET1
        - Réserves (légales, statutaires, autres)
        - Résultats non distribués
        - Autres éléments du résultat global accumulés
        - Intérêts minoritaires éligibles
        - Déductions réglementaires
        
        **AT1 (Additional Tier 1)**
        - Instruments hybrides éligibles
        - Primes d'émission liées aux instruments AT1
        - Intérêts minoritaires non inclus dans CET1
        - Déductions spécifiques AT1
        
        **Tier 2**
        - Instruments de capital Tier 2
        - Primes d'émission liées aux instruments Tier 2
        - Provisions générales (approche standardisée)
        - Déductions spécifiques Tier 2
        
        #### 📏 Exigences Minimales
        
        **Pilier 1 (Minimum Absolu)**
        ```
        CET1 Ratio = CET1 / RWA ≥ 4.5%
        Tier 1 Ratio = (CET1 + AT1) / RWA ≥ 6.0%
        Total Capital Ratio = (CET1 + AT1 + Tier 2) / RWA ≥ 8.0%
        ```
        
        **Buffers de Capital**
        
        *Conservation Buffer :*
        - Exigence : 2.5% de CET1
        - Objectif : Absorber les pertes en période de stress
        - Restriction de distribution si non respecté
        
        *Countercyclical Buffer :*
        - Fourchette : 0% à 2.5% de CET1
        - Fixé par les autorités nationales
        - Varie selon le cycle économique
        
        *Systemic Risk Buffer :*
        - Fourchette : 1% à 5% de CET1
        - Pour les banques systémiques (G-SIB, O-SIB)
        - Basé sur la taille et l'interconnexion
        
        **Exigences Combinées**
        ```
        CET1 Total = 4.5% + 2.5% + CCyB + SRB + P2R
        
        Où :
        CCyB = Countercyclical Buffer
        SRB = Systemic Risk Buffer  
        P2R = Pillar 2 Requirements
        ```
        
        #### ⚖️ Ratio de Levier
        
        **Formule**
        ```
        Leverage Ratio = Tier 1 Capital / Exposition Totale ≥ 3.0%
        ```
        
        **Exposition Totale**
        - Actifs du bilan (valeur comptable)
        - Expositions hors bilan (après CCF)
        - Expositions sur dérivés (méthode SA-CCR)
        - Expositions sur titres financés (SFT)
        
        #### 🛡️ MREL (Minimum Requirement for Own Funds and Eligible Liabilities)
        
        **Objectif**
        Assurer une capacité d'absorption des pertes suffisante 
        pour la résolution bancaire.
        
        **Formule**
        ```
        MREL = (Fonds Propres + Passifs Éligibles) / TLAC ≥ Seuil
        
        TLAC = Total Loss Absorbing Capacity
        ```
        
        **Seuils Indicatifs**
        - Banques G-SIB : 18% des RWA + 6.75% du ratio de levier
        - Autres banques : 16% des RWA + 6% du ratio de levier
        
        #### 📈 Surveillance et Actions Correctives
        
        **Échelle d'Intervention Progressive**
        
        *Zone Verte (> Exigences Combinées) :*
        - Aucune restriction
        - Distribution libre des bénéfices
        
        *Zone Orange (Entre Pilier 1 et Exigences Combinées) :*
        - Restrictions sur les distributions
        - Plan de conservation du capital
        
        *Zone Rouge (< Pilier 1) :*
        - Interdiction de distribution
        - Mesures correctives immédiates
        - Supervision renforcée
        
        **Mesures Correctives Types**
        - Augmentation de capital
        - Réduction des RWA
        - Limitation de la croissance
        - Cession d'activités
        - Amélioration de la gouvernance
        """)
    
    elif doc_section == "📊 Classification IFRS 9":
        st.markdown("""
        ### 📊 Classification IFRS 9 et Provisions ECL
        
        #### 🎯 Objectifs d'IFRS 9
        
        **Remplacement d'IAS 39**
        - Modèle de pertes attendues vs pertes encourues
        - Reconnaissance plus précoce des pertes
        - Approche prospective (forward-looking)
        - Cohérence avec la gestion des risques
        
        **Champ d'Application**
        - Instruments financiers au coût amorti
        - Instruments de dette à la juste valeur par OCI
        - Engagements de financement
        - Contrats de garantie financière
        
        #### 📋 Modèle de Classification par Stages
        
        **Stage 1 : Performing**
        
        *Critères :*
        - Pas d'augmentation significative du risque de crédit
        - Depuis la comptabilisation initiale
        - Pas d'indication objective de dépréciation
        
        *Provisionnement :*
        - ECL 12 mois
        - Pertes attendues sur les défauts probables dans les 12 prochains mois
        
        *Formule :*
        ```
        ECL_12M = EAD × PD_12M × LGD
        ```
        
        **Stage 2 : Underperforming**
        
        *Critères :*
        - Augmentation significative du risque de crédit
        - Mais pas encore en défaut
        - Indicateurs de détérioration
        
        *Provisionnement :*
        - ECL Lifetime (durée de vie)
        - Pertes attendues sur toute la durée de vie résiduelle
        
        *Formule :*
        ```
        ECL_Lifetime = Σ(t=1 to n) EAD(t) × PD_Marginale(t) × LGD(t) × DF(t)
        
        Où DF(t) = Facteur d'actualisation
        ```
        
        **Stage 3 : Non-Performing**
        
        *Critères :*
        - Indication objective de dépréciation
        - Défaut avéré (> 90 jours de retard)
        - Restructuration pour difficultés financières
        
        *Provisionnement :*
        - ECL Lifetime
        - Arrêt de la comptabilisation des intérêts
        
        #### 🔍 Critères de Transfert entre Stages
        
        **Stage 1 → Stage 2**
        
        *Indicateurs Quantitatifs :*
        - Augmentation de PD > seuil (ex: doublement)
        - Dégradation de notation interne
        - Variation défavorable de spread de crédit
        
        *Indicateurs Qualitatifs :*
        - Retards de paiement < 30 jours mais récurrents
        - Restructuration préventive
        - Détérioration de la situation financière
        
        **Stage 2 → Stage 3**
        
        *Critères de Défaut :*
        - Retard > 90 jours sur obligation significative
        - Probabilité faible de paiement intégral
        - Restructuration pour difficultés financières
        
        **Retour vers Stages Antérieurs**
        
        *Conditions :*
        - Amélioration durable de la qualité de crédit
        - Période probatoire (généralement 3-6 mois)
        - Validation par les comités de risque
        
        #### 📊 Méthodologies de Calcul ECL
        
        **Approche Générale (3 Scénarios)**
        
        *Scénario Central (Probabilité ~50%) :*
        - Conditions économiques attendues
        - Trajectoire de croissance normale
        
        *Scénario Défavorable (Probabilité ~30%) :*
        - Récession modérée
        - Augmentation du chômage
        
        *Scénario Très Défavorable (Probabilité ~20%) :*
        - Crise économique sévère
        - Choc systémique
        
        **Formule Pondérée**
        ```
        ECL = Σ(i=1 to 3) Probabilité(i) × ECL_Scénario(i)
        ```
        
        **Approche Simplifiée (Matrice de Provisions)**
        
        *Pour Créances Commerciales :*
        - Buckets de retard prédéfinis
        - Taux de provision historiques
        - Ajustements prospectifs
        
        *Exemple de Matrice :*
        - Courant : 0.5%
        - 1-30 jours : 2%
        - 31-60 jours : 5%
        - 61-90 jours : 15%
        - > 90 jours : 50%
        
        #### 🔄 Intégration avec la Gestion des Risques
        
        **Cohérence des Modèles**
        - Utilisation des PD/LGD réglementaires
        - Ajustements pour différences conceptuelles
        - Validation indépendante des paramètres
        
        **Gouvernance**
        - Comité IFRS 9 dédié
        - Revue périodique des modèles
        - Documentation des jugements d'experts
        - Audit interne et externe
        
        **Reporting**
        - Réconciliation avec les données réglementaires
        - Analyse de sensibilité aux scénarios
        - Suivi des transferts entre stages
        - Communication aux parties prenantes
        """)
    
    elif doc_section == "🔧 Guide Technique":
        st.markdown("""
        ### 🔧 Guide Technique de l'Application
        
        #### 💻 Architecture Technique
        
        **Technologies Utilisées**
        - **Frontend** : Streamlit (Python web framework)
        - **Calculs** : Pandas, NumPy (traitement de données)
        - **Visualisations** : Plotly (graphiques interactifs)
        - **Export** : OpenPyXL (fichiers Excel)
        - **Déploiement** : Compatible Windows/Linux/Mac
        
        **Structure du Code**
        ```
        Banking_Simulator.py
        ├── Configuration et imports
        ├── Fonctions utilitaires
        ├── Génération de positions
        ├── Calculs RWA avancés
        ├── Calculs de liquidité
        ├── Ratios de capital
        ├── Export Excel
        ├── Interface utilisateur
        └── Documentation
        ```
        
        #### 🔧 Installation et Configuration
        
        **Prérequis Système**
        ```bash
        Python 3.8+ (recommandé : 3.11)
        RAM : 4 GB minimum, 8 GB recommandé
        Espace disque : 1 GB libre
        Connexion internet (pour les packages)
        ```
        
        **Installation des Dépendances**
        ```bash
        pip install streamlit pandas plotly openpyxl
        ```
        
        **Lancement de l'Application**
        ```bash
        streamlit run Banking_Simulator.py
        ```
        
        **Configuration Avancée**
        ```bash
        # Port personnalisé
        streamlit run Banking_Simulator.py --server.port 8502
        
        # Adresse spécifique
        streamlit run Banking_Simulator.py --server.address 0.0.0.0
        
        # Mode développement
        streamlit run Banking_Simulator.py --server.runOnSave true
        ```
        
        #### 🔍 Fonctions Principales
        
        **Génération de Positions**
        ```python
        def generate_positions_advanced(num_positions, seed, config):
            # Génère des positions bancaires réalistes
            # Paramètres de risque cohérents
        # Analyse spécifique des dérivés si inclus
        derivatives_positions = positions[positions["product_id"].str.contains("Derivative", na=False)]
        if not derivatives_positions.empty:
            st.markdown("#### ⚡ Analyse des Produits Dérivés")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_notional = derivatives_positions["commitment_amount"].sum()
                st.metric("Notionnel Total", f"{total_notional:,.0f} EUR")
            
            with col2:
                total_mtm = derivatives_positions.get("mtm_value", pd.Series([0])).sum()
                st.metric("MTM Total", f"{total_mtm:,.0f} EUR")
            
            with col3:
                total_cva = derivatives_positions.get("cva_charge", pd.Series([0])).sum()
                st.metric("Charge CVA", f"{total_mtm:,.0f} EUR")
            
            with col4:
                num_derivatives = len(derivatives_positions)
                st.metric("Nombre Dérivés", f"{num_derivatives:,}")
            
            # Graphiques spécifiques aux dérivés
            col1, col2 = st.columns(2)
            
            with col1:
                if "derivative_type" in derivatives_positions.columns:
                    derivative_summary = derivatives_positions.groupby("derivative_type")["commitment_amount"].sum().reset_index()
                    fig = px.pie(derivative_summary, values="commitment_amount", names="derivative_type",
                               title="Répartition du Notionnel par Type de Dérivé")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if "counterparty_rating" in derivatives_positions.columns:
                    rating_summary = derivatives_positions.groupby("counterparty_rating")["ead"].sum().reset_index()
                    fig = px.bar(rating_summary, x="counterparty_rating", y="ead",
                               title="EAD par Rating de Contrepartie", color="counterparty_rating")
                    st.plotly_chart(fig, use_container_width=True)

            # Classification IFRS 9 automatique
            return positions_dataframe
        ```
        
        **Calcul RWA**
        ```python
        def calculate_rwa_advanced(positions_df):
            # Approche IRB Foundation
            # Approche Standardisée  
            # Traitement spécial SME
            return rwa_dataframe
        ```
        
        **Ratios de Liquidité**
        ```python
        def calculate_liquidity_advanced(positions_df):
            # LCR avec HQLA détaillés
            # NSFR avec ASF/RSF
            # ALMM par buckets de maturité
            return lcr_df, nsfr_df, almm_results
        ```
        
        #### 📊 Structures de Données
        
        **DataFrame Positions**
        ```python
        columns = [
            'position_id',      # Identifiant unique
            'entity_id',        # Entité (EU_SUB, US_SUB, CN_SUB)
            'product_id',       # Type de produit
            'exposure_class',   # Classe d'exposition CRR
            'currency',         # Devise
            'ead',             # Exposition au défaut
            'pd',              # Probabilité de défaut
            'lgd',             # Perte en cas de défaut
            'maturity',        # Maturité en années
            'stage',           # Stage IFRS 9
            'ecl_provision',   # Provision ECL
            'interest_rate',   # Taux d'intérêt
            'interest_income', # Revenus d'intérêts
            'booking_date',    # Date de comptabilisation
            'country_risk',    # Risque pays
            'sector'           # Secteur économique
        ]
        ```
        
        **DataFrame RWA**
        ```python
        columns = [
            'position_id',     # Lien avec positions
            'entity_id',       # Entité
            'exposure_class',  # Classe d'exposition
            'ead',            # Exposition
            'rwa_amount',     # Montant RWA
            'rwa_density',    # Densité RWA (%)
            'approach',       # Approche de calcul
            'pd', 'lgd',      # Paramètres de risque
            'maturity'        # Maturité
        ]
        ```
        
        #### 🔒 Sécurité et Validation
        
        **Validation des Données**
        ```python
        def validate_positions(df):
            # Vérification des colonnes obligatoires
            # Contrôle des plages de valeurs
            # Détection des valeurs aberrantes
            # Cohérence entre paramètres
        ```
        
        **Gestion d'Erreurs**
        ```python
        try:
            # Opération risquée
            result = calculate_rwa(positions)
        except Exception as e:
            st.error(f"Erreur de calcul: {e}")
            # Fallback ou valeurs par défaut
        ```
        
        **Contrôles de Cohérence**
        - PD entre 0 et 1
        - LGD entre 0 et 1  
        - EAD > 0
        - Maturité > 0
        - Devises valides
        
        #### 📈 Performance et Optimisation
        
        **Gestion Mémoire**
        ```python
        # Utilisation de chunks pour gros volumes
        chunk_size = 1000
        for chunk in pd.read_excel(file, chunksize=chunk_size):
            process_chunk(chunk)
        ```
        
        **Cache Streamlit**
        ```python
        @st.cache_data
        def expensive_calculation(data):
            # Calcul coûteux mis en cache
            return result
        ```
        
        **Optimisations Pandas**
        ```python
        # Utilisation de types optimaux
        df['pd'] = df['pd'].astype('float32')
        df['entity_id'] = df['entity_id'].astype('category')
        
        # Vectorisation des calculs
        df['rwa'] = df['ead'] * df['risk_weight']
        ```
        
        #### 🐛 Débogage et Maintenance
        
        **Logs de Débogage**
        ```python
        import logging
# Import de la page d'accueil mise à jour
try:
    from home_page import show_updated_home
except ImportError:
    def show_updated_home():
        st.error("Page d'accueil mise à jour non disponible")

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Calcul RWA pour {len(positions)} positions")
        ```
        
        **Tests Unitaires**
        ```python
        def test_rwa_calculation():
            # Données de test
            test_positions = create_test_data()
            
            # Calcul
            rwa_result = calculate_rwa(test_positions)
            
            # Assertions
            assert len(rwa_result) == len(test_positions)
            assert rwa_result['rwa_amount'].min() >= 0
        ```
        
        **Profiling de Performance**
        ```python
        import cProfile
        
        def profile_calculation():
            pr = cProfile.Profile()
            pr.enable()
            
            # Code à profiler
            calculate_rwa(large_dataset)
            
            pr.disable()
            pr.print_stats(sort='cumulative')
        ```
        """)
    
    elif doc_section == "📚 Références et Sources":
        st.markdown("""
        ### 📚 Références et Sources Officielles
        
        #### 🇪🇺 Réglementation Européenne
        
        **Textes Principaux**
        - [Règlement (UE) 2024/1623 - CRR3](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024R1623)
        - [Directive (UE) 2024/1619 - CRD VI](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L1619)
        - [Règlement (UE) 575/2013 - CRR](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32013R0575)
        - [Directive 2013/36/UE - CRD IV](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32013L0036)
        
        **Standards Techniques EBA**
        - [RTS on IRB Assessment Methodology](https://www.eba.europa.eu/regulation-and-policy/credit-risk/regulatory-technical-standards-on-irb-assessment-methodology)
        - [Guidelines on ICAAP and ILAAP](https://www.eba.europa.eu/regulation-and-policy/supervisory-review-and-evaluation-srep-and-pillar-2/guidelines-on-icaap-and-ilaap-information)
        - [Technical Standards on Supervisory Reporting](https://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting)
        
        #### 🌍 Standards Internationaux
        
        **Comité de Bâle**
        - [Basel III Framework](https://www.bis.org/basel_framework/)
        - [Basel III Monitoring Report](https://www.bis.org/bcbs/publ/d521.htm)
        - [Revisions to the Basel III Framework](https://www.bis.org/bcbs/publ/d424.htm)
        - [Liquidity Coverage Ratio](https://www.bis.org/publ/bcbs238.htm)
        - [Net Stable Funding Ratio](https://www.bis.org/bcbs/publ/d295.htm)
        
        **IFRS Foundation**
        - [IFRS 9 Financial Instruments](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/)
        - [Implementation Guidance IFRS 9](https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ifrs-9.pdf)
        - [Educational Material ECL](https://www.ifrs.org/content/dam/ifrs/supporting-implementation/ifrs-9/ifrs-9-ecl-educational-examples.pdf)
        
        #### 🏛️ Autorités de Supervision
        
        **Banque Centrale Européenne**
        - [SSM Supervisory Manual](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm_supervisory_manual_201403en.pdf)
        - [SREP Methodology Booklet](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.srep_methodology_booklet_2018.en.pdf)
        - [Guide to Internal Models](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.guidetointernalmodels_consolidated_201710.en.pdf)
        
        **ACPR (France)**
        - [Guide Pratique IFRS 9](https://acpr.banque-france.fr/sites/default/files/medias/documents/guide_pratique_ifrs9.pdf)
        - [Recommandations Stress Tests](https://acpr.banque-france.fr/supervision-bancaire/controles-et-sanctions/exercices-de-stress)
        
        **Autorité Bancaire Européenne (EBA)**
        - [Risk Assessment Report](https://www.eba.europa.eu/risk-analysis-and-data/risk-assessment-reports)
        - [Methodological Guide EU-wide Stress Test](https://www.eba.europa.eu/risk-analysis-and-data/eu-wide-stress-testing/2023)
        
        #### 📊 Templates et Formats de Reporting
        
        **FINREP (Financial Reporting)**
        - [FINREP Templates v3.3](https://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting)
        - [FINREP Validation Rules](https://www.eba.europa.eu/documents/10180/359626/FINREP+validation+rules+v3.3.xlsx)
        
        **COREP (Common Reporting)**
        - [COREP Templates v3.3](https://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting)
        - [COREP Instructions](https://www.eba.europa.eu/documents/10180/359626/COREP+instructions+v3.3.pdf)
        
        **RUBA (Resolution Planning)**
        - [RUBA Templates](https://www.srb.europa.eu/en/content/ruba-reporting)
        - [RUBA Technical Standards](https://www.srb.europa.eu/sites/default/files/rts_2022_2405_ruba_reporting.pdf)
        
        #### 🔬 Recherche et Études
        
        **Publications Académiques**
        - "Basel III and Bank Capital Regulation" - Journal of Banking & Finance
        - "IFRS 9 Expected Credit Loss Modelling" - Risk Management
        - "Liquidity Risk Management in Banking" - Financial Markets Review
        
        **Études d'Impact**
        - [EBA Impact Assessment CRR3](https://www.eba.europa.eu/regulation-and-policy/single-rulebook/interactive-single-rulebook/10002)
        - [Basel Committee QIS Results](https://www.bis.org/bcbs/qis/)
        - [ECB Financial Stability Review](https://www.ecb.europa.eu/pub/financial-stability/fsr/html/index.en.html)
        
        #### 🛠️ Outils et Ressources Techniques
        
        **Calculateurs Officiels**
        - [EBA Risk Assessment Calculator](https://www.eba.europa.eu/risk-analysis-and-data)
        - [Basel Committee Risk Weight Calculator](https://www.bis.org/bcbs/irbriskweight.htm)
        
        **Bases de Données**
        - [ECB Statistical Data Warehouse](https://sdw.ecb.europa.eu/)
        - [EBA Risk Dashboard](https://www.eba.europa.eu/risk-analysis-and-data/risk-dashboard)
        - [BIS Statistics](https://www.bis.org/statistics/)
        
        **Formation et Certification**
        - [Risk Management Association (RMA)](https://www.rmahq.org/)
        - [Global Association of Risk Professionals (GARP)](https://www.garp.org/)
        - [Professional Risk Managers' International Association (PRMIA)](https://www.prmia.org/)
        
        #### 📖 Bibliographie Recommandée
        
        **Ouvrages de Référence**
        1. "The Basel Handbook" - Risk Books
        2. "Credit Risk Modeling using Excel and VBA" - Löffler & Posch
        3. "Liquidity Risk Management" - Duttweiler
        4. "IFRS 9 and CECL Credit Loss Modelling" - Bellini
        5. "Regulatory Capital and Earnings Management" - Ahmed et al.
        
        **Revues Spécialisées**
        - Journal of Risk Management in Financial Institutions
        - Risk Magazine
        - The Journal of Credit Risk
        - International Journal of Central Banking
        - European Financial Management
        
        #### 🔗 Liens Utiles
        
        **Sites Officiels**
        - [Banque Centrale Européenne](https://www.ecb.europa.eu/)
        - [Autorité Bancaire Européenne](https://www.eba.europa.eu/)
        - [Comité de Bâle](https://www.bis.org/bcbs/)
        - [IFRS Foundation](https://www.ifrs.org/)
        - [ACPR France](https://acpr.banque-france.fr/)
        
        **Communautés Professionnelles**
        - [Risk.net](https://www.risk.net/)
        - [OpenRisk](https://www.openriskmanagement.com/)
        - [Quantitative Finance Stack Exchange](https://quant.stackexchange.com/)
        
        ---
        
        *Cette documentation est fournie à des fins éducatives. Pour les implémentations 
        réglementaires réelles, consultez toujours les textes officiels et faites appel 
        à des experts qualifiés.*
        """)

if __name__ == "__main__":
    main()

# Import de l'analyse drill-down
try:
    from drill_down_analysis import show_drill_down_analysis
except ImportError:
    def show_drill_down_analysis(positions_df, rwa_df=None):
        st.error('Module drill-down non disponible')

