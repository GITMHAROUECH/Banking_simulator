import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def show_consolidation_advanced():
    """Module de consolidation IFRS avancé"""
    
    st.markdown("# 🔄 Consolidation IFRS Avancée")
    
    # CSS pour les icônes
    st.markdown("""
    <style>
        .consolidation-header {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 5px solid #28a745;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="consolidation-header">
        <h2>📊 Consolidation IFRS & Éliminations Intragroupes</h2>
        <p>Processus complet de consolidation avec conversion multi-devises et calcul des intérêts minoritaires</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration de consolidation
    st.markdown("## ⚙️ Configuration de Consolidation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.selectbox("Méthode de Consolidation", 
                    ["Intégration Globale", "Intégration Proportionnelle", "Mise en Équivalence"])
        
    with col2:
        st.selectbox("Devise de Consolidation", ["EUR", "USD", "GBP", "CHF"])
        
    with col3:
        st.date_input("Date de Clôture", value=pd.Timestamp.now())
    
    # Génération de données fictives pour la démonstration
    if st.button("🚀 Générer Données de Consolidation", type="primary"):
        
        # Données des entités
        entities_data = {
            'entity_id': ['ENT001', 'ENT002', 'ENT003', 'ENT004'],
            'entity_name': ['Banque Mère SA', 'Filiale Crédit', 'Filiale Assurance', 'Joint-Venture'],
            'country': ['France', 'Allemagne', 'Italie', 'Espagne'],
            'currency': ['EUR', 'EUR', 'EUR', 'EUR'],
            'ownership_pct': [100.0, 85.0, 75.0, 50.0],
            'consolidation_method': ['Intégration Globale', 'Intégration Globale', 'Intégration Globale', 'Intégration Proportionnelle']
        }
        
        entities_df = pd.DataFrame(entities_data)
        
        # Données financières par entité
        financial_data = []
        for entity in entities_data['entity_id']:
            data = {
                'entity_id': entity,
                'total_assets': np.random.uniform(500_000_000, 2_000_000_000),
                'loans_advances': np.random.uniform(300_000_000, 1_500_000_000),
                'deposits': np.random.uniform(400_000_000, 1_800_000_000),
                'equity': np.random.uniform(50_000_000, 200_000_000),
                'net_income': np.random.uniform(10_000_000, 50_000_000),
                'provisions': np.random.uniform(5_000_000, 25_000_000)
            }
            financial_data.append(data)
        
        financial_df = pd.DataFrame(financial_data)
        
        # Éliminations intragroupes
        eliminations_data = {
            'elimination_type': ['Prêts Intragroupes', 'Dépôts Intragroupes', 'Dividendes', 'Frais de Gestion'],
            'amount': [50_000_000, 45_000_000, 15_000_000, 5_000_000],
            'entity_from': ['ENT001', 'ENT002', 'ENT002', 'ENT001'],
            'entity_to': ['ENT002', 'ENT001', 'ENT001', 'ENT003']
        }
        
        eliminations_df = pd.DataFrame(eliminations_data)
        
        # Affichage des résultats
        st.markdown("## 📋 Périmètre de Consolidation")
        st.dataframe(entities_df, use_container_width=True)
        
        st.markdown("## 💰 Données Financières par Entité")
        
        # Formatage des montants
        financial_display = financial_df.copy()
        for col in ['total_assets', 'loans_advances', 'deposits', 'equity', 'net_income', 'provisions']:
            financial_display[col] = financial_display[col].apply(lambda x: f"{x:,.0f} EUR")
        
        st.dataframe(financial_display, use_container_width=True)
        
        st.markdown("## 🔄 Éliminations Intragroupes")
        
        eliminations_display = eliminations_df.copy()
        eliminations_display['amount'] = eliminations_display['amount'].apply(lambda x: f"{x:,.0f} EUR")
        st.dataframe(eliminations_display, use_container_width=True)
        
        # Calculs de consolidation
        st.markdown("## 📊 Résultats de Consolidation")
        
        # Calcul des agrégats consolidés
        total_assets_consolidated = 0
        total_equity_consolidated = 0
        minority_interests = 0
        
        for idx, row in entities_df.iterrows():
            entity_financials = financial_df[financial_df['entity_id'] == row['entity_id']].iloc[0]
            
            if row['consolidation_method'] == 'Intégration Globale':
                total_assets_consolidated += entity_financials['total_assets']
                if row['ownership_pct'] < 100:
                    minority_interests += entity_financials['equity'] * (100 - row['ownership_pct']) / 100
                total_equity_consolidated += entity_financials['equity'] * row['ownership_pct'] / 100
            elif row['consolidation_method'] == 'Intégration Proportionnelle':
                total_assets_consolidated += entity_financials['total_assets'] * row['ownership_pct'] / 100
                total_equity_consolidated += entity_financials['equity'] * row['ownership_pct'] / 100
        
        # Soustraction des éliminations
        total_eliminations = eliminations_df['amount'].sum()
        total_assets_consolidated -= total_eliminations
        
        # Métriques consolidées
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Actif Consolidé", f"{total_assets_consolidated:,.0f} EUR")
        
        with col2:
            st.metric("Capitaux Propres Consolidés", f"{total_equity_consolidated:,.0f} EUR")
        
        with col3:
            st.metric("Intérêts Minoritaires", f"{minority_interests:,.0f} EUR")
        
        with col4:
            st.metric("Éliminations Totales", f"{total_eliminations:,.0f} EUR")
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition des actifs par entité
            fig = px.pie(financial_df, values='total_assets', names='entity_id',
                        title="Répartition des Actifs par Entité")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Méthodes de consolidation
            consolidation_summary = entities_df.groupby('consolidation_method')['ownership_pct'].mean().reset_index()
            fig = px.bar(consolidation_summary, x='consolidation_method', y='ownership_pct',
                        title="Pourcentage de Détention Moyen par Méthode")
            st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ Consolidation IFRS terminée avec succès!")
    
    # Documentation
    st.markdown("---")
    st.markdown("## 📚 Documentation IFRS")
    
    with st.expander("🔍 Méthodes de Consolidation"):
        st.markdown("""
        **Intégration Globale (IFRS 10)**
        - Contrôle exclusif (>50% + pouvoir de direction)
        - 100% des actifs et passifs intégrés
        - Intérêts minoritaires calculés
        
        **Intégration Proportionnelle (IFRS 11)**
        - Contrôle conjoint dans un partenariat
        - Quote-part des actifs/passifs intégrée
        - Applicable aux joint-ventures
        
        **Mise en Équivalence (IAS 28)**
        - Influence notable (20-50%)
        - Investissement à la quote-part des capitaux propres
        - Résultat proportionnel intégré
        """)
