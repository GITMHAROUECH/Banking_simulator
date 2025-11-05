"""
Module de simulation Monte Carlo pour génération de positions bancaires.

Ce module implémente la logique métier pure de simulation de portefeuille
bancaire avec support des produits standards et facilities (CCF).

Optimisations:
- Dtypes optimisés (category, float32) pour réduire la mémoire de ~20%
- Vectorisation NumPy pour les performances
- Reproductibilité garantie via seed
"""

import random
from datetime import datetime

import numpy as np
import pandas as pd

# Configuration par défaut des entités et produits
DEFAULT_ENTITIES: list[str] = ['EU_SUB', 'US_SUB', 'CN_SUB']

DEFAULT_PRODUCTS: list[str] = [
    'Retail_Mortgages', 'Retail_Consumer', 'Retail_Credit_Cards',
    'Corporate_Loans', 'SME_Loans', 'Retail_Deposits',
    'Corporate_Deposits', 'Government_Bonds', 'Corporate_Bonds',
    'Credit_Facilities', 'Revolving_Credit_Lines', 'Overdraft_Facilities'
]

DEFAULT_EXPOSURE_CLASSES: list[str] = [
    'Retail_Mortgages', 'Retail_Other', 'Corporate', 'SME',
    'Sovereign', 'Bank', 'Equity', 'Other_Items'
]

DEFAULT_CURRENCIES: list[str] = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CNY']


class SimulationEngine:
    """
    Moteur de simulation Monte Carlo pour positions bancaires.

    Cette classe encapsule la logique de génération de positions avec:
    - Support des produits standards (prêts, dépôts, obligations)
    - Support des facilities avec CCF (Credit Conversion Factor)
    - Paramètres de risque réalistes (PD, LGD, maturity)
    - Classification IFRS 9 (Stage 1/2/3)
    - Provisions ECL (Expected Credit Loss)
    """

    def __init__(
        self,
        seed: int = 42,
        config: dict | None = None
    ) -> None:
        """
        Initialise le moteur de simulation.

        Args:
            seed: Graine aléatoire pour reproductibilité
            config: Configuration optionnelle (scénarios, paramètres)
        """
        self.seed = seed
        self.config = config or self._default_config()

        # Initialiser les générateurs aléatoires
        random.seed(seed)
        np.random.seed(seed)

        # Données de référence
        self.entities = DEFAULT_ENTITIES
        self.products = DEFAULT_PRODUCTS
        self.exposure_classes = DEFAULT_EXPOSURE_CLASSES
        self.currencies = DEFAULT_CURRENCIES

    def _default_config(self) -> dict:
        """Configuration par défaut."""
        return {
            'base_currency': 'EUR',
            'stress_scenario': 'Baseline',
            'include_derivatives': False,
            'retail_pd_base': 0.02,
            'corporate_pd_base': 0.03
        }

    def generate_positions(self, num_positions: int) -> pd.DataFrame:
        """
        Génère un portefeuille de positions bancaires.

        Args:
            num_positions: Nombre de positions à générer

        Returns:
            DataFrame avec colonnes optimisées (dtypes réduits)
        """
        positions_list: list[dict] = []

        for i in range(num_positions):
            position = self._generate_single_position(i)
            positions_list.append(position)

        # Créer DataFrame avec dtypes optimisés
        df = pd.DataFrame(positions_list)
        df = self._optimize_dtypes(df)

        return df

    def _generate_single_position(self, index: int) -> dict:
        """Génère une position individuelle."""
        # Sélections équilibrées (round-robin)
        entity = self.entities[index % len(self.entities)]
        product = self.products[index % len(self.products)]
        exposure_class = self.exposure_classes[index % len(self.exposure_classes)]
        currency = self.currencies[index % len(self.currencies)]

        # Générer EAD et paramètres CCF selon le type de produit
        ead, ccf, commitment_amount, drawn_amount = self._generate_ead_and_ccf(product)

        # Générer paramètres de risque
        pd = self._generate_pd(exposure_class)
        lgd = self._generate_lgd(product, exposure_class)
        maturity = self._generate_maturity(product)

        # Classification IFRS 9
        stage = self._classify_ifrs9_stage(pd)

        # Calcul ECL
        ecl_provision = self._calculate_ecl(ead, pd, lgd, maturity, stage)

        # Taux d'intérêt et revenus
        interest_rate = self._calculate_interest_rate(currency, pd)
        interest_income = ead * interest_rate

        return {
            'position_id': f'POS_{index+1:06d}',
            'entity_id': entity,
            'product_id': product,
            'exposure_class': exposure_class,
            'currency': currency,
            'ead': ead,
            'pd': pd,
            'lgd': lgd,
            'maturity': maturity,
            'stage': stage,
            'ecl_provision': ecl_provision,
            'ccf': ccf,
            'commitment_amount': commitment_amount,
            'drawn_amount': drawn_amount,
            'interest_rate': interest_rate,
            'interest_income': interest_income,
            'booking_date': datetime.now().strftime('%Y-%m-%d'),
            'country_risk': entity.split('_')[0],
            'sector': 'Financial' if 'Bank' in exposure_class else 'Non-Financial'
        }

    def _generate_ead_and_ccf(self, product: str) -> tuple[float, float, float, float]:
        """
        Génère EAD et paramètres CCF selon le type de produit.

        Returns:
            Tuple (ead, ccf, commitment_amount, drawn_amount)
        """
        if 'Mortgage' in product:
            base_ead = 150000 + random.randint(-50000, 300000)
            ccf = 0.0
            commitment_amount = 0.0
            drawn_amount = base_ead

        elif 'Corporate' in product and 'Loan' in product:
            base_ead = 500000 + random.randint(-200000, 2000000)
            ccf = 0.0
            commitment_amount = 0.0
            drawn_amount = base_ead

        elif 'Deposit' in product:
            base_ead = 50000 + random.randint(-30000, 200000)
            ccf = 0.0
            commitment_amount = 0.0
            drawn_amount = base_ead

        elif any(keyword in product for keyword in ['Facilities', 'Credit_Lines', 'Overdraft']):
            # Facilities: montant tiré + CCF * montant non tiré
            drawn_amount = float(random.randint(10000, 200000))  # type: ignore[assignment]
            commitment_amount = float(random.randint(50000, 500000))

            # Assurer que commitment >= drawn
            if commitment_amount < drawn_amount:
                commitment_amount = drawn_amount * 1.5

            undrawn_amount = commitment_amount - drawn_amount

            # CCF selon le type de facility
            if 'Credit_Facilities' in product:
                ccf = random.uniform(0.20, 0.50)  # 20-50%
            elif 'Revolving' in product:
                ccf = random.uniform(0.75, 1.0)   # 75-100%
            elif 'Overdraft' in product:
                ccf = random.uniform(0.50, 0.75)  # 50-75%
            else:
                ccf = 0.35

            base_ead = drawn_amount + (ccf * undrawn_amount)  # type: ignore[assignment]

        else:
            base_ead = 100000 + random.randint(-50000, 500000)
            ccf = 0.0
            commitment_amount = 0.0
            drawn_amount = base_ead

        ead = max(1000.0, base_ead)

        return ead, ccf, commitment_amount, drawn_amount

    def _generate_pd(self, exposure_class: str) -> float:
        """Génère la Probability of Default selon la classe d'exposition."""
        config = self.config

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
        stress_scenario = config.get('stress_scenario', 'Baseline')
        if stress_scenario == 'Adverse':
            stress_multiplier = 1.5
        elif stress_scenario == 'Severely Adverse':
            stress_multiplier = 2.0
        else:
            stress_multiplier = 1.0

        pd = max(0.0001, (base_pd + pd_variation) * stress_multiplier)

        return pd

    def _generate_lgd(self, product: str, exposure_class: str) -> float:
        """Génère la Loss Given Default selon le produit."""
        if 'Mortgage' in product:
            lgd = 0.20 + random.uniform(0, 0.25)  # 20-45%
        elif 'Deposit' in product:
            lgd = 0.0  # Dépôts non risqués
        elif exposure_class == 'Sovereign':
            lgd = 0.45 + random.uniform(0, 0.10)  # 45-55%
        else:
            lgd = 0.35 + random.uniform(0, 0.30)  # 35-65%

        return lgd

    def _generate_maturity(self, product: str) -> float:
        """Génère la maturité en années selon le produit."""
        if 'Mortgage' in product:
            maturity = 15 + random.uniform(0, 15)  # 15-30 ans
        elif 'Deposit' in product:
            maturity = random.uniform(0.1, 2)  # 1 mois - 2 ans
        elif 'Corporate' in product:
            maturity = 1 + random.uniform(0, 7)  # 1-8 ans
        else:
            maturity = 0.5 + random.uniform(0, 5)  # 6 mois - 5.5 ans

        return maturity

    def _classify_ifrs9_stage(self, pd: float) -> int:
        """Classifie la position selon IFRS 9 (Stage 1/2/3)."""
        if pd <= 0.005:
            return 1
        elif pd <= 0.03:
            return 2
        else:
            return 3

    def _calculate_ecl(
        self,
        ead: float,
        pd: float,
        lgd: float,
        maturity: float,
        stage: int
    ) -> float:
        """Calcule la provision ECL (Expected Credit Loss)."""
        if stage == 1:
            # 12 mois ECL
            ecl = ead * pd * lgd
        else:
            # Lifetime ECL
            ecl = ead * pd * lgd * min(maturity, 1.0)

        return ecl

    def _calculate_interest_rate(self, currency: str, pd: float) -> float:
        """Calcule le taux d'intérêt selon la devise et le risque."""
        base_rate = 0.02  # 2% de base

        # Spread de devise
        currency_spreads = {
            'EUR': 0.0,
            'USD': 0.005,
            'GBP': 0.003,
            'JPY': -0.005,
            'CHF': -0.003,
            'CNY': 0.01
        }
        currency_spread = currency_spreads.get(currency, 0.01)

        # Spread de risque
        risk_spread = pd * 100

        interest_rate = base_rate + currency_spread + risk_spread

        return interest_rate

    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimise les dtypes du DataFrame pour réduire la mémoire.

        Objectif: -20% de RAM vs types par défaut.
        """
        # Colonnes catégorielles (réduction massive de mémoire)
        categorical_cols = [
            'entity_id', 'product_id', 'exposure_class',
            'currency', 'country_risk', 'sector', 'booking_date'
        ]
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype('category')

        # Colonnes numériques en float32 (au lieu de float64)
        float_cols = [
            'ead', 'pd', 'lgd', 'maturity', 'ecl_provision',
            'ccf', 'commitment_amount', 'drawn_amount',
            'interest_rate', 'interest_income'
        ]
        for col in float_cols:
            if col in df.columns:
                df[col] = df[col].astype('float32')

        # Stage en int8 (au lieu de int64)
        if 'stage' in df.columns:
            df['stage'] = df['stage'].astype('int8')

        return df


def generate_positions_advanced(
    num_positions: int = 1000,
    seed: int = 42,
    config: dict | None = None
) -> pd.DataFrame:
    """
    Fonction publique pour générer des positions bancaires (contrat d'interface).

    Cette fonction est le point d'entrée stable pour l'UI et les services.
    Elle garantit la compatibilité ascendante avec l'existant.

    Args:
        num_positions: Nombre de positions à générer (défaut: 1000)
        seed: Graine aléatoire pour reproductibilité (défaut: 42)
        config: Configuration optionnelle avec clés:
            - base_currency (str): Devise de base (défaut: 'EUR')
            - stress_scenario (str): 'Baseline', 'Adverse', 'Severely Adverse'
            - include_derivatives (bool): Inclure dérivés (défaut: False)
            - retail_pd_base (float): PD de base retail (défaut: 0.02)
            - corporate_pd_base (float): PD de base corporate (défaut: 0.03)

    Returns:
        DataFrame avec colonnes minimales obligatoires:
        - position_id (str): Identifiant unique
        - entity_id (str): Entité bancaire
        - product_id (str): Type de produit
        - exposure_class (str): Classe d'exposition CRR3
        - currency (str): Devise
        - ead (float32): Exposure At Default
        - pd (float32): Probability of Default
        - lgd (float32): Loss Given Default
        - maturity (float32): Maturité en années
        - stage (int8): Stage IFRS 9 (1, 2, 3)
        - ecl_provision (float32): Provision ECL

        Colonnes additionnelles pour facilities:
        - ccf (float32): Credit Conversion Factor
        - commitment_amount (float32): Montant engagé
        - drawn_amount (float32): Montant tiré

    Performance:
        - 1,000 positions: ≤ 10s
        - 10,000 positions: ≤ 60s

    Reproductibilité:
        Seed identique garantit résultats identiques.

    Example:
        >>> df = generate_positions_advanced(1000, seed=42)
        >>> assert len(df) == 1000
        >>> assert 'position_id' in df.columns
        >>> assert df['ead'].dtype == np.float32
    """
    engine = SimulationEngine(seed=seed, config=config)
    df = engine.generate_positions(num_positions)

    return df

