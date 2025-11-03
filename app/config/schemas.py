"""
Schémas de données pour l'application bancaire
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from datetime import datetime, date
from enum import Enum
import pandas as pd

class Currency(Enum):
    """Devises supportées"""
    EUR = "EUR"
    USD = "USD"
    CNY = "CNY"

class Country(Enum):
    """Pays supportés"""
    FRANCE = "FR"
    UNITED_STATES = "US"
    CHINA = "CN"

class ProductClass(Enum):
    """Classes de produits financiers"""
    LOAN = "loan"
    DEPOSIT = "deposit"
    DERIVATIVE = "derivative"
    SECURITY = "security"
    COMMITMENT = "commitment"

class ExposureClass(Enum):
    """Classes d'exposition pour CRR3"""
    CENTRAL_GOVERNMENTS = "central_governments"
    REGIONAL_GOVERNMENTS = "regional_governments"
    PUBLIC_SECTOR_ENTITIES = "public_sector_entities"
    MULTILATERAL_DEVELOPMENT_BANKS = "multilateral_development_banks"
    INTERNATIONAL_ORGANISATIONS = "international_organisations"
    INSTITUTIONS = "institutions"
    CORPORATES = "corporates"
    RETAIL = "retail"
    SECURED_BY_MORTGAGES = "secured_by_mortgages"
    EXPOSURES_IN_DEFAULT = "exposures_in_default"
    HIGH_RISK_CATEGORIES = "high_risk_categories"
    COVERED_BONDS = "covered_bonds"
    CLAIMS_ON_INSTITUTIONS_AND_CORPORATES_SHORT_TERM = "claims_institutions_corporates_short_term"
    COLLECTIVE_INVESTMENT_UNDERTAKINGS = "collective_investment_undertakings"
    EQUITY = "equity"
    OTHER_ITEMS = "other_items"

class ECLStage(Enum):
    """Stages ECL IFRS 9"""
    STAGE_1 = 1  # 12 mois ECL
    STAGE_2 = 2  # Lifetime ECL
    STAGE_3 = 3  # Lifetime ECL (crédit dépréciés)

@dataclass
class EntitySchema:
    """Schéma pour les entités bancaires"""
    id: str
    name: str
    country: Country
    currency: Currency
    ownership_pct: float  # Pourcentage de détention par le groupe
    is_parent: bool = False
    
    def __post_init__(self):
        if not 0 <= self.ownership_pct <= 100:
            raise ValueError("ownership_pct doit être entre 0 et 100")

@dataclass
class FXRateSchema:
    """Schéma pour les taux de change"""
    date: date
    from_currency: Currency
    to_currency: Currency
    rate: float
    is_closing: bool = False  # Taux de clôture
    is_average: bool = False  # Taux moyen
    
    def __post_init__(self):
        if self.rate <= 0:
            raise ValueError("Le taux de change doit être positif")

@dataclass
class ProductSchema:
    """Schéma pour les produits financiers"""
    id: str
    name: str
    product_class: ProductClass
    exposure_class: ExposureClass
    is_retail: bool
    maturity_bucket: str  # "0-1Y", "1-5Y", "5Y+", etc.
    risk_weight_std: Optional[float] = None  # Pondération standardisée
    
    def __post_init__(self):
        if self.risk_weight_std is not None and self.risk_weight_std < 0:
            raise ValueError("risk_weight_std doit être positif ou nul")

@dataclass
class PositionSchema:
    """Schéma pour les positions"""
    entity_id: str
    product_id: str
    date: date
    ead: float  # Exposition au défaut
    eir: float  # Taux d'intérêt effectif
    pd: Optional[float] = None  # Probabilité de défaut
    lgd: Optional[float] = None  # Perte en cas de défaut
    ccf: Optional[float] = None  # Facteur de conversion crédit
    stage: ECLStage = ECLStage.STAGE_1
    provisions: float = 0.0
    mtm: Optional[float] = None  # Mark-to-market pour dérivés
    notional: Optional[float] = None  # Notionnel pour dérivés
    undrawn: float = 0.0  # Montant non tiré pour engagements
    
    def __post_init__(self):
        if self.ead < 0:
            raise ValueError("EAD doit être positif ou nul")
        if self.pd is not None and not 0 <= self.pd <= 1:
            raise ValueError("PD doit être entre 0 et 1")
        if self.lgd is not None and not 0 <= self.lgd <= 1:
            raise ValueError("LGD doit être entre 0 et 1")
        if self.ccf is not None and not 0 <= self.ccf <= 1:
            raise ValueError("CCF doit être entre 0 et 1")

@dataclass
class CashFlowSchema:
    """Schéma pour les flux de trésorerie"""
    entity_id: str
    product_id: str
    date: date
    interest_in: float = 0.0  # Intérêts reçus
    interest_out: float = 0.0  # Intérêts payés
    principal_in: float = 0.0  # Principal reçu
    principal_out: float = 0.0  # Principal payé
    fees: float = 0.0  # Commissions

@dataclass
class TrialBalanceSchema:
    """Schéma pour la balance"""
    entity_id: str
    account_code: str
    account_name: str
    amount_lcy: float  # Montant en devise locale
    amount_eur: float  # Montant en EUR
    account_type: str  # "ASSET", "LIABILITY", "EQUITY", "INCOME", "EXPENSE"

@dataclass
class IRBParametersSchema:
    """Paramètres IRB pour le calcul des RWA"""
    exposure_class: ExposureClass
    pd: float  # Probabilité de défaut
    lgd: float  # Perte en cas de défaut
    maturity: float = 2.5  # Maturité effective (défaut 2.5 ans)
    correlation: Optional[float] = None  # Corrélation (calculée si None)
    
    def __post_init__(self):
        if not 0 <= self.pd <= 1:
            raise ValueError("PD doit être entre 0 et 1")
        if not 0 <= self.lgd <= 1:
            raise ValueError("LGD doit être entre 0 et 1")
        if self.maturity <= 0:
            raise ValueError("Maturity doit être positive")

@dataclass
class LCRComponentSchema:
    """Composants pour le calcul LCR"""
    entity_id: str
    date: date
    hqla_level_1: float = 0.0  # Actifs liquides niveau 1
    hqla_level_2a: float = 0.0  # Actifs liquides niveau 2A
    hqla_level_2b: float = 0.0  # Actifs liquides niveau 2B
    cash_outflows_30d: float = 0.0  # Sorties de trésorerie 30 jours
    cash_inflows_30d: float = 0.0  # Entrées de trésorerie 30 jours
    
    @property
    def total_hqla(self) -> float:
        """HQLA total après haircuts"""
        return (self.hqla_level_1 + 
                self.hqla_level_2a * 0.85 + 
                self.hqla_level_2b * 0.75)
    
    @property
    def net_cash_outflows(self) -> float:
        """Sorties nettes de trésorerie"""
        return max(self.cash_outflows_30d - self.cash_inflows_30d * 0.75, 
                   self.cash_outflows_30d * 0.25)
    
    @property
    def lcr_ratio(self) -> float:
        """Ratio LCR"""
        if self.net_cash_outflows == 0:
            return float('inf')
        return self.total_hqla / self.net_cash_outflows

@dataclass
class NSFRComponentSchema:
    """Composants pour le calcul NSFR"""
    entity_id: str
    date: date
    available_stable_funding: float = 0.0  # ASF
    required_stable_funding: float = 0.0  # RSF
    
    @property
    def nsfr_ratio(self) -> float:
        """Ratio NSFR"""
        if self.required_stable_funding == 0:
            return float('inf')
        return self.available_stable_funding / self.required_stable_funding

# Schémas pour les mappings réglementaires
@dataclass
class FINREPMappingSchema:
    """Mapping vers les templates FINREP"""
    account_code: str
    finrep_code: str
    finrep_description: str
    sheet_name: str

@dataclass
class COREPMappingSchema:
    """Mapping vers les templates COREP"""
    exposure_class: ExposureClass
    corep_code: str
    corep_description: str
    sheet_name: str

# Fonctions utilitaires pour la validation
def validate_entity_data(entities: List[Dict]) -> List[EntitySchema]:
    """Valider et convertir les données d'entités"""
    validated_entities = []
    for entity_data in entities:
        try:
            entity = EntitySchema(
                id=entity_data['id'],
                name=entity_data['name'],
                country=Country(entity_data['country']),
                currency=Currency(entity_data['currency']),
                ownership_pct=float(entity_data['ownership_pct']),
                is_parent=entity_data.get('is_parent', False)
            )
            validated_entities.append(entity)
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Erreur de validation pour l'entité {entity_data}: {e}")
    
    return validated_entities

def validate_fx_rates(fx_data: List[Dict]) -> List[FXRateSchema]:
    """Valider et convertir les données de taux de change"""
    validated_rates = []
    for rate_data in fx_data:
        try:
            rate = FXRateSchema(
                date=pd.to_datetime(rate_data['date']).date(),
                from_currency=Currency(rate_data['from_currency']),
                to_currency=Currency(rate_data['to_currency']),
                rate=float(rate_data['rate']),
                is_closing=rate_data.get('is_closing', False),
                is_average=rate_data.get('is_average', False)
            )
            validated_rates.append(rate)
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Erreur de validation pour le taux de change {rate_data}: {e}")
    
    return validated_rates

def validate_products(products_data: List[Dict]) -> List[ProductSchema]:
    """Valider et convertir les données de produits"""
    validated_products = []
    for product_data in products_data:
        try:
            product = ProductSchema(
                id=product_data['id'],
                name=product_data['name'],
                product_class=ProductClass(product_data['product_class']),
                exposure_class=ExposureClass(product_data['exposure_class']),
                is_retail=bool(product_data['is_retail']),
                maturity_bucket=product_data['maturity_bucket'],
                risk_weight_std=product_data.get('risk_weight_std')
            )
            validated_products.append(product)
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Erreur de validation pour le produit {product_data}: {e}")
    
    return validated_products
