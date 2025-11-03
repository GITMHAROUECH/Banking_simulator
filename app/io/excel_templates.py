"""
Générateur de templates Excel pour l'application bancaire
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import logging

from ..config.defaults import DEFAULT_CONFIG, EXCEL_TEMPLATES
from ..config.schemas import EntitySchema, FXRateSchema, ProductSchema

logger = logging.getLogger(__name__)

class ExcelTemplateGenerator:
    """Générateur de templates Excel avec données d'exemple"""
    
    def __init__(self, output_dir: str = "data/inputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_all_templates(self) -> Dict[str, str]:
        """Générer tous les templates Excel"""
        generated_files = {}
        
        try:
            # Template entités
            entities_file = self.generate_entities_template()
            generated_files['entities'] = entities_file
            
            # Template taux de change
            fx_file = self.generate_fx_template()
            generated_files['fx_rates'] = fx_file
            
            # Template portefeuilles
            portfolios_file = self.generate_portfolios_template()
            generated_files['portfolios'] = portfolios_file
            
            # Template paramètres IRB
            irb_file = self.generate_irb_parameters_template()
            generated_files['irb_parameters'] = irb_file
            
            # Template configuration
            config_file = self.generate_config_template()
            generated_files['config'] = config_file
            
            logger.info(f"Templates générés avec succès: {list(generated_files.keys())}")
            return generated_files
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des templates: {e}")
            raise
    
    def generate_entities_template(self) -> str:
        """Générer le template des entités"""
        filename = "input_entities.xlsx"
        filepath = self.output_dir / filename
        
        # Données d'exemple basées sur la configuration par défaut
        entities_data = DEFAULT_CONFIG['entities']
        
        # Créer le DataFrame
        df = pd.DataFrame(entities_data)
        
        # Ajouter des métadonnées
        metadata = {
            'Template': 'Entités bancaires',
            'Description': 'Configuration des entités du groupe bancaire',
            'Date_Creation': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Version': '1.0'
        }
        
        # Écrire dans Excel avec plusieurs feuilles
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Feuille principale
            df.to_excel(writer, sheet_name='Entities', index=False)
            
            # Feuille de métadonnées
            pd.DataFrame([metadata]).to_excel(writer, sheet_name='Metadata', index=False)
            
            # Feuille de documentation
            doc_data = {
                'Colonne': ['id', 'name', 'country', 'currency', 'ownership_pct', 'is_parent'],
                'Description': [
                    'Identifiant unique de l\'entité',
                    'Nom de l\'entité',
                    'Code pays (FR, US, CN)',
                    'Devise de base (EUR, USD, CNY)',
                    'Pourcentage de détention par le groupe (0-100)',
                    'Indique si c\'est l\'entité mère (True/False)'
                ],
                'Type': ['Texte', 'Texte', 'Texte', 'Texte', 'Numérique', 'Booléen'],
                'Obligatoire': ['Oui', 'Oui', 'Oui', 'Oui', 'Oui', 'Non']
            }
            pd.DataFrame(doc_data).to_excel(writer, sheet_name='Documentation', index=False)
        
        logger.info(f"Template entités généré: {filepath}")
        return str(filepath)
    
    def generate_fx_template(self) -> str:
        """Générer le template des taux de change"""
        filename = "input_fx.xlsx"
        filepath = self.output_dir / filename
        
        # Générer des taux de change pour l'année
        fx_data = []
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        # Taux mensuels USD/EUR
        current_date = start_date
        usd_base_rate = 1.10
        while current_date <= end_date:
            # Ajouter de la volatilité
            volatility = np.random.normal(0, 0.02)
            rate = max(0.8, min(1.4, usd_base_rate + volatility))
            
            fx_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'from_currency': 'USD',
                'to_currency': 'EUR',
                'rate': round(rate, 4),
                'is_closing': current_date.day == 31 and current_date.month == 12,
                'is_average': current_date.day == 15  # Milieu de mois pour moyenne
            })
            
            # Mois suivant
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Taux mensuels CNY/EUR
        current_date = start_date
        cny_base_rate = 7.85
        while current_date <= end_date:
            volatility = np.random.normal(0, 0.1)
            rate = max(6.5, min(9.0, cny_base_rate + volatility))
            
            fx_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'from_currency': 'CNY',
                'to_currency': 'EUR',
                'rate': round(rate, 4),
                'is_closing': current_date.day == 31 and current_date.month == 12,
                'is_average': current_date.day == 15
            })
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        df = pd.DataFrame(fx_data)
        
        # Métadonnées
        metadata = {
            'Template': 'Taux de change',
            'Description': 'Taux de change historiques et de clôture',
            'Date_Creation': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Periode': '2024-01-01 à 2024-12-31'
        }
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='FX_Rates', index=False)
            pd.DataFrame([metadata]).to_excel(writer, sheet_name='Metadata', index=False)
            
            # Documentation
            doc_data = {
                'Colonne': ['date', 'from_currency', 'to_currency', 'rate', 'is_closing', 'is_average'],
                'Description': [
                    'Date du taux de change',
                    'Devise source',
                    'Devise cible',
                    'Taux de change',
                    'Taux de clôture (True/False)',
                    'Taux moyen (True/False)'
                ]
            }
            pd.DataFrame(doc_data).to_excel(writer, sheet_name='Documentation', index=False)
        
        logger.info(f"Template FX généré: {filepath}")
        return str(filepath)
    
    def generate_portfolios_template(self) -> str:
        """Générer le template des portefeuilles"""
        filename = "input_portfolios.xlsx"
        filepath = self.output_dir / filename
        
        # Générer des positions d'exemple
        entities = ['EU_SUB', 'US_SUB', 'CN_SUB']
        products = DEFAULT_CONFIG['products']
        
        portfolios_data = []
        np.random.seed(42)  # Pour la reproductibilité
        
        for entity in entities:
            for product in products:
                # Taille de portefeuille selon l'entité
                if entity == 'EU_SUB':
                    base_size = 1000  # M€
                elif entity == 'US_SUB':
                    base_size = 800
                else:  # CN_SUB
                    base_size = 600
                
                # Ajuster selon le type de produit
                if product['product_class'] == 'loan':
                    size_factor = np.random.uniform(0.8, 1.2)
                elif product['product_class'] == 'deposit':
                    size_factor = np.random.uniform(0.5, 0.8)
                elif product['product_class'] == 'security':
                    size_factor = np.random.uniform(0.1, 0.3)
                else:
                    size_factor = np.random.uniform(0.05, 0.15)
                
                ead = base_size * size_factor
                
                # Paramètres de risque
                if product['is_retail']:
                    pd_val = np.random.uniform(0.01, 0.05)  # 1-5%
                    lgd_val = np.random.uniform(0.20, 0.60)  # 20-60%
                else:
                    pd_val = np.random.uniform(0.005, 0.03)  # 0.5-3%
                    lgd_val = np.random.uniform(0.30, 0.70)  # 30-70%
                
                # CCF pour les engagements
                if product['product_class'] == 'commitment':
                    ccf_val = 0.50
                    undrawn = ead * 0.6  # 60% non tiré
                    ead = ead * 0.4  # 40% tiré
                else:
                    ccf_val = 0.0
                    undrawn = 0.0
                
                # EIR selon le produit
                if product['product_class'] == 'loan':
                    eir = np.random.uniform(0.02, 0.06)  # 2-6%
                elif product['product_class'] == 'deposit':
                    eir = np.random.uniform(0.001, 0.02)  # 0.1-2%
                else:
                    eir = np.random.uniform(0.01, 0.04)  # 1-4%
                
                # Stage ECL
                rand_stage = np.random.random()
                if rand_stage < 0.85:
                    stage = 1
                elif rand_stage < 0.97:
                    stage = 2
                else:
                    stage = 3
                
                portfolios_data.append({
                    'entity_id': entity,
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'ead': round(ead, 2),
                    'eir': round(eir, 4),
                    'pd': round(pd_val, 4),
                    'lgd': round(lgd_val, 4),
                    'ccf': round(ccf_val, 2),
                    'stage': stage,
                    'undrawn': round(undrawn, 2),
                    'provisions': round(ead * pd_val * lgd_val, 2),
                    'is_retail': product['is_retail'],
                    'exposure_class': product['exposure_class']
                })
        
        df = pd.DataFrame(portfolios_data)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Portfolios', index=False)
            
            # Résumé par entité
            summary = df.groupby('entity_id').agg({
                'ead': 'sum',
                'provisions': 'sum',
                'undrawn': 'sum'
            }).round(2)
            summary.to_excel(writer, sheet_name='Summary_by_Entity')
            
            # Résumé par classe d'exposition
            exposure_summary = df.groupby('exposure_class').agg({
                'ead': 'sum',
                'provisions': 'sum'
            }).round(2)
            exposure_summary.to_excel(writer, sheet_name='Summary_by_Exposure')
        
        logger.info(f"Template portefeuilles généré: {filepath}")
        return str(filepath)
    
    def generate_irb_parameters_template(self) -> str:
        """Générer le template des paramètres IRB"""
        filename = "input_irb_parameters.xlsx"
        filepath = self.output_dir / filename
        
        # Paramètres IRB par classe d'exposition
        irb_data = []
        
        # Retail - Mortgages
        irb_data.append({
            'exposure_class': 'secured_by_mortgages',
            'segment': 'retail_mortgages',
            'pd_min': 0.005,
            'pd_max': 0.030,
            'pd_average': 0.015,
            'lgd_min': 0.10,
            'lgd_max': 0.30,
            'lgd_average': 0.20,
            'maturity': 15.0,
            'correlation_formula': 'retail_mortgage'
        })
        
        # Retail - Consumer
        irb_data.append({
            'exposure_class': 'retail',
            'segment': 'retail_consumer',
            'pd_min': 0.015,
            'pd_max': 0.050,
            'pd_average': 0.025,
            'lgd_min': 0.30,
            'lgd_max': 0.60,
            'lgd_average': 0.45,
            'maturity': 3.0,
            'correlation_formula': 'retail_other'
        })
        
        # Retail - Credit Cards
        irb_data.append({
            'exposure_class': 'retail',
            'segment': 'retail_revolving',
            'pd_min': 0.025,
            'pd_max': 0.080,
            'pd_average': 0.035,
            'lgd_min': 0.70,
            'lgd_max': 0.95,
            'lgd_average': 0.85,
            'maturity': 1.0,
            'correlation_formula': 'retail_revolving'
        })
        
        df = pd.DataFrame(irb_data)
        
        # Formules de corrélation
        correlation_formulas = {
            'Formula': [
                'retail_mortgage',
                'retail_revolving', 
                'retail_other',
                'corporate_large',
                'corporate_sme'
            ],
            'Description': [
                'R = 0.15',
                'R = 0.04',
                'R = 0.03 + (PD - 0.03) * 0.16',
                'R = 0.12 * (1 - EXP(-50*PD)) + 0.24 * (1 - (1 - EXP(-50*PD)))',
                'R = 0.12 * (1 - EXP(-50*PD)) + 0.24 * (1 - (1 - EXP(-50*PD))) - 0.04 * (1 - (S-5)/45)'
            ],
            'Reference': [
                'CRR3 Art. 154(5)',
                'CRR3 Art. 154(5)',
                'CRR3 Art. 154(5)',
                'CRR3 Art. 153(1)',
                'CRR3 Art. 153(2)'
            ]
        }
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='IRB_Parameters', index=False)
            pd.DataFrame(correlation_formulas).to_excel(writer, sheet_name='Correlation_Formulas', index=False)
        
        logger.info(f"Template paramètres IRB généré: {filepath}")
        return str(filepath)
    
    def generate_config_template(self) -> str:
        """Générer le template de configuration générale"""
        filename = "input_config.xlsx"
        filepath = self.output_dir / filename
        
        # Configuration générale
        general_config = {
            'Parameter': [
                'base_currency',
                'reporting_date',
                'simulation_seed',
                'minimum_capital_ratio',
                'capital_conservation_buffer',
                'leverage_ratio_minimum',
                'lcr_minimum',
                'nsfr_minimum'
            ],
            'Value': [
                'EUR',
                '2024-12-31',
                42,
                0.08,
                0.025,
                0.03,
                1.00,
                1.00
            ],
            'Description': [
                'Devise de base pour la consolidation',
                'Date de reporting',
                'Graine pour la simulation',
                'Ratio de capital minimum (8%)',
                'Coussin de conservation du capital (2.5%)',
                'Ratio de levier minimum (3%)',
                'LCR minimum (100%)',
                'NSFR minimum (100%)'
            ]
        }
        
        # Pondérations de risque standardisées
        risk_weights = []
        for exposure_class, weight in DEFAULT_CONFIG['standard_risk_weights'].items():
            risk_weights.append({
                'exposure_class': exposure_class,
                'risk_weight': weight,
                'description': f'Pondération pour {exposure_class.replace("_", " ")}'
            })
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            pd.DataFrame(general_config).to_excel(writer, sheet_name='General_Config', index=False)
            pd.DataFrame(risk_weights).to_excel(writer, sheet_name='Risk_Weights', index=False)
        
        logger.info(f"Template configuration généré: {filepath}")
        return str(filepath)
    
    def validate_template(self, filepath: str, template_type: str) -> bool:
        """Valider un template généré"""
        try:
            df = pd.read_excel(filepath)
            
            if template_type == 'entities':
                required_columns = ['id', 'name', 'country', 'currency', 'ownership_pct']
                return all(col in df.columns for col in required_columns)
            
            elif template_type == 'fx_rates':
                required_columns = ['date', 'from_currency', 'to_currency', 'rate']
                return all(col in df.columns for col in required_columns)
            
            elif template_type == 'portfolios':
                required_columns = ['entity_id', 'product_id', 'ead', 'eir']
                return all(col in df.columns for col in required_columns)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du template {filepath}: {e}")
            return False
