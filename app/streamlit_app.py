"""
Application Streamlit principale pour la simulation bancaire et le reporting CRR3
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import logging
from pathlib import Path
import zipfile
import tempfile
import os

# Configuration de la page
st.set_page_config(
    page_title="Banking Simulation & CRR3 Reporting",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajouter le chemin du module
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports des modules
try:
    from core.simulation import SimulationEngine
    from core.accounting import AccountingEngine
    from core.consolidation import ConsolidationEngine
    from core.credit_risk import CreditRiskEngine
    from core.liquidity import LiquidityEngine
    from core.reporting import ReportingEngine
    from io.readers import ExcelReader
    from io.writers import ExcelWriter
    from io.excel_templates import ExcelTemplateGenerator
    from config.defaults import DEFAULT_CONFIG, CRR3_CONSTANTS
except ImportError as e:
    st.error(f"Erreur d'import des modules: {e}")
    st.error("Veuillez vérifier que tous les modules sont présents dans le répertoire.")
    st.stop()

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f4e79;
        padding-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4e79;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Fonction principale de l'application"""
    
    # En-tête principal
    st.markdown('<h1 class="main-header">🏦 Banking Simulation & CRR3 Reporting</h1>', unsafe_allow_html=True)
    
    # Sidebar pour la navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choisir une section",
        [
            "🏠 Accueil",
            "⚙️ Configuration",
            "📊 Simulation",
            "📋 Comptabilité",
            "🔄 Consolidation",
            "⚠️ Risque de Crédit",
            "💧 Liquidité",
            "📈 Reporting",
            "📁 Templates Excel",
            "📥 Import/Export",
            "ℹ️ Documentation"
        ]
    )
    
    # Routage des pages
    if page == "🏠 Accueil":
        show_home_page()
    elif page == "⚙️ Configuration":
        show_configuration_page()
    elif page == "📊 Simulation":
        show_simulation_page()
    elif page == "📋 Comptabilité":
        show_accounting_page()
    elif page == "🔄 Consolidation":
        show_consolidation_page()
    elif page == "⚠️ Risque de Crédit":
        show_credit_risk_page()
    elif page == "💧 Liquidité":
        show_liquidity_page()
    elif page == "📈 Reporting":
        show_reporting_page()
    elif page == "📁 Templates Excel":
        show_templates_page()
    elif page == "📥 Import/Export":
        show_import_export_page()
    elif page == "ℹ️ Documentation":
        show_documentation_page()

def show_home_page():
    """Page d'accueil"""
    st.markdown("## Bienvenue dans l'application de simulation bancaire")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Objectifs de l'application
        
        Cette application permet de :
        - **Simuler** des positions bancaires réalistes
        - **Calculer** les états comptables selon IFRS
        - **Consolider** les données de groupe
        - **Évaluer** les risques de crédit (CRR3)
        - **Analyser** la liquidité (LCR, NSFR, ALMM)
        - **Générer** les rapports réglementaires (FINREP, COREP, RUBA)
        """)
    
    with col2:
        st.markdown("""
        ### 📋 Fonctionnalités principales
        
        - ✅ Moteur de simulation Monte Carlo
        - ✅ Comptabilité IFRS simplifiée
        - ✅ Consolidation multi-devises
        - ✅ Calculs RWA selon CRR3
        - ✅ Ratios de liquidité réglementaires
        - ✅ Export Excel formaté
        - ✅ Templates d'import/export
        """)
    
    # Métriques de démonstration
    st.markdown("### 📊 Aperçu des capacités")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Entités simulées",
            value="3",
            delta="EU, US, CN"
        )
    
    with col2:
        st.metric(
            label="Produits financiers",
            value="12+",
            delta="Prêts, Dépôts, Titres, Dérivés"
        )
    
    with col3:
        st.metric(
            label="Rapports générés",
            value="7",
            delta="FINREP, COREP, RUBA, etc."
        )
    
    with col4:
        st.metric(
            label="Conformité",
            value="CRR3",
            delta="Réglementation européenne"
        )
    
    # Guide de démarrage rapide
    st.markdown("### 🚀 Démarrage rapide")
    
    with st.expander("Guide étape par étape"):
        st.markdown("""
        1. **Configuration** : Définir les paramètres de simulation
        2. **Simulation** : Générer les positions bancaires
        3. **Comptabilité** : Calculer les états financiers
        4. **Consolidation** : Agréger les données de groupe
        5. **Risques** : Évaluer les risques de crédit et liquidité
        6. **Reporting** : Générer les rapports réglementaires
        7. **Export** : Télécharger les fichiers Excel
        """)
    
    # Avertissement
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Avertissement :</strong> Cette application est destinée à des fins éducatives et de démonstration. 
    Elle ne doit pas être utilisée pour des calculs réglementaires réels sans validation appropriée.
    </div>
    """, unsafe_allow_html=True)

def show_configuration_page():
    """Page de configuration"""
    st.markdown("## ⚙️ Configuration de la simulation")
    
    # Configuration du scénario
    st.markdown("### 📋 Paramètres du scénario")
    
    col1, col2 = st.columns(2)
    
    with col1:
        scenario_name = st.text_input("Nom du scénario", value="Scénario_Base_2024")
        scenario_seed = st.number_input("Graine aléatoire", value=42, min_value=1, max_value=9999)
        start_date = st.date_input("Date de début", value=date(2024, 1, 1))
        end_date = st.date_input("Date de fin", value=date(2024, 12, 31))
    
    with col2:
        base_currency = st.selectbox("Devise de base", ["EUR", "USD", "GBP"], index=0)
        num_positions = st.number_input("Nombre de positions", value=1000, min_value=100, max_value=10000)
        stress_scenario = st.selectbox("Scénario de stress", ["Baseline", "Adverse", "Severely Adverse"], index=0)
        include_derivatives = st.checkbox("Inclure les dérivés", value=True)
    
    # Configuration des entités
    st.markdown("### 🏢 Configuration des entités")
    
    entities_config = st.expander("Paramètres des entités")
    with entities_config:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🇪🇺 Entité EU**")
            eu_currency = st.selectbox("Devise EU", ["EUR"], index=0, key="eu_curr")
            eu_ownership = st.slider("Détention EU (%)", 0, 100, 100, key="eu_own")
            eu_size = st.selectbox("Taille EU", ["Large", "Medium", "Small"], index=0, key="eu_size")
        
        with col2:
            st.markdown("**🇺🇸 Entité US**")
            us_currency = st.selectbox("Devise US", ["USD"], index=0, key="us_curr")
            us_ownership = st.slider("Détention US (%)", 0, 100, 80, key="us_own")
            us_size = st.selectbox("Taille US", ["Large", "Medium", "Small"], index=1, key="us_size")
        
        with col3:
            st.markdown("**🇨🇳 Entité CN**")
            cn_currency = st.selectbox("Devise CN", ["CNY"], index=0, key="cn_curr")
            cn_ownership = st.slider("Détention CN (%)", 0, 100, 60, key="cn_own")
            cn_size = st.selectbox("Taille CN", ["Large", "Medium", "Small"], index=2, key="cn_size")
    
    # Configuration des produits
    st.markdown("### 💼 Configuration des produits")
    
    products_config = st.expander("Paramètres des produits")
    with products_config:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Produits de crédit**")
            retail_mortgages = st.checkbox("Prêts hypothécaires retail", value=True)
            retail_consumer = st.checkbox("Crédits à la consommation", value=True)
            retail_credit_cards = st.checkbox("Cartes de crédit", value=True)
            corporate_loans = st.checkbox("Prêts corporate", value=True)
            sme_loans = st.checkbox("Prêts PME", value=True)
        
        with col2:
            st.markdown("**Autres produits**")
            retail_deposits = st.checkbox("Dépôts retail", value=True)
            corporate_deposits = st.checkbox("Dépôts corporate", value=True)
            government_bonds = st.checkbox("Obligations d'État", value=True)
            corporate_bonds = st.checkbox("Obligations corporate", value=True)
            derivatives = st.checkbox("Dérivés", value=include_derivatives)
    
    # Sauvegarde de la configuration
    if st.button("💾 Sauvegarder la configuration"):
        config = {
            'scenario_name': scenario_name,
            'scenario_seed': scenario_seed,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'base_currency': base_currency,
            'num_positions': num_positions,
            'stress_scenario': stress_scenario,
            'entities': {
                'EU_SUB': {'currency': eu_currency, 'ownership': eu_ownership/100, 'size': eu_size},
                'US_SUB': {'currency': us_currency, 'ownership': us_ownership/100, 'size': us_size},
                'CN_SUB': {'currency': cn_currency, 'ownership': cn_ownership/100, 'size': cn_size}
            },
            'products': {
                'retail_mortgages': retail_mortgages,
                'retail_consumer': retail_consumer,
                'retail_credit_cards': retail_credit_cards,
                'corporate_loans': corporate_loans,
                'sme_loans': sme_loans,
                'retail_deposits': retail_deposits,
                'corporate_deposits': corporate_deposits,
                'government_bonds': government_bonds,
                'corporate_bonds': corporate_bonds,
                'derivatives': derivatives
            }
        }
        
        st.session_state['simulation_config'] = config
        st.success("✅ Configuration sauvegardée avec succès!")
        
        # Afficher la configuration
        with st.expander("Voir la configuration sauvegardée"):
            st.json(config)

def show_simulation_page():
    """Page de simulation"""
    st.markdown("## 📊 Simulation des positions bancaires")
    
    # Vérifier la configuration
    if 'simulation_config' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord configurer les paramètres dans la section Configuration.")
        return
    
    config = st.session_state['simulation_config']
    
    # Afficher les paramètres
    st.markdown("### 📋 Paramètres de simulation")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Scénario", config['scenario_name'])
        st.metric("Positions", f"{config['num_positions']:,}")
    
    with col2:
        st.metric("Période", f"{config['start_date']} → {config['end_date']}")
        st.metric("Devise base", config['base_currency'])
    
    with col3:
        st.metric("Stress", config['stress_scenario'])
        st.metric("Graine", config['scenario_seed'])
    
    # Bouton de lancement
    if st.button("🚀 Lancer la simulation", type="primary"):
        with st.spinner("Simulation en cours..."):
            try:
                # Initialiser le moteur de simulation
                sim_engine = SimulationEngine(config)
                
                # Générer les données
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Génération des entités...")
                progress_bar.progress(20)
                entities = sim_engine.generate_entities()
                
                status_text.text("Génération des positions...")
                progress_bar.progress(40)
                positions = sim_engine.generate_positions()
                
                status_text.text("Génération des flux de trésorerie...")
                progress_bar.progress(60)
                cash_flows = sim_engine.generate_cash_flows(positions)
                
                status_text.text("Génération des dérivés...")
                progress_bar.progress(80)
                derivatives = sim_engine.generate_derivatives()
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                # Sauvegarder les résultats
                simulation_results = {
                    'entities': entities,
                    'positions': positions,
                    'cash_flows': cash_flows,
                    'derivatives': derivatives,
                    'summary': sim_engine.create_simulation_summary(positions, cash_flows, derivatives)
                }
                
                st.session_state['simulation_results'] = simulation_results
                
                status_text.text("✅ Simulation terminée avec succès!")
                progress_bar.empty()
                
                st.success("🎉 Simulation terminée avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la simulation: {e}")
                logger.error(f"Erreur simulation: {e}")
                return
    
    # Afficher les résultats si disponibles
    if 'simulation_results' in st.session_state:
        results = st.session_state['simulation_results']
        
        st.markdown("### 📊 Résultats de la simulation")
        
        # Résumé
        if 'summary' in results:
            summary = results['summary']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_assets = summary[summary['metric'] == 'total_assets']['value'].iloc[0]
                st.metric("Total Actifs", f"{total_assets:,.0f} EUR")
            
            with col2:
                total_loans = summary[summary['metric'] == 'total_loans']['value'].iloc[0]
                st.metric("Total Prêts", f"{total_loans:,.0f} EUR")
            
            with col3:
                total_deposits = summary[summary['metric'] == 'total_deposits']['value'].iloc[0]
                st.metric("Total Dépôts", f"{total_deposits:,.0f} EUR")
            
            with col4:
                num_positions = summary[summary['metric'] == 'num_positions']['value'].iloc[0]
                st.metric("Nb Positions", f"{num_positions:,.0f}")
        
        # Graphiques
        if 'positions' in results:
            positions = results['positions']
            
            # Répartition par entité
            col1, col2 = st.columns(2)
            
            with col1:
                entity_summary = positions.groupby('entity_id')['ead'].sum().reset_index()
                fig = px.pie(entity_summary, values='ead', names='entity_id', 
                           title="Répartition des expositions par entité")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                product_summary = positions.groupby('product_id')['ead'].sum().reset_index()
                fig = px.bar(product_summary, x='product_id', y='ead',
                           title="Expositions par produit")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Aperçu des données
        st.markdown("### 👀 Aperçu des données générées")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Positions", "Flux de trésorerie", "Dérivés", "Entités"])
        
        with tab1:
            if 'positions' in results:
                st.dataframe(results['positions'].head(100), use_container_width=True)
        
        with tab2:
            if 'cash_flows' in results:
                st.dataframe(results['cash_flows'].head(100), use_container_width=True)
        
        with tab3:
            if 'derivatives' in results:
                st.dataframe(results['derivatives'], use_container_width=True)
        
        with tab4:
            if 'entities' in results:
                st.dataframe(results['entities'], use_container_width=True)

def show_accounting_page():
    """Page de comptabilité"""
    st.markdown("## 📋 Comptabilité et états financiers")
    
    # Vérifier les données de simulation
    if 'simulation_results' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation.")
        return
    
    simulation_results = st.session_state['simulation_results']
    config = st.session_state.get('simulation_config', {})
    
    # Bouton de calcul
    if st.button("📊 Calculer les états comptables", type="primary"):
        with st.spinner("Calcul des états comptables..."):
            try:
                # Initialiser le moteur comptable
                acc_engine = AccountingEngine(config)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Calculer les balances par entité
                status_text.text("Calcul des balances par entité...")
                progress_bar.progress(25)
                trial_balances = acc_engine.calculate_trial_balances(
                    simulation_results['positions'],
                    simulation_results['cash_flows']
                )
                
                # Calculer les états financiers
                status_text.text("Génération des états financiers...")
                progress_bar.progress(50)
                financial_statements = acc_engine.generate_financial_statements(trial_balances)
                
                # Calculer les provisions
                status_text.text("Calcul des provisions...")
                progress_bar.progress(75)
                provisions = acc_engine.calculate_provisions(simulation_results['positions'])
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                # Sauvegarder les résultats
                accounting_results = {
                    **trial_balances,
                    **financial_statements,
                    'provisions': provisions
                }
                
                st.session_state['accounting_results'] = accounting_results
                
                status_text.text("✅ Calculs comptables terminés!")
                progress_bar.empty()
                
                st.success("🎉 États comptables calculés avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul comptable: {e}")
                logger.error(f"Erreur comptabilité: {e}")
                return
    
    # Afficher les résultats
    if 'accounting_results' in st.session_state:
        results = st.session_state['accounting_results']
        
        st.markdown("### 📊 États comptables par entité")
        
        # Sélection de l'entité
        entities = [key.replace('tb_', '') for key in results.keys() if key.startswith('tb_')]
        selected_entity = st.selectbox("Choisir une entité", entities)
        
        if selected_entity:
            # Balance de l'entité
            tb_key = f'tb_{selected_entity.lower()}'
            if tb_key in results:
                st.markdown(f"#### Balance - {selected_entity}")
                trial_balance = results[tb_key]
                
                # Métriques
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_assets = trial_balance[trial_balance['account_type'] == 'ASSET']['amount_local'].sum()
                    st.metric("Total Actifs", f"{total_assets:,.0f}")
                
                with col2:
                    total_liabilities = trial_balance[trial_balance['account_type'] == 'LIABILITY']['amount_local'].sum()
                    st.metric("Total Passifs", f"{total_liabilities:,.0f}")
                
                with col3:
                    total_equity = trial_balance[trial_balance['account_type'] == 'EQUITY']['amount_local'].sum()
                    st.metric("Capitaux Propres", f"{total_equity:,.0f}")
                
                with col4:
                    net_income = trial_balance[trial_balance['account_type'] == 'INCOME']['amount_local'].sum() - \
                                trial_balance[trial_balance['account_type'] == 'EXPENSE']['amount_local'].sum()
                    st.metric("Résultat Net", f"{net_income:,.0f}")
                
                # Graphique de répartition
                account_summary = trial_balance.groupby('account_type')['amount_local'].sum().reset_index()
                account_summary = account_summary[account_summary['amount_local'] > 0]
                
                fig = px.pie(account_summary, values='amount_local', names='account_type',
                           title=f"Répartition du bilan - {selected_entity}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Détail de la balance
                st.markdown("#### Détail de la balance")
                st.dataframe(trial_balance, use_container_width=True)
            
            # États financiers
            bs_key = f'bs_{selected_entity.lower()}'
            pl_key = f'pl_{selected_entity.lower()}'
            
            col1, col2 = st.columns(2)
            
            with col1:
                if bs_key in results:
                    st.markdown(f"#### Bilan - {selected_entity}")
                    st.dataframe(results[bs_key], use_container_width=True)
            
            with col2:
                if pl_key in results:
                    st.markdown(f"#### Compte de résultat - {selected_entity}")
                    st.dataframe(results[pl_key], use_container_width=True)
        
        # Provisions
        if 'provisions' in results:
            st.markdown("### 💰 Provisions IFRS 9")
            provisions = results['provisions']
            
            # Résumé des provisions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                stage1_provisions = provisions[provisions['stage'] == 1]['provision_amount'].sum()
                st.metric("Provisions Stage 1", f"{stage1_provisions:,.0f} EUR")
            
            with col2:
                stage2_provisions = provisions[provisions['stage'] == 2]['provision_amount'].sum()
                st.metric("Provisions Stage 2", f"{stage2_provisions:,.0f} EUR")
            
            with col3:
                stage3_provisions = provisions[provisions['stage'] == 3]['provision_amount'].sum()
                st.metric("Provisions Stage 3", f"{stage3_provisions:,.0f} EUR")
            
            # Graphique des provisions par entité
            prov_by_entity = provisions.groupby('entity_id')['provision_amount'].sum().reset_index()
            fig = px.bar(prov_by_entity, x='entity_id', y='provision_amount',
                        title="Provisions par entité")
            st.plotly_chart(fig, use_container_width=True)
            
            # Détail des provisions
            st.dataframe(provisions.head(100), use_container_width=True)

def show_consolidation_page():
    """Page de consolidation"""
    st.markdown("## 🔄 Consolidation de groupe")
    
    # Vérifier les données comptables
    if 'accounting_results' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord calculer les états comptables.")
        return
    
    accounting_results = st.session_state['accounting_results']
    config = st.session_state.get('simulation_config', {})
    
    # Bouton de consolidation
    if st.button("🔄 Effectuer la consolidation", type="primary"):
        with st.spinner("Consolidation en cours..."):
            try:
                # Initialiser le moteur de consolidation
                cons_engine = ConsolidationEngine(config)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Conversion des devises
                status_text.text("Conversion des devises...")
                progress_bar.progress(25)
                fx_rates = cons_engine.get_fx_rates()
                converted_balances = cons_engine.convert_trial_balances(accounting_results, fx_rates)
                
                # Consolidation
                status_text.text("Consolidation des balances...")
                progress_bar.progress(50)
                consolidated_data = cons_engine.consolidate_trial_balances(converted_balances)
                
                # États consolidés
                status_text.text("Génération des états consolidés...")
                progress_bar.progress(75)
                consolidated_statements = cons_engine.generate_consolidated_statements(consolidated_data)
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                # Sauvegarder les résultats
                consolidation_results = {
                    'fx_rates': fx_rates,
                    'converted_balances': converted_balances,
                    **consolidated_data,
                    **consolidated_statements
                }
                
                st.session_state['consolidation_results'] = consolidation_results
                
                status_text.text("✅ Consolidation terminée!")
                progress_bar.empty()
                
                st.success("🎉 Consolidation effectuée avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la consolidation: {e}")
                logger.error(f"Erreur consolidation: {e}")
                return
    
    # Afficher les résultats
    if 'consolidation_results' in st.session_state:
        results = st.session_state['consolidation_results']
        
        st.markdown("### 📊 Résultats de la consolidation")
        
        # Taux de change
        if 'fx_rates' in results:
            st.markdown("#### 💱 Taux de change utilisés")
            fx_rates = results['fx_rates']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("EUR/USD", f"{fx_rates.get('USD', 1.0):.4f}")
            with col2:
                st.metric("EUR/CNY", f"{fx_rates.get('CNY', 1.0):.4f}")
            with col3:
                st.metric("Date", fx_rates.get('date', 'N/A'))
        
        # Balance consolidée
        if 'group_trial_balance' in results:
            st.markdown("#### 🏦 Balance consolidée du groupe")
            group_tb = results['group_trial_balance']
            
            # Métriques consolidées
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_assets = group_tb[group_tb['account_type'] == 'ASSET']['amount_eur'].sum()
                st.metric("Total Actifs", f"{total_assets:,.0f} EUR")
            
            with col2:
                total_liabilities = group_tb[group_tb['account_type'] == 'LIABILITY']['amount_eur'].sum()
                st.metric("Total Passifs", f"{total_liabilities:,.0f} EUR")
            
            with col3:
                total_equity = group_tb[group_tb['account_type'] == 'EQUITY']['amount_eur'].sum()
                st.metric("Capitaux Propres", f"{total_equity:,.0f} EUR")
            
            with col4:
                minority_interests = group_tb[group_tb['account_code'] == '3400']['amount_eur'].sum()
                st.metric("Intérêts Minoritaires", f"{minority_interests:,.0f} EUR")
            
            # Graphique de répartition
            account_summary = group_tb.groupby('account_type')['amount_eur'].sum().reset_index()
            account_summary = account_summary[account_summary['amount_eur'] > 0]
            
            fig = px.pie(account_summary, values='amount_eur', names='account_type',
                        title="Répartition du bilan consolidé")
            st.plotly_chart(fig, use_container_width=True)
            
            # Détail de la balance
            st.dataframe(group_tb, use_container_width=True)
        
        # États consolidés
        col1, col2 = st.columns(2)
        
        with col1:
            if 'consolidated_balance_sheet' in results:
                st.markdown("#### Bilan consolidé")
                st.dataframe(results['consolidated_balance_sheet'], use_container_width=True)
        
        with col2:
            if 'consolidated_income_statement' in results:
                st.markdown("#### Compte de résultat consolidé")
                st.dataframe(results['consolidated_income_statement'], use_container_width=True)
        
        # Liasse de consolidation
        if 'consolidation_package' in results:
            st.markdown("#### 📋 Liasse de consolidation")
            st.dataframe(results['consolidation_package'], use_container_width=True)

def show_credit_risk_page():
    """Page de risque de crédit"""
    st.markdown("## ⚠️ Risque de crédit et RWA")
    
    # Vérifier les données de simulation
    if 'simulation_results' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation.")
        return
    
    simulation_results = st.session_state['simulation_results']
    config = st.session_state.get('simulation_config', {})
    
    # Bouton de calcul
    if st.button("⚠️ Calculer les RWA", type="primary"):
        with st.spinner("Calcul des RWA en cours..."):
            try:
                # Initialiser le moteur de risque de crédit
                risk_engine = CreditRiskEngine(config)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Calcul des RWA...")
                progress_bar.progress(50)
                
                # Calculer les RWA
                rwa_results = risk_engine.calculate_rwa(simulation_results['positions'])
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                st.session_state['rwa_results'] = rwa_results
                
                status_text.text("✅ Calcul des RWA terminé!")
                progress_bar.empty()
                
                st.success("🎉 RWA calculés avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul des RWA: {e}")
                logger.error(f"Erreur RWA: {e}")
                return
    
    # Afficher les résultats
    if 'rwa_results' in st.session_state:
        results = st.session_state['rwa_results']
        
        st.markdown("### 📊 Résultats des RWA")
        
        # Ratios de capital
        if 'capital_ratios' in results:
            capital_ratios = results['capital_ratios']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cet1_ratio = capital_ratios['cet1_ratio'].iloc[0] if not capital_ratios.empty else 0
                st.metric("Ratio CET1", f"{cet1_ratio:.2f}%", 
                         delta=f"{cet1_ratio - 4.5:.2f}% vs min")
            
            with col2:
                tier1_ratio = capital_ratios['tier1_ratio'].iloc[0] if not capital_ratios.empty else 0
                st.metric("Ratio Tier 1", f"{tier1_ratio:.2f}%",
                         delta=f"{tier1_ratio - 6.0:.2f}% vs min")
            
            with col3:
                total_ratio = capital_ratios['total_capital_ratio'].iloc[0] if not capital_ratios.empty else 0
                st.metric("Ratio Total", f"{total_ratio:.2f}%",
                         delta=f"{total_ratio - 8.0:.2f}% vs min")
            
            with col4:
                total_rwa = capital_ratios['rwa_amount'].iloc[0] if not capital_ratios.empty else 0
                st.metric("Total RWA", f"{total_rwa:,.0f} EUR")
        
        # Ratio de levier
        if 'leverage_ratio' in results:
            leverage_ratio = results['leverage_ratio']
            if not leverage_ratio.empty:
                st.markdown("#### 📏 Ratio de levier")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    lr_ratio = leverage_ratio['leverage_ratio'].iloc[0]
                    st.metric("Ratio de Levier", f"{lr_ratio:.2f}%",
                             delta=f"{lr_ratio - 3.0:.2f}% vs min")
                
                with col2:
                    total_exposure = leverage_ratio['total_exposure'].iloc[0]
                    st.metric("Exposition Totale", f"{total_exposure:,.0f} EUR")
                
                with col3:
                    tier1_capital = leverage_ratio['tier1_capital'].iloc[0]
                    st.metric("Tier 1 Capital", f"{tier1_capital:,.0f} EUR")
        
        # RWA par classe d'exposition
        if 'rwa_summary' in results:
            rwa_summary = results['rwa_summary']
            
            st.markdown("#### 📊 RWA par classe d'exposition")
            
            # Graphique
            fig = px.bar(rwa_summary, x='exposure_class', y='rwa_amount', color='approach',
                        title="RWA par classe d'exposition et approche")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé
            st.dataframe(rwa_summary, use_container_width=True)
        
        # Détail des RWA
        if 'rwa_detail' in results:
            st.markdown("#### 🔍 Détail des RWA")
            rwa_detail = results['rwa_detail']
            
            # Aperçu
            st.dataframe(rwa_detail.head(100), use_container_width=True)
            
            # Statistiques
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Statistiques IRB**")
                irb_data = rwa_detail[rwa_detail['approach'] == 'IRB']
                if not irb_data.empty:
                    st.write(f"Nombre d'expositions: {len(irb_data):,}")
                    st.write(f"PD moyenne: {irb_data['pd'].mean():.4f}")
                    st.write(f"LGD moyenne: {irb_data['lgd'].mean():.4f}")
                    st.write(f"Densité RWA moyenne: {irb_data['rwa_density'].mean():.2f}%")
            
            with col2:
                st.markdown("**Statistiques Standardisées**")
                std_data = rwa_detail[rwa_detail['approach'] == 'Standardised']
                if not std_data.empty:
                    st.write(f"Nombre d'expositions: {len(std_data):,}")
                    st.write(f"Densité RWA moyenne: {std_data['rwa_density'].mean():.2f}%")

def show_liquidity_page():
    """Page de liquidité"""
    st.markdown("## 💧 Liquidité (LCR, NSFR, ALMM)")
    
    # Vérifier les données de simulation
    if 'simulation_results' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation.")
        return
    
    simulation_results = st.session_state['simulation_results']
    config = st.session_state.get('simulation_config', {})
    
    # Bouton de calcul
    if st.button("💧 Calculer les ratios de liquidité", type="primary"):
        with st.spinner("Calcul des ratios de liquidité..."):
            try:
                # Initialiser le moteur de liquidité
                liq_engine = LiquidityEngine(config)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Calcul des ratios de liquidité...")
                progress_bar.progress(50)
                
                # Calculer les ratios
                liquidity_results = liq_engine.calculate_liquidity_ratios(
                    simulation_results['positions'],
                    simulation_results['cash_flows']
                )
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                st.session_state['liquidity_results'] = liquidity_results
                
                status_text.text("✅ Calcul de liquidité terminé!")
                progress_bar.empty()
                
                st.success("🎉 Ratios de liquidité calculés avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul de liquidité: {e}")
                logger.error(f"Erreur liquidité: {e}")
                return
    
    # Afficher les résultats
    if 'liquidity_results' in st.session_state:
        results = st.session_state['liquidity_results']
        
        st.markdown("### 📊 Ratios de liquidité")
        
        # LCR
        if 'lcr_summary' in results:
            lcr_summary = results['lcr_summary']
            if not lcr_summary.empty:
                st.markdown("#### 🌊 Liquidity Coverage Ratio (LCR)")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    lcr_ratio = lcr_summary['lcr_ratio'].iloc[0]
                    st.metric("LCR", f"{lcr_ratio:.1f}%",
                             delta=f"{lcr_ratio - 100:.1f}% vs min")
                
                with col2:
                    total_hqla = lcr_summary['total_hqla'].iloc[0]
                    st.metric("HQLA Total", f"{total_hqla:,.0f} EUR")
                
                with col3:
                    net_outflows = lcr_summary['net_cash_outflows'].iloc[0]
                    st.metric("Sorties Nettes 30j", f"{net_outflows:,.0f} EUR")
                
                with col4:
                    lcr_surplus = lcr_summary['lcr_surplus'].iloc[0]
                    st.metric("Excédent LCR", f"{lcr_surplus:.1f}%")
        
        # NSFR
        if 'nsfr_summary' in results:
            nsfr_summary = results['nsfr_summary']
            if not nsfr_summary.empty:
                st.markdown("#### 🏗️ Net Stable Funding Ratio (NSFR)")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    nsfr_ratio = nsfr_summary['nsfr_ratio'].iloc[0]
                    st.metric("NSFR", f"{nsfr_ratio:.1f}%",
                             delta=f"{nsfr_ratio - 100:.1f}% vs min")
                
                with col2:
                    asf = nsfr_summary['available_stable_funding'].iloc[0]
                    st.metric("ASF", f"{asf:,.0f} EUR")
                
                with col3:
                    rsf = nsfr_summary['required_stable_funding'].iloc[0]
                    st.metric("RSF", f"{rsf:,.0f} EUR")
                
                with col4:
                    nsfr_surplus = nsfr_summary['nsfr_surplus'].iloc[0]
                    st.metric("Excédent NSFR", f"{nsfr_surplus:.1f}%")
        
        # ALMM
        if 'almm_maturity_ladder' in results:
            almm_ladder = results['almm_maturity_ladder']
            if not almm_ladder.empty:
                st.markdown("#### ⏰ Asset Liability Maturity Mismatch (ALMM)")
                
                # Graphique ALMM
                almm_pivot = almm_ladder.pivot_table(
                    index='maturity_bucket',
                    columns='entity_id',
                    values='net_position',
                    aggfunc='sum',
                    fill_value=0
                )
                
                fig = px.bar(almm_pivot.reset_index(), x='maturity_bucket', 
                           y=almm_pivot.columns.tolist(),
                           title="Gap de liquidité par bucket de maturité")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                # Tableau ALMM
                st.dataframe(almm_ladder, use_container_width=True)
        
        # Détails LCR
        if 'lcr_detail' in results:
            st.markdown("#### 🔍 Détail LCR par entité")
            lcr_detail = results['lcr_detail']
            st.dataframe(lcr_detail, use_container_width=True)
        
        # Détails NSFR
        if 'nsfr_detail' in results:
            st.markdown("#### 🔍 Détail NSFR par entité")
            nsfr_detail = results['nsfr_detail']
            st.dataframe(nsfr_detail, use_container_width=True)

def show_reporting_page():
    """Page de reporting"""
    st.markdown("## 📈 Reporting réglementaire")
    
    # Vérifier les données nécessaires
    required_data = ['consolidation_results', 'rwa_results', 'liquidity_results']
    missing_data = [data for data in required_data if data not in st.session_state]
    
    if missing_data:
        st.warning(f"⚠️ Données manquantes: {', '.join(missing_data)}")
        st.info("Veuillez compléter les étapes précédentes (consolidation, RWA, liquidité).")
        return
    
    consolidation_results = st.session_state['consolidation_results']
    rwa_results = st.session_state['rwa_results']
    liquidity_results = st.session_state['liquidity_results']
    config = st.session_state.get('simulation_config', {})
    
    # Bouton de génération
    if st.button("📈 Générer les rapports réglementaires", type="primary"):
        with st.spinner("Génération des rapports..."):
            try:
                # Initialiser le moteur de reporting
                rep_engine = ReportingEngine(config)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Génération des rapports...")
                progress_bar.progress(50)
                
                # Générer tous les rapports
                all_reports = rep_engine.generate_all_reports(
                    consolidation_results,
                    rwa_results,
                    liquidity_results
                )
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                st.session_state['reporting_results'] = all_reports
                
                status_text.text("✅ Rapports générés!")
                progress_bar.empty()
                
                st.success("🎉 Rapports réglementaires générés avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération des rapports: {e}")
                logger.error(f"Erreur reporting: {e}")
                return
    
    # Afficher les résultats
    if 'reporting_results' in st.session_state:
        reports = st.session_state['reporting_results']
        
        st.markdown("### 📊 Rapports générés")
        
        # Onglets pour les différents rapports
        tab_names = []
        tab_data = []
        
        if any(key.startswith('finrep_') for key in reports.keys()):
            tab_names.append("FINREP")
            tab_data.append([key for key in reports.keys() if key.startswith('finrep_')])
        
        if any(key.startswith('corep_') for key in reports.keys()):
            tab_names.append("COREP")
            tab_data.append([key for key in reports.keys() if key.startswith('corep_')])
        
        if any(key.startswith('lcr_') or key.startswith('nsfr_') for key in reports.keys()):
            tab_names.append("Liquidité")
            tab_data.append([key for key in reports.keys() if key.startswith(('lcr_', 'nsfr_'))])
        
        if any(key.startswith('ruba_') for key in reports.keys()):
            tab_names.append("RUBA")
            tab_data.append([key for key in reports.keys() if key.startswith('ruba_')])
        
        if tab_names:
            tabs = st.tabs(tab_names)
            
            for i, tab in enumerate(tabs):
                with tab:
                    for report_key in tab_data[i]:
                        if report_key in reports:
                            st.markdown(f"#### {report_key.replace('_', ' ').title()}")
                            st.dataframe(reports[report_key], use_container_width=True)
        
        # Résumé des rapports
        st.markdown("### 📋 Résumé des rapports")
        
        summary_data = []
        for report_name, report_df in reports.items():
            summary_data.append({
                'Rapport': report_name.replace('_', ' ').title(),
                'Nombre de lignes': len(report_df),
                'Nombre de colonnes': len(report_df.columns),
                'Dernière mise à jour': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

def show_templates_page():
    """Page de génération de templates Excel"""
    st.markdown("## 📁 Templates Excel")
    
    st.markdown("""
    Cette section permet de générer les templates Excel d'entrée pour l'application.
    Ces fichiers peuvent être utilisés pour importer des données personnalisées.
    """)
    
    # Configuration des templates
    st.markdown("### ⚙️ Configuration des templates")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_entities = st.checkbox("Template Entités", value=True)
        include_fx = st.checkbox("Template Taux de Change", value=True)
        include_products = st.checkbox("Template Produits", value=True)
    
    with col2:
        include_positions = st.checkbox("Template Positions", value=True)
        include_cash_flows = st.checkbox("Template Flux de Trésorerie", value=True)
        include_config = st.checkbox("Template Configuration", value=True)
    
    # Bouton de génération
    if st.button("📁 Générer les templates Excel", type="primary"):
        with st.spinner("Génération des templates..."):
            try:
                # Initialiser le générateur de templates
                template_gen = ExcelTemplateGenerator()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                generated_files = []
                
                if include_entities:
                    status_text.text("Génération du template Entités...")
                    progress_bar.progress(15)
                    entities_file = template_gen.generate_entities_template()
                    generated_files.append(("Entités", entities_file))
                
                if include_fx:
                    status_text.text("Génération du template Taux de Change...")
                    progress_bar.progress(30)
                    fx_file = template_gen.generate_fx_template()
                    generated_files.append(("Taux de Change", fx_file))
                
                if include_products:
                    status_text.text("Génération du template Produits...")
                    progress_bar.progress(45)
                    products_file = template_gen.generate_products_template()
                    generated_files.append(("Produits", products_file))
                
                if include_positions:
                    status_text.text("Génération du template Positions...")
                    progress_bar.progress(60)
                    positions_file = template_gen.generate_positions_template()
                    generated_files.append(("Positions", positions_file))
                
                if include_cash_flows:
                    status_text.text("Génération du template Flux de Trésorerie...")
                    progress_bar.progress(75)
                    cf_file = template_gen.generate_cash_flows_template()
                    generated_files.append(("Flux de Trésorerie", cf_file))
                
                if include_config:
                    status_text.text("Génération du template Configuration...")
                    progress_bar.progress(90)
                    config_file = template_gen.generate_config_template()
                    generated_files.append(("Configuration", config_file))
                
                status_text.text("Finalisation...")
                progress_bar.progress(100)
                
                st.session_state['generated_templates'] = generated_files
                
                status_text.text("✅ Templates générés!")
                progress_bar.empty()
                
                st.success("🎉 Templates Excel générés avec succès!")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération des templates: {e}")
                logger.error(f"Erreur templates: {e}")
                return
    
    # Afficher les templates générés
    if 'generated_templates' in st.session_state:
        templates = st.session_state['generated_templates']
        
        st.markdown("### 📋 Templates générés")
        
        for template_name, template_path in templates:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"📄 **{template_name}**: {Path(template_path).name}")
            
            with col2:
                # Bouton de téléchargement
                try:
                    with open(template_path, 'rb') as file:
                        st.download_button(
                            label="⬇️ Télécharger",
                            data=file.read(),
                            file_name=Path(template_path).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_{template_name}"
                        )
                except Exception as e:
                    st.error(f"Erreur de téléchargement: {e}")
    
    # Instructions d'utilisation
    with st.expander("📖 Instructions d'utilisation"):
        st.markdown("""
        ### Comment utiliser les templates
        
        1. **Téléchargez** les templates Excel générés
        2. **Remplissez** les données dans les fichiers Excel
        3. **Respectez** le format et les colonnes existantes
        4. **Utilisez** la section Import/Export pour charger vos données
        
        ### Structure des templates
        
        - **Entités**: Informations sur les filiales (devise, pourcentage de détention, etc.)
        - **Taux de Change**: Taux de conversion entre devises
        - **Produits**: Définition des produits financiers et leurs paramètres
        - **Positions**: Expositions détaillées par entité et produit
        - **Flux de Trésorerie**: Flux d'intérêts et de remboursements
        - **Configuration**: Paramètres généraux de simulation
        
        ### Conseils
        
        - Ne modifiez pas les en-têtes de colonnes
        - Respectez les formats de dates (YYYY-MM-DD)
        - Utilisez des valeurs numériques pour les montants
        - Vérifiez la cohérence entre les fichiers
        """)

def show_import_export_page():
    """Page d'import/export"""
    st.markdown("## 📥 Import/Export de données")
    
    # Section Import
    st.markdown("### 📥 Import de données")
    
    uploaded_files = st.file_uploader(
        "Choisir des fichiers Excel",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Sélectionnez les fichiers Excel à importer"
    )
    
    if uploaded_files:
        st.markdown("#### Fichiers sélectionnés")
        
        for uploaded_file in uploaded_files:
            st.write(f"📄 {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        if st.button("📥 Importer les données", type="primary"):
            with st.spinner("Import en cours..."):
                try:
                    # Initialiser le lecteur Excel
                    reader = ExcelReader()
                    
                    imported_data = {}
                    
                    for uploaded_file in uploaded_files:
                        # Sauvegarder temporairement le fichier
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        try:
                            # Lire le fichier
                            file_data = reader.read_excel_file(tmp_path)
                            imported_data[uploaded_file.name] = file_data
                            
                        finally:
                            # Nettoyer le fichier temporaire
                            os.unlink(tmp_path)
                    
                    st.session_state['imported_data'] = imported_data
                    st.success("✅ Données importées avec succès!")
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'import: {e}")
                    logger.error(f"Erreur import: {e}")
    
    # Afficher les données importées
    if 'imported_data' in st.session_state:
        imported_data = st.session_state['imported_data']
        
        st.markdown("### 📊 Données importées")
        
        for filename, file_data in imported_data.items():
            with st.expander(f"📄 {filename}"):
                for sheet_name, sheet_data in file_data.items():
                    st.markdown(f"**Feuille: {sheet_name}**")
                    st.dataframe(sheet_data.head(10), use_container_width=True)
                    st.write(f"Dimensions: {sheet_data.shape[0]} lignes × {sheet_data.shape[1]} colonnes")
    
    # Section Export
    st.markdown("### 📤 Export de données")
    
    # Vérifier les données disponibles pour l'export
    available_data = []
    
    if 'simulation_results' in st.session_state:
        available_data.append("Simulation")
    if 'accounting_results' in st.session_state:
        available_data.append("Comptabilité")
    if 'consolidation_results' in st.session_state:
        available_data.append("Consolidation")
    if 'rwa_results' in st.session_state:
        available_data.append("RWA")
    if 'liquidity_results' in st.session_state:
        available_data.append("Liquidité")
    if 'reporting_results' in st.session_state:
        available_data.append("Reporting")
    
    if available_data:
        st.markdown("#### Données disponibles pour l'export")
        
        export_selection = st.multiselect(
            "Choisir les données à exporter",
            available_data,
            default=available_data
        )
        
        if export_selection and st.button("📤 Générer les fichiers Excel", type="primary"):
            with st.spinner("Génération des fichiers Excel..."):
                try:
                    # Initialiser l'écrivain Excel
                    writer = ExcelWriter()
                    
                    # Préparer les données pour l'export
                    reports_data = {}
                    config = st.session_state.get('simulation_config', {})
                    
                    if "Simulation" in export_selection and 'simulation_results' in st.session_state:
                        reports_data['simulation'] = st.session_state['simulation_results']
                    
                    if "Comptabilité" in export_selection and 'accounting_results' in st.session_state:
                        reports_data['accounting'] = st.session_state['accounting_results']
                    
                    if "Consolidation" in export_selection and 'consolidation_results' in st.session_state:
                        reports_data['consolidation'] = st.session_state['consolidation_results']
                    
                    if "RWA" in export_selection and 'rwa_results' in st.session_state:
                        reports_data['corep'] = st.session_state['rwa_results']
                    
                    if "Liquidité" in export_selection and 'liquidity_results' in st.session_state:
                        reports_data['liquidity'] = st.session_state['liquidity_results']
                    
                    if "Reporting" in export_selection and 'reporting_results' in st.session_state:
                        # Organiser les rapports par type
                        reporting_results = st.session_state['reporting_results']
                        
                        finrep_data = {k: v for k, v in reporting_results.items() if k.startswith('finrep_')}
                        if finrep_data:
                            reports_data['finrep'] = finrep_data
                        
                        ruba_data = {k: v for k, v in reporting_results.items() if k.startswith('ruba_')}
                        if ruba_data:
                            reports_data['ruba'] = ruba_data
                    
                    # Générer les fichiers
                    generated_files = writer.write_all_reports(reports_data, config)
                    
                    # Créer un fichier de synthèse
                    master_file = writer.create_master_summary(generated_files, config)
                    generated_files['master_summary'] = master_file
                    
                    st.session_state['generated_files'] = generated_files
                    
                    st.success("🎉 Fichiers Excel générés avec succès!")
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération: {e}")
                    logger.error(f"Erreur export: {e}")
    
    # Afficher les fichiers générés
    if 'generated_files' in st.session_state:
        generated_files = st.session_state['generated_files']
        
        st.markdown("### 📁 Fichiers générés")
        
        for report_type, filepath in generated_files.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                file_size = Path(filepath).stat().st_size / 1024  # KB
                st.write(f"📄 **{report_type.replace('_', ' ').title()}**: {Path(filepath).name} ({file_size:.1f} KB)")
            
            with col2:
                # Bouton de téléchargement
                try:
                    with open(filepath, 'rb') as file:
                        st.download_button(
                            label="⬇️ Télécharger",
                            data=file.read(),
                            file_name=Path(filepath).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_{report_type}"
                        )
                except Exception as e:
                    st.error(f"Erreur de téléchargement: {e}")
        
        # Option de téléchargement groupé
        if len(generated_files) > 1:
            if st.button("📦 Télécharger tout (ZIP)", type="secondary"):
                with st.spinner("Création de l'archive ZIP..."):
                    try:
                        # Créer un fichier ZIP temporaire
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                            with zipfile.ZipFile(tmp_zip.name, 'w') as zipf:
                                for report_type, filepath in generated_files.items():
                                    zipf.write(filepath, Path(filepath).name)
                            
                            # Bouton de téléchargement du ZIP
                            with open(tmp_zip.name, 'rb') as zip_file:
                                st.download_button(
                                    label="⬇️ Télécharger l'archive ZIP",
                                    data=zip_file.read(),
                                    file_name=f"Banking_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                    mime="application/zip"
                                )
                        
                        # Nettoyer le fichier temporaire
                        os.unlink(tmp_zip.name)
                        
                    except Exception as e:
                        st.error(f"Erreur lors de la création du ZIP: {e}")
    
    else:
        st.info("💡 Aucune donnée disponible pour l'export. Veuillez d'abord effectuer une simulation.")

def show_documentation_page():
    """Page de documentation"""
    st.markdown("## ℹ️ Documentation")
    
    # Documentation générale
    st.markdown("""
    ### 📖 Guide d'utilisation
    
    Cette application de simulation bancaire et de reporting CRR3 permet de :
    
    1. **Simuler** des positions bancaires réalistes pour un groupe multi-entités
    2. **Calculer** les états comptables selon les normes IFRS simplifiées
    3. **Consolider** les données en devise de base (EUR)
    4. **Évaluer** les risques de crédit selon CRR3 (IRB et standardisé)
    5. **Analyser** la liquidité (LCR, NSFR, ALMM)
    6. **Générer** les rapports réglementaires (FINREP, COREP, RUBA)
    7. **Exporter** tous les résultats en fichiers Excel formatés
    """)
    
    # Architecture technique
    with st.expander("🏗️ Architecture technique"):
        st.markdown("""
        ### Modules principaux
        
        - **`core/simulation.py`**: Moteur de simulation Monte Carlo
        - **`core/accounting.py`**: Moteur comptable IFRS
        - **`core/consolidation.py`**: Moteur de consolidation
        - **`core/credit_risk.py`**: Calculs RWA selon CRR3
        - **`core/liquidity.py`**: Ratios de liquidité (LCR, NSFR, ALMM)
        - **`core/reporting.py`**: Génération des rapports réglementaires
        - **`io/readers.py`**: Lecture des fichiers Excel
        - **`io/writers.py`**: Écriture des fichiers Excel
        - **`io/excel_templates.py`**: Génération des templates
        - **`config/schemas.py`**: Schémas de données
        - **`config/defaults.py`**: Configuration par défaut
        
        ### Technologies utilisées
        
        - **Python 3.11+**
        - **Streamlit**: Interface utilisateur
        - **Pandas**: Manipulation des données
        - **NumPy**: Calculs numériques
        - **OpenPyXL**: Manipulation Excel
        - **Plotly**: Visualisations
        - **SciPy**: Fonctions statistiques
        """)
    
    # Méthodologies
    with st.expander("📊 Méthodologies"):
        st.markdown("""
        ### Simulation
        
        - **Méthode**: Monte Carlo avec graine fixe pour la reproductibilité
        - **Entités**: 3 filiales (EU, US, CN) avec devises locales
        - **Produits**: 12+ types de produits bancaires
        - **Paramètres**: PD, LGD, CCF selon les standards de l'industrie
        - **Stages ECL**: Classification IFRS 9 (Stage 1, 2, 3)
        
        ### Comptabilité
        
        - **Normes**: IFRS simplifiées
        - **Plan comptable**: Structure bancaire standard
        - **Provisions**: ECL selon IFRS 9
        - **Équilibrage**: Automatique des balances
        
        ### Consolidation
        
        - **Méthode**: Intégration globale
        - **Conversion**: Taux de clôture (bilan) et taux moyen (P&L)
        - **Éliminations**: Transactions intercompagnies
        - **Minoritaires**: Calculés selon les pourcentages de détention
        
        ### Risque de crédit
        
        - **Retail**: Approche IRB avec formules CRR3
        - **Non-retail**: Approche standardisée
        - **Corrélations**: Selon le type de produit
        - **Maturités**: Effectives par produit
        
        ### Liquidité
        
        - **LCR**: Horizon 30 jours, HQLA niveaux 1/2A/2B
        - **NSFR**: Facteurs ASF/RSF réglementaires
        - **ALMM**: Buckets de maturité standard
        """)
    
    # Limitations et avertissements
    with st.expander("⚠️ Limitations et avertissements"):
        st.markdown("""
        ### Limitations techniques
        
        - **Simulation**: Données fictives générées aléatoirement
        - **Simplifications**: Modèles simplifiés par rapport à la réalité
        - **Périmètre**: Limité aux principaux risques (crédit, liquidité)
        - **Validation**: Aucune validation réglementaire officielle
        
        ### Avertissements d'usage
        
        ⚠️ **Cette application est destinée uniquement à des fins éducatives et de démonstration.**
        
        - Ne pas utiliser pour des calculs réglementaires réels
        - Les résultats ne sont pas auditables
        - Les méthodologies sont simplifiées
        - Aucune garantie de conformité réglementaire
        
        ### Recommandations
        
        - Utiliser uniquement pour l'apprentissage
        - Valider toute méthodologie avant usage réel
        - Consulter les textes réglementaires officiels
        - Faire appel à des experts pour les implémentations réelles
        """)
    
    # Références réglementaires
    with st.expander("📚 Références réglementaires"):
        st.markdown("""
        ### Textes européens
        
        - **CRR3**: Règlement (UE) 2024/1623 (Capital Requirements Regulation)
        - **CRD VI**: Directive (UE) 2024/1619 (Capital Requirements Directive)
        - **FINREP**: Templates EBA pour le reporting financier
        - **COREP**: Templates EBA pour le reporting prudentiel
        
        ### Standards internationaux
        
        - **Bâle III**: Accords du Comité de Bâle sur le contrôle bancaire
        - **IFRS 9**: Norme comptable internationale sur les instruments financiers
        - **LCR**: Liquidity Coverage Ratio (Bâle III)
        - **NSFR**: Net Stable Funding Ratio (Bâle III)
        
        ### Autorités de supervision
        
        - **EBA**: European Banking Authority
        - **BCE**: Banque Centrale Européenne
        - **ACPR**: Autorité de Contrôle Prudentiel et de Résolution (France)
        - **BCBS**: Basel Committee on Banking Supervision
        
        ### Liens utiles
        
        - [EBA Guidelines](https://www.eba.europa.eu/)
        - [ECB Banking Supervision](https://www.bankingsupervision.europa.eu/)
        - [ACPR](https://acpr.banque-france.fr/)
        - [BIS Basel Framework](https://www.bis.org/basel_framework/)
        """)
    
    # Contact et support
    with st.expander("📞 Contact et support"):
        st.markdown("""
        ### Support technique
        
        Cette application a été développée à des fins éducatives.
        
        ### Contributions
        
        Les améliorations et corrections sont les bienvenues.
        
        ### Licence
        
        Application développée pour démonstration des capacités de simulation bancaire.
        
        ### Remerciements
        
        - Équipe de développement
        - Communauté open source
        - Autorités réglementaires pour la documentation publique
        """)

if __name__ == "__main__":
    main()
