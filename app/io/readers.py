"""
Lecteurs de fichiers Excel pour l'application bancaire
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, date

from ..config.schemas import (
    EntitySchema, FXRateSchema, ProductSchema, PositionSchema,
    validate_entity_data, validate_fx_rates, validate_products
)

logger = logging.getLogger(__name__)

class ExcelReader:
    """Lecteur de fichiers Excel d'entrée"""
    
    def __init__(self, input_dir: str = "data/inputs"):
        self.input_dir = Path(input_dir)
        
        if not self.input_dir.exists():
            logger.warning(f"Dossier d'entrée {input_dir} n'existe pas")
    
    def read_all_inputs(self) -> Dict[str, pd.DataFrame]:
        """Lire tous les fichiers d'entrée"""
        logger.info("Lecture de tous les fichiers d'entrée")
        
        inputs = {}
        
        try:
            # Entités
            entities_file = self.input_dir / "input_entities.xlsx"
            if entities_file.exists():
                inputs['entities'] = self.read_entities(entities_file)
            else:
                logger.warning(f"Fichier entités non trouvé: {entities_file}")
            
            # Taux de change
            fx_file = self.input_dir / "input_fx.xlsx"
            if fx_file.exists():
                inputs['fx_rates'] = self.read_fx_rates(fx_file)
            else:
                logger.warning(f"Fichier FX non trouvé: {fx_file}")
            
            # Portefeuilles
            portfolios_file = self.input_dir / "input_portfolios.xlsx"
            if portfolios_file.exists():
                inputs['portfolios'] = self.read_portfolios(portfolios_file)
            else:
                logger.warning(f"Fichier portefeuilles non trouvé: {portfolios_file}")
            
            # Paramètres IRB
            irb_file = self.input_dir / "input_irb_parameters.xlsx"
            if irb_file.exists():
                inputs['irb_parameters'] = self.read_irb_parameters(irb_file)
            else:
                logger.warning(f"Fichier paramètres IRB non trouvé: {irb_file}")
            
            # Configuration
            config_file = self.input_dir / "input_config.xlsx"
            if config_file.exists():
                inputs['config'] = self.read_config(config_file)
            else:
                logger.warning(f"Fichier configuration non trouvé: {config_file}")
            
            logger.info(f"Lecture terminée: {list(inputs.keys())}")
            return inputs
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des fichiers: {e}")
            raise
    
    def read_entities(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Lire le fichier des entités"""
        logger.info(f"Lecture des entités: {filepath}")
        
        try:
            # Lire le fichier Excel
            df = pd.read_excel(filepath, sheet_name='Entities')
            
            # Validation des colonnes requises
            required_columns = ['id', 'name', 'country', 'currency', 'ownership_pct']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Colonnes manquantes dans le fichier entités: {missing_columns}")
            
            # Nettoyage des données
            df = df.dropna(subset=required_columns)
            
            # Validation des types
            df['ownership_pct'] = pd.to_numeric(df['ownership_pct'], errors='coerce')
            df['is_parent'] = df.get('is_parent', False).fillna(False).astype(bool)
            
            # Validation des valeurs
            if not df['ownership_pct'].between(0, 100).all():
                raise ValueError("ownership_pct doit être entre 0 et 100")
            
            # Validation des devises
            valid_currencies = ['EUR', 'USD', 'CNY']
            invalid_currencies = df[~df['currency'].isin(valid_currencies)]['currency'].unique()
            if len(invalid_currencies) > 0:
                raise ValueError(f"Devises non supportées: {invalid_currencies}")
            
            # Validation des pays
            valid_countries = ['FR', 'US', 'CN']
            invalid_countries = df[~df['country'].isin(valid_countries)]['country'].unique()
            if len(invalid_countries) > 0:
                raise ValueError(f"Pays non supportés: {invalid_countries}")
            
            logger.info(f"Entités lues avec succès: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des entités: {e}")
            raise
    
    def read_fx_rates(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Lire le fichier des taux de change"""
        logger.info(f"Lecture des taux de change: {filepath}")
        
        try:
            df = pd.read_excel(filepath, sheet_name='FX_Rates')
            
            # Validation des colonnes requises
            required_columns = ['date', 'from_currency', 'to_currency', 'rate']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Colonnes manquantes dans le fichier FX: {missing_columns}")
            
            # Nettoyage des données
            df = df.dropna(subset=required_columns)
            
            # Conversion des types
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
            df['is_closing'] = df.get('is_closing', False).fillna(False).astype(bool)
            df['is_average'] = df.get('is_average', False).fillna(False).astype(bool)
            
            # Validation des taux
            if not (df['rate'] > 0).all():
                raise ValueError("Tous les taux de change doivent être positifs")
            
            # Validation des devises
            valid_currencies = ['EUR', 'USD', 'CNY']
            invalid_from = df[~df['from_currency'].isin(valid_currencies)]['from_currency'].unique()
            invalid_to = df[~df['to_currency'].isin(valid_currencies)]['to_currency'].unique()
            
            if len(invalid_from) > 0:
                raise ValueError(f"Devises source non supportées: {invalid_from}")
            if len(invalid_to) > 0:
                raise ValueError(f"Devises cible non supportées: {invalid_to}")
            
            logger.info(f"Taux de change lus avec succès: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des taux de change: {e}")
            raise
    
    def read_portfolios(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Lire le fichier des portefeuilles"""
        logger.info(f"Lecture des portefeuilles: {filepath}")
        
        try:
            df = pd.read_excel(filepath, sheet_name='Portfolios')
            
            # Validation des colonnes requises
            required_columns = ['entity_id', 'product_id', 'ead', 'eir']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Colonnes manquantes dans le fichier portefeuilles: {missing_columns}")
            
            # Nettoyage des données
            df = df.dropna(subset=required_columns)
            
            # Conversion des types numériques
            numeric_columns = ['ead', 'eir', 'pd', 'lgd', 'ccf', 'undrawn', 'provisions']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Valeurs par défaut
            df['pd'] = df.get('pd', 0.02).fillna(0.02)
            df['lgd'] = df.get('lgd', 0.45).fillna(0.45)
            df['ccf'] = df.get('ccf', 0.0).fillna(0.0)
            df['stage'] = df.get('stage', 1).fillna(1).astype(int)
            df['undrawn'] = df.get('undrawn', 0.0).fillna(0.0)
            df['provisions'] = df.get('provisions', 0.0).fillna(0.0)
            
            # Validation des valeurs
            if not (df['ead'] >= 0).all():
                raise ValueError("EAD doit être positif ou nul")
            
            if not df['pd'].between(0, 1).all():
                raise ValueError("PD doit être entre 0 et 1")
            
            if not df['lgd'].between(0, 1).all():
                raise ValueError("LGD doit être entre 0 et 1")
            
            if not df['ccf'].between(0, 1).all():
                raise ValueError("CCF doit être entre 0 et 1")
            
            if not df['stage'].isin([1, 2, 3]).all():
                raise ValueError("Stage doit être 1, 2 ou 3")
            
            logger.info(f"Portefeuilles lus avec succès: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des portefeuilles: {e}")
            raise
    
    def read_irb_parameters(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Lire le fichier des paramètres IRB"""
        logger.info(f"Lecture des paramètres IRB: {filepath}")
        
        try:
            df = pd.read_excel(filepath, sheet_name='IRB_Parameters')
            
            # Validation des colonnes requises
            required_columns = ['exposure_class', 'segment', 'pd_average', 'lgd_average']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Colonnes manquantes dans le fichier IRB: {missing_columns}")
            
            # Nettoyage des données
            df = df.dropna(subset=required_columns)
            
            # Conversion des types numériques
            numeric_columns = ['pd_min', 'pd_max', 'pd_average', 'lgd_min', 'lgd_max', 'lgd_average', 'maturity']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validation des valeurs
            pd_columns = ['pd_min', 'pd_max', 'pd_average']
            for col in pd_columns:
                if col in df.columns and not df[col].between(0, 1).all():
                    raise ValueError(f"{col} doit être entre 0 et 1")
            
            lgd_columns = ['lgd_min', 'lgd_max', 'lgd_average']
            for col in lgd_columns:
                if col in df.columns and not df[col].between(0, 1).all():
                    raise ValueError(f"{col} doit être entre 0 et 1")
            
            logger.info(f"Paramètres IRB lus avec succès: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des paramètres IRB: {e}")
            raise
    
    def read_config(self, filepath: Union[str, Path]) -> Dict[str, pd.DataFrame]:
        """Lire le fichier de configuration"""
        logger.info(f"Lecture de la configuration: {filepath}")
        
        try:
            config_data = {}
            
            # Configuration générale
            general_df = pd.read_excel(filepath, sheet_name='General_Config')
            config_data['general'] = general_df
            
            # Pondérations de risque
            risk_weights_df = pd.read_excel(filepath, sheet_name='Risk_Weights')
            config_data['risk_weights'] = risk_weights_df
            
            logger.info("Configuration lue avec succès")
            return config_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la configuration: {e}")
            raise
    
    def validate_data_consistency(self, inputs: Dict[str, pd.DataFrame]) -> bool:
        """Valider la cohérence entre les différents fichiers"""
        logger.info("Validation de la cohérence des données")
        
        try:
            # Vérifier que les entités dans portfolios existent dans entities
            if 'entities' in inputs and 'portfolios' in inputs:
                entity_ids = set(inputs['entities']['id'])
                portfolio_entities = set(inputs['portfolios']['entity_id'])
                
                missing_entities = portfolio_entities - entity_ids
                if missing_entities:
                    raise ValueError(f"Entités manquantes dans le fichier entités: {missing_entities}")
            
            # Vérifier les devises dans FX rates correspondent aux entités
            if 'entities' in inputs and 'fx_rates' in inputs:
                entity_currencies = set(inputs['entities']['currency'])
                fx_currencies = set(inputs['fx_rates']['from_currency']) | set(inputs['fx_rates']['to_currency'])
                
                missing_fx = entity_currencies - fx_currencies - {'EUR'}  # EUR est la devise de base
                if missing_fx:
                    logger.warning(f"Devises manquantes dans les taux de change: {missing_fx}")
            
            # Vérifier les dates de FX rates couvrent la période de simulation
            if 'fx_rates' in inputs:
                fx_dates = inputs['fx_rates']['date']
                min_date = fx_dates.min()
                max_date = fx_dates.max()
                
                logger.info(f"Période couverte par les taux de change: {min_date} à {max_date}")
            
            logger.info("Validation de cohérence terminée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de cohérence: {e}")
            raise
    
    def get_file_info(self, filepath: Union[str, Path]) -> Dict:
        """Obtenir des informations sur un fichier Excel"""
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                return {'exists': False}
            
            # Lire les métadonnées
            xl_file = pd.ExcelFile(filepath)
            sheet_names = xl_file.sheet_names
            
            info = {
                'exists': True,
                'size_mb': filepath.stat().st_size / (1024 * 1024),
                'modified': datetime.fromtimestamp(filepath.stat().st_mtime),
                'sheet_names': sheet_names
            }
            
            # Compter les lignes dans chaque feuille
            for sheet in sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet)
                    info[f'{sheet}_rows'] = len(df)
                    info[f'{sheet}_columns'] = len(df.columns)
                except:
                    info[f'{sheet}_rows'] = 'Erreur'
                    info[f'{sheet}_columns'] = 'Erreur'
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des informations du fichier: {e}")
            return {'exists': False, 'error': str(e)}
    
    def preview_file(self, filepath: Union[str, Path], sheet_name: str = None, 
                    max_rows: int = 10) -> pd.DataFrame:
        """Prévisualiser un fichier Excel"""
        try:
            if sheet_name:
                df = pd.read_excel(filepath, sheet_name=sheet_name, nrows=max_rows)
            else:
                df = pd.read_excel(filepath, nrows=max_rows)
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation: {e}")
            return pd.DataFrame()
    
    def repair_file(self, filepath: Union[str, Path], file_type: str) -> bool:
        """Tenter de réparer un fichier corrompu"""
        logger.info(f"Tentative de réparation du fichier: {filepath}")
        
        try:
            # Stratégies de réparation selon le type de fichier
            if file_type == 'entities':
                return self._repair_entities_file(filepath)
            elif file_type == 'fx_rates':
                return self._repair_fx_file(filepath)
            elif file_type == 'portfolios':
                return self._repair_portfolios_file(filepath)
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la réparation: {e}")
            return False
    
    def _repair_entities_file(self, filepath: Path) -> bool:
        """Réparer le fichier des entités"""
        try:
            # Lire avec des paramètres plus permissifs
            df = pd.read_excel(filepath, sheet_name=0)  # Première feuille
            
            # Nettoyer les colonnes
            df.columns = df.columns.str.strip().str.lower()
            
            # Mapper les noms de colonnes possibles
            column_mapping = {
                'entity_id': 'id',
                'entity_name': 'name',
                'country_code': 'country',
                'currency_code': 'currency',
                'ownership': 'ownership_pct',
                'ownership_percent': 'ownership_pct'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Sauvegarder le fichier réparé
            backup_path = filepath.with_suffix('.backup.xlsx')
            filepath.rename(backup_path)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Entities', index=False)
            
            logger.info(f"Fichier entités réparé. Sauvegarde: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Impossible de réparer le fichier entités: {e}")
            return False
    
    def _repair_fx_file(self, filepath: Path) -> bool:
        """Réparer le fichier des taux de change"""
        # Implémentation similaire pour les FX rates
        return False
    
    def _repair_portfolios_file(self, filepath: Path) -> bool:
        """Réparer le fichier des portefeuilles"""
        # Implémentation similaire pour les portefeuilles
        return False
