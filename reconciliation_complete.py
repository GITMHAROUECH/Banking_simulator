import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def show_reconciliation_advanced():
    """Module de réconciliation comptabilité-risque avancé"""
    
    st.markdown("# 🔍 Réconciliation Comptabilité-Risque")
    
    # CSS pour le style
    st.markdown("""
    <style>
        .reconciliation-header {
            background: linear-gradient(135deg, #fd7e14, #e83e8c);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
        }
        .variance-card {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .error-card {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="reconciliation-header">
        <h2>🔍 Réconciliation Comptabilité-Risque</h2>
        <p>Détection et analyse des écarts entre données comptables et de risque</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration de réconciliation
    st.markdown("## ⚙️ Configuration de Réconciliation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        reconciliation_date = st.date_input("Date de Réconciliation", value=pd.Timestamp.now())
        
    with col2:
        tolerance_threshold = st.number_input("Seuil de Tolérance (%)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
        
    with col3:
        reconciliation_scope = st.selectbox("Périmètre", ["Toutes Entités", "Banque Mère", "Filiales"])
    
    # Génération de données de réconciliation
    if st.button("🚀 Lancer Réconciliation", type="primary"):
        
        # Données comptables simulées
        accounting_data = {
            'entity_id': ['ENT001', 'ENT002', 'ENT003', 'ENT004', 'ENT005'],
            'entity_name': ['Banque Mère', 'Filiale Crédit', 'Filiale Assurance', 'Joint-Venture', 'Succursale'],
            'loans_gross_accounting': [1_500_000_000, 800_000_000, 300_000_000, 200_000_000, 150_000_000],
            'provisions_accounting': [45_000_000, 28_000_000, 12_000_000, 8_000_000, 6_000_000],
            'deposits_accounting': [1_800_000_000, 900_000_000, 400_000_000, 250_000_000, 180_000_000],
            'equity_accounting': [180_000_000, 85_000_000, 35_000_000, 22_000_000, 18_000_000]
        }
        
        accounting_df = pd.DataFrame(accounting_data)
        
        # Données de risque simulées (avec écarts volontaires)
        risk_data = {
            'entity_id': ['ENT001', 'ENT002', 'ENT003', 'ENT004', 'ENT005'],
            'entity_name': ['Banque Mère', 'Filiale Crédit', 'Filiale Assurance', 'Joint-Venture', 'Succursale'],
            'ead_risk': [1_485_000_000, 805_000_000, 298_000_000, 202_000_000, 149_000_000],
            'provisions_risk': [43_500_000, 29_200_000, 11_800_000, 8_100_000, 5_900_000],
            'rwa_total': [1_200_000_000, 650_000_000, 240_000_000, 160_000_000, 120_000_000]
        }
        
        risk_df = pd.DataFrame(risk_data)
        
        # Calcul des écarts
        reconciliation_df = accounting_df.merge(risk_df, on=['entity_id', 'entity_name'])
        
        # Écarts en valeur absolue et pourcentage
        reconciliation_df['loans_variance'] = reconciliation_df['loans_gross_accounting'] - reconciliation_df['ead_risk']
        reconciliation_df['loans_variance_pct'] = (reconciliation_df['loans_variance'] / reconciliation_df['loans_gross_accounting']) * 100
        
        reconciliation_df['provisions_variance'] = reconciliation_df['provisions_accounting'] - reconciliation_df['provisions_risk']
        reconciliation_df['provisions_variance_pct'] = (reconciliation_df['provisions_variance'] / reconciliation_df['provisions_accounting']) * 100
        
        # Classification des écarts
        reconciliation_df['loans_status'] = reconciliation_df['loans_variance_pct'].abs().apply(
            lambda x: '✅ OK' if x <= tolerance_threshold else '⚠️ Écart' if x <= 5 else '❌ Critique'
        )
        
        reconciliation_df['provisions_status'] = reconciliation_df['provisions_variance_pct'].abs().apply(
            lambda x: '✅ OK' if x <= tolerance_threshold else '⚠️ Écart' if x <= 5 else '❌ Critique'
        )
        
        # Affichage des résultats
        st.markdown("## 📊 Résultats de Réconciliation")
        
        # Métriques globales
        total_entities = len(reconciliation_df)
        entities_ok = len(reconciliation_df[(reconciliation_df['loans_status'] == '✅ OK') & 
                                          (reconciliation_df['provisions_status'] == '✅ OK')])
        entities_warning = len(reconciliation_df[(reconciliation_df['loans_status'] == '⚠️ Écart') | 
                                                (reconciliation_df['provisions_status'] == '⚠️ Écart')])
        entities_critical = len(reconciliation_df[(reconciliation_df['loans_status'] == '❌ Critique') | 
                                                 (reconciliation_df['provisions_status'] == '❌ Critique')])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Entités Totales", total_entities)
        
        with col2:
            st.metric("✅ Conformes", entities_ok, delta=f"{entities_ok/total_entities*100:.1f}%")
        
        with col3:
            st.metric("⚠️ Écarts Mineurs", entities_warning, delta=f"{entities_warning/total_entities*100:.1f}%")
        
        with col4:
            st.metric("❌ Écarts Critiques", entities_critical, delta=f"{entities_critical/total_entities*100:.1f}%")
        
        # Tableau détaillé de réconciliation
        st.markdown("## 📋 Détail des Réconciliations")
        
        # Formatage pour affichage
        display_df = reconciliation_df[['entity_name', 'loans_gross_accounting', 'ead_risk', 'loans_variance', 
                                       'loans_variance_pct', 'loans_status', 'provisions_accounting', 
                                       'provisions_risk', 'provisions_variance', 'provisions_variance_pct', 
                                       'provisions_status']].copy()
        
        # Formatage des colonnes numériques
        for col in ['loans_gross_accounting', 'ead_risk', 'loans_variance', 'provisions_accounting', 'provisions_risk', 'provisions_variance']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f} EUR")
        
        for col in ['loans_variance_pct', 'provisions_variance_pct']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")
        
        # Renommage des colonnes
        display_df.columns = ['Entité', 'Prêts Compta', 'EAD Risque', 'Écart Prêts', 'Écart %', 'Statut Prêts',
                             'Provisions Compta', 'Provisions Risque', 'Écart Provisions', 'Écart %', 'Statut Provisions']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Graphiques d'analyse
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique des écarts sur les prêts
            fig = px.bar(reconciliation_df, x='entity_name', y='loans_variance_pct',
                        title="Écarts sur les Prêts par Entité (%)",
                        color='loans_status',
                        color_discrete_map={'✅ OK': 'green', '⚠️ Écart': 'orange', '❌ Critique': 'red'})
            fig.add_hline(y=tolerance_threshold, line_dash="dash", line_color="red", 
                         annotation_text=f"Seuil: {tolerance_threshold}%")
            fig.add_hline(y=-tolerance_threshold, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Graphique des écarts sur les provisions
            fig = px.bar(reconciliation_df, x='entity_name', y='provisions_variance_pct',
                        title="Écarts sur les Provisions par Entité (%)",
                        color='provisions_status',
                        color_discrete_map={'✅ OK': 'green', '⚠️ Écart': 'orange', '❌ Critique': 'red'})
            fig.add_hline(y=tolerance_threshold, line_dash="dash", line_color="red",
                         annotation_text=f"Seuil: {tolerance_threshold}%")
            fig.add_hline(y=-tolerance_threshold, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
        
        # Analyse des causes d'écarts
        st.markdown("## 🔍 Analyse des Causes d'Écarts")
        
        # Simulation des causes d'écarts
        causes_data = {
            'Cause': ['Différence de périmètre', 'Timing de comptabilisation', 'Méthode de valorisation', 
                     'Données manquantes', 'Erreur de saisie', 'Différence de cut-off'],
            'Fréquence': [25, 20, 18, 15, 12, 10],
            'Impact_Moyen': [2.5, 1.8, 3.2, 1.5, 0.8, 2.1]
        }
        
        causes_df = pd.DataFrame(causes_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(causes_df, x='Cause', y='Fréquence',
                        title="Fréquence des Causes d'Écarts")
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(causes_df, x='Fréquence', y='Impact_Moyen', size='Fréquence',
                           hover_name='Cause', title="Impact vs Fréquence des Causes")
            st.plotly_chart(fig, use_container_width=True)
        
        # Actions correctives
        st.markdown("## 🔧 Actions Correctives Recommandées")
        
        if entities_critical > 0:
            st.error(f"⚠️ {entities_critical} entité(s) présentent des écarts critiques nécessitant une action immédiate")
        
        if entities_warning > 0:
            st.warning(f"⚠️ {entities_warning} entité(s) présentent des écarts mineurs à surveiller")
        
        if entities_ok == total_entities:
            st.success("✅ Toutes les entités sont dans les seuils de tolérance")
        
        # Plan d'action
        action_plan = {
            'Priorité': ['Haute', 'Haute', 'Moyenne', 'Moyenne', 'Basse'],
            'Action': [
                'Revoir les écarts critiques (>5%)',
                'Harmoniser les méthodes de valorisation',
                'Améliorer les contrôles de cohérence',
                'Automatiser les rapprochements',
                'Former les équipes sur les procédures'
            ],
            'Responsable': ['Contrôle de Gestion', 'Risk Management', 'IT', 'Opérations', 'RH'],
            'Délai': ['Immédiat', '1 semaine', '1 mois', '3 mois', '6 mois']
        }
        
        action_df = pd.DataFrame(action_plan)
        st.dataframe(action_df, use_container_width=True)
        
        st.success("✅ Réconciliation terminée avec succès!")
    
    # Documentation
    st.markdown("---")
    st.markdown("## 📚 Documentation Réconciliation")
    
    with st.expander("🔍 Méthodologie de Réconciliation"):
        st.markdown("""
        **Étapes de Réconciliation**
        1. Extraction des données comptables et de risque
        2. Alignement des périmètres et dates
        3. Calcul des écarts en valeur et pourcentage
        4. Classification selon les seuils de tolérance
        5. Analyse des causes d'écarts
        6. Plan d'action corrective
        
        **Seuils de Tolérance Standards**
        - ✅ OK: < 1%
        - ⚠️ Écart mineur: 1-5%
        - ❌ Écart critique: > 5%
        """)
