"""
Moteur de génération de rapports réglementaires (FINREP, COREP, RUBA)
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

from ..config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class ReportingEngine:
    """Moteur de génération des rapports réglementaires"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.finrep_mapping = DEFAULT_CONFIG['finrep_mapping']
        self.chart_of_accounts = DEFAULT_CONFIG['chart_of_accounts']
        
        logger.info("Moteur de reporting initialisé")
    
    def generate_all_reports(self, consolidation_data: Dict[str, pd.DataFrame],
                           rwa_data: Dict[str, pd.DataFrame],
                           liquidity_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer tous les rapports réglementaires"""
        logger.info("Génération de tous les rapports réglementaires")
        
        try:
            reports = {}
            
            # FINREP
            finrep_reports = self._generate_finrep(consolidation_data)
            reports.update(finrep_reports)
            
            # COREP
            corep_reports = self._generate_corep(rwa_data)
            reports.update(corep_reports)
            
            # LCR/NSFR
            liquidity_reports = self._generate_liquidity_reports(liquidity_data)
            reports.update(liquidity_reports)
            
            # RUBA (France)
            ruba_reports = self._generate_ruba(consolidation_data)
            reports.update(ruba_reports)
            
            # ALMM
            almm_reports = self._generate_almm_reports(liquidity_data)
            reports.update(almm_reports)
            
            logger.info(f"Rapports générés: {list(reports.keys())}")
            return reports
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des rapports: {e}")
            raise
    
    def _generate_finrep(self, consolidation_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les rapports FINREP"""
        logger.info("Génération des rapports FINREP")
        
        finrep_reports = {}
        
        if 'group_trial_balance' in consolidation_data:
            group_tb = consolidation_data['group_trial_balance']
            
            # FINREP Balance Sheet
            finrep_bs = self._create_finrep_balance_sheet(group_tb)
            finrep_reports['finrep_balance_sheet'] = finrep_bs
            
            # FINREP Profit & Loss
            finrep_pl = self._create_finrep_profit_loss(group_tb)
            finrep_reports['finrep_profit_loss'] = finrep_pl
            
            # FINREP Statement of Changes in Equity
            finrep_equity = self._create_finrep_equity_changes(group_tb)
            finrep_reports['finrep_equity_changes'] = finrep_equity
            
            # FINREP Breakdown by Product
            finrep_breakdown = self._create_finrep_breakdown(consolidation_data)
            finrep_reports['finrep_breakdown'] = finrep_breakdown
        
        return finrep_reports
    
    def _create_finrep_balance_sheet(self, group_tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le bilan FINREP"""
        finrep_bs_data = []
        
        # Structure FINREP Balance Sheet
        finrep_structure = {
            # ACTIF
            '010': {'name': 'Cash, cash balances at central banks and other demand deposits', 'accounts': ['1000']},
            '020': {'name': 'Financial assets held for trading', 'accounts': ['1400']},
            '030': {'name': 'Non-trading financial assets mandatorily at fair value through profit or loss', 'accounts': []},
            '040': {'name': 'Financial assets designated at fair value through profit or loss', 'accounts': []},
            '050': {'name': 'Financial assets at fair value through other comprehensive income', 'accounts': []},
            '060': {'name': 'Financial assets at amortised cost', 'accounts': ['1100', '1200', '1300']},
            '070': {'name': 'Derivatives – Hedge accounting', 'accounts': []},
            '080': {'name': 'Fair value changes of the hedged items in portfolio hedge of interest rate risk', 'accounts': []},
            '090': {'name': 'Investments in subsidiaries, joint ventures and associates', 'accounts': []},
            '100': {'name': 'Tangible assets', 'accounts': ['1500']},
            '110': {'name': 'Intangible assets', 'accounts': []},
            '120': {'name': 'Tax assets', 'accounts': []},
            '130': {'name': 'Other assets', 'accounts': ['1900']},
            '140': {'name': 'Non-current assets and disposal groups classified as held for sale', 'accounts': []},
            '150': {'name': 'TOTAL ASSETS', 'accounts': []},
            
            # PASSIF
            '010_L': {'name': 'Financial liabilities held for trading', 'accounts': ['2400']},
            '020_L': {'name': 'Financial liabilities designated at fair value through profit or loss', 'accounts': []},
            '030_L': {'name': 'Financial liabilities measured at amortised cost', 'accounts': ['2000', '2100', '2200', '2300']},
            '040_L': {'name': 'Derivatives – Hedge accounting', 'accounts': []},
            '050_L': {'name': 'Fair value changes of the hedged items in portfolio hedge of interest rate risk', 'accounts': []},
            '060_L': {'name': 'Provisions', 'accounts': ['2500']},
            '070_L': {'name': 'Tax liabilities', 'accounts': []},
            '080_L': {'name': 'Share capital repayable on demand', 'accounts': []},
            '090_L': {'name': 'Other liabilities', 'accounts': ['2900']},
            '100_L': {'name': 'Liabilities included in disposal groups classified as held for sale', 'accounts': []},
            '110_L': {'name': 'TOTAL LIABILITIES', 'accounts': []},
            
            # CAPITAUX PROPRES
            '120': {'name': 'Capital', 'accounts': ['3000']},
            '130': {'name': 'Share premium', 'accounts': []},
            '140': {'name': 'Equity instruments issued other than capital', 'accounts': []},
            '150': {'name': 'Other equity', 'accounts': []},
            '160': {'name': 'Retained earnings', 'accounts': ['3100', '3200']},
            '170': {'name': 'Revaluation reserves', 'accounts': []},
            '180': {'name': 'Other reserves', 'accounts': []},
            '190': {'name': 'Accumulated other comprehensive income', 'accounts': []},
            '200': {'name': 'Minority interests', 'accounts': ['3400']},
            '210': {'name': 'TOTAL EQUITY', 'accounts': []},
            '220': {'name': 'TOTAL EQUITY AND LIABILITIES', 'accounts': []}
        }
        
        # Calculer les montants pour chaque ligne FINREP
        for finrep_code, info in finrep_structure.items():
            if info['accounts']:
                # Sommer les comptes correspondants
                amount = group_tb[group_tb['account_code'].isin(info['accounts'])]['amount_eur'].sum()
            else:
                # Lignes de total - calculer selon la logique
                if finrep_code == '150':  # Total actifs
                    amount = group_tb[group_tb['account_type'] == 'ASSET']['amount_eur'].sum()
                elif finrep_code == '110_L':  # Total passifs
                    amount = group_tb[group_tb['account_type'] == 'LIABILITY']['amount_eur'].sum()
                elif finrep_code == '210':  # Total capitaux propres
                    amount = group_tb[group_tb['account_type'] == 'EQUITY']['amount_eur'].sum()
                elif finrep_code == '220':  # Total passif + capitaux propres
                    amount = (group_tb[group_tb['account_type'].isin(['LIABILITY', 'EQUITY'])]['amount_eur'].sum())
                else:
                    amount = 0.0
            
            finrep_bs_data.append({
                'finrep_code': finrep_code,
                'description': info['name'],
                'amount_eur': round(amount, 2),
                'accounts_mapped': ', '.join(info['accounts']) if info['accounts'] else ''
            })
        
        return pd.DataFrame(finrep_bs_data)
    
    def _create_finrep_profit_loss(self, group_tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le compte de résultat FINREP"""
        finrep_pl_data = []
        
        # Structure FINREP Profit & Loss
        finrep_pl_structure = {
            '010': {'name': 'Interest income', 'accounts': ['7000']},
            '020': {'name': 'Interest expenses', 'accounts': ['6000']},
            '030': {'name': 'Dividend income', 'accounts': []},
            '040': {'name': 'Fee and commission income', 'accounts': ['7100']},
            '050': {'name': 'Fee and commission expenses', 'accounts': ['6100']},
            '060': {'name': 'Gains or losses on derecognition of financial assets and liabilities not measured at fair value through profit or loss, net', 'accounts': []},
            '070': {'name': 'Gains or losses on financial assets and liabilities held for trading, net', 'accounts': ['7200']},
            '080': {'name': 'Gains or losses on non-trading financial assets mandatorily at fair value through profit or loss, net', 'accounts': []},
            '090': {'name': 'Gains or losses on financial assets and liabilities designated at fair value through profit or loss, net', 'accounts': []},
            '100': {'name': 'Gains or losses from hedge accounting, net', 'accounts': []},
            '110': {'name': 'Exchange differences, net', 'accounts': []},
            '120': {'name': 'Gains or losses on derecognition of investments in subsidiaries, joint ventures and associates', 'accounts': []},
            '130': {'name': 'Gains or losses from investments in subsidiaries, joint ventures and associates', 'accounts': []},
            '140': {'name': 'Gains or losses on derecognition of tangible and intangible assets', 'accounts': []},
            '150': {'name': 'Other operating income', 'accounts': ['7900']},
            '160': {'name': 'Other operating expenses', 'accounts': ['6900']},
            '170': {'name': 'TOTAL OPERATING INCOME, NET', 'accounts': []},
            '180': {'name': 'Administrative expenses', 'accounts': ['6300']},
            '190': {'name': 'Depreciation', 'accounts': ['6400']},
            '200': {'name': 'Provisions or reversal of provisions', 'accounts': []},
            '210': {'name': 'Impairment or reversal of impairment on financial assets not measured at fair value through profit or loss', 'accounts': ['6500']},
            '220': {'name': 'Impairment or reversal of impairment of investments in subsidiaries, joint ventures and associates', 'accounts': []},
            '230': {'name': 'Impairment or reversal of impairment on tangible assets', 'accounts': []},
            '240': {'name': 'Impairment or reversal of impairment on intangible assets', 'accounts': []},
            '250': {'name': 'Negative goodwill recognised in profit or loss', 'accounts': []},
            '260': {'name': 'Share of the profit or loss of investments in subsidiaries, joint ventures and associates', 'accounts': []},
            '270': {'name': 'Profit or loss from non-current assets and disposal groups classified as held for sale not qualifying as discontinued operations', 'accounts': []},
            '280': {'name': 'PROFIT OR LOSS BEFORE TAX FROM CONTINUING OPERATIONS', 'accounts': []},
            '290': {'name': 'Tax expense or income related to profit or loss from continuing operations', 'accounts': []},
            '300': {'name': 'PROFIT OR LOSS AFTER TAX FROM CONTINUING OPERATIONS', 'accounts': []},
            '310': {'name': 'Profit or loss after tax from discontinued operations', 'accounts': []},
            '320': {'name': 'PROFIT OR LOSS FOR THE YEAR', 'accounts': []}
        }
        
        # Calculer les montants
        for finrep_code, info in finrep_pl_structure.items():
            if info['accounts']:
                amount = group_tb[group_tb['account_code'].isin(info['accounts'])]['amount_eur'].sum()
            else:
                # Lignes de total
                if finrep_code == '170':  # Total operating income
                    income = group_tb[group_tb['account_type'] == 'INCOME']['amount_eur'].sum()
                    amount = income
                elif finrep_code == '280':  # Profit before tax
                    income = group_tb[group_tb['account_type'] == 'INCOME']['amount_eur'].sum()
                    expenses = group_tb[group_tb['account_type'] == 'EXPENSE']['amount_eur'].sum()
                    amount = income - expenses
                elif finrep_code in ['300', '320']:  # Profit after tax
                    income = group_tb[group_tb['account_type'] == 'INCOME']['amount_eur'].sum()
                    expenses = group_tb[group_tb['account_type'] == 'EXPENSE']['amount_eur'].sum()
                    amount = (income - expenses) * 0.75  # Approximation après impôts (25% d'impôts)
                else:
                    amount = 0.0
            
            finrep_pl_data.append({
                'finrep_code': finrep_code,
                'description': info['name'],
                'amount_eur': round(amount, 2),
                'accounts_mapped': ', '.join(info['accounts']) if info['accounts'] else ''
            })
        
        return pd.DataFrame(finrep_pl_data)
    
    def _create_finrep_equity_changes(self, group_tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le tableau de variation des capitaux propres FINREP"""
        equity_data = []
        
        # Composants des capitaux propres
        equity_components = {
            'Capital': group_tb[group_tb['account_code'] == '3000']['amount_eur'].sum(),
            'Retained earnings': group_tb[group_tb['account_code'].isin(['3100', '3200'])]['amount_eur'].sum(),
            'Current year profit': group_tb[group_tb['account_code'] == '3300']['amount_eur'].sum(),
            'Minority interests': group_tb[group_tb['account_code'] == '3400']['amount_eur'].sum()
        }
        
        for component, amount in equity_components.items():
            equity_data.append({
                'equity_component': component,
                'opening_balance': amount * 0.9,  # Approximation solde d'ouverture
                'changes_during_year': amount * 0.1,  # Approximation variations
                'closing_balance': amount
            })
        
        return pd.DataFrame(equity_data)
    
    def _create_finrep_breakdown(self, consolidation_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Créer la ventilation FINREP par produit"""
        breakdown_data = []
        
        # Exemple de ventilation par géographie et produit
        if 'consolidation_package' in consolidation_data:
            package = consolidation_data['consolidation_package']
            
            for _, row in package.iterrows():
                breakdown_data.append({
                    'account_code': row['account_code'],
                    'account_name': row['account_name'],
                    'eu_amount': row.get('EU_SUB_converted', 0),
                    'us_amount': row.get('US_SUB_converted', 0),
                    'cn_amount': row.get('CN_SUB_converted', 0),
                    'eliminations': row.get('eliminations', 0),
                    'consolidated_total': row.get('consolidated_total', 0)
                })
        
        return pd.DataFrame(breakdown_data)
    
    def _generate_corep(self, rwa_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les rapports COREP"""
        logger.info("Génération des rapports COREP")
        
        corep_reports = {}
        
        if 'rwa_detail' in rwa_data:
            # COREP Credit Risk
            corep_credit_risk = self._create_corep_credit_risk(rwa_data['rwa_detail'])
            corep_reports['corep_credit_risk'] = corep_credit_risk
            
            # COREP Own Funds
            corep_own_funds = self._create_corep_own_funds(rwa_data)
            corep_reports['corep_own_funds'] = corep_own_funds
            
            # COREP Capital Ratios
            if 'capital_ratios' in rwa_data:
                corep_capital_ratios = self._create_corep_capital_ratios(rwa_data['capital_ratios'])
                corep_reports['corep_capital_ratios'] = corep_capital_ratios
            
            # COREP Leverage Ratio
            if 'leverage_ratio' in rwa_data:
                corep_leverage = self._create_corep_leverage_ratio(rwa_data['leverage_ratio'])
                corep_reports['corep_leverage_ratio'] = corep_leverage
        
        return corep_reports
    
    def _create_corep_credit_risk(self, rwa_detail: pd.DataFrame) -> pd.DataFrame:
        """Créer le rapport COREP Credit Risk"""
        # Agrégation par classe d'exposition et approche
        corep_data = rwa_detail.groupby(['exposure_class', 'approach']).agg({
            'ead': 'sum',
            'rwa_amount': 'sum',
            'capital_requirement': 'sum'
        }).reset_index()
        
        # Ajouter les codes COREP
        corep_mapping = {
            'central_governments': 'C 01.00',
            'regional_governments': 'C 02.00',
            'public_sector_entities': 'C 03.00',
            'institutions': 'C 06.00',
            'corporates': 'C 07.00',
            'retail': 'C 08.00',
            'secured_by_mortgages': 'C 09.00',
            'exposures_in_default': 'C 10.00'
        }
        
        corep_data['corep_code'] = corep_data['exposure_class'].map(corep_mapping)
        corep_data['rwa_density'] = (corep_data['rwa_amount'] / corep_data['ead'] * 100).round(2)
        
        return corep_data
    
    def _create_corep_own_funds(self, rwa_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Créer le rapport COREP Own Funds"""
        own_funds_data = []
        
        # Estimation des fonds propres
        if 'rwa_summary' in rwa_data:
            total_rwa = rwa_data['rwa_summary']['rwa_amount'].sum()
            
            # Composants des fonds propres (estimation)
            cet1_capital = total_rwa * 0.12  # 12% CET1
            tier1_capital = cet1_capital  # Pas d'AT1 dans cet exemple
            tier2_capital = total_rwa * 0.03  # 3% Tier 2
            total_capital = tier1_capital + tier2_capital
            
            own_funds_items = [
                {'item': 'Common Equity Tier 1 capital', 'amount': cet1_capital, 'code': 'OF1'},
                {'item': 'Additional Tier 1 capital', 'amount': 0, 'code': 'OF2'},
                {'item': 'Tier 1 capital', 'amount': tier1_capital, 'code': 'OF3'},
                {'item': 'Tier 2 capital', 'amount': tier2_capital, 'code': 'OF4'},
                {'item': 'Total own funds', 'amount': total_capital, 'code': 'OF5'}
            ]
            
            own_funds_data = own_funds_items
        
        return pd.DataFrame(own_funds_data)
    
    def _create_corep_capital_ratios(self, capital_ratios: pd.DataFrame) -> pd.DataFrame:
        """Créer le rapport COREP Capital Ratios"""
        # Agrégation consolidée
        total_rwa = capital_ratios['rwa_amount'].sum()
        total_tier1 = capital_ratios['tier1_capital'].sum()
        total_capital = capital_ratios['total_capital'].sum()
        
        ratios_data = [
            {
                'ratio_type': 'Common Equity Tier 1 ratio',
                'ratio_value': round(total_tier1 / total_rwa * 100, 2) if total_rwa > 0 else 0,
                'requirement': 4.5,
                'buffer': 2.5,
                'surplus': round(total_tier1 / total_rwa * 100 - 7.0, 2) if total_rwa > 0 else 0
            },
            {
                'ratio_type': 'Tier 1 ratio',
                'ratio_value': round(total_tier1 / total_rwa * 100, 2) if total_rwa > 0 else 0,
                'requirement': 6.0,
                'buffer': 2.5,
                'surplus': round(total_tier1 / total_rwa * 100 - 8.5, 2) if total_rwa > 0 else 0
            },
            {
                'ratio_type': 'Total capital ratio',
                'ratio_value': round(total_capital / total_rwa * 100, 2) if total_rwa > 0 else 0,
                'requirement': 8.0,
                'buffer': 2.5,
                'surplus': round(total_capital / total_rwa * 100 - 10.5, 2) if total_rwa > 0 else 0
            }
        ]
        
        return pd.DataFrame(ratios_data)
    
    def _create_corep_leverage_ratio(self, leverage_ratio: pd.DataFrame) -> pd.DataFrame:
        """Créer le rapport COREP Leverage Ratio"""
        # Agrégation consolidée
        total_exposure = leverage_ratio['total_exposure'].sum()
        total_tier1 = leverage_ratio['tier1_capital'].sum()
        
        leverage_data = [{
            'exposure_measure': total_exposure,
            'tier1_capital': total_tier1,
            'leverage_ratio': round(total_tier1 / total_exposure * 100, 2) if total_exposure > 0 else 0,
            'minimum_requirement': 3.0,
            'surplus': round(total_tier1 / total_exposure * 100 - 3.0, 2) if total_exposure > 0 else 0
        }]
        
        return pd.DataFrame(leverage_data)
    
    def _generate_liquidity_reports(self, liquidity_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les rapports de liquidité"""
        logger.info("Génération des rapports de liquidité")
        
        liquidity_reports = {}
        
        # LCR Report
        if 'lcr_summary' in liquidity_data:
            lcr_report = self._create_lcr_report(liquidity_data['lcr_summary'])
            liquidity_reports['lcr_report'] = lcr_report
        
        # NSFR Report
        if 'nsfr_summary' in liquidity_data:
            nsfr_report = self._create_nsfr_report(liquidity_data['nsfr_summary'])
            liquidity_reports['nsfr_report'] = nsfr_report
        
        return liquidity_reports
    
    def _create_lcr_report(self, lcr_summary: pd.DataFrame) -> pd.DataFrame:
        """Créer le rapport LCR"""
        return lcr_summary.copy()
    
    def _create_nsfr_report(self, nsfr_summary: pd.DataFrame) -> pd.DataFrame:
        """Créer le rapport NSFR"""
        return nsfr_summary.copy()
    
    def _generate_ruba(self, consolidation_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les rapports RUBA (France)"""
        logger.info("Génération des rapports RUBA")
        
        ruba_reports = {}
        
        if 'group_trial_balance' in consolidation_data:
            group_tb = consolidation_data['group_trial_balance']
            
            # RUBA Bilan
            ruba_bilan = self._create_ruba_bilan(group_tb)
            ruba_reports['ruba_bilan'] = ruba_bilan
            
            # RUBA Compte de résultat
            ruba_compte_resultat = self._create_ruba_compte_resultat(group_tb)
            ruba_reports['ruba_compte_resultat'] = ruba_compte_resultat
            
            # RUBA Ratios prudentiels
            ruba_ratios = self._create_ruba_ratios_prudentiels()
            ruba_reports['ruba_ratios_prudentiels'] = ruba_ratios
        
        return ruba_reports
    
    def _create_ruba_bilan(self, group_tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le bilan RUBA"""
        ruba_bilan_data = []
        
        # Structure RUBA simplifiée
        ruba_structure = {
            'A1': {'name': 'Caisse, Banques centrales', 'accounts': ['1000']},
            'A2': {'name': 'Créances sur établissements de crédit', 'accounts': ['1100']},
            'A3': {'name': 'Créances sur clientèle', 'accounts': ['1200']},
            'A4': {'name': 'Titres de transaction', 'accounts': ['1300']},
            'A5': {'name': 'Titres de placement', 'accounts': ['1300']},
            'A6': {'name': 'Immobilisations', 'accounts': ['1500']},
            'P1': {'name': 'Dettes envers établissements de crédit', 'accounts': ['2100']},
            'P2': {'name': 'Dettes envers clientèle', 'accounts': ['2200']},
            'P3': {'name': 'Dettes représentées par un titre', 'accounts': ['2300']},
            'P4': {'name': 'Provisions', 'accounts': ['2500']},
            'C1': {'name': 'Capital', 'accounts': ['3000']},
            'C2': {'name': 'Réserves', 'accounts': ['3100']},
            'C3': {'name': 'Report à nouveau', 'accounts': ['3200']},
            'C4': {'name': 'Résultat', 'accounts': ['3300']}
        }
        
        for ruba_code, info in ruba_structure.items():
            amount = group_tb[group_tb['account_code'].isin(info['accounts'])]['amount_eur'].sum()
            
            ruba_bilan_data.append({
                'ruba_code': ruba_code,
                'description': info['name'],
                'amount_eur': round(amount, 2)
            })
        
        return pd.DataFrame(ruba_bilan_data)
    
    def _create_ruba_compte_resultat(self, group_tb: pd.DataFrame) -> pd.DataFrame:
        """Créer le compte de résultat RUBA"""
        ruba_cr_data = []
        
        # Structure compte de résultat RUBA
        ruba_cr_structure = {
            'R1': {'name': 'Intérêts et produits assimilés', 'accounts': ['7000']},
            'R2': {'name': 'Intérêts et charges assimilées', 'accounts': ['6000']},
            'R3': {'name': 'Commissions (produits)', 'accounts': ['7100']},
            'R4': {'name': 'Commissions (charges)', 'accounts': ['6100']},
            'R5': {'name': 'Gains ou pertes sur opérations financières', 'accounts': ['7200', '6200']},
            'R6': {'name': 'Autres produits d\'exploitation bancaire', 'accounts': ['7900']},
            'R7': {'name': 'Charges générales d\'exploitation', 'accounts': ['6300']},
            'R8': {'name': 'Dotations aux amortissements', 'accounts': ['6400']},
            'R9': {'name': 'Coût du risque', 'accounts': ['6500']}
        }
        
        for ruba_code, info in ruba_cr_structure.items():
            amount = group_tb[group_tb['account_code'].isin(info['accounts'])]['amount_eur'].sum()
            
            ruba_cr_data.append({
                'ruba_code': ruba_code,
                'description': info['name'],
                'amount_eur': round(amount, 2)
            })
        
        return pd.DataFrame(ruba_cr_data)
    
    def _create_ruba_ratios_prudentiels(self) -> pd.DataFrame:
        """Créer les ratios prudentiels RUBA"""
        ratios_data = [
            {'ratio': 'Ratio de solvabilité', 'valeur': 15.2, 'minimum': 8.0, 'statut': 'Conforme'},
            {'ratio': 'Ratio de levier', 'valeur': 5.8, 'minimum': 3.0, 'statut': 'Conforme'},
            {'ratio': 'LCR', 'valeur': 125.3, 'minimum': 100.0, 'statut': 'Conforme'},
            {'ratio': 'NSFR', 'valeur': 110.7, 'minimum': 100.0, 'statut': 'Conforme'}
        ]
        
        return pd.DataFrame(ratios_data)
    
    def _generate_almm_reports(self, liquidity_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les rapports ALMM"""
        logger.info("Génération des rapports ALMM")
        
        almm_reports = {}
        
        if 'almm_maturity_ladder' in liquidity_data:
            almm_ladder = liquidity_data['almm_maturity_ladder']
            
            # ALMM Maturity Ladder
            almm_reports['almm_maturity_ladder'] = almm_ladder
            
            # ALMM Summary
            if 'almm_summary' in liquidity_data:
                almm_reports['almm_summary'] = liquidity_data['almm_summary']
        
        return almm_reports
    
    def generate_methodology_sheets(self, reports: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Générer les feuilles de méthodologie pour chaque rapport"""
        logger.info("Génération des feuilles de méthodologie")
        
        methodology_sheets = {}
        
        for report_name, report_df in reports.items():
            methodology = self._create_methodology_sheet(report_name)
            methodology_sheets[f'{report_name}_methodology'] = methodology
        
        return methodology_sheets
    
    def _create_methodology_sheet(self, report_name: str) -> pd.DataFrame:
        """Créer une feuille de méthodologie pour un rapport"""
        methodology_data = []
        
        # Méthodologie générale
        general_info = {
            'Section': 'Informations générales',
            'Description': f'Méthodologie pour le rapport {report_name}',
            'Date_generation': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Version': '1.0',
            'Perimetre': 'Groupe bancaire consolidé',
            'Devise_base': 'EUR',
            'Date_reference': '2024-12-31'
        }
        
        for key, value in general_info.items():
            methodology_data.append({
                'Element': key,
                'Valeur': str(value),
                'Description': f'Information sur {key.lower().replace("_", " ")}'
            })
        
        # Hypothèses spécifiques selon le rapport
        if 'finrep' in report_name.lower():
            specific_assumptions = [
                {'Element': 'Normes_comptables', 'Valeur': 'IFRS', 'Description': 'Normes comptables appliquées'},
                {'Element': 'Consolidation', 'Valeur': 'Intégration globale', 'Description': 'Méthode de consolidation'},
                {'Element': 'Conversion_devises', 'Valeur': 'Taux de clôture', 'Description': 'Méthode de conversion des devises'}
            ]
        elif 'corep' in report_name.lower():
            specific_assumptions = [
                {'Element': 'Approche_IRB', 'Valeur': 'Retail uniquement', 'Description': 'Périmètre d\'application IRB'},
                {'Element': 'Approche_standard', 'Valeur': 'Non-retail', 'Description': 'Périmètre d\'application standardisée'},
                {'Element': 'Plancher_fonds_propres', 'Valeur': 'Non applicable', 'Description': 'Application du plancher'}
            ]
        elif 'lcr' in report_name.lower():
            specific_assumptions = [
                {'Element': 'HQLA_niveau_1', 'Valeur': 'Obligations d\'État', 'Description': 'Composition HQLA niveau 1'},
                {'Element': 'Taux_sortie_depots', 'Valeur': 'Selon réglementation', 'Description': 'Taux de sortie appliqués'},
                {'Element': 'Horizon_stress', 'Valeur': '30 jours', 'Description': 'Horizon de stress LCR'}
            ]
        else:
            specific_assumptions = [
                {'Element': 'Hypotheses_generales', 'Valeur': 'Selon CRR3', 'Description': 'Hypothèses réglementaires'}
            ]
        
        methodology_data.extend(specific_assumptions)
        
        return pd.DataFrame(methodology_data)
