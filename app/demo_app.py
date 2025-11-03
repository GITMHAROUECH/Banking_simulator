"""
Application de démonstration Banking Simulation & CRR3 Reporting
Version simplifiée fonctionnelle
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import logging
from pathlib import Path
import tempfile
import os
import random

# Configuration de la page
st.set_page_config(
    page_title="Banking Simulation & CRR3 Reporting - Demo",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def generate_sample_positions(num_positions=1000, seed=42):
    """Générer des positions d'exemple"""
    np.random.seed(seed)
    random.seed(seed)
    
    entities = ['EU_SUB', 'US_SUB', 'CN_SUB']
    products = ['Retail_Mortgages', 'Retail_Consumer', 'Corporate_Loans', 'SME_Loans', 'Retail_Deposits']
    exposure_classes = ['Retail_Mortgages', 'Retail_Other', 'Corporate', 'SME', 'Other_Items']
    
    positions = []
    
    for i in range(num_positions):
        entity = np.random.choice(entities)
        product = np.random.choice(products)
        exposure_class = np.random.choice(exposure_classes)
        
        # Générer des paramètres réalistes
        ead = np.random.lognormal(mean=10, sigma=1.5)  # EAD entre 1K et 1M
        pd = np.random.beta(2, 50) if 'Retail' in exposure_class else np.random.beta(1, 20)
        lgd = np.random.beta(2, 3) * 0.8  # LGD entre 0 et 80%
        maturity = np.random.exponential(3) + 0.5  # Maturité moyenne 3.5 ans
        
        # Stage IFRS 9
        if pd < 0.01:
            stage = 1
        elif pd < 0.05:
            stage = 2
        else:
            stage = 3
        
        # Provision ECL
        provision = ead * pd * lgd
        
        positions.append({
            'position_id': f'POS_{i+1:06d}',
            'entity_id': entity,
            'product_id': product,
            'exposure_class': exposure_class,
            'ead': round(ead, 2),
            'pd': round(pd, 6),
            'lgd': round(lgd, 4),
            'maturity': round(maturity, 2),
            'stage': stage,
            'provision_amount': round(provision, 2)
        })
    
    return pd.DataFrame(positions)

def calculate_rwa(positions_df):
    """Calculer les RWA simplifiés"""
    rwa_data = []
    
    for _, pos in positions_df.iterrows():
        if 'Retail' in pos['exposure_class']:
            # Approche IRB pour retail
            correlation = 0.15 if 'Mortgages' in pos['exposure_class'] else 0.04
            maturity_adj = 1.0  # Simplifié
            
            # Formule CRR3 simplifiée
            k = pos['lgd'] * pos['pd'] * (1 + 0.5 * correlation)
            rwa = pos['ead'] * k * 12.5  # 8% minimum
            approach = 'IRB'
        else:
            # Approche standardisée
            if pos['exposure_class'] == 'Corporate':
                risk_weight = 1.0  # 100%
            elif pos['exposure_class'] == 'SME':
                risk_weight = 0.75  # 75%
            else:
                risk_weight = 1.0
            
            rwa = pos['ead'] * risk_weight
            approach = 'Standardised'
        
        rwa_data.append({
            'position_id': pos['position_id'],
            'entity_id': pos['entity_id'],
            'exposure_class': pos['exposure_class'],
            'ead': pos['ead'],
            'rwa_amount': round(rwa, 2),
            'rwa_density': round((rwa / pos['ead']) * 100, 2) if pos['ead'] > 0 else 0,
            'approach': approach
        })
    
    return pd.DataFrame(rwa_data)

def calculate_liquidity_ratios(positions_df):
    """Calculer les ratios de liquidité simplifiés"""
    
    # LCR simplifié
    lcr_data = []
    for entity in positions_df['entity_id'].unique():
        entity_positions = positions_df[positions_df['entity_id'] == entity]
        
        # HQLA (actifs liquides de haute qualité)
        total_assets = entity_positions['ead'].sum()
        hqla = total_assets * 0.15  # 15% en HQLA
        
        # Sorties nettes 30 jours
        deposits = entity_positions[entity_positions['product_id'].str.contains('Deposit', na=False)]['ead'].sum()
        net_outflows = deposits * 0.1  # 10% de sorties
        
        lcr_ratio = (hqla / net_outflows * 100) if net_outflows > 0 else 200
        
        lcr_data.append({
            'entity_id': entity,
            'total_hqla': round(hqla, 2),
            'net_cash_outflows': round(net_outflows, 2),
            'lcr_ratio': round(lcr_ratio, 1),
            'lcr_surplus': round(lcr_ratio - 100, 1)
        })
    
    # NSFR simplifié
    nsfr_data = []
    for entity in positions_df['entity_id'].unique():
        entity_positions = positions_df[positions_df['entity_id'] == entity]
        
        total_assets = entity_positions['ead'].sum()
        
        # ASF (financement stable disponible)
        asf = total_assets * 0.8  # 80% de financement stable
        
        # RSF (financement stable requis)
        rsf = total_assets * 0.7  # 70% requis
        
        nsfr_ratio = (asf / rsf * 100) if rsf > 0 else 150
        
        nsfr_data.append({
            'entity_id': entity,
            'available_stable_funding': round(asf, 2),
            'required_stable_funding': round(rsf, 2),
            'nsfr_ratio': round(nsfr_ratio, 1),
            'nsfr_surplus': round(nsfr_ratio - 100, 1)
        })
    
    return pd.DataFrame(lcr_data), pd.DataFrame(nsfr_data)

def main():
    """Fonction principale de l'application"""
    
    # En-tête principal
    st.markdown('<h1 class="main-header">🏦 Banking Simulation & CRR3 Reporting - Demo</h1>', unsafe_allow_html=True)
    
    # Sidebar pour la navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choisir une section",
        [
            "🏠 Accueil",
            "⚙️ Configuration",
            "📊 Simulation",
            "⚠️ Risque de Crédit",
            "💧 Liquidité",
            "📈 Reporting",
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
    elif page == "⚠️ Risque de Crédit":
        show_credit_risk_page()
    elif page == "💧 Liquidité":
        show_liquidity_page()
    elif page == "📈 Reporting":
        show_reporting_page()
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
        - **Calculer** les risques de crédit (CRR3)
        - **Analyser** la liquidité (LCR, NSFR)
        - **Générer** les rapports réglementaires
        """)
    
    with col2:
        st.markdown("""
        ### 📋 Fonctionnalités principales
        
        - ✅ Moteur de simulation Monte Carlo
        - ✅ Calculs RWA selon CRR3
        - ✅ Ratios de liquidité réglementaires
        - ✅ Visualisations interactives
        - ✅ Export des résultats
        """)
    
    # Métriques de démonstration
    st.markdown("### 📊 Aperçu des capacités")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Entités simulées", "3", "EU, US, CN")
    
    with col2:
        st.metric("Produits financiers", "5+", "Prêts, Dépôts")
    
    with col3:
        st.metric("Positions générées", "1,000+", "Par défaut")
    
    with col4:
        st.metric("Conformité", "CRR3", "Réglementation européenne")
    
    # Avertissement
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Version de démonstration :</strong> Cette application est destinée à des fins éducatives. 
    Elle ne doit pas être utilisée pour des calculs réglementaires réels.
    </div>
    """, unsafe_allow_html=True)

def show_configuration_page():
    """Page de configuration"""
    st.markdown("## ⚙️ Configuration de la simulation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        scenario_name = st.text_input("Nom du scénario", value="Demo_Scenario_2024")
        scenario_seed = st.number_input("Graine aléatoire", value=42, min_value=1, max_value=9999)
        num_positions = st.number_input("Nombre de positions", value=1000, min_value=100, max_value=5000)
    
    with col2:
        base_currency = st.selectbox("Devise de base", ["EUR", "USD", "GBP"], index=0)
        stress_scenario = st.selectbox("Scénario de stress", ["Baseline", "Adverse", "Severely Adverse"], index=0)
        include_derivatives = st.checkbox("Inclure les dérivés", value=False)
    
    if st.button("💾 Sauvegarder la configuration"):
        config = {
            'scenario_name': scenario_name,
            'scenario_seed': scenario_seed,
            'num_positions': num_positions,
            'base_currency': base_currency,
            'stress_scenario': stress_scenario,
            'include_derivatives': include_derivatives
        }
        
        st.session_state['demo_config'] = config
        st.success("✅ Configuration sauvegardée avec succès!")
        
        with st.expander("Voir la configuration"):
            st.json(config)

def show_simulation_page():
    """Page de simulation"""
    st.markdown("## 📊 Simulation des positions bancaires")
    
    # Configuration par défaut si pas encore définie
    if 'demo_config' not in st.session_state:
        st.session_state['demo_config'] = {
            'scenario_name': 'Demo_Scenario_2024',
            'scenario_seed': 42,
            'num_positions': 1000,
            'base_currency': 'EUR',
            'stress_scenario': 'Baseline',
            'include_derivatives': False
        }
    
    config = st.session_state['demo_config']
    
    # Afficher les paramètres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Scénario", config['scenario_name'])
        st.metric("Positions", f"{config['num_positions']:,}")
    
    with col2:
        st.metric("Devise base", config['base_currency'])
        st.metric("Stress", config['stress_scenario'])
    
    with col3:
        st.metric("Graine", config['scenario_seed'])
        st.metric("Dérivés", "Oui" if config['include_derivatives'] else "Non")
    
    # Bouton de simulation
    if st.button("🚀 Lancer la simulation", type="primary"):
        with st.spinner("Simulation en cours..."):
            # Générer les positions
            positions = generate_sample_positions(
                num_positions=config['num_positions'],
                seed=config['scenario_seed']
            )
            
            st.session_state['demo_positions'] = positions
            st.success("🎉 Simulation terminée avec succès!")
    
    # Afficher les résultats
    if 'demo_positions' in st.session_state:
        positions = st.session_state['demo_positions']
        
        st.markdown("### 📊 Résultats de la simulation")
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ead = positions['ead'].sum()
            st.metric("Total EAD", f"{total_ead:,.0f} EUR")
        
        with col2:
            avg_pd = positions['pd'].mean()
            st.metric("PD Moyenne", f"{avg_pd:.2%}")
        
        with col3:
            total_provisions = positions['provision_amount'].sum()
            st.metric("Total Provisions", f"{total_provisions:,.0f} EUR")
        
        with col4:
            num_positions = len(positions)
            st.metric("Nb Positions", f"{num_positions:,}")
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition par entité
            entity_summary = positions.groupby('entity_id')['ead'].sum().reset_index()
            fig = px.pie(entity_summary, values='ead', names='entity_id', 
                       title="Répartition des expositions par entité")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Répartition par produit
            product_summary = positions.groupby('product_id')['ead'].sum().reset_index()
            fig = px.bar(product_summary, x='product_id', y='ead',
                       title="Expositions par produit")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Aperçu des données
        st.markdown("### 👀 Aperçu des positions générées")
        st.dataframe(positions.head(100), use_container_width=True)

def show_credit_risk_page():
    """Page de risque de crédit"""
    st.markdown("## ⚠️ Risque de crédit et RWA")
    
    if 'demo_positions' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation.")
        return
    
    positions = st.session_state['demo_positions']
    
    if st.button("⚠️ Calculer les RWA", type="primary"):
        with st.spinner("Calcul des RWA en cours..."):
            rwa_results = calculate_rwa(positions)
            st.session_state['demo_rwa'] = rwa_results
            st.success("🎉 RWA calculés avec succès!")
    
    if 'demo_rwa' in st.session_state:
        rwa_results = st.session_state['demo_rwa']
        
        st.markdown("### 📊 Résultats des RWA")
        
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rwa = rwa_results['rwa_amount'].sum()
            st.metric("Total RWA", f"{total_rwa:,.0f} EUR")
        
        with col2:
            total_ead = rwa_results['ead'].sum()
            avg_density = (total_rwa / total_ead * 100) if total_ead > 0 else 0
            st.metric("Densité RWA Moyenne", f"{avg_density:.1f}%")
        
        with col3:
            # Capital requis (8%)
            capital_required = total_rwa * 0.08
            st.metric("Capital Requis (8%)", f"{capital_required:,.0f} EUR")
        
        with col4:
            # Ratio CET1 simulé (12%)
            cet1_capital = capital_required * 1.5  # 12% vs 8%
            cet1_ratio = (cet1_capital / total_rwa * 100) if total_rwa > 0 else 0
            st.metric("Ratio CET1", f"{cet1_ratio:.1f}%")
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            # RWA par classe d'exposition
            rwa_by_class = rwa_results.groupby('exposure_class')['rwa_amount'].sum().reset_index()
            fig = px.bar(rwa_by_class, x='exposure_class', y='rwa_amount',
                       title="RWA par classe d'exposition")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Densité RWA par approche
            density_by_approach = rwa_results.groupby('approach')['rwa_density'].mean().reset_index()
            fig = px.bar(density_by_approach, x='approach', y='rwa_density',
                       title="Densité RWA moyenne par approche")
            st.plotly_chart(fig, use_container_width=True)
        
        # Détail des RWA
        st.markdown("### 🔍 Détail des RWA")
        st.dataframe(rwa_results.head(100), use_container_width=True)

def show_liquidity_page():
    """Page de liquidité"""
    st.markdown("## 💧 Liquidité (LCR, NSFR)")
    
    if 'demo_positions' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation.")
        return
    
    positions = st.session_state['demo_positions']
    
    if st.button("💧 Calculer les ratios de liquidité", type="primary"):
        with st.spinner("Calcul des ratios de liquidité..."):
            lcr_results, nsfr_results = calculate_liquidity_ratios(positions)
            st.session_state['demo_lcr'] = lcr_results
            st.session_state['demo_nsfr'] = nsfr_results
            st.success("🎉 Ratios de liquidité calculés avec succès!")
    
    if 'demo_lcr' in st.session_state and 'demo_nsfr' in st.session_state:
        lcr_results = st.session_state['demo_lcr']
        nsfr_results = st.session_state['demo_nsfr']
        
        st.markdown("### 📊 Ratios de liquidité")
        
        # LCR
        st.markdown("#### 🌊 Liquidity Coverage Ratio (LCR)")
        
        col1, col2, col3 = st.columns(3)
        
        for i, entity in enumerate(['EU_SUB', 'US_SUB', 'CN_SUB']):
            entity_lcr = lcr_results[lcr_results['entity_id'] == entity]
            if not entity_lcr.empty:
                with [col1, col2, col3][i]:
                    lcr_ratio = entity_lcr['lcr_ratio'].iloc[0]
                    st.metric(
                        f"LCR {entity}",
                        f"{lcr_ratio:.1f}%",
                        delta=f"{lcr_ratio - 100:.1f}% vs min"
                    )
        
        # NSFR
        st.markdown("#### 🏗️ Net Stable Funding Ratio (NSFR)")
        
        col1, col2, col3 = st.columns(3)
        
        for i, entity in enumerate(['EU_SUB', 'US_SUB', 'CN_SUB']):
            entity_nsfr = nsfr_results[nsfr_results['entity_id'] == entity]
            if not entity_nsfr.empty:
                with [col1, col2, col3][i]:
                    nsfr_ratio = entity_nsfr['nsfr_ratio'].iloc[0]
                    st.metric(
                        f"NSFR {entity}",
                        f"{nsfr_ratio:.1f}%",
                        delta=f"{nsfr_ratio - 100:.1f}% vs min"
                    )
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(lcr_results, x='entity_id', y='lcr_ratio',
                       title="LCR par entité", color='entity_id')
            fig.add_hline(y=100, line_dash="dash", line_color="red", 
                         annotation_text="Minimum réglementaire (100%)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(nsfr_results, x='entity_id', y='nsfr_ratio',
                       title="NSFR par entité", color='entity_id')
            fig.add_hline(y=100, line_dash="dash", line_color="red",
                         annotation_text="Minimum réglementaire (100%)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Détails
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Détail LCR")
            st.dataframe(lcr_results, use_container_width=True)
        
        with col2:
            st.markdown("#### Détail NSFR")
            st.dataframe(nsfr_results, use_container_width=True)

def show_reporting_page():
    """Page de reporting"""
    st.markdown("## 📈 Reporting réglementaire")
    
    # Vérifier les données disponibles
    available_data = []
    if 'demo_positions' in st.session_state:
        available_data.append("Positions")
    if 'demo_rwa' in st.session_state:
        available_data.append("RWA")
    if 'demo_lcr' in st.session_state:
        available_data.append("Liquidité")
    
    if not available_data:
        st.warning("⚠️ Aucune donnée disponible. Veuillez effectuer les calculs précédents.")
        return
    
    st.markdown("### 📊 Données disponibles pour le reporting")
    
    for data_type in available_data:
        st.write(f"✅ {data_type}")
    
    if st.button("📈 Générer le rapport de synthèse", type="primary"):
        with st.spinner("Génération du rapport..."):
            
            # Rapport de synthèse
            st.markdown("### 📋 Rapport de synthèse réglementaire")
            
            if 'demo_positions' in st.session_state:
                positions = st.session_state['demo_positions']
                
                # Résumé des positions
                st.markdown("#### Résumé des expositions")
                
                summary_data = []
                for entity in positions['entity_id'].unique():
                    entity_positions = positions[positions['entity_id'] == entity]
                    
                    summary_data.append({
                        'Entité': entity,
                        'Nombre de positions': len(entity_positions),
                        'EAD totale (EUR)': f"{entity_positions['ead'].sum():,.0f}",
                        'PD moyenne': f"{entity_positions['pd'].mean():.2%}",
                        'Provisions totales (EUR)': f"{entity_positions['provision_amount'].sum():,.0f}"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
            
            if 'demo_rwa' in st.session_state:
                rwa_results = st.session_state['demo_rwa']
                
                # Résumé RWA
                st.markdown("#### Résumé des RWA")
                
                rwa_summary = []
                for entity in rwa_results['entity_id'].unique():
                    entity_rwa = rwa_results[rwa_results['entity_id'] == entity]
                    
                    rwa_summary.append({
                        'Entité': entity,
                        'RWA total (EUR)': f"{entity_rwa['rwa_amount'].sum():,.0f}",
                        'Densité RWA moyenne': f"{entity_rwa['rwa_density'].mean():.1f}%",
                        'Capital requis (8%)': f"{entity_rwa['rwa_amount'].sum() * 0.08:,.0f}"
                    })
                
                rwa_summary_df = pd.DataFrame(rwa_summary)
                st.dataframe(rwa_summary_df, use_container_width=True)
            
            if 'demo_lcr' in st.session_state and 'demo_nsfr' in st.session_state:
                lcr_results = st.session_state['demo_lcr']
                nsfr_results = st.session_state['demo_nsfr']
                
                # Résumé liquidité
                st.markdown("#### Résumé de liquidité")
                
                liquidity_summary = []
                for entity in lcr_results['entity_id'].unique():
                    entity_lcr = lcr_results[lcr_results['entity_id'] == entity]
                    entity_nsfr = nsfr_results[nsfr_results['entity_id'] == entity]
                    
                    liquidity_summary.append({
                        'Entité': entity,
                        'LCR': f"{entity_lcr['lcr_ratio'].iloc[0]:.1f}%" if not entity_lcr.empty else "N/A",
                        'NSFR': f"{entity_nsfr['nsfr_ratio'].iloc[0]:.1f}%" if not entity_nsfr.empty else "N/A",
                        'Statut LCR': "✅ Conforme" if not entity_lcr.empty and entity_lcr['lcr_ratio'].iloc[0] >= 100 else "❌ Non conforme",
                        'Statut NSFR': "✅ Conforme" if not entity_nsfr.empty and entity_nsfr['nsfr_ratio'].iloc[0] >= 100 else "❌ Non conforme"
                    })
                
                liquidity_summary_df = pd.DataFrame(liquidity_summary)
                st.dataframe(liquidity_summary_df, use_container_width=True)
            
            st.success("🎉 Rapport de synthèse généré avec succès!")

def show_documentation_page():
    """Page de documentation"""
    st.markdown("## ℹ️ Documentation")
    
    st.markdown("""
    ### 📖 Guide d'utilisation - Version de démonstration
    
    Cette version simplifiée de l'application de simulation bancaire permet de :
    
    1. **Configurer** les paramètres de simulation
    2. **Générer** des positions bancaires réalistes
    3. **Calculer** les RWA selon les approches CRR3
    4. **Analyser** les ratios de liquidité (LCR, NSFR)
    5. **Produire** un rapport de synthèse
    
    ### 🔧 Fonctionnalités disponibles
    
    - ✅ Simulation Monte Carlo de 1000+ positions
    - ✅ Calculs RWA (IRB pour retail, standardisé pour corporate)
    - ✅ Ratios LCR et NSFR par entité
    - ✅ Visualisations interactives
    - ✅ Rapport de synthèse réglementaire
    
    ### ⚠️ Limitations de cette version
    
    - Version simplifiée à des fins de démonstration
    - Calculs approximatifs (non auditables)
    - Pas d'export Excel dans cette version
    - Données fictives uniquement
    
    ### 🚀 Version complète
    
    La version complète inclut :
    - Comptabilité IFRS complète
    - Consolidation multi-devises
    - Rapports FINREP, COREP, RUBA
    - Export Excel formaté
    - Import de données personnalisées
    - Tests unitaires complets
    
    ### 📚 Références
    
    - **CRR3** : Règlement (UE) 2024/1623
    - **Bâle III** : Accords du Comité de Bâle
    - **EBA Guidelines** : [eba.europa.eu](https://www.eba.europa.eu/)
    """)

if __name__ == "__main__":
    main()
