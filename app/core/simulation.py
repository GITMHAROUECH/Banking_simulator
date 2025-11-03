"""
Moteur de simulation pour l'application bancaire
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import asdict

from ..config.schemas import (
    EntitySchema, ProductSchema, PositionSchema, CashFlowSchema,
    ECLStage, ProductClass, ExposureClass
)
from ..config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class SimulationEngine:
    """Moteur de simulation des positions et flux bancaires"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.entities = self._load_entities()
        self.products = self._load_products()
        self.start_date = pd.to_datetime(config['dates']['start']).date()
        self.end_date = pd.to_datetime(config['dates']['end']).date()
        self.seed = config.get('scenario_seed', 42)
        
        # Initialiser le générateur aléatoire
        np.random.seed(self.seed)
        
        logger.info(f"Moteur de simulation initialisé avec seed {self.seed}")
    
    def _load_entities(self) -> List[EntitySchema]:
        """Charger les entités depuis la configuration"""
        entities = []
        for entity_data in DEFAULT_CONFIG['entities']:
            if not entity_data['is_parent']:  # Exclure le HQ pour la simulation
                entity = EntitySchema(
                    id=entity_data['id'],
                    name=entity_data['name'],
                    country=entity_data['country'],
                    currency=entity_data['currency'],
                    ownership_pct=self.config['ownership'].get(
                        entity_data['id'].split('_')[0], 
                        entity_data['ownership_pct']
                    )
                )
                entities.append(entity)
        return entities
    
    def _load_products(self) -> List[ProductSchema]:
        """Charger les produits depuis la configuration"""
        products = []
        for product_data in DEFAULT_CONFIG['products']:
            product = ProductSchema(
                id=product_data['id'],
                name=product_data['name'],
                product_class=ProductClass(product_data['product_class']),
                exposure_class=ExposureClass(product_data['exposure_class']),
                is_retail=product_data['is_retail'],
                maturity_bucket=product_data['maturity_bucket'],
                risk_weight_std=product_data.get('risk_weight_std')
            )
            products.append(product)
        return products
    
    def run_simulation(self) -> Dict[str, pd.DataFrame]:
        """Exécuter la simulation complète"""
        logger.info("Début de la simulation")
        
        try:
            # Générer les positions initiales
            positions = self._generate_initial_positions()
            
            # Simuler l'évolution mensuelle
            monthly_positions = self._simulate_monthly_evolution(positions)
            
            # Générer les flux de trésorerie
            cash_flows = self._generate_cash_flows(monthly_positions)
            
            # Calculer les provisions ECL
            positions_with_ecl = self._calculate_ecl_provisions(monthly_positions)
            
            # Simuler les dérivés
            derivatives_data = self._simulate_derivatives()
            
            # Assembler les résultats
            results = {
                'positions': positions_with_ecl,
                'cash_flows': cash_flows,
                'derivatives': derivatives_data,
                'summary': self._generate_summary(positions_with_ecl, cash_flows)
            }
            
            logger.info("Simulation terminée avec succès")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la simulation: {e}")
            raise
    
    def _generate_initial_positions(self) -> pd.DataFrame:
        """Générer les positions initiales"""
        positions_data = []
        
        for entity in self.entities:
            # Taille de portefeuille selon l'entité
            portfolio_size = self.config['portfolio_sizes'].get(
                entity.id.split('_')[0], 1000.0
            )
            
            for product in self.products:
                # Calculer la taille de position selon le type de produit
                position_size = self._calculate_position_size(
                    entity, product, portfolio_size
                )
                
                if position_size > 0:
                    # Générer les paramètres de risque
                    risk_params = self._generate_risk_parameters(entity, product)
                    
                    # Créer la position
                    position = PositionSchema(
                        entity_id=entity.id,
                        product_id=product.id,
                        date=self.start_date,
                        ead=position_size,
                        eir=risk_params['eir'],
                        pd=risk_params.get('pd'),
                        lgd=risk_params.get('lgd'),
                        ccf=risk_params.get('ccf', 0.0),
                        stage=ECLStage.STAGE_1,
                        undrawn=risk_params.get('undrawn', 0.0)
                    )
                    
                    positions_data.append(asdict(position))
        
        df = pd.DataFrame(positions_data)
        logger.info(f"Généré {len(df)} positions initiales")
        return df
    
    def _calculate_position_size(self, entity: EntitySchema, product: ProductSchema, 
                               portfolio_size: float) -> float:
        """Calculer la taille d'une position"""
        # Facteurs de taille selon le type de produit
        size_factors = {
            ProductClass.LOAN: np.random.uniform(0.15, 0.25),
            ProductClass.DEPOSIT: np.random.uniform(0.20, 0.35),
            ProductClass.SECURITY: np.random.uniform(0.05, 0.15),
            ProductClass.DERIVATIVE: np.random.uniform(0.02, 0.08),
            ProductClass.COMMITMENT: np.random.uniform(0.03, 0.10)
        }
        
        base_factor = size_factors.get(product.product_class, 0.1)
        
        # Ajustement selon l'entité
        if entity.id == 'EU_SUB':
            entity_factor = 1.0
        elif entity.id == 'US_SUB':
            entity_factor = 0.8
        else:  # CN_SUB
            entity_factor = 0.6
        
        # Ajustement selon retail/corporate
        retail_factor = 0.7 if product.is_retail else 1.3
        
        # Ajouter de la variabilité
        variability = np.random.uniform(0.8, 1.2)
        
        return portfolio_size * base_factor * entity_factor * retail_factor * variability
    
    def _generate_risk_parameters(self, entity: EntitySchema, 
                                product: ProductSchema) -> Dict:
        """Générer les paramètres de risque pour une position"""
        params = {}
        
        # Taux d'intérêt effectif
        if product.product_class == ProductClass.LOAN:
            params['eir'] = np.random.uniform(0.02, 0.06)
        elif product.product_class == ProductClass.DEPOSIT:
            params['eir'] = np.random.uniform(0.001, 0.02)
        elif product.product_class == ProductClass.SECURITY:
            params['eir'] = np.random.uniform(0.01, 0.04)
        else:
            params['eir'] = np.random.uniform(0.005, 0.03)
        
        # Paramètres de crédit pour les expositions de crédit
        if product.product_class in [ProductClass.LOAN, ProductClass.COMMITMENT]:
            if product.is_retail:
                # Utiliser les paramètres IRB configurés
                irb_params = self.config.get('irb_params', {})
                params['pd'] = irb_params.get('retail_pd', np.random.uniform(0.01, 0.05))
                params['lgd'] = irb_params.get('retail_lgd', np.random.uniform(0.20, 0.60))
            else:
                params['pd'] = np.random.uniform(0.005, 0.03)
                params['lgd'] = np.random.uniform(0.30, 0.70)
            
            # CCF pour les engagements
            if product.product_class == ProductClass.COMMITMENT:
                params['ccf'] = 0.50
                params['undrawn'] = np.random.uniform(0.4, 0.8)  # Fraction non tirée
        
        return params
    
    def _simulate_monthly_evolution(self, initial_positions: pd.DataFrame) -> pd.DataFrame:
        """Simuler l'évolution mensuelle des positions"""
        all_positions = []
        current_positions = initial_positions.copy()
        
        # Générer les positions pour chaque mois
        current_date = self.start_date
        while current_date <= self.end_date:
            # Copier les positions actuelles avec la nouvelle date
            monthly_positions = current_positions.copy()
            monthly_positions['date'] = current_date
            
            # Appliquer l'évolution mensuelle
            monthly_positions = self._apply_monthly_changes(monthly_positions, current_date)
            
            all_positions.append(monthly_positions)
            
            # Mois suivant
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
            
            # Mettre à jour les positions pour le mois suivant
            current_positions = monthly_positions.copy()
        
        result = pd.concat(all_positions, ignore_index=True)
        logger.info(f"Simulé {len(result)} positions mensuelles")
        return result
    
    def _apply_monthly_changes(self, positions: pd.DataFrame, current_date: date) -> pd.DataFrame:
        """Appliquer les changements mensuels aux positions"""
        # Croissance/décroissance des portefeuilles
        growth_factor = np.random.uniform(0.98, 1.02)  # ±2% par mois
        positions['ead'] *= growth_factor
        
        # Évolution des paramètres de risque
        # PD peut évoluer selon les conditions économiques
        if 'pd' in positions.columns:
            pd_volatility = np.random.normal(1.0, 0.05, len(positions))
            positions['pd'] *= pd_volatility
            positions['pd'] = np.clip(positions['pd'], 0.001, 0.20)  # Borner entre 0.1% et 20%
        
        # Migration des stages ECL
        positions = self._simulate_ecl_migration(positions)
        
        # Remboursements et nouveaux crédits
        positions = self._simulate_portfolio_turnover(positions)
        
        return positions
    
    def _simulate_ecl_migration(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Simuler la migration entre les stages ECL"""
        # Probabilités de migration
        migration_probs = {
            1: {'stay': 0.95, 'to_2': 0.04, 'to_3': 0.01},
            2: {'to_1': 0.30, 'stay': 0.65, 'to_3': 0.05},
            3: {'to_1': 0.10, 'to_2': 0.20, 'stay': 0.70}
        }
        
        for idx, row in positions.iterrows():
            current_stage = row['stage']
            rand = np.random.random()
            
            if current_stage == 1:
                if rand < migration_probs[1]['to_2']:
                    positions.at[idx, 'stage'] = 2
                elif rand < migration_probs[1]['to_2'] + migration_probs[1]['to_3']:
                    positions.at[idx, 'stage'] = 3
            elif current_stage == 2:
                if rand < migration_probs[2]['to_1']:
                    positions.at[idx, 'stage'] = 1
                elif rand < migration_probs[2]['to_1'] + migration_probs[2]['to_3']:
                    positions.at[idx, 'stage'] = 3
            elif current_stage == 3:
                if rand < migration_probs[3]['to_1']:
                    positions.at[idx, 'stage'] = 1
                elif rand < migration_probs[3]['to_1'] + migration_probs[3]['to_2']:
                    positions.at[idx, 'stage'] = 2
        
        return positions
    
    def _simulate_portfolio_turnover(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Simuler le renouvellement du portefeuille"""
        # Taux de remboursement mensuel selon le type de produit
        prepayment_rates = {
            'RETAIL_MORTGAGE': 0.005,  # 0.5% par mois
            'RETAIL_CONSUMER': 0.02,   # 2% par mois
            'RETAIL_CREDIT_CARDS': 0.15,  # 15% par mois (revolving)
            'CORPORATE_LOANS': 0.01,   # 1% par mois
            'SME_LOANS': 0.015         # 1.5% par mois
        }
        
        for product_id, rate in prepayment_rates.items():
            mask = positions['product_id'] == product_id
            if mask.any():
                # Appliquer les remboursements
                prepayment_factor = np.random.uniform(0.8, 1.2) * rate
                positions.loc[mask, 'ead'] *= (1 - prepayment_factor)
        
        return positions
    
    def _generate_cash_flows(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Générer les flux de trésorerie"""
        cash_flows_data = []
        
        # Grouper par entité, produit et date
        grouped = positions.groupby(['entity_id', 'product_id', 'date'])
        
        for (entity_id, product_id, date), group in grouped:
            total_ead = group['ead'].sum()
            avg_eir = group['eir'].mean()
            
            # Calculer les intérêts mensuels
            monthly_interest = total_ead * avg_eir / 12
            
            # Déterminer si c'est un actif ou un passif
            product_info = next((p for p in self.products if p.id == product_id), None)
            
            if product_info:
                if product_info.product_class in [ProductClass.LOAN, ProductClass.SECURITY]:
                    # Actif - intérêts reçus
                    interest_in = monthly_interest
                    interest_out = 0.0
                elif product_info.product_class == ProductClass.DEPOSIT:
                    # Passif - intérêts payés
                    interest_in = 0.0
                    interest_out = monthly_interest
                else:
                    # Autres produits
                    interest_in = monthly_interest * 0.5
                    interest_out = monthly_interest * 0.5
                
                # Flux de principal (remboursements)
                principal_flow = total_ead * 0.01  # 1% par mois en moyenne
                
                cash_flow = CashFlowSchema(
                    entity_id=entity_id,
                    product_id=product_id,
                    date=date,
                    interest_in=interest_in,
                    interest_out=interest_out,
                    principal_in=principal_flow if product_info.product_class == ProductClass.LOAN else 0.0,
                    principal_out=principal_flow if product_info.product_class == ProductClass.DEPOSIT else 0.0,
                    fees=total_ead * 0.001  # 0.1% de commissions
                )
                
                cash_flows_data.append(asdict(cash_flow))
        
        df = pd.DataFrame(cash_flows_data)
        logger.info(f"Généré {len(df)} flux de trésorerie")
        return df
    
    def _calculate_ecl_provisions(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Calculer les provisions ECL"""
        positions_copy = positions.copy()
        
        # Calculer les provisions selon le stage
        def calculate_provision(row):
            if pd.isna(row['pd']) or pd.isna(row['lgd']):
                return 0.0
            
            if row['stage'] == 1:
                # 12 mois ECL
                return row['ead'] * row['pd'] * row['lgd'] * (1/12)
            else:
                # Lifetime ECL (stages 2 et 3)
                lifetime_pd = min(row['pd'] * 5, 1.0)  # Approximation sur 5 ans
                return row['ead'] * lifetime_pd * row['lgd']
        
        positions_copy['provisions'] = positions_copy.apply(calculate_provision, axis=1)
        
        return positions_copy
    
    def _simulate_derivatives(self) -> pd.DataFrame:
        """Simuler les positions sur dérivés"""
        derivatives_data = []
        
        for entity in self.entities:
            # Swaps de taux d'intérêt
            notional = np.random.uniform(50, 200)  # M€
            mtm = np.random.normal(0, notional * 0.02)  # MTM avec volatilité
            
            derivatives_data.append({
                'entity_id': entity.id,
                'product_id': 'INTEREST_RATE_SWAPS',
                'date': self.end_date,
                'notional': notional,
                'mtm': mtm,
                'type': 'IRS',
                'maturity': '5Y',
                'counterparty_type': 'Bank'
            })
        
        return pd.DataFrame(derivatives_data)
    
    def _generate_summary(self, positions: pd.DataFrame, cash_flows: pd.DataFrame) -> pd.DataFrame:
        """Générer un résumé de la simulation"""
        # Résumé par entité
        entity_summary = positions.groupby('entity_id').agg({
            'ead': 'sum',
            'provisions': 'sum',
            'undrawn': 'sum'
        }).round(2)
        
        # Ajouter les flux de trésorerie
        cf_summary = cash_flows.groupby('entity_id').agg({
            'interest_in': 'sum',
            'interest_out': 'sum',
            'fees': 'sum'
        }).round(2)
        
        summary = entity_summary.join(cf_summary, how='left')
        summary['net_interest_income'] = summary['interest_in'] - summary['interest_out']
        summary['provision_rate'] = (summary['provisions'] / summary['ead'] * 100).round(2)
        
        return summary
