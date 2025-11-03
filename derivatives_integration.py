import random
import math
from datetime import datetime, timedelta

def generate_derivatives_for_simulation(num_derivatives, entities, config):
    """Générer des dérivés intégrés dans la simulation principale"""
    
    derivatives_data = []
    
    # Types de dérivés avec leurs caractéristiques
    derivative_types = {
        'Interest_Rate_Swap': {
            'asset_class': 'Interest Rate',
            'typical_maturity': [1, 2, 3, 5, 7, 10, 15, 20, 30],
            'notional_range': [1000000, 100000000],
            'volatility': 0.15,
            'exposure_class': 'Bank'
        },
        'FX_Forward': {
            'asset_class': 'Foreign Exchange',
            'typical_maturity': [0.25, 0.5, 1, 2, 3, 5],
            'notional_range': [500000, 50000000],
            'volatility': 0.12,
            'exposure_class': 'Bank'
        },
        'Credit_Default_Swap': {
            'asset_class': 'Credit',
            'typical_maturity': [1, 3, 5, 7, 10],
            'notional_range': [1000000, 25000000],
            'volatility': 0.25,
            'exposure_class': 'Corporate'
        },
        'Equity_Option': {
            'asset_class': 'Equity',
            'typical_maturity': [0.25, 0.5, 1, 2],
            'notional_range': [100000, 10000000],
            'volatility': 0.30,
            'exposure_class': 'Corporate'
        },
        'Commodity_Swap': {
            'asset_class': 'Commodity',
            'typical_maturity': [0.5, 1, 2, 3, 5],
            'notional_range': [500000, 20000000],
            'volatility': 0.35,
            'exposure_class': 'Corporate'
        }
    }
    
    # Contreparties avec ratings
    counterparties = [
        {'name': 'BANK_AAA_01', 'rating': 'AAA', 'pd': 0.0003, 'lgd': 0.45},
        {'name': 'BANK_AA_02', 'rating': 'AA', 'pd': 0.0008, 'lgd': 0.45},
        {'name': 'BANK_A_03', 'rating': 'A', 'pd': 0.0025, 'lgd': 0.45},
        {'name': 'CORP_BBB_04', 'rating': 'BBB', 'pd': 0.0080, 'lgd': 0.60},
        {'name': 'CORP_BB_05', 'rating': 'BB', 'pd': 0.0250, 'lgd': 0.60},
        {'name': 'HEDGE_FUND_06', 'rating': 'B', 'pd': 0.0500, 'lgd': 0.75},
        {'name': 'SOVEREIGN_07', 'rating': 'AA', 'pd': 0.0005, 'lgd': 0.30},
        {'name': 'INSURANCE_08', 'rating': 'A', 'pd': 0.0020, 'lgd': 0.50}
    ]
    
    # Devises
    currencies = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD']
    
    for i in range(num_derivatives):
        # Sélection aléatoire du type de dérivé
        derivative_type = random.choice(list(derivative_types.keys()))
        derivative_info = derivative_types[derivative_type]
        
        # Sélection de la contrepartie
        counterparty = random.choice(counterparties)
        
        # Paramètres de base
        notional = random.uniform(*derivative_info['notional_range'])
        maturity_years = random.choice(derivative_info['typical_maturity'])
        
        # Calcul de la valeur de marché (MTM)
        mtm_volatility = derivative_info['volatility']
        mtm = random.gauss(0, notional * mtm_volatility * 0.1)
        
        # Calcul du PFE (Potential Future Exposure) selon SA-CCR
        pfe = calculate_pfe_simple(
            derivative_type, 
            notional, 
            maturity_years, 
            derivative_info['volatility']
        )
        
        # Calcul de l'EAD selon SA-CCR
        replacement_cost = max(mtm, 0)  # RC = max(V, 0)
        ead_sa_ccr = 1.4 * (replacement_cost + pfe)  # Alpha = 1.4
        
        # Collatéral (pour certains dérivés)
        has_collateral = random.choice([True, False]) if derivative_type in ['Interest_Rate_Swap', 'FX_Forward'] else False
        collateral_amount = random.uniform(0.7, 0.9) * max(mtm, 0) if has_collateral else 0
        
        # EAD finale après collatéral
        final_ead = max(0, ead_sa_ccr - collateral_amount)
        
        # Calcul CVA (Credit Valuation Adjustment)
        cva_charge = calculate_cva_simple(
            final_ead, 
            counterparty['pd'], 
            counterparty['lgd'], 
            maturity_years
        )
        
        # Classification IFRS 9 (Stage 1 par défaut pour les dérivés)
        stage = 1
        if counterparty['pd'] > 0.01:  # Si PD > 1%, considérer Stage 2
            stage = 2
        
        # Calcul ECL pour les dérivés (basé sur CVA)
        ecl = cva_charge
        
        # Taux d'intérêt et revenus (pour les swaps de taux)
        if derivative_type == 'Interest_Rate_Swap':
            interest_rate = random.uniform(0.01, 0.05)
            interest_income = notional * interest_rate * 0.1  # Approximation
        else:
            interest_rate = 0.0
            interest_income = 0.0
        
        # Créer la position dérivé compatible avec le format standard
        derivative_position = {
            'position_id': f"DRV_{i+1:05d}",
            'entity_id': random.choice(entities),
            'product_type': f"Derivative_{derivative_type}",
            'exposure_class': derivative_info['exposure_class'],
            'currency': random.choice(currencies),
            'ead': round(final_ead, 2),
            'pd': round(counterparty['pd'], 6),
            'lgd': round(counterparty['lgd'], 4),
            'maturity': round(maturity_years, 2),
            'stage': stage,
            'ecl_provision': round(ecl, 2),
            'interest_rate': round(interest_rate, 4),
            'interest_income': round(interest_income, 2),
            'booking_date': datetime.now().strftime('%Y-%m-%d'),
            'country_risk': random.choice(entities).split('_')[0],
            'sector': 'Financial',
            'ccf': 0.0,  # Pas de CCF pour les dérivés
            'commitment_amount': round(notional, 2),  # Notionnel comme engagement
            'drawn_amount': round(final_ead, 2),  # EAD comme montant tiré
            
            # Champs spécifiques aux dérivés
            'derivative_type': derivative_type,
            'asset_class': derivative_info['asset_class'],
            'counterparty_name': counterparty['name'],
            'counterparty_rating': counterparty['rating'],
            'notional_amount': round(notional, 2),
            'mtm_value': round(mtm, 2),
            'replacement_cost': round(replacement_cost, 2),
            'pfe_amount': round(pfe, 2),
            'ead_sa_ccr': round(ead_sa_ccr, 2),
            'has_collateral': has_collateral,
            'collateral_amount': round(collateral_amount, 2),
            'cva_charge': round(cva_charge, 2),
            'dva_charge': round(cva_charge * 0.3, 2),
            'fva_charge': round(cva_charge * 0.2, 2)
        }
        
        derivatives_data.append(derivative_position)
    
    return derivatives_data

def calculate_pfe_simple(derivative_type, notional, maturity, volatility):
    """Calculer le PFE selon l'approche SA-CCR simplifiée"""
    
    # Facteurs de supervisory delta selon le type de dérivé
    supervisory_factors = {
        'Interest_Rate_Swap': {'delta': 0.5},
        'FX_Forward': {'delta': 0.8},
        'Credit_Default_Swap': {'delta': 0.38},
        'Equity_Option': {'delta': 0.75},
        'Commodity_Swap': {'delta': 0.40}
    }
    
    # Facteur de maturité
    maturity_factor = min(1, math.sqrt(maturity / 1))
    
    # Facteur supervisory
    supervisory_delta = supervisory_factors.get(derivative_type, {'delta': 0.5})['delta']
    
    # Calcul du PFE
    supervisory_factor = 0.15  # Facteur standard
    pfe = supervisory_delta * notional * supervisory_factor * maturity_factor * volatility
    
    return max(pfe, 0)

def calculate_cva_simple(ead, pd, lgd, maturity):
    """Calculer la charge CVA simplifiée"""
    
    # Formule simplifiée CVA = EAD * PD * LGD * sqrt(maturity)
    survival_probability = math.exp(-pd * maturity)
    default_probability = 1 - survival_probability
    
    cva = ead * default_probability * lgd * math.sqrt(maturity)
    
    return max(cva, 0)
