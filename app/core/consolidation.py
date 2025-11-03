"""
Moteur de consolidation pour l'application bancaire
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

from ..config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class ConsolidationEngine:
    """Moteur de consolidation des comptes"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.fx_rates = self._load_fx_rates()
        self.ownership_percentages = self._load_ownership()
        
        logger.info("Moteur de consolidation initialisé")
    
    def _load_fx_rates(self) -> Dict[str, float]:
        """Charger les taux de change de clôture"""
        fx_rates = {
            'USD_EUR': self.config.get('fx_rates', {}).get('USD_EUR', 1.10),
            'CNY_EUR': self.config.get('fx_rates', {}).get('CNY_EUR', 7.85),
            'EUR_EUR': 1.0
        }
        return fx_rates
    
    def _load_ownership(self) -> Dict[str, float]:
        """Charger les pourcentages de détention"""
        ownership = {
            'EU_SUB': self.config.get('ownership', {}).get('EU', 100.0) / 100,
            'US_SUB': self.config.get('ownership', {}).get('US', 80.0) / 100,
            'CN_SUB': self.config.get('ownership', {}).get('CN', 60.0) / 100
        }
        return ownership
    
    def consolidate(self, accounting_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Effectuer la consolidation complète"""
        logger.info("Début de la consolidation")
        
        try:
            # 1. Conversion des devises
            converted_balances = self._convert_currencies(accounting_data)
            
            # 2. Éliminations intercompagnies
            eliminated_balances = self._eliminate_intercompany(converted_balances)
            
            # 3. Calcul des intérêts minoritaires
            consolidated_balances = self._calculate_minority_interests(eliminated_balances)
            
            # 4. Agrégation finale
            group_balance = self._aggregate_group_balance(consolidated_balances)
            
            # 5. Génération des états consolidés
            consolidated_statements = self._generate_consolidated_statements(group_balance)
            
            # 6. Liasse de consolidation
            consolidation_package = self._generate_consolidation_package(
                converted_balances, eliminated_balances, group_balance
            )
            
            results = {
                'group_trial_balance': group_balance,
                'consolidated_balance_sheet': consolidated_statements['balance_sheet'],
                'consolidated_income_statement': consolidated_statements['income_statement'],
                'consolidation_package': consolidation_package,
                'fx_translation_details': self._generate_fx_details(accounting_data, converted_balances),
                'minority_interests_details': self._generate_minority_details(eliminated_balances, consolidated_balances)
            }
            
            logger.info("Consolidation terminée avec succès")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la consolidation: {e}")
            raise
    
    def _convert_currencies(self, accounting_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Convertir toutes les devises en EUR"""
        logger.info("Conversion des devises")
        
        converted_data = {}
        
        for entity_key, tb in accounting_data.items():
            entity_id = entity_key.replace('tb_', '').upper()
            
            # Déterminer la devise de l'entité
            entity_currency = self._get_entity_currency(entity_id)
            
            if entity_currency == 'EUR':
                # Pas de conversion nécessaire
                converted_tb = tb.copy()
                converted_tb['fx_rate_used'] = 1.0
                converted_tb['translation_method'] = 'No conversion'
            else:
                # Conversion nécessaire
                converted_tb = self._convert_entity_currency(tb, entity_currency, entity_id)
            
            converted_data[entity_key] = converted_tb
        
        return converted_data
    
    def _convert_entity_currency(self, tb: pd.DataFrame, from_currency: str, entity_id: str) -> pd.DataFrame:
        """Convertir la balance d'une entité vers EUR"""
        converted_tb = tb.copy()
        
        # Taux de change à utiliser
        fx_key = f"{from_currency}_EUR"
        fx_rate = self.fx_rates.get(fx_key, 1.0)
        
        # Méthode de conversion selon le type de compte
        for idx, row in converted_tb.iterrows():
            account_type = row['account_type']
            amount_lcy = row['amount_lcy']
            
            if account_type in ['ASSET', 'LIABILITY']:
                # Comptes de bilan: taux de clôture
                converted_amount = amount_lcy / fx_rate
                method = 'Closing rate'
            elif account_type in ['INCOME', 'EXPENSE']:
                # Comptes de P&L: taux moyen (approximé par le taux de clôture)
                converted_amount = amount_lcy / fx_rate
                method = 'Average rate (approx.)'
            else:  # EQUITY
                # Capitaux propres: taux historique (approximé par le taux de clôture)
                converted_amount = amount_lcy / fx_rate
                method = 'Historical rate (approx.)'
            
            converted_tb.at[idx, 'amount_eur'] = converted_amount
            converted_tb.at[idx, 'fx_rate_used'] = fx_rate
            converted_tb.at[idx, 'translation_method'] = method
        
        # Calculer l'écart de conversion
        total_lcy = converted_tb[converted_tb['account_type'].isin(['ASSET', 'LIABILITY', 'EQUITY'])]['amount_lcy'].sum()
        total_eur = converted_tb[converted_tb['account_type'].isin(['ASSET', 'LIABILITY', 'EQUITY'])]['amount_eur'].sum()
        
        if abs(total_eur) > 0.01:  # Seuil de matérialité
            # Ajouter l'écart de conversion aux capitaux propres
            translation_diff = {
                'entity_id': entity_id,
                'account_code': '3900',
                'account_name': 'Écarts de conversion',
                'amount_lcy': 0.0,
                'amount_eur': -total_eur,  # Équilibrage
                'account_type': 'EQUITY',
                'fx_rate_used': fx_rate,
                'translation_method': 'Translation adjustment'
            }
            
            converted_tb = pd.concat([converted_tb, pd.DataFrame([translation_diff])], ignore_index=True)
        
        return converted_tb
    
    def _eliminate_intercompany(self, converted_balances: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Éliminer les opérations intercompagnies"""
        logger.info("Élimination des opérations intercompagnies")
        
        eliminated_balances = {}
        
        for entity_key, tb in converted_balances.items():
            eliminated_tb = tb.copy()
            
            # Identifier et éliminer les créances/dettes intercompagnies
            eliminated_tb = self._eliminate_intercompany_loans(eliminated_tb)
            
            # Éliminer les revenus/charges intercompagnies
            eliminated_tb = self._eliminate_intercompany_income(eliminated_tb)
            
            # Éliminer les dividendes intra-groupe
            eliminated_tb = self._eliminate_intercompany_dividends(eliminated_tb)
            
            eliminated_balances[entity_key] = eliminated_tb
        
        return eliminated_balances
    
    def _eliminate_intercompany_loans(self, tb: pd.DataFrame) -> pd.DataFrame:
        """Éliminer les prêts intercompagnies"""
        # Identifier les comptes de prêts intercompagnies (simplification)
        intercompany_accounts = ['1100']  # Prêts aux établissements de crédit
        
        for account in intercompany_accounts:
            mask = tb['account_code'] == account
            if mask.any():
                # Réduire de 20% (estimation des opérations intercompagnies)
                intercompany_amount = tb.loc[mask, 'amount_eur'].sum() * 0.20
                
                if intercompany_amount > 0.01:
                    # Ajouter une écriture d'élimination
                    elimination_entry = {
                        'entity_id': tb['entity_id'].iloc[0],
                        'account_code': f"{account}_ELIM",
                        'account_name': f"Élimination {tb.loc[mask, 'account_name'].iloc[0]}",
                        'amount_lcy': 0.0,
                        'amount_eur': -intercompany_amount,
                        'account_type': tb.loc[mask, 'account_type'].iloc[0],
                        'fx_rate_used': 1.0,
                        'translation_method': 'Elimination'
                    }
                    
                    tb = pd.concat([tb, pd.DataFrame([elimination_entry])], ignore_index=True)
        
        return tb
    
    def _eliminate_intercompany_income(self, tb: pd.DataFrame) -> pd.DataFrame:
        """Éliminer les revenus/charges intercompagnies"""
        # Identifier les comptes de revenus d'intérêts intercompagnies
        intercompany_income_accounts = ['7000']  # Intérêts et produits assimilés
        
        for account in intercompany_income_accounts:
            mask = tb['account_code'] == account
            if mask.any():
                # Réduire de 15% (estimation des revenus intercompagnies)
                intercompany_income = tb.loc[mask, 'amount_eur'].sum() * 0.15
                
                if intercompany_income > 0.01:
                    elimination_entry = {
                        'entity_id': tb['entity_id'].iloc[0],
                        'account_code': f"{account}_ELIM",
                        'account_name': f"Élimination {tb.loc[mask, 'account_name'].iloc[0]}",
                        'amount_lcy': 0.0,
                        'amount_eur': -intercompany_income,
                        'account_type': 'INCOME',
                        'fx_rate_used': 1.0,
                        'translation_method': 'Elimination'
                    }
                    
                    tb = pd.concat([tb, pd.DataFrame([elimination_entry])], ignore_index=True)
        
        return tb
    
    def _eliminate_intercompany_dividends(self, tb: pd.DataFrame) -> pd.DataFrame:
        """Éliminer les dividendes intra-groupe"""
        # Rechercher les comptes de dividendes
        dividend_accounts = ['7900']  # Autres produits (incluant dividendes)
        
        for account in dividend_accounts:
            mask = tb['account_code'] == account
            if mask.any():
                # Estimer les dividendes intra-groupe (10% des autres produits)
                dividend_amount = tb.loc[mask, 'amount_eur'].sum() * 0.10
                
                if dividend_amount > 0.01:
                    elimination_entry = {
                        'entity_id': tb['entity_id'].iloc[0],
                        'account_code': f"{account}_DIV_ELIM",
                        'account_name': "Élimination dividendes intra-groupe",
                        'amount_lcy': 0.0,
                        'amount_eur': -dividend_amount,
                        'account_type': 'INCOME',
                        'fx_rate_used': 1.0,
                        'translation_method': 'Dividend elimination'
                    }
                    
                    tb = pd.concat([tb, pd.DataFrame([elimination_entry])], ignore_index=True)
        
        return tb
    
    def _calculate_minority_interests(self, eliminated_balances: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Calculer les intérêts minoritaires"""
        logger.info("Calcul des intérêts minoritaires")
        
        consolidated_balances = {}
        
        for entity_key, tb in eliminated_balances.items():
            entity_id = entity_key.replace('tb_', '').upper()
            ownership_pct = self.ownership_percentages.get(entity_id, 1.0)
            minority_pct = 1.0 - ownership_pct
            
            if minority_pct > 0.01:  # Il y a des intérêts minoritaires
                consolidated_tb = tb.copy()
                
                # Calculer les capitaux propres de l'entité
                equity_mask = consolidated_tb['account_type'] == 'EQUITY'
                total_equity = consolidated_tb.loc[equity_mask, 'amount_eur'].sum()
                
                # Calculer le résultat net
                income_mask = consolidated_tb['account_type'] == 'INCOME'
                expense_mask = consolidated_tb['account_type'] == 'EXPENSE'
                net_income = (consolidated_tb.loc[income_mask, 'amount_eur'].sum() - 
                            consolidated_tb.loc[expense_mask, 'amount_eur'].sum())
                
                # Intérêts minoritaires sur les capitaux propres
                minority_equity = total_equity * minority_pct
                
                # Intérêts minoritaires sur le résultat
                minority_income = net_income * minority_pct
                
                # Ajouter les intérêts minoritaires
                if abs(minority_equity) > 0.01:
                    minority_entry = {
                        'entity_id': entity_id,
                        'account_code': '3400',
                        'account_name': 'Intérêts minoritaires',
                        'amount_lcy': 0.0,
                        'amount_eur': minority_equity,
                        'account_type': 'EQUITY',
                        'fx_rate_used': 1.0,
                        'translation_method': 'Minority interests'
                    }
                    
                    consolidated_tb = pd.concat([consolidated_tb, pd.DataFrame([minority_entry])], ignore_index=True)
                
                # Ajuster les capitaux propres du groupe
                group_equity_adjustment = -minority_equity
                if abs(group_equity_adjustment) > 0.01:
                    adjustment_entry = {
                        'entity_id': entity_id,
                        'account_code': '3100',
                        'account_name': 'Réserves (ajustement consolidation)',
                        'amount_lcy': 0.0,
                        'amount_eur': group_equity_adjustment,
                        'account_type': 'EQUITY',
                        'fx_rate_used': 1.0,
                        'translation_method': 'Consolidation adjustment'
                    }
                    
                    consolidated_tb = pd.concat([consolidated_tb, pd.DataFrame([adjustment_entry])], ignore_index=True)
            
            else:
                # Pas d'intérêts minoritaires
                consolidated_tb = tb.copy()
            
            consolidated_balances[entity_key] = consolidated_tb
        
        return consolidated_balances
    
    def _aggregate_group_balance(self, consolidated_balances: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Agréger les balances en balance groupe"""
        logger.info("Agrégation de la balance groupe")
        
        # Concaténer toutes les balances
        all_balances = []
        for entity_key, tb in consolidated_balances.items():
            all_balances.append(tb)
        
        combined_tb = pd.concat(all_balances, ignore_index=True)
        
        # Agréger par compte
        group_balance = combined_tb.groupby(['account_code', 'account_name', 'account_type']).agg({
            'amount_eur': 'sum',
            'amount_lcy': 'sum'  # Somme des montants en devise locale (pour info)
        }).reset_index()
        
        # Ajouter des informations de consolidation
        group_balance['entity_id'] = 'GROUP'
        group_balance['fx_rate_used'] = 1.0
        group_balance['translation_method'] = 'Consolidated'
        
        # Réorganiser les colonnes
        group_balance = group_balance[['entity_id', 'account_code', 'account_name', 
                                     'amount_lcy', 'amount_eur', 'account_type',
                                     'fx_rate_used', 'translation_method']]
        
        # Trier par code de compte
        group_balance = group_balance.sort_values('account_code').reset_index(drop=True)
        
        return group_balance
    
    def _generate_consolidated_statements(self, group_balance: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Générer les états financiers consolidés"""
        logger.info("Génération des états financiers consolidés")
        
        # Bilan consolidé
        balance_sheet_data = []
        
        # Actifs
        assets = group_balance[group_balance['account_type'] == 'ASSET']
        for _, row in assets.iterrows():
            balance_sheet_data.append({
                'section': 'ACTIF',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_eur': row['amount_eur']
            })
        
        # Passifs
        liabilities = group_balance[group_balance['account_type'] == 'LIABILITY']
        for _, row in liabilities.iterrows():
            balance_sheet_data.append({
                'section': 'PASSIF',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_eur': row['amount_eur']
            })
        
        # Capitaux propres
        equity = group_balance[group_balance['account_type'] == 'EQUITY']
        for _, row in equity.iterrows():
            balance_sheet_data.append({
                'section': 'CAPITAUX PROPRES',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_eur': row['amount_eur']
            })
        
        balance_sheet = pd.DataFrame(balance_sheet_data)
        
        # Compte de résultat consolidé
        income_statement_data = []
        
        # Produits
        income = group_balance[group_balance['account_type'] == 'INCOME']
        for _, row in income.iterrows():
            income_statement_data.append({
                'section': 'PRODUITS',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_eur': row['amount_eur']
            })
        
        # Charges
        expenses = group_balance[group_balance['account_type'] == 'EXPENSE']
        for _, row in expenses.iterrows():
            income_statement_data.append({
                'section': 'CHARGES',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_eur': row['amount_eur']
            })
        
        income_statement = pd.DataFrame(income_statement_data)
        
        return {
            'balance_sheet': balance_sheet,
            'income_statement': income_statement
        }
    
    def _generate_consolidation_package(self, converted_balances: Dict[str, pd.DataFrame],
                                      eliminated_balances: Dict[str, pd.DataFrame],
                                      group_balance: pd.DataFrame) -> pd.DataFrame:
        """Générer la liasse de consolidation"""
        logger.info("Génération de la liasse de consolidation")
        
        package_data = []
        
        # Pour chaque compte, montrer le détail par entité et les éliminations
        all_accounts = group_balance['account_code'].unique()
        
        for account_code in all_accounts:
            account_name = group_balance[group_balance['account_code'] == account_code]['account_name'].iloc[0]
            
            row_data = {
                'account_code': account_code,
                'account_name': account_name
            }
            
            # Montants par entité (après conversion)
            for entity_key, tb in converted_balances.items():
                entity_id = entity_key.replace('tb_', '').upper()
                entity_amount = tb[tb['account_code'] == account_code]['amount_eur'].sum()
                row_data[f'{entity_id}_converted'] = entity_amount
            
            # Éliminations
            total_eliminations = 0
            for entity_key, tb in eliminated_balances.items():
                elim_accounts = tb[tb['account_code'].str.contains(account_code) & 
                                tb['account_code'].str.contains('ELIM')]['amount_eur'].sum()
                total_eliminations += elim_accounts
            
            row_data['eliminations'] = total_eliminations
            
            # Total consolidé
            row_data['consolidated_total'] = group_balance[group_balance['account_code'] == account_code]['amount_eur'].sum()
            
            package_data.append(row_data)
        
        return pd.DataFrame(package_data)
    
    def _generate_fx_details(self, original_balances: Dict[str, pd.DataFrame],
                           converted_balances: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Générer le détail des conversions de change"""
        fx_details = []
        
        for entity_key in original_balances.keys():
            entity_id = entity_key.replace('tb_', '').upper()
            entity_currency = self._get_entity_currency(entity_id)
            
            if entity_currency != 'EUR':
                original_tb = original_balances[entity_key]
                converted_tb = converted_balances[entity_key]
                
                fx_rate = self.fx_rates.get(f"{entity_currency}_EUR", 1.0)
                
                total_lcy = original_tb['amount_lcy'].sum()
                total_eur = converted_tb['amount_eur'].sum()
                
                fx_details.append({
                    'entity_id': entity_id,
                    'currency': entity_currency,
                    'fx_rate': fx_rate,
                    'total_lcy': total_lcy,
                    'total_eur': total_eur,
                    'translation_difference': total_eur - (total_lcy / fx_rate)
                })
        
        return pd.DataFrame(fx_details)
    
    def _generate_minority_details(self, eliminated_balances: Dict[str, pd.DataFrame],
                                 consolidated_balances: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Générer le détail des intérêts minoritaires"""
        minority_details = []
        
        for entity_key in eliminated_balances.keys():
            entity_id = entity_key.replace('tb_', '').upper()
            ownership_pct = self.ownership_percentages.get(entity_id, 1.0)
            minority_pct = 1.0 - ownership_pct
            
            if minority_pct > 0.01:
                tb = eliminated_balances[entity_key]
                
                # Calculer les capitaux propres
                equity_amount = tb[tb['account_type'] == 'EQUITY']['amount_eur'].sum()
                
                # Calculer le résultat net
                income = tb[tb['account_type'] == 'INCOME']['amount_eur'].sum()
                expenses = tb[tb['account_type'] == 'EXPENSE']['amount_eur'].sum()
                net_income = income - expenses
                
                minority_details.append({
                    'entity_id': entity_id,
                    'ownership_pct': ownership_pct * 100,
                    'minority_pct': minority_pct * 100,
                    'total_equity': equity_amount,
                    'net_income': net_income,
                    'minority_equity': equity_amount * minority_pct,
                    'minority_income': net_income * minority_pct
                })
        
        return pd.DataFrame(minority_details)
    
    def _get_entity_currency(self, entity_id: str) -> str:
        """Obtenir la devise d'une entité"""
        currency_mapping = {
            'EU_SUB': 'EUR',
            'US_SUB': 'USD',
            'CN_SUB': 'CNY'
        }
        return currency_mapping.get(entity_id, 'EUR')
