"""
Capital Ratios UI page - refactored to use service layer.
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


def safe_dataframe_creation(data):
    """Safely create DataFrame from dict"""
    try:
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error creating DataFrame: {e}")
        return pd.DataFrame()


def show_capital_ratios():
    """Page des ratios de capital - version refactorisée"""
    st.markdown("## 🏛️ Ratios de Capital Réglementaires")

    if 'capital_ratios' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord calculer les RWA dans la section Risque de Crédit.")
        return

    capital_ratios = st.session_state['capital_ratios']

    st.markdown("### 📊 Vue d'Ensemble des Ratios de Capital")

    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("RWA Total", f"{capital_ratios['total_rwa']:,.0f} EUR")
        st.metric("Capital CET1", f"{capital_ratios['cet1_capital']:,.0f} EUR")

    with col2:
        cet1_ratio = capital_ratios['cet1_ratio']
        capital_ratios['cet1_requirement']
        cet1_surplus = capital_ratios['cet1_surplus']
        color = "normal" if cet1_surplus > 0 else "inverse"
        st.metric("CET1 Ratio", f"{cet1_ratio:.1f}%",
                 delta=f"{cet1_surplus:+.1f}% vs exigence",
                 delta_color=color)

    with col3:
        tier1_ratio = capital_ratios['tier1_ratio']
        tier1_surplus = capital_ratios['tier1_surplus']
        color = "normal" if tier1_surplus > 0 else "inverse"
        st.metric("Tier 1 Ratio", f"{tier1_ratio:.1f}%",
                 delta=f"{tier1_surplus:+.1f}% vs exigence",
                 delta_color=color)

    with col4:
        total_ratio = capital_ratios['total_capital_ratio']
        total_surplus = capital_ratios['total_surplus']
        color = "normal" if total_surplus > 0 else "inverse"
        st.metric("Total Capital Ratio", f"{total_ratio:.1f}%",
                 delta=f"{total_surplus:+.1f}% vs exigence",
                 delta_color=color)

    # Graphique en cascade des exigences
    st.markdown("#### 📊 Exigences de Capital en Cascade")

    # Données pour le graphique en cascade
    cascade_data = {
        'Composant': [
            'Pilier 1 (CET1)',
            'Conservation Buffer',
            'Countercyclical Buffer',
            'Systemic Buffer',
            'Total CET1 Requirement',
            'Additional Tier 1',
            'Tier 2 Capital'
        ],
        'Pourcentage': [
            4.5,  # Pilier 1 CET1
            2.5,  # Conservation buffer
            0.0,  # Countercyclical (simulé à 0)
            1.0,  # Systemic buffer (simulé)
            capital_ratios['cet1_requirement'],  # Total CET1
            capital_ratios['tier1_requirement'] - capital_ratios['cet1_requirement'],  # AT1
            capital_ratios['total_requirement'] - capital_ratios['tier1_requirement']   # Tier 2
        ],
        'Type': [
            'CET1', 'CET1', 'CET1', 'CET1', 'CET1', 'AT1', 'Tier2'
        ]
    }

    cascade_df = safe_dataframe_creation(cascade_data)

    fig = px.bar(cascade_df, x='Composant', y='Pourcentage', color='Type',
               title="Composition des Exigences de Capital")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Comparaison avec les ratios actuels
    st.markdown("#### 📈 Comparaison Ratios Actuels vs Exigences")

    comparison_data = {
        'Ratio': ['CET1', 'Tier 1', 'Total Capital'],
        'Actuel': [
            capital_ratios['cet1_ratio'],
            capital_ratios['tier1_ratio'],
            capital_ratios['total_capital_ratio']
        ],
        'Exigence': [
            capital_ratios['cet1_requirement'],
            capital_ratios['tier1_requirement'],
            capital_ratios['total_requirement']
        ],
        'Surplus': [
            capital_ratios['cet1_surplus'],
            capital_ratios['tier1_surplus'],
            capital_ratios['total_surplus']
        ]
    }

    comparison_df = safe_dataframe_creation(comparison_data)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Ratio Actuel',
            x=comparison_df['Ratio'],
            y=comparison_df['Actuel'],
            marker_color='lightblue'
        ))

        fig.add_trace(go.Bar(
            name='Exigence Réglementaire',
            x=comparison_df['Ratio'],
            y=comparison_df['Exigence'],
            marker_color='red'
        ))

        fig.update_layout(
            title="Ratios Actuels vs Exigences",
            yaxis_title="Pourcentage (%)",
            barmode='group'
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Graphique des surplus/déficits
        ['green' if x > 0 else 'red' for x in comparison_df['Surplus']]

        fig = px.bar(comparison_df, x='Ratio', y='Surplus',
                   title="Surplus/Déficit de Capital",
                   color='Surplus',
                   color_continuous_scale='RdYlGn')
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig, use_container_width=True)

    # Tableau détaillé
    st.markdown("#### 📋 Détail des Ratios de Capital")

    detail_data = {
        'Métrique': [
            'RWA Total (EUR)',
            'Capital CET1 (EUR)',
            'Capital Tier 1 (EUR)',
            'Capital Total (EUR)',
            'CET1 Ratio (%)',
            'Tier 1 Ratio (%)',
            'Total Capital Ratio (%)',
            'CET1 Exigence (%)',
            'Tier 1 Exigence (%)',
            'Total Capital Exigence (%)',
            'CET1 Surplus/Déficit (%)',
            'Tier 1 Surplus/Déficit (%)',
            'Total Capital Surplus/Déficit (%)'
        ],
        'Valeur': [
            f"{capital_ratios['total_rwa']:,.0f}",
            f"{capital_ratios['cet1_capital']:,.0f}",
            f"{capital_ratios['tier1_capital']:,.0f}",
            f"{capital_ratios['total_capital']:,.0f}",
            f"{capital_ratios['cet1_ratio']:.2f}",
            f"{capital_ratios['tier1_ratio']:.2f}",
            f"{capital_ratios['total_capital_ratio']:.2f}",
            f"{capital_ratios['cet1_requirement']:.2f}",
            f"{capital_ratios['tier1_requirement']:.2f}",
            f"{capital_ratios['total_requirement']:.2f}",
            f"{capital_ratios['cet1_surplus']:+.2f}",
            f"{capital_ratios['tier1_surplus']:+.2f}",
            f"{capital_ratios['total_surplus']:+.2f}"
        ]
    }

    detail_df = safe_dataframe_creation(detail_data)
    st.dataframe(detail_df, use_container_width=True)

    # Analyse spécifique des dérivés dans les RWA (si disponible)
    if 'advanced_rwa' in st.session_state:
        rwa_results = st.session_state['advanced_rwa']
        total_rwa = capital_ratios['total_rwa']

        derivatives_rwa = rwa_results[rwa_results["product_id"].str.contains("Derivative", na=False)]
        if not derivatives_rwa.empty:
            st.markdown("#### ⚡ RWA des Produits Dérivés")

            col1, col2, col3 = st.columns(3)

            with col1:
                derivatives_total_rwa = derivatives_rwa["rwa_amount"].sum()
                derivatives_pct = (derivatives_total_rwa / total_rwa * 100) if total_rwa > 0 else 0
                st.metric("RWA Dérivés", f"{derivatives_total_rwa:,.0f} EUR", f"{derivatives_pct:.1f}% du total")

            with col2:
                avg_rwa_density_derivatives = derivatives_rwa["rwa_density"].mean()
                st.metric("Densité RWA Moyenne", f"{avg_rwa_density_derivatives:.1%}")

            with col3:
                num_derivatives_rwa = len(derivatives_rwa)
                st.metric("Positions Dérivés", f"{num_derivatives_rwa:,}")

            # Graphique RWA par type de dérivé
            if "derivative_type" in derivatives_rwa.columns:
                derivative_rwa_summary = derivatives_rwa.groupby("derivative_type")["rwa_amount"].sum().reset_index()
                fig = px.bar(derivative_rwa_summary, x="derivative_type", y="rwa_amount",
                           title="RWA par Type de Dérivé", color="derivative_type")
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

    # Analyse de sensibilité du capital
    st.markdown("#### 🎯 Analyse de Sensibilité du Capital")

    with st.expander("Voir l'impact des variations de RWA"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Impact d'une augmentation des RWA**")

            rwa_increases = [10, 25, 50, 100]  # Pourcentages

            sensitivity_data = []
            for increase in rwa_increases:
                new_rwa = capital_ratios['total_rwa'] * (1 + increase/100)
                new_cet1_ratio = (capital_ratios['cet1_capital'] / new_rwa * 100)

                sensitivity_data.append({
                    'Augmentation RWA (%)': f"+{increase}%",
                    'Nouveau RWA (EUR)': f"{new_rwa:,.0f}",
                    'Nouveau CET1 (%)': f"{new_cet1_ratio:.1f}",
                    'Impact CET1 (pp)': f"{new_cet1_ratio - capital_ratios['cet1_ratio']:+.1f}"
                })

            sensitivity_df = safe_dataframe_creation(sensitivity_data)
            st.dataframe(sensitivity_df, use_container_width=True)

        with col2:
            st.markdown("**Capital additionnel requis**")

            # Calculer le capital additionnel pour maintenir les ratios cibles
            target_cet1 = capital_ratios['cet1_requirement']

            additional_capital_data = []
            for increase in rwa_increases:
                new_rwa = capital_ratios['total_rwa'] * (1 + increase/100)
                required_capital = new_rwa * (target_cet1 / 100)
                additional_capital = required_capital - capital_ratios['cet1_capital']

                additional_capital_data.append({
                    'Augmentation RWA (%)': f"+{increase}%",
                    'Capital Requis (EUR)': f"{required_capital:,.0f}",
                    'Capital Additionnel (EUR)': f"{additional_capital:,.0f}",
                    'Coût Opportunité (%)': f"{(additional_capital / capital_ratios['cet1_capital'] * 100):+.1f}"
                })

            additional_df = safe_dataframe_creation(additional_capital_data)
            st.dataframe(additional_df, use_container_width=True)

    # Recommandations
    st.markdown("#### 💡 Recommandations")

    recommendations = []

    if capital_ratios['cet1_surplus'] < 1.0:
        recommendations.append("⚠️ **CET1 Ratio proche de l'exigence** : Envisager une augmentation de capital ou une réduction des RWA")

    if capital_ratios['tier1_surplus'] < 1.0:
        recommendations.append("⚠️ **Tier 1 Ratio faible** : Surveiller de près et préparer des mesures correctives")

    if capital_ratios['total_surplus'] < 2.0:
        recommendations.append("⚠️ **Total Capital Ratio serré** : Maintenir une surveillance renforcée")

    if capital_ratios['cet1_surplus'] > 5.0:
        recommendations.append("✅ **CET1 Ratio confortable** : Possibilité d'optimiser l'allocation du capital")

    if len(recommendations) > 0:
        for rec in recommendations:
            st.markdown(rec)
    else:
        st.success("✅ Tous les ratios de capital sont conformes aux exigences réglementaires")

