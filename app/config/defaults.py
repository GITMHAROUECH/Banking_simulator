"""
Configuration par défaut pour l'application bancaire
"""

from datetime import date
from .schemas import Currency, Country, ProductClass, ExposureClass

# Configuration par défaut
DEFAULT_CONFIG = {
    # Entités par défaut
    "entities": [
        {
            "id": "GROUP_HQ",
            "name": "Banking Group HQ",
            "country": "FR",
            "currency": "EUR",
            "ownership_pct": 100.0,
            "is_parent": True
        },
        {
            "id": "EU_SUB",
            "name": "European Subsidiary",
            "country": "FR",
            "currency": "EUR",
            "ownership_pct": 100.0,
            "is_parent": False
        },
        {
            "id": "US_SUB",
            "name": "US Subsidiary",
            "country": "US",
            "currency": "USD",
            "ownership_pct": 80.0,
            "is_parent": False
        },
        {
            "id": "CN_SUB",
            "name": "China Subsidiary",
            "country": "CN",
            "currency": "CNY",
            "ownership_pct": 60.0,
            "is_parent": False
        }
    ],
    
    # Taux de change par défaut
    "fx_rates": [
        {
            "date": "2024-12-31",
            "from_currency": "USD",
            "to_currency": "EUR",
            "rate": 1.10,
            "is_closing": True,
            "is_average": False
        },
        {
            "date": "2024-12-31",
            "from_currency": "CNY",
            "to_currency": "EUR",
            "rate": 7.85,
            "is_closing": True,
            "is_average": False
        },
        {
            "date": "2024-06-30",
            "from_currency": "USD",
            "to_currency": "EUR",
            "rate": 1.08,
            "is_closing": False,
            "is_average": True
        },
        {
            "date": "2024-06-30",
            "from_currency": "CNY",
            "to_currency": "EUR",
            "rate": 7.90,
            "is_closing": False,
            "is_average": True
        }
    ],
    
    # Produits par défaut
    "products": [
        # Prêts retail
        {
            "id": "RETAIL_MORTGAGE",
            "name": "Retail Mortgages",
            "product_class": "loan",
            "exposure_class": "secured_by_mortgages",
            "is_retail": True,
            "maturity_bucket": "5Y+",
            "risk_weight_std": 35.0
        },
        {
            "id": "RETAIL_CONSUMER",
            "name": "Retail Consumer Loans",
            "product_class": "loan",
            "exposure_class": "retail",
            "is_retail": True,
            "maturity_bucket": "1-5Y",
            "risk_weight_std": 75.0
        },
        {
            "id": "RETAIL_CREDIT_CARDS",
            "name": "Retail Credit Cards",
            "product_class": "loan",
            "exposure_class": "retail",
            "is_retail": True,
            "maturity_bucket": "0-1Y",
            "risk_weight_std": 75.0
        },
        
        # Prêts corporate
        {
            "id": "CORPORATE_LOANS",
            "name": "Corporate Loans",
            "product_class": "loan",
            "exposure_class": "corporates",
            "is_retail": False,
            "maturity_bucket": "1-5Y",
            "risk_weight_std": 100.0
        },
        {
            "id": "SME_LOANS",
            "name": "SME Loans",
            "product_class": "loan",
            "exposure_class": "corporates",
            "is_retail": False,
            "maturity_bucket": "1-5Y",
            "risk_weight_std": 85.0
        },
        
        # Dépôts
        {
            "id": "RETAIL_DEPOSITS",
            "name": "Retail Deposits",
            "product_class": "deposit",
            "exposure_class": "retail",
            "is_retail": True,
            "maturity_bucket": "0-1Y",
            "risk_weight_std": 0.0
        },
        {
            "id": "CORPORATE_DEPOSITS",
            "name": "Corporate Deposits",
            "product_class": "deposit",
            "exposure_class": "corporates",
            "is_retail": False,
            "maturity_bucket": "0-1Y",
            "risk_weight_std": 0.0
        },
        
        # Titres
        {
            "id": "GOVERNMENT_BONDS",
            "name": "Government Bonds",
            "product_class": "security",
            "exposure_class": "central_governments",
            "is_retail": False,
            "maturity_bucket": "1-5Y",
            "risk_weight_std": 0.0
        },
        {
            "id": "CORPORATE_BONDS",
            "name": "Corporate Bonds",
            "product_class": "security",
            "exposure_class": "corporates",
            "is_retail": False,
            "maturity_bucket": "1-5Y",
            "risk_weight_std": 100.0
        },
        
        # Dérivés
        {
            "id": "INTEREST_RATE_SWAPS",
            "name": "Interest Rate Swaps",
            "product_class": "derivative",
            "exposure_class": "institutions",
            "is_retail": False,
            "maturity_bucket": "1-5Y",
            "risk_weight_std": 100.0
        },
        
        # Engagements
        {
            "id": "CREDIT_LINES",
            "name": "Credit Lines",
            "product_class": "commitment",
            "exposure_class": "corporates",
            "is_retail": False,
            "maturity_bucket": "0-1Y",
            "risk_weight_std": 100.0
        }
    ],
    
    # Paramètres IRB par défaut
    "irb_parameters": {
        "retail": {
            "mortgages": {
                "pd": 0.015,  # 1.5%
                "lgd": 0.20,  # 20%
                "maturity": 15.0
            },
            "consumer": {
                "pd": 0.025,  # 2.5%
                "lgd": 0.45,  # 45%
                "maturity": 3.0
            },
            "credit_cards": {
                "pd": 0.035,  # 3.5%
                "lgd": 0.85,  # 85%
                "maturity": 1.0
            }
        }
    },
    
    # Pondérations de risque standardisées
    "standard_risk_weights": {
        "central_governments": 0.0,
        "regional_governments": 0.20,
        "public_sector_entities": 0.20,
        "multilateral_development_banks": 0.0,
        "international_organisations": 0.0,
        "institutions": 0.20,
        "corporates": 1.00,
        "retail": 0.75,
        "secured_by_mortgages": 0.35,
        "exposures_in_default": 1.50,
        "high_risk_categories": 1.50,
        "covered_bonds": 0.10,
        "claims_institutions_corporates_short_term": 0.20,
        "collective_investment_undertakings": 1.00,
        "equity": 1.00,
        "other_items": 1.00
    },
    
    # Facteurs de conversion crédit (CCF)
    "ccf_factors": {
        "credit_lines_unconditionally_cancellable": 0.0,
        "credit_lines_original_maturity_1y": 0.20,
        "credit_lines_original_maturity_1y_plus": 0.50,
        "note_issuance_facilities": 0.50,
        "revolving_underwriting_facilities": 0.50,
        "other_commitments": 1.00
    },
    
    # Paramètres LCR
    "lcr_parameters": {
        "hqla_haircuts": {
            "level_1": 0.0,
            "level_2a": 0.15,
            "level_2b": 0.25
        },
        "outflow_rates": {
            "retail_deposits_stable": 0.05,
            "retail_deposits_less_stable": 0.10,
            "operational_deposits": 0.25,
            "non_operational_deposits": 1.00,
            "secured_funding": 0.0
        },
        "inflow_rates": {
            "secured_lending": 0.0,
            "inflows_from_fully_performing": 0.50,
            "other_contractual_inflows": 1.00
        }
    },
    
    # Paramètres NSFR
    "nsfr_parameters": {
        "asf_factors": {
            "capital": 1.00,
            "retail_deposits_stable": 0.95,
            "retail_deposits_less_stable": 0.90,
            "operational_deposits": 0.50,
            "other_wholesale_funding": 0.50
        },
        "rsf_factors": {
            "coins_banknotes": 0.0,
            "central_bank_reserves": 0.0,
            "hqla_level_1": 0.05,
            "hqla_level_2a": 0.15,
            "hqla_level_2b": 0.50,
            "loans_to_financial_institutions": 0.85,
            "loans_to_non_financial_corporates": 0.85,
            "retail_mortgages": 0.65,
            "other_retail_loans": 0.85
        }
    },
    
    # Plan comptable simplifié
    "chart_of_accounts": {
        # Actif
        "1000": {"name": "Caisse et banques centrales", "type": "ASSET"},
        "1100": {"name": "Prêts et créances sur établissements de crédit", "type": "ASSET"},
        "1200": {"name": "Prêts et créances sur clientèle", "type": "ASSET"},
        "1300": {"name": "Titres financiers", "type": "ASSET"},
        "1400": {"name": "Dérivés actifs", "type": "ASSET"},
        "1500": {"name": "Immobilisations", "type": "ASSET"},
        "1900": {"name": "Autres actifs", "type": "ASSET"},
        
        # Passif
        "2000": {"name": "Banques centrales", "type": "LIABILITY"},
        "2100": {"name": "Dettes envers établissements de crédit", "type": "LIABILITY"},
        "2200": {"name": "Dettes envers clientèle", "type": "LIABILITY"},
        "2300": {"name": "Titres de dette émis", "type": "LIABILITY"},
        "2400": {"name": "Dérivés passifs", "type": "LIABILITY"},
        "2500": {"name": "Provisions", "type": "LIABILITY"},
        "2900": {"name": "Autres passifs", "type": "LIABILITY"},
        
        # Capitaux propres
        "3000": {"name": "Capital", "type": "EQUITY"},
        "3100": {"name": "Réserves", "type": "EQUITY"},
        "3200": {"name": "Résultat reporté", "type": "EQUITY"},
        "3300": {"name": "Résultat de l'exercice", "type": "EQUITY"},
        "3400": {"name": "Intérêts minoritaires", "type": "EQUITY"},
        
        # Produits
        "7000": {"name": "Intérêts et produits assimilés", "type": "INCOME"},
        "7100": {"name": "Commissions perçues", "type": "INCOME"},
        "7200": {"name": "Gains sur opérations financières", "type": "INCOME"},
        "7900": {"name": "Autres produits", "type": "INCOME"},
        
        # Charges
        "6000": {"name": "Intérêts et charges assimilées", "type": "EXPENSE"},
        "6100": {"name": "Commissions versées", "type": "EXPENSE"},
        "6200": {"name": "Pertes sur opérations financières", "type": "EXPENSE"},
        "6300": {"name": "Charges générales d'exploitation", "type": "EXPENSE"},
        "6400": {"name": "Dotations aux amortissements", "type": "EXPENSE"},
        "6500": {"name": "Coût du risque", "type": "EXPENSE"},
        "6900": {"name": "Autres charges", "type": "EXPENSE"}
    },
    
    # Mapping FINREP
    "finrep_mapping": {
        "1000": {"finrep_code": "010", "description": "Cash, cash balances at central banks", "sheet": "BS"},
        "1100": {"finrep_code": "020", "description": "Financial assets held for trading", "sheet": "BS"},
        "1200": {"finrep_code": "040", "description": "Financial assets at amortised cost", "sheet": "BS"},
        "1300": {"finrep_code": "050", "description": "Financial assets at fair value", "sheet": "BS"},
        "2200": {"finrep_code": "010", "description": "Financial liabilities held for trading", "sheet": "BS"},
        "2300": {"finrep_code": "020", "description": "Financial liabilities at amortised cost", "sheet": "BS"},
        "3000": {"finrep_code": "010", "description": "Capital", "sheet": "BS"},
        "7000": {"finrep_code": "010", "description": "Interest income", "sheet": "PL"},
        "6000": {"finrep_code": "020", "description": "Interest expenses", "sheet": "PL"}
    },
    
    # Dates par défaut
    "dates": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "reporting_date": "2024-12-31"
    },
    
    # Paramètres de simulation
    "simulation": {
        "seed": 42,
        "monthly_granularity": True,
        "include_seasonality": True,
        "stress_scenarios": False
    }
}

# Constantes réglementaires CRR3
CRR3_CONSTANTS = {
    "minimum_capital_ratio": 0.08,  # 8%
    "capital_conservation_buffer": 0.025,  # 2.5%
    "leverage_ratio_minimum": 0.03,  # 3%
    "lcr_minimum": 1.00,  # 100%
    "nsfr_minimum": 1.00,  # 100%
    
    # Corrélations IRB
    "irb_correlations": {
        "corporate": {
            "large": 0.24,
            "sme": 0.12
        },
        "retail": {
            "mortgage": 0.15,
            "revolving": 0.04,
            "other": 0.03
        }
    },
    
    # Maturités par défaut
    "default_maturities": {
        "corporate": 2.5,
        "retail": 1.0,
        "mortgage": 2.5
    }
}

# Templates Excel par défaut
EXCEL_TEMPLATES = {
    "input_entities": {
        "sheet_name": "Entities",
        "columns": ["id", "name", "country", "currency", "ownership_pct", "is_parent"]
    },
    "input_fx": {
        "sheet_name": "FX_Rates",
        "columns": ["date", "from_currency", "to_currency", "rate", "is_closing", "is_average"]
    },
    "input_portfolios": {
        "sheet_name": "Portfolios",
        "columns": ["entity_id", "product_id", "ead", "eir", "pd", "lgd", "ccf", "stage", "undrawn"]
    }
}
