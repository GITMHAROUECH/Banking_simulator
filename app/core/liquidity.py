"""
Moteur de calcul de liquidité (LCR, NSFR, ALMM) selon CRR3
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from ..config.schemas import LCRComponentSchema, NSFRComponentSchema
from ..config.defaults import DEFAULT_CONFIG, CRR3_CONSTANTS

logger = logging.getLogger(__name__)

class LiquidityEngine:
    """Moteur de calcul des ratios de liquidité"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.lcr_parameters = DEFAULT_CONFIG['lcr_parameters']
        self.nsfr_parameters = DEFAULT_CONFIG['nsfr_parameters']
        
        logger.info("Moteur de liquidité initialisé")
    
    def calculate_liquidity_ratios(self, positions: pd.DataFrame, 
                                 cash_flows: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Calculer tous les ratios de liquidité"""
        logger.info("Calcul des ratios de liquidité")
        
        try:
            # Filtrer les données de fin d'année
            year_end_positions = positions[positions['date'] == positions['date'].max()].copy()
            
            # Calculer LCR
            lcr_results = self._calculate_lcr(year_end_positions, cash_flows)
            
            # Calculer NSFR
            nsfr_results = self._calculate_nsfr(year_end_positions)
            
            # Calculer ALMM (Asset Liability Maturity Mismatch)
            almm_results = self._calculate_almm(year_end_positions, cash_flows)
            
            # Générer les templates réglementaires
            regulatory_templates = self._generate_liquidity_templates(
                lcr_results, nsfr_results, almm_results
            )
            
            results = {
                'lcr_detail': lcr_results['detail'],
                'lcr_summary': lcr_results['summary'],
                'nsfr_detail': nsfr_results['detail'],
                'nsfr_summary': nsfr_results['summary'],
                'almm_maturity_ladder': almm_results['maturity_ladder'],
                'almm_summary': almm_results['summary'],
                'regulatory_templates': regulatory_templates
            }
            
            logger.info("Calcul des ratios de liquidité terminé avec succès")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des ratios de liquidité: {e}")
            raise
    
    def _calculate_lcr(self, positions: pd.DataFrame, 
                      cash_flows: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Calculer le Liquidity Coverage Ratio (LCR)"""
        logger.info("Calcul du LCR")
        
        lcr_detail = []
        lcr_summary = []
        
        entities = positions['entity_id'].unique()
        
        for entity_id in entities:
            entity_positions = positions[positions['entity_id'] == entity_id]
            entity_cash_flows = cash_flows[cash_flows['entity_id'] == entity_id] if not cash_flows.empty else pd.DataFrame()
            
            # 1. Calculer les HQLA (High Quality Liquid Assets)
            hqla = self._calculate_hqla(entity_positions)
            
            # 2. Calculer les sorties de trésorerie sur 30 jours
            cash_outflows = self._calculate_cash_outflows_30d(entity_positions, entity_cash_flows)
            
            # 3. Calculer les entrées de trésorerie sur 30 jours
            cash_inflows = self._calculate_cash_inflows_30d(entity_positions, entity_cash_flows)
            
            # 4. Calculer les sorties nettes
            net_cash_outflows = max(
                cash_outflows - cash_inflows * 0.75,  # Cap à 75% des entrées
                cash_outflows * 0.25  # Minimum 25% des sorties brutes
            )
            
            # 5. Calculer le ratio LCR
            lcr_ratio = (hqla['total_hqla'] / net_cash_outflows * 100) if net_cash_outflows > 0 else float('inf')
            
            # Détail par entité
            lcr_detail.append({
                'entity_id': entity_id,
                'hqla_level_1': hqla['level_1'],
                'hqla_level_2a': hqla['level_2a'],
                'hqla_level_2b': hqla['level_2b'],
                'total_hqla': hqla['total_hqla'],
                'cash_outflows_30d': cash_outflows,
                'cash_inflows_30d': cash_inflows,
                'net_cash_outflows': net_cash_outflows,
                'lcr_ratio': round(lcr_ratio, 2),
                'lcr_requirement': CRR3_CONSTANTS['lcr_minimum'] * 100,
                'lcr_surplus': round(lcr_ratio - CRR3_CONSTANTS['lcr_minimum'] * 100, 2)
            })
        
        # Résumé consolidé
        if lcr_detail:
            total_hqla = sum(item['total_hqla'] for item in lcr_detail)
            total_net_outflows = sum(item['net_cash_outflows'] for item in lcr_detail)
            consolidated_lcr = (total_hqla / total_net_outflows * 100) if total_net_outflows > 0 else float('inf')
            
            lcr_summary.append({
                'entity_id': 'GROUP',
                'total_hqla': total_hqla,
                'net_cash_outflows': total_net_outflows,
                'lcr_ratio': round(consolidated_lcr, 2),
                'lcr_requirement': CRR3_CONSTANTS['lcr_minimum'] * 100,
                'lcr_surplus': round(consolidated_lcr - CRR3_CONSTANTS['lcr_minimum'] * 100, 2)
            })
        
        return {
            'detail': pd.DataFrame(lcr_detail),
            'summary': pd.DataFrame(lcr_summary)
        }
    
    def _calculate_hqla(self, positions: pd.DataFrame) -> Dict[str, float]:
        """Calculer les High Quality Liquid Assets"""
        hqla = {
            'level_1': 0.0,
            'level_2a': 0.0,
            'level_2b': 0.0,
            'total_hqla': 0.0
        }
        
        for _, position in positions.iterrows():
            product_id = position['product_id']
            ead = position['ead']
            
            # Classification HQLA selon le produit
            if 'GOVERNMENT_BONDS' in product_id:
                # Obligations d'État = HQLA Niveau 1
                hqla['level_1'] += ead
            elif 'CORPORATE_BONDS' in product_id:
                # Obligations corporate de haute qualité = HQLA Niveau 2A
                hqla['level_2a'] += ead * 0.3  # Seulement 30% éligibles
            elif product_id == 'RETAIL_DEPOSITS' and ead > 0:
                # Liquidités = HQLA Niveau 1
                cash_equivalent = ead * 0.1  # 10% considéré comme liquidités
                hqla['level_1'] += cash_equivalent
        
        # Appliquer les haircuts
        hqla_after_haircuts = {
            'level_1': hqla['level_1'] * (1 - self.lcr_parameters['hqla_haircuts']['level_1']),
            'level_2a': hqla['level_2a'] * (1 - self.lcr_parameters['hqla_haircuts']['level_2a']),
            'level_2b': hqla['level_2b'] * (1 - self.lcr_parameters['hqla_haircuts']['level_2b'])
        }
        
        # Limites sur les niveaux 2A et 2B
        total_level_2 = hqla_after_haircuts['level_2a'] + hqla_after_haircuts['level_2b']
        total_before_limits = hqla_after_haircuts['level_1'] + total_level_2
        
        # Niveau 2 limité à 40% du total
        if total_level_2 > total_before_limits * 0.4:
            reduction_factor = (total_before_limits * 0.4) / total_level_2
            hqla_after_haircuts['level_2a'] *= reduction_factor
            hqla_after_haircuts['level_2b'] *= reduction_factor
        
        # Niveau 2B limité à 15% du total
        if hqla_after_haircuts['level_2b'] > total_before_limits * 0.15:
            hqla_after_haircuts['level_2b'] = total_before_limits * 0.15
        
        hqla_after_haircuts['total_hqla'] = (hqla_after_haircuts['level_1'] + 
                                           hqla_after_haircuts['level_2a'] + 
                                           hqla_after_haircuts['level_2b'])
        
        return hqla_after_haircuts
    
    def _calculate_cash_outflows_30d(self, positions: pd.DataFrame, 
                                   cash_flows: pd.DataFrame) -> float:
        """Calculer les sorties de trésorerie sur 30 jours"""
        total_outflows = 0.0
        
        for _, position in positions.iterrows():
            product_id = position['product_id']
            ead = position['ead']
            
            # Taux de sortie selon le type de dépôt/financement
            if product_id == 'RETAIL_DEPOSITS':
                # Dépôts retail - distinguer stable vs moins stable
                if ead < 100:  # Petits dépôts = plus stables
                    outflow_rate = self.lcr_parameters['outflow_rates']['retail_deposits_stable']
                else:
                    outflow_rate = self.lcr_parameters['outflow_rates']['retail_deposits_less_stable']
                total_outflows += ead * outflow_rate
                
            elif product_id == 'CORPORATE_DEPOSITS':
                # Dépôts corporate
                outflow_rate = self.lcr_parameters['outflow_rates']['non_operational_deposits']
                total_outflows += ead * outflow_rate
        
        # Ajouter les engagements hors bilan
        for _, position in positions.iterrows():
            if position['product_id'] == 'CREDIT_LINES':
                undrawn = position.get('undrawn', 0)
                # Taux de tirage en stress sur 30 jours
                stress_drawdown_rate = 0.10  # 10% des lignes non tirées
                total_outflows += undrawn * stress_drawdown_rate
        
        return total_outflows
    
    def _calculate_cash_inflows_30d(self, positions: pd.DataFrame, 
                                  cash_flows: pd.DataFrame) -> float:
        """Calculer les entrées de trésorerie sur 30 jours"""
        total_inflows = 0.0
        
        # Remboursements de prêts sur 30 jours
        for _, position in positions.iterrows():
            if 'LOAN' in position['product_id'] or 'MORTGAGE' in position['product_id']:
                ead = position['ead']
                # Remboursements mensuels normaux
                monthly_repayment = ead * 0.02  # 2% par mois en moyenne
                total_inflows += monthly_repayment
        
        # Flux d'intérêts
        if not cash_flows.empty:
            monthly_interest_income = cash_flows['interest_in'].sum() / 12  # Moyenne mensuelle
            total_inflows += monthly_interest_income
        
        # Appliquer le cap réglementaire (75% des entrées)
        return total_inflows
    
    def _calculate_nsfr(self, positions: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Calculer le Net Stable Funding Ratio (NSFR)"""
        logger.info("Calcul du NSFR")
        
        nsfr_detail = []
        nsfr_summary = []
        
        entities = positions['entity_id'].unique()
        
        for entity_id in entities:
            entity_positions = positions[positions['entity_id'] == entity_id]
            
            # 1. Calculer l'Available Stable Funding (ASF)
            asf = self._calculate_asf(entity_positions)
            
            # 2. Calculer le Required Stable Funding (RSF)
            rsf = self._calculate_rsf(entity_positions)
            
            # 3. Calculer le ratio NSFR
            nsfr_ratio = (asf / rsf * 100) if rsf > 0 else float('inf')
            
            nsfr_detail.append({
                'entity_id': entity_id,
                'available_stable_funding': asf,
                'required_stable_funding': rsf,
                'nsfr_ratio': round(nsfr_ratio, 2),
                'nsfr_requirement': CRR3_CONSTANTS['nsfr_minimum'] * 100,
                'nsfr_surplus': round(nsfr_ratio - CRR3_CONSTANTS['nsfr_minimum'] * 100, 2)
            })
        
        # Résumé consolidé
        if nsfr_detail:
            total_asf = sum(item['available_stable_funding'] for item in nsfr_detail)
            total_rsf = sum(item['required_stable_funding'] for item in nsfr_detail)
            consolidated_nsfr = (total_asf / total_rsf * 100) if total_rsf > 0 else float('inf')
            
            nsfr_summary.append({
                'entity_id': 'GROUP',
                'available_stable_funding': total_asf,
                'required_stable_funding': total_rsf,
                'nsfr_ratio': round(consolidated_nsfr, 2),
                'nsfr_requirement': CRR3_CONSTANTS['nsfr_minimum'] * 100,
                'nsfr_surplus': round(consolidated_nsfr - CRR3_CONSTANTS['nsfr_minimum'] * 100, 2)
            })
        
        return {
            'detail': pd.DataFrame(nsfr_detail),
            'summary': pd.DataFrame(nsfr_summary)
        }
    
    def _calculate_asf(self, positions: pd.DataFrame) -> float:
        """Calculer l'Available Stable Funding"""
        total_asf = 0.0
        
        # Estimer les capitaux propres (12% des actifs)
        total_assets = positions[positions['ead'] > 0]['ead'].sum()
        equity = total_assets * 0.12
        total_asf += equity * self.nsfr_parameters['asf_factors']['capital']
        
        # Financement par dépôts
        for _, position in positions.iterrows():
            product_id = position['product_id']
            ead = position['ead']
            
            if product_id == 'RETAIL_DEPOSITS':
                if ead < 100:  # Dépôts stables
                    asf_factor = self.nsfr_parameters['asf_factors']['retail_deposits_stable']
                else:  # Dépôts moins stables
                    asf_factor = self.nsfr_parameters['asf_factors']['retail_deposits_less_stable']
                total_asf += ead * asf_factor
                
            elif product_id == 'CORPORATE_DEPOSITS':
                asf_factor = self.nsfr_parameters['asf_factors']['other_wholesale_funding']
                total_asf += ead * asf_factor
        
        return total_asf
    
    def _calculate_rsf(self, positions: pd.DataFrame) -> float:
        """Calculer le Required Stable Funding"""
        total_rsf = 0.0
        
        for _, position in positions.iterrows():
            product_id = position['product_id']
            ead = position['ead']
            
            # Facteurs RSF selon le type d'actif
            if 'MORTGAGE' in product_id:
                rsf_factor = self.nsfr_parameters['rsf_factors']['retail_mortgages']
            elif 'RETAIL' in product_id and 'LOAN' in product_id:
                rsf_factor = self.nsfr_parameters['rsf_factors']['other_retail_loans']
            elif 'CORPORATE' in product_id and 'LOAN' in product_id:
                rsf_factor = self.nsfr_parameters['rsf_factors']['loans_to_non_financial_corporates']
            elif 'GOVERNMENT_BONDS' in product_id:
                rsf_factor = self.nsfr_parameters['rsf_factors']['hqla_level_1']
            elif 'CORPORATE_BONDS' in product_id:
                rsf_factor = self.nsfr_parameters['rsf_factors']['hqla_level_2a']
            else:
                rsf_factor = 0.85  # Facteur par défaut
            
            total_rsf += ead * rsf_factor
        
        return total_rsf
    
    def _calculate_almm(self, positions: pd.DataFrame, 
                       cash_flows: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Calculer l'Asset Liability Maturity Mismatch (ALMM)"""
        logger.info("Calcul de l'ALMM")
        
        # Buckets de maturité
        maturity_buckets = [
            'Overnight', '1-7 days', '8-30 days', '1-3 months', 
            '3-6 months', '6-12 months', '1-2 years', '2-5 years', '5+ years'
        ]
        
        almm_data = []
        
        entities = positions['entity_id'].unique()
        
        for entity_id in entities:
            entity_positions = positions[positions['entity_id'] == entity_id]
            
            for bucket in maturity_buckets:
                # Répartir les positions selon les buckets de maturité
                assets, liabilities = self._allocate_to_maturity_bucket(entity_positions, bucket)
                
                net_position = assets - liabilities
                cumulative_gap = net_position  # Simplifié - devrait être cumulatif
                
                almm_data.append({
                    'entity_id': entity_id,
                    'maturity_bucket': bucket,
                    'assets': assets,
                    'liabilities': liabilities,
                    'net_position': net_position,
                    'cumulative_gap': cumulative_gap
                })
        
        almm_df = pd.DataFrame(almm_data)
        
        # Résumé par entité
        almm_summary = almm_df.groupby('entity_id').agg({
            'assets': 'sum',
            'liabilities': 'sum',
            'net_position': 'sum'
        }).reset_index()
        
        return {
            'maturity_ladder': almm_df,
            'summary': almm_summary
        }
    
    def _allocate_to_maturity_bucket(self, positions: pd.DataFrame, bucket: str) -> Tuple[float, float]:
        """Allouer les positions à un bucket de maturité"""
        assets = 0.0
        liabilities = 0.0
        
        for _, position in positions.iterrows():
            product_id = position['product_id']
            ead = position['ead']
            maturity_bucket = position.get('maturity_bucket', '1-5Y')
            
            # Mapping simplifié des maturités
            if bucket == 'Overnight' and 'DEPOSITS' in product_id:
                liabilities += ead * 0.1  # 10% overnight
            elif bucket == '1-3 months' and 'CREDIT_CARDS' in product_id:
                assets += ead * 0.5  # 50% court terme
            elif bucket == '1-2 years' and '1-5Y' in maturity_bucket:
                if 'LOAN' in product_id or 'MORTGAGE' in product_id:
                    assets += ead * 0.3  # 30% dans ce bucket
                elif 'DEPOSITS' in product_id:
                    liabilities += ead * 0.2  # 20% dans ce bucket
            elif bucket == '5+ years' and ('5Y+' in maturity_bucket or 'MORTGAGE' in product_id):
                if 'LOAN' in product_id or 'MORTGAGE' in product_id:
                    assets += ead * 0.6  # 60% long terme
        
        return assets, liabilities
    
    def _generate_liquidity_templates(self, lcr_results: Dict, nsfr_results: Dict, 
                                    almm_results: Dict) -> Dict[str, pd.DataFrame]:
        """Générer les templates réglementaires de liquidité"""
        logger.info("Génération des templates de liquidité")
        
        templates = {}
        
        # Template LCR
        if not lcr_results['detail'].empty:
            lcr_template = self._create_lcr_template(lcr_results['detail'])
            templates['lcr_template'] = lcr_template
        
        # Template NSFR
        if not nsfr_results['detail'].empty:
            nsfr_template = self._create_nsfr_template(nsfr_results['detail'])
            templates['nsfr_template'] = nsfr_template
        
        # Template ALMM
        if not almm_results['maturity_ladder'].empty:
            almm_template = self._create_almm_template(almm_results['maturity_ladder'])
            templates['almm_template'] = almm_template
        
        return templates
    
    def _create_lcr_template(self, lcr_detail: pd.DataFrame) -> pd.DataFrame:
        """Créer le template LCR réglementaire"""
        template_data = []
        
        # Agrégation pour le template
        total_row = lcr_detail.sum(numeric_only=True)
        
        # Structure du template LCR
        lcr_items = [
            {'item': 'HQLA Level 1', 'amount': total_row.get('hqla_level_1', 0), 'weight': '100%'},
            {'item': 'HQLA Level 2A', 'amount': total_row.get('hqla_level_2a', 0), 'weight': '85%'},
            {'item': 'HQLA Level 2B', 'amount': total_row.get('hqla_level_2b', 0), 'weight': '75%'},
            {'item': 'Total HQLA', 'amount': total_row.get('total_hqla', 0), 'weight': ''},
            {'item': 'Cash Outflows 30d', 'amount': total_row.get('cash_outflows_30d', 0), 'weight': ''},
            {'item': 'Cash Inflows 30d', 'amount': total_row.get('cash_inflows_30d', 0), 'weight': '75%'},
            {'item': 'Net Cash Outflows', 'amount': total_row.get('net_cash_outflows', 0), 'weight': ''},
            {'item': 'LCR Ratio (%)', 'amount': total_row.get('lcr_ratio', 0), 'weight': '≥100%'}
        ]
        
        return pd.DataFrame(lcr_items)
    
    def _create_nsfr_template(self, nsfr_detail: pd.DataFrame) -> pd.DataFrame:
        """Créer le template NSFR réglementaire"""
        template_data = []
        
        # Agrégation pour le template
        total_row = nsfr_detail.sum(numeric_only=True)
        
        # Structure du template NSFR
        nsfr_items = [
            {'item': 'Available Stable Funding', 'amount': total_row.get('available_stable_funding', 0)},
            {'item': 'Required Stable Funding', 'amount': total_row.get('required_stable_funding', 0)},
            {'item': 'NSFR Ratio (%)', 'amount': total_row.get('nsfr_ratio', 0)}
        ]
        
        return pd.DataFrame(nsfr_items)
    
    def _create_almm_template(self, almm_ladder: pd.DataFrame) -> pd.DataFrame:
        """Créer le template ALMM réglementaire"""
        # Pivoter pour avoir les buckets en colonnes
        almm_pivot = almm_ladder.pivot_table(
            index='entity_id',
            columns='maturity_bucket',
            values=['assets', 'liabilities', 'net_position'],
            aggfunc='sum',
            fill_value=0
        )
        
        # Aplatir les colonnes multi-niveaux
        almm_pivot.columns = [f"{col[0]}_{col[1]}" for col in almm_pivot.columns]
        almm_pivot = almm_pivot.reset_index()
        
        return almm_pivot
    
    def calculate_additional_liquidity_metrics(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Calculer des métriques de liquidité supplémentaires"""
        logger.info("Calcul de métriques de liquidité supplémentaires")
        
        additional_metrics = []
        
        entities = positions['entity_id'].unique()
        
        for entity_id in entities:
            entity_positions = positions[positions['entity_id'] == entity_id]
            
            # Ratio prêts/dépôts
            total_loans = entity_positions[entity_positions['product_id'].str.contains('LOAN|MORTGAGE', na=False)]['ead'].sum()
            total_deposits = entity_positions[entity_positions['product_id'].str.contains('DEPOSIT', na=False)]['ead'].sum()
            loan_to_deposit_ratio = (total_loans / total_deposits * 100) if total_deposits > 0 else 0
            
            # Concentration des dépôts
            retail_deposits = entity_positions[entity_positions['product_id'] == 'RETAIL_DEPOSITS']['ead'].sum()
            corporate_deposits = entity_positions[entity_positions['product_id'] == 'CORPORATE_DEPOSITS']['ead'].sum()
            retail_deposit_ratio = (retail_deposits / total_deposits * 100) if total_deposits > 0 else 0
            
            # Actifs liquides / Total actifs
            liquid_assets = entity_positions[entity_positions['product_id'].str.contains('GOVERNMENT_BONDS|CASH', na=False)]['ead'].sum()
            total_assets = entity_positions['ead'].sum()
            liquidity_ratio = (liquid_assets / total_assets * 100) if total_assets > 0 else 0
            
            additional_metrics.append({
                'entity_id': entity_id,
                'loan_to_deposit_ratio': round(loan_to_deposit_ratio, 2),
                'retail_deposit_ratio': round(retail_deposit_ratio, 2),
                'liquidity_ratio': round(liquidity_ratio, 2),
                'total_loans': total_loans,
                'total_deposits': total_deposits,
                'liquid_assets': liquid_assets
            })
        
        return pd.DataFrame(additional_metrics)
