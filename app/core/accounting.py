"""
Moteur comptable pour l'application bancaire
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import asdict

from ..config.schemas import TrialBalanceSchema, ProductClass
from ..config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class AccountingEngine:
    """Moteur de génération des écritures comptables et balances"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.chart_of_accounts = DEFAULT_CONFIG['chart_of_accounts']
        self.product_mapping = self._create_product_mapping()
        
        logger.info("Moteur comptable initialisé")
    
    def _create_product_mapping(self) -> Dict[str, Dict]:
        """Créer le mapping produits vers comptes comptables"""
        mapping = {
            # Prêts
            'RETAIL_MORTGAGE': {
                'asset_account': '1200',
                'provision_account': '2500',
                'interest_income_account': '7000'
            },
            'RETAIL_CONSUMER': {
                'asset_account': '1200',
                'provision_account': '2500',
                'interest_income_account': '7000'
            },
            'RETAIL_CREDIT_CARDS': {
                'asset_account': '1200',
                'provision_account': '2500',
                'interest_income_account': '7000'
            },
            'CORPORATE_LOANS': {
                'asset_account': '1200',
                'provision_account': '2500',
                'interest_income_account': '7000'
            },
            'SME_LOANS': {
                'asset_account': '1200',
                'provision_account': '2500',
                'interest_income_account': '7000'
            },
            
            # Dépôts
            'RETAIL_DEPOSITS': {
                'liability_account': '2200',
                'interest_expense_account': '6000'
            },
            'CORPORATE_DEPOSITS': {
                'liability_account': '2200',
                'interest_expense_account': '6000'
            },
            
            # Titres
            'GOVERNMENT_BONDS': {
                'asset_account': '1300',
                'interest_income_account': '7000'
            },
            'CORPORATE_BONDS': {
                'asset_account': '1300',
                'interest_income_account': '7000'
            },
            
            # Dérivés
            'INTEREST_RATE_SWAPS': {
                'asset_account': '1400',  # Si MTM positif
                'liability_account': '2400',  # Si MTM négatif
                'pnl_account': '7200'  # Gains/pertes
            },
            
            # Engagements
            'CREDIT_LINES': {
                'off_balance_account': '9000',  # Hors bilan
                'provision_account': '2500'
            }
        }
        
        return mapping
    
    def generate_trial_balance(self, simulation_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les balances par entité"""
        logger.info("Génération des balances comptables")
        
        try:
            positions = simulation_data['positions']
            cash_flows = simulation_data['cash_flows']
            derivatives = simulation_data.get('derivatives', pd.DataFrame())
            
            # Filtrer les positions de fin d'année
            year_end_positions = positions[positions['date'] == positions['date'].max()].copy()
            
            # Générer les balances par entité
            trial_balances = {}
            entities = year_end_positions['entity_id'].unique()
            
            for entity_id in entities:
                entity_positions = year_end_positions[year_end_positions['entity_id'] == entity_id]
                entity_cash_flows = cash_flows[cash_flows['entity_id'] == entity_id]
                entity_derivatives = derivatives[derivatives['entity_id'] == entity_id] if not derivatives.empty else pd.DataFrame()
                
                tb = self._generate_entity_trial_balance(
                    entity_id, entity_positions, entity_cash_flows, entity_derivatives
                )
                trial_balances[f'tb_{entity_id.lower()}'] = tb
            
            logger.info(f"Balances générées pour {len(trial_balances)} entités")
            return trial_balances
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des balances: {e}")
            raise
    
    def _generate_entity_trial_balance(self, entity_id: str, positions: pd.DataFrame, 
                                     cash_flows: pd.DataFrame, derivatives: pd.DataFrame) -> pd.DataFrame:
        """Générer la balance d'une entité"""
        tb_entries = []
        
        # 1. Traiter les positions de bilan
        tb_entries.extend(self._process_balance_sheet_positions(entity_id, positions))
        
        # 2. Traiter les flux de P&L
        tb_entries.extend(self._process_pnl_flows(entity_id, cash_flows))
        
        # 3. Traiter les dérivés
        if not derivatives.empty:
            tb_entries.extend(self._process_derivatives(entity_id, derivatives))
        
        # 4. Ajouter les capitaux propres et autres postes
        tb_entries.extend(self._add_equity_and_other_items(entity_id, positions))
        
        # 5. Convertir en DataFrame et équilibrer
        tb_df = pd.DataFrame(tb_entries)
        tb_df = self._balance_trial_balance(tb_df)
        
        return tb_df
    
    def _process_balance_sheet_positions(self, entity_id: str, positions: pd.DataFrame) -> List[Dict]:
        """Traiter les positions de bilan"""
        entries = []
        
        # Grouper par produit
        product_groups = positions.groupby('product_id')
        
        for product_id, group in product_groups:
            mapping = self.product_mapping.get(product_id, {})
            total_ead = group['ead'].sum()
            total_provisions = group['provisions'].sum()
            
            # Déterminer la devise locale
            entity_currency = self._get_entity_currency(entity_id)
            
            # Actifs (prêts, titres)
            if 'asset_account' in mapping and total_ead > 0:
                entries.append({
                    'entity_id': entity_id,
                    'account_code': mapping['asset_account'],
                    'account_name': self.chart_of_accounts[mapping['asset_account']]['name'],
                    'amount_lcy': total_ead,
                    'amount_eur': self._convert_to_eur(total_ead, entity_currency),
                    'account_type': 'ASSET'
                })
                
                # Provisions associées
                if total_provisions > 0:
                    entries.append({
                        'entity_id': entity_id,
                        'account_code': mapping['provision_account'],
                        'account_name': self.chart_of_accounts[mapping['provision_account']]['name'],
                        'amount_lcy': -total_provisions,  # Négatif car diminue l'actif
                        'amount_eur': -self._convert_to_eur(total_provisions, entity_currency),
                        'account_type': 'LIABILITY'
                    })
            
            # Passifs (dépôts)
            elif 'liability_account' in mapping and total_ead > 0:
                entries.append({
                    'entity_id': entity_id,
                    'account_code': mapping['liability_account'],
                    'account_name': self.chart_of_accounts[mapping['liability_account']]['name'],
                    'amount_lcy': total_ead,
                    'amount_eur': self._convert_to_eur(total_ead, entity_currency),
                    'account_type': 'LIABILITY'
                })
        
        return entries
    
    def _process_pnl_flows(self, entity_id: str, cash_flows: pd.DataFrame) -> List[Dict]:
        """Traiter les flux de P&L"""
        entries = []
        
        if cash_flows.empty:
            return entries
        
        # Agréger les flux par produit
        product_flows = cash_flows.groupby('product_id').agg({
            'interest_in': 'sum',
            'interest_out': 'sum',
            'fees': 'sum'
        })
        
        entity_currency = self._get_entity_currency(entity_id)
        
        for product_id, flows in product_flows.iterrows():
            mapping = self.product_mapping.get(product_id, {})
            
            # Produits d'intérêts
            if flows['interest_in'] > 0 and 'interest_income_account' in mapping:
                entries.append({
                    'entity_id': entity_id,
                    'account_code': mapping['interest_income_account'],
                    'account_name': self.chart_of_accounts[mapping['interest_income_account']]['name'],
                    'amount_lcy': flows['interest_in'],
                    'amount_eur': self._convert_to_eur(flows['interest_in'], entity_currency),
                    'account_type': 'INCOME'
                })
            
            # Charges d'intérêts
            if flows['interest_out'] > 0 and 'interest_expense_account' in mapping:
                entries.append({
                    'entity_id': entity_id,
                    'account_code': mapping['interest_expense_account'],
                    'account_name': self.chart_of_accounts[mapping['interest_expense_account']]['name'],
                    'amount_lcy': flows['interest_out'],
                    'amount_eur': self._convert_to_eur(flows['interest_out'], entity_currency),
                    'account_type': 'EXPENSE'
                })
            
            # Commissions
            if flows['fees'] > 0:
                entries.append({
                    'entity_id': entity_id,
                    'account_code': '7100',  # Commissions perçues
                    'account_name': self.chart_of_accounts['7100']['name'],
                    'amount_lcy': flows['fees'],
                    'amount_eur': self._convert_to_eur(flows['fees'], entity_currency),
                    'account_type': 'INCOME'
                })
        
        return entries
    
    def _process_derivatives(self, entity_id: str, derivatives: pd.DataFrame) -> List[Dict]:
        """Traiter les positions sur dérivés"""
        entries = []
        entity_currency = self._get_entity_currency(entity_id)
        
        for _, deriv in derivatives.iterrows():
            mtm = deriv['mtm']
            
            if mtm > 0:
                # Dérivé actif
                entries.append({
                    'entity_id': entity_id,
                    'account_code': '1400',
                    'account_name': self.chart_of_accounts['1400']['name'],
                    'amount_lcy': mtm,
                    'amount_eur': self._convert_to_eur(mtm, entity_currency),
                    'account_type': 'ASSET'
                })
            elif mtm < 0:
                # Dérivé passif
                entries.append({
                    'entity_id': entity_id,
                    'account_code': '2400',
                    'account_name': self.chart_of_accounts['2400']['name'],
                    'amount_lcy': abs(mtm),
                    'amount_eur': self._convert_to_eur(abs(mtm), entity_currency),
                    'account_type': 'LIABILITY'
                })
            
            # P&L sur dérivés (variation de MTM)
            pnl_amount = mtm * 0.1  # Approximation de la variation
            if abs(pnl_amount) > 0.01:  # Seuil de matérialité
                entries.append({
                    'entity_id': entity_id,
                    'account_code': '7200' if pnl_amount > 0 else '6200',
                    'account_name': self.chart_of_accounts['7200' if pnl_amount > 0 else '6200']['name'],
                    'amount_lcy': abs(pnl_amount),
                    'amount_eur': self._convert_to_eur(abs(pnl_amount), entity_currency),
                    'account_type': 'INCOME' if pnl_amount > 0 else 'EXPENSE'
                })
        
        return entries
    
    def _add_equity_and_other_items(self, entity_id: str, positions: pd.DataFrame) -> List[Dict]:
        """Ajouter les capitaux propres et autres postes"""
        entries = []
        entity_currency = self._get_entity_currency(entity_id)
        
        # Calculer le total des actifs pour dimensionner les capitaux propres
        total_assets = positions['ead'].sum()
        
        # Capital (environ 8% des actifs)
        capital_amount = total_assets * 0.08
        entries.append({
            'entity_id': entity_id,
            'account_code': '3000',
            'account_name': self.chart_of_accounts['3000']['name'],
            'amount_lcy': capital_amount,
            'amount_eur': self._convert_to_eur(capital_amount, entity_currency),
            'account_type': 'EQUITY'
        })
        
        # Réserves (environ 5% des actifs)
        reserves_amount = total_assets * 0.05
        entries.append({
            'entity_id': entity_id,
            'account_code': '3100',
            'account_name': self.chart_of_accounts['3100']['name'],
            'amount_lcy': reserves_amount,
            'amount_eur': self._convert_to_eur(reserves_amount, entity_currency),
            'account_type': 'EQUITY'
        })
        
        # Caisse et banques centrales (environ 10% des actifs)
        cash_amount = total_assets * 0.10
        entries.append({
            'entity_id': entity_id,
            'account_code': '1000',
            'account_name': self.chart_of_accounts['1000']['name'],
            'amount_lcy': cash_amount,
            'amount_eur': self._convert_to_eur(cash_amount, entity_currency),
            'account_type': 'ASSET'
        })
        
        # Charges générales d'exploitation (environ 2% des actifs)
        opex_amount = total_assets * 0.02
        entries.append({
            'entity_id': entity_id,
            'account_code': '6300',
            'account_name': self.chart_of_accounts['6300']['name'],
            'amount_lcy': opex_amount,
            'amount_eur': self._convert_to_eur(opex_amount, entity_currency),
            'account_type': 'EXPENSE'
        })
        
        return entries
    
    def _balance_trial_balance(self, tb_df: pd.DataFrame) -> pd.DataFrame:
        """Équilibrer la balance"""
        if tb_df.empty:
            return tb_df
        
        # Calculer les totaux par type de compte
        totals = tb_df.groupby('account_type')['amount_lcy'].sum()
        
        assets = totals.get('ASSET', 0)
        liabilities = totals.get('LIABILITY', 0)
        equity = totals.get('EQUITY', 0)
        income = totals.get('INCOME', 0)
        expenses = totals.get('EXPENSE', 0)
        
        # Le résultat net
        net_income = income - expenses
        
        # Différence à équilibrer
        balance_diff = assets - (liabilities + equity + net_income)
        
        if abs(balance_diff) > 0.01:  # Seuil de matérialité
            # Ajouter une écriture d'équilibrage
            entity_id = tb_df['entity_id'].iloc[0]
            entity_currency = self._get_entity_currency(entity_id)
            
            if balance_diff > 0:
                # Manque au passif - ajouter aux réserves
                account_code = '3100'
                account_type = 'EQUITY'
            else:
                # Manque à l'actif - ajouter aux autres actifs
                account_code = '1900'
                account_type = 'ASSET'
                balance_diff = abs(balance_diff)
            
            balance_entry = {
                'entity_id': entity_id,
                'account_code': account_code,
                'account_name': f"{self.chart_of_accounts[account_code]['name']} (Équilibrage)",
                'amount_lcy': balance_diff,
                'amount_eur': self._convert_to_eur(balance_diff, entity_currency),
                'account_type': account_type
            }
            
            tb_df = pd.concat([tb_df, pd.DataFrame([balance_entry])], ignore_index=True)
        
        # Ajouter le résultat net aux capitaux propres
        if abs(net_income) > 0.01:
            entity_id = tb_df['entity_id'].iloc[0]
            entity_currency = self._get_entity_currency(entity_id)
            
            result_entry = {
                'entity_id': entity_id,
                'account_code': '3300',
                'account_name': self.chart_of_accounts['3300']['name'],
                'amount_lcy': net_income,
                'amount_eur': self._convert_to_eur(net_income, entity_currency),
                'account_type': 'EQUITY'
            }
            
            tb_df = pd.concat([tb_df, pd.DataFrame([result_entry])], ignore_index=True)
        
        # Trier par code de compte
        tb_df = tb_df.sort_values('account_code').reset_index(drop=True)
        
        return tb_df
    
    def _get_entity_currency(self, entity_id: str) -> str:
        """Obtenir la devise d'une entité"""
        currency_mapping = {
            'EU_SUB': 'EUR',
            'US_SUB': 'USD',
            'CN_SUB': 'CNY'
        }
        return currency_mapping.get(entity_id, 'EUR')
    
    def _convert_to_eur(self, amount: float, from_currency: str) -> float:
        """Convertir un montant vers EUR"""
        if from_currency == 'EUR':
            return amount
        
        # Utiliser les taux de change de la configuration
        fx_rates = self.config.get('fx_rates', {})
        
        if from_currency == 'USD':
            rate = fx_rates.get('USD_EUR', 1.10)
            return amount / rate
        elif from_currency == 'CNY':
            rate = fx_rates.get('CNY_EUR', 7.85)
            return amount / rate
        
        return amount  # Par défaut, pas de conversion
    
    def generate_financial_statements(self, trial_balances: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les états financiers à partir des balances"""
        financial_statements = {}
        
        for entity_key, tb in trial_balances.items():
            entity_id = entity_key.replace('tb_', '').upper()
            
            # Bilan
            balance_sheet = self._create_balance_sheet(tb)
            financial_statements[f'bs_{entity_id.lower()}'] = balance_sheet
            
            # Compte de résultat
            income_statement = self._create_income_statement(tb)
            financial_statements[f'pl_{entity_id.lower()}'] = income_statement
        
        return financial_statements
    
    def _create_balance_sheet(self, tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le bilan à partir de la balance"""
        # Filtrer les comptes de bilan
        balance_accounts = tb[tb['account_type'].isin(['ASSET', 'LIABILITY', 'EQUITY'])].copy()
        
        # Regrouper par grandes masses
        balance_sheet_data = []
        
        # Actifs
        assets = balance_accounts[balance_accounts['account_type'] == 'ASSET']
        for _, row in assets.iterrows():
            balance_sheet_data.append({
                'section': 'ACTIF',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_lcy': row['amount_lcy'],
                'amount_eur': row['amount_eur']
            })
        
        # Passifs
        liabilities = balance_accounts[balance_accounts['account_type'] == 'LIABILITY']
        for _, row in liabilities.iterrows():
            balance_sheet_data.append({
                'section': 'PASSIF',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_lcy': row['amount_lcy'],
                'amount_eur': row['amount_eur']
            })
        
        # Capitaux propres
        equity = balance_accounts[balance_accounts['account_type'] == 'EQUITY']
        for _, row in equity.iterrows():
            balance_sheet_data.append({
                'section': 'CAPITAUX PROPRES',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_lcy': row['amount_lcy'],
                'amount_eur': row['amount_eur']
            })
        
        return pd.DataFrame(balance_sheet_data)
    
    def _create_income_statement(self, tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le compte de résultat à partir de la balance"""
        # Filtrer les comptes de P&L
        pnl_accounts = tb[tb['account_type'].isin(['INCOME', 'EXPENSE'])].copy()
        
        income_statement_data = []
        
        # Produits
        income = pnl_accounts[pnl_accounts['account_type'] == 'INCOME']
        for _, row in income.iterrows():
            income_statement_data.append({
                'section': 'PRODUITS',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_lcy': row['amount_lcy'],
                'amount_eur': row['amount_eur']
            })
        
        # Charges
        expenses = pnl_accounts[pnl_accounts['account_type'] == 'EXPENSE']
        for _, row in expenses.iterrows():
            income_statement_data.append({
                'section': 'CHARGES',
                'account_code': row['account_code'],
                'account_name': row['account_name'],
                'amount_lcy': row['amount_lcy'],
                'amount_eur': row['amount_eur']
            })
        
        return pd.DataFrame(income_statement_data)
