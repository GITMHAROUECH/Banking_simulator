import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_drill_down_analysis(positions_df, rwa_df=None):
    """Afficher l'analyse drill-down détaillée"""
    
    st.markdown("### 🔍 Analyse Drill-Down Détaillée")
    
    # Sélecteurs de filtrage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entities = ['Toutes'] + list(positions_df['entity_id'].unique())
        selected_entity = st.selectbox("Entité", entities)
    
    with col2:
        exposure_classes = ['Toutes'] + list(positions_df['exposure_class'].unique())
        selected_exposure = st.selectbox("Classe d'Exposition", exposure_classes)
    
    with col3:
        stages = ['Tous'] + list(positions_df['stage'].unique())
        selected_stage = st.selectbox("Stage IFRS 9", stages)
    
    # Filtrage des données
    filtered_df = positions_df.copy()
    
    if selected_entity != 'Toutes':
        filtered_df = filtered_df[filtered_df['entity_id'] == selected_entity]
    
    if selected_exposure != 'Toutes':
        filtered_df = filtered_df[filtered_df['exposure_class'] == selected_exposure]
    
    if selected_stage != 'Tous':
        filtered_df = filtered_df[filtered_df['stage'] == selected_stage]
    
    # Métriques filtrées
    st.markdown("#### 📊 Métriques Filtrées")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_ead = filtered_df['ead'].sum()
        st.metric("EAD Total", f"{total_ead:,.0f} EUR")
    
    with col2:
        avg_pd = filtered_df['pd'].mean()
        st.metric("PD Moyenne", f"{avg_pd:.2%}")
    
    with col3:
        total_ecl = filtered_df['ecl_provision'].sum()
        st.metric("Provisions ECL", f"{total_ecl:,.0f} EUR")
    
    with col4:
        count_positions = len(filtered_df)
        st.metric("Nombre de Positions", f"{count_positions:,}")
    
    # Graphiques détaillés
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribution par PD
            fig = px.histogram(filtered_df, x='pd', nbins=20, 
                             title="Distribution des Probabilités de Défaut")
            fig.update_layout(xaxis_title="PD", yaxis_title="Nombre de Positions")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # EAD par classe d'exposition
            ead_by_class = filtered_df.groupby('exposure_class')['ead'].sum().reset_index()
            fig = px.pie(ead_by_class, values='ead', names='exposure_class',
                        title="Répartition EAD par Classe d'Exposition")
            st.plotly_chart(fig, use_container_width=True)
        
        # Tableau détaillé
        st.markdown("#### 📋 Positions Détaillées")
        
        # Options d'affichage
        show_all = st.checkbox("Afficher toutes les colonnes")
        
        if show_all:
            display_df = filtered_df
        else:
            display_df = filtered_df[['position_id', 'entity_id', 'exposure_class', 
                                    'ead', 'pd', 'lgd', 'ecl_provision', 'stage']]
        
        # Pagination
        page_size = st.selectbox("Nombre de lignes par page", [10, 25, 50, 100], index=1)
        
        total_pages = (len(display_df) - 1) // page_size + 1
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(display_df.iloc[start_idx:end_idx], use_container_width=True)
        
        st.info(f"Affichage de {start_idx + 1} à {min(end_idx, len(display_df))} sur {len(display_df)} positions")
        
        # Analyse de corrélation
        if len(filtered_df) > 1:
            st.markdown("#### 🔗 Analyse de Corrélation")
            
            numeric_cols = ['ead', 'pd', 'lgd', 'maturity', 'ecl_provision']
            corr_matrix = filtered_df[numeric_cols].corr()
            
            fig = px.imshow(corr_matrix, 
                          text_auto=True, 
                          aspect="auto",
                          title="Matrice de Corrélation")
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("Aucune position ne correspond aux filtres sélectionnés.")
