"""
Moteur de calcul des risques de crédit et RWA selon CRR3
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging
import math

from ..config.schemas import ExposureClass, ECLStage
from ..config.defaults import DEFAULT_CONFIG, CRR3_CONSTANTS

logger = logging.getLogger(__name__)

class CreditRiskEngine:
    """Moteur de calcul des risques de crédit et RWA"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.irb_parameters = config.get('irb_params', {})
        self.standard_risk_weights = DEFAULT_CONFIG['standard_risk_weights']
        self.ccf_factors = DEFAULT_CONFIG['ccf_factors']
        
        logger.info("Moteur de risque de crédit initialisé")
    
    def calculate_rwa(self, positions: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Calculer les RWA selon CRR3"""
        logger.info("Calcul des RWA")
        
        try:
            # Filtrer les positions de fin d'année
            year_end_positions = positions[positions['date'] == positions['date'].max()].copy()
            
            # Séparer retail et non-retail
            retail_positions = year_end_positions[year_end_positions['is_retail'] == True].copy()
            non_retail_positions = year_end_positions[year_end_positions['is_retail'] == False].copy()
            
            # Calcul IRB pour retail
            retail_rwa = self._calculate_irb_rwa(retail_positions)
            
            # Calcul standardisé pour non-retail
            standard_rwa = self._calculate_standard_rwa(non_retail_positions)
            
            # Combiner les résultats
            all_rwa = pd.concat([retail_rwa, standard_rwa], ignore_index=True)
            
            # Calculer les agrégats
            rwa_summary = self._calculate_rwa_summary(all_rwa)
            
            # Calculer le ratio de capital
            capital_ratios = self._calculate_capital_ratios(rwa_summary)
            
            # Calculer le ratio de levier
            leverage_ratio = self._calculate_leverage_ratio(year_end_positions)
            
            results = {
                'rwa_detail': all_rwa,
                'rwa_summary': rwa_summary,
                'capital_ratios': capital_ratios,
                'leverage_ratio': leverage_ratio,
                'corep_templates': self._generate_corep_templates(all_rwa, rwa_summary)
            }
            
            logger.info("Calcul des RWA terminé avec succès")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des RWA: {e}")
            raise
    
    def _calculate_irb_rwa(self, retail_positions: pd.DataFrame) -> pd.DataFrame:
        """Calculer les RWA selon l'approche IRB pour le retail"""
        logger.info("Calcul IRB RWA pour le retail")
        
        if retail_positions.empty:
            return pd.DataFrame()
        
        irb_results = []
        
        for _, position in retail_positions.iterrows():
            # Paramètres de base
            ead = position['ead']
            pd_val = position.get('pd', 0.025)
            lgd_val = position.get('lgd', 0.45)
            
            # Déterminer la maturité selon le produit
            maturity = self._get_irb_maturity(position['product_id'])
            
            # Calculer la corrélation
            correlation = self._calculate_irb_correlation(position['product_id'], pd_val)
            
            # Formule IRB
            rwa_density = self._irb_formula(pd_val, lgd_val, correlation, maturity)
            rwa_amount = ead * rwa_density
            
            # Calculer les fonds propres requis
            capital_requirement = rwa_amount * CRR3_CONSTANTS['minimum_capital_ratio']
            
            irb_results.append({
                'entity_id': position['entity_id'],
                'product_id': position['product_id'],
                'exposure_class': position.get('exposure_class', 'retail'),
                'approach': 'IRB',
                'ead': ead,
                'pd': pd_val,
                'lgd': lgd_val,
                'maturity': maturity,
                'correlation': correlation,
                'rwa_density': rwa_density,
                'rwa_amount': rwa_amount,
                'capital_requirement': capital_requirement,
                'stage': position.get('stage', 1)
            })
        
        return pd.DataFrame(irb_results)
    
    def _calculate_standard_rwa(self, non_retail_positions: pd.DataFrame) -> pd.DataFrame:
        """Calculer les RWA selon l'approche standardisée"""
        logger.info("Calcul RWA standardisé pour le non-retail")
        
        if non_retail_positions.empty:
            return pd.DataFrame()
        
        standard_results = []
        
        for _, position in non_retail_positions.iterrows():
            ead = position['ead']
            exposure_class = position.get('exposure_class', 'corporates')
            
            # Obtenir la pondération de risque
            risk_weight = self._get_standard_risk_weight(exposure_class, position)
            
            # Calculer les RWA
            rwa_amount = ead * risk_weight
            capital_requirement = rwa_amount * CRR3_CONSTANTS['minimum_capital_ratio']
            
            standard_results.append({
                'entity_id': position['entity_id'],
                'product_id': position['product_id'],
                'exposure_class': exposure_class,
                'approach': 'Standardised',
                'ead': ead,
                'pd': None,
                'lgd': None,
                'maturity': None,
                'correlation': None,
                'rwa_density': risk_weight,
                'rwa_amount': rwa_amount,
                'capital_requirement': capital_requirement,
                'stage': position.get('stage', 1)
            })
        
        return pd.DataFrame(standard_results)
    
    def _irb_formula(self, pd_val: float, lgd_val: float, correlation: float, maturity: float) -> float:
        """Formule IRB pour calculer la densité de RWA"""
        try:
            # Éviter les valeurs extrêmes
            pd_val = max(0.0001, min(0.9999, pd_val))
            lgd_val = max(0.01, min(0.99, lgd_val))
            correlation = max(0.01, min(0.99, correlation))
            maturity = max(1.0, min(7.0, maturity))
            
            # Calcul de la fonction de répartition normale inverse
            from scipy.stats import norm
            
            # Capital réglementaire selon la formule CRR3
            # K = LGD * N[(1-R)^(-0.5) * G(PD) + (R/(1-R))^0.5 * G(0.999)] - PD * LGD
            
            g_pd = norm.ppf(pd_val)
            g_999 = norm.ppf(0.999)
            
            sqrt_r = math.sqrt(correlation)
            sqrt_1_minus_r = math.sqrt(1 - correlation)
            
            n_arg = (g_pd / sqrt_1_minus_r) + (sqrt_r / sqrt_1_minus_r) * g_999
            n_value = norm.cdf(n_arg)
            
            k = lgd_val * n_value - pd_val * lgd_val
            
            # Ajustement de maturité pour les expositions non-retail
            if maturity > 1.0:
                b = (0.11852 - 0.05478 * math.log(pd_val)) ** 2
                maturity_adjustment = (1 + (maturity - 2.5) * b) / (1 - 1.5 * b)
                k *= maturity_adjustment
            
            # RWA density = K * 12.5 (inverse du ratio minimum de 8%)
            rwa_density = max(0, k * 12.5)
            
            return rwa_density
            
        except Exception as e:
            logger.warning(f"Erreur dans le calcul IRB: {e}, utilisation d'une valeur par défaut")
            return 1.0  # 100% par défaut en cas d'erreur
    
    def _calculate_irb_correlation(self, product_id: str, pd_val: float) -> float:
        """Calculer la corrélation IRB selon le produit"""
        if 'MORTGAGE' in product_id:
            # Retail secured by mortgages
            return 0.15
        elif 'CREDIT_CARDS' in product_id:
            # Retail revolving
            return 0.04
        else:
            # Other retail
            return 0.03 + (pd_val - 0.03) * 0.16 if pd_val > 0.03 else 0.03
    
    def _get_irb_maturity(self, product_id: str) -> float:
        """Obtenir la maturité effective pour IRB"""
        maturity_mapping = {
            'RETAIL_MORTGAGE': 15.0,
            'RETAIL_CONSUMER': 3.0,
            'RETAIL_CREDIT_CARDS': 1.0
        }
        return maturity_mapping.get(product_id, 2.5)  # 2.5 ans par défaut
    
    def _get_standard_risk_weight(self, exposure_class: str, position: pd.Series) -> float:
        """Obtenir la pondération de risque standardisée"""
        base_weight = self.standard_risk_weights.get(exposure_class, 1.0)
        
        # Ajustements selon les caractéristiques de l'exposition
        if exposure_class == 'corporates':
            # Ajustement pour les PME
            if 'SME' in position.get('product_id', ''):
                base_weight = 0.85  # Pondération réduite pour les PME
        
        elif exposure_class == 'institutions':
            # Pondération selon la notation (simplifiée)
            base_weight = 0.20  # Pondération standard pour les institutions
        
        elif exposure_class == 'secured_by_mortgages':
            # Pondération selon le LTV (simplifiée)
            base_weight = 0.35  # Pondération standard pour les hypothèques
        
        return base_weight
    
    def _calculate_rwa_summary(self, all_rwa: pd.DataFrame) -> pd.DataFrame:
        """Calculer le résumé des RWA"""
        if all_rwa.empty:
            return pd.DataFrame()
        
        # Agrégation par entité et classe d'exposition
        summary = all_rwa.groupby(['entity_id', 'exposure_class', 'approach']).agg({
            'ead': 'sum',
            'rwa_amount': 'sum',
            'capital_requirement': 'sum'
        }).reset_index()
        
        # Calculer la densité moyenne de RWA
        summary['avg_rwa_density'] = summary['rwa_amount'] / summary['ead']
        summary['avg_rwa_density'] = summary['avg_rwa_density'].fillna(0)
        
        return summary
    
    def _calculate_capital_ratios(self, rwa_summary: pd.DataFrame) -> pd.DataFrame:
        """Calculer les ratios de capital"""
        if rwa_summary.empty:
            return pd.DataFrame()
        
        # Agrégation totale par entité
        entity_totals = rwa_summary.groupby('entity_id').agg({
            'ead': 'sum',
            'rwa_amount': 'sum',
            'capital_requirement': 'sum'
        }).reset_index()
        
        # Estimer les fonds propres (simplification)
        entity_totals['tier1_capital'] = entity_totals['ead'] * 0.12  # 12% des expositions
        entity_totals['total_capital'] = entity_totals['ead'] * 0.15  # 15% des expositions
        
        # Calculer les ratios
        entity_totals['cet1_ratio'] = (entity_totals['tier1_capital'] / entity_totals['rwa_amount'] * 100).round(2)
        entity_totals['tier1_ratio'] = (entity_totals['tier1_capital'] / entity_totals['rwa_amount'] * 100).round(2)
        entity_totals['total_capital_ratio'] = (entity_totals['total_capital'] / entity_totals['rwa_amount'] * 100).round(2)
        
        # Vérifier les exigences minimales
        entity_totals['cet1_requirement'] = CRR3_CONSTANTS['minimum_capital_ratio'] * 100
        entity_totals['cet1_buffer'] = CRR3_CONSTANTS['capital_conservation_buffer'] * 100
        entity_totals['cet1_surplus'] = entity_totals['cet1_ratio'] - entity_totals['cet1_requirement'] - entity_totals['cet1_buffer']
        
        return entity_totals
    
    def _calculate_leverage_ratio(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Calculer le ratio de levier"""
        if positions.empty:
            return pd.DataFrame()
        
        # Calculer la mesure d'exposition pour le ratio de levier
        leverage_data = []
        
        entities = positions['entity_id'].unique()
        
        for entity_id in entities:
            entity_positions = positions[positions['entity_id'] == entity_id]
            
            # Expositions de bilan
            on_balance_exposure = entity_positions['ead'].sum()
            
            # Expositions hors bilan (engagements avec CCF)
            off_balance_exposure = (entity_positions['undrawn'] * entity_positions.get('ccf', 0)).sum()
            
            # Exposures sur dérivés (simplifiée)
            derivatives_exposure = entity_positions[entity_positions['product_id'].str.contains('SWAP', na=False)]['ead'].sum() * 0.05
            
            # Mesure d'exposition totale
            total_exposure = on_balance_exposure + off_balance_exposure + derivatives_exposure
            
            # Fonds propres Tier 1 (estimation)
            tier1_capital = total_exposure * 0.12
            
            # Ratio de levier
            leverage_ratio = (tier1_capital / total_exposure * 100) if total_exposure > 0 else 0
            
            leverage_data.append({
                'entity_id': entity_id,
                'on_balance_exposure': on_balance_exposure,
                'off_balance_exposure': off_balance_exposure,
                'derivatives_exposure': derivatives_exposure,
                'total_exposure': total_exposure,
                'tier1_capital': tier1_capital,
                'leverage_ratio': round(leverage_ratio, 2),
                'minimum_requirement': CRR3_CONSTANTS['leverage_ratio_minimum'] * 100,
                'surplus': round(leverage_ratio - CRR3_CONSTANTS['leverage_ratio_minimum'] * 100, 2)
            })
        
        return pd.DataFrame(leverage_data)
    
    def _generate_corep_templates(self, rwa_detail: pd.DataFrame, rwa_summary: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Générer les templates COREP"""
        logger.info("Génération des templates COREP")
        
        templates = {}
        
        # Template COREP Credit Risk
        if not rwa_detail.empty:
            corep_credit_risk = self._create_corep_credit_risk_template(rwa_detail)
            templates['corep_credit_risk'] = corep_credit_risk
        
        # Template COREP RWA Overview
        if not rwa_summary.empty:
            corep_rwa_overview = self._create_corep_rwa_overview_template(rwa_summary)
            templates['corep_rwa_overview'] = corep_rwa_overview
        
        return templates
    
    def _create_corep_credit_risk_template(self, rwa_detail: pd.DataFrame) -> pd.DataFrame:
        """Créer le template COREP Credit Risk"""
        # Mapping vers les codes COREP
        corep_mapping = {
            'central_governments': '010',
            'regional_governments': '020',
            'public_sector_entities': '030',
            'multilateral_development_banks': '040',
            'international_organisations': '050',
            'institutions': '060',
            'corporates': '070',
            'retail': '080',
            'secured_by_mortgages': '090',
            'exposures_in_default': '100',
            'high_risk_categories': '110',
            'covered_bonds': '120',
            'claims_institutions_corporates_short_term': '130',
            'collective_investment_undertakings': '140',
            'equity': '150',
            'other_items': '160'
        }
        
        corep_data = []
        
        # Agrégation par classe d'exposition
        exposure_summary = rwa_detail.groupby(['exposure_class', 'approach']).agg({
            'ead': 'sum',
            'rwa_amount': 'sum',
            'capital_requirement': 'sum'
        }).reset_index()
        
        for _, row in exposure_summary.iterrows():
            corep_code = corep_mapping.get(row['exposure_class'], '999')
            
            corep_data.append({
                'corep_code': corep_code,
                'exposure_class': row['exposure_class'],
                'approach': row['approach'],
                'original_exposure': row['ead'],
                'risk_weighted_exposure': row['rwa_amount'],
                'capital_requirements': row['capital_requirement'],
                'rwa_density': (row['rwa_amount'] / row['ead'] * 100) if row['ead'] > 0 else 0
            })
        
        return pd.DataFrame(corep_data)
    
    def _create_corep_rwa_overview_template(self, rwa_summary: pd.DataFrame) -> pd.DataFrame:
        """Créer le template COREP RWA Overview"""
        # Agrégation totale
        total_summary = rwa_summary.groupby('approach').agg({
            'ead': 'sum',
            'rwa_amount': 'sum',
            'capital_requirement': 'sum'
        }).reset_index()
        
        overview_data = []
        
        for _, row in total_summary.iterrows():
            overview_data.append({
                'risk_category': 'Credit Risk',
                'approach': row['approach'],
                'total_exposure': row['ead'],
                'total_rwa': row['rwa_amount'],
                'capital_requirements': row['capital_requirement'],
                'percentage_of_total_rwa': 100.0  # Simplifié - seulement risque de crédit
            })
        
        # Ajouter les totaux
        total_row = {
            'risk_category': 'TOTAL',
            'approach': 'All',
            'total_exposure': total_summary['ead'].sum(),
            'total_rwa': total_summary['rwa_amount'].sum(),
            'capital_requirements': total_summary['capital_requirement'].sum(),
            'percentage_of_total_rwa': 100.0
        }
        
        overview_data.append(total_row)
        
        return pd.DataFrame(overview_data)
    
    def calculate_credit_risk_adjustments(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Calculer les ajustements de valeur de crédit (CVA)"""
        logger.info("Calcul des ajustements de valeur de crédit")
        
        # Filtrer les dérivés
        derivatives = positions[positions['product_id'].str.contains('SWAP|DERIVATIVE', na=False)]
        
        if derivatives.empty:
            return pd.DataFrame()
        
        cva_data = []
        
        for _, deriv in derivatives.iterrows():
            # Paramètres CVA simplifiés
            exposure = deriv['ead']
            pd_counterparty = 0.01  # 1% PD contrepartie
            lgd_counterparty = 0.60  # 60% LGD contrepartie
            maturity = 5.0  # 5 ans maturité moyenne
            
            # CVA = EAD * PD * LGD * sqrt(Maturity)
            cva_amount = exposure * pd_counterparty * lgd_counterparty * math.sqrt(maturity)
            
            cva_data.append({
                'entity_id': deriv['entity_id'],
                'product_id': deriv['product_id'],
                'exposure': exposure,
                'counterparty_pd': pd_counterparty,
                'counterparty_lgd': lgd_counterparty,
                'maturity': maturity,
                'cva_amount': cva_amount
            })
        
        return pd.DataFrame(cva_data)
