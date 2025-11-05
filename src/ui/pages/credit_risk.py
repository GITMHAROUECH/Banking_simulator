"""
Credit Risk UI page - refactored to use service layer.
"""

import os
import sys

import plotly.express as px
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app.config.defaults import DEFAULT_CONFIG
from src.services.credit_risk_service import compute_capital, compute_rwa


def show_credit_risk_advanced():
    """Page de risque de crédit avancée - version refactorisée"""
    st.markdown("## ⚠️ Risque de Crédit et RWA selon CRR3")

    if 'advanced_positions' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord effectuer une simulation Monte Carlo.")
        return

    positions = st.session_state['advanced_positions']

    st.markdown("### 📊 Calculs RWA selon les Approches CRR3")

    # Informations sur les approches
    with st.expander("ℹ️ Approches de Calcul CRR3"):
        st.markdown("""
        **IRB Foundation (Internal Ratings Based)**
        - Utilisée pour les expositions Retail et Corporate
        - Formules de corrélation selon CRR3
        - Ajustements de maturité pour Corporate
        - Réduction de 23.81% pour les SME

        **Approche Standardisée**
        - Utilisée pour Souverains, Banques et autres expositions
        - Pondérations de risque fixes selon la notation
        - Pas d'ajustement de maturité

        **Paramètres Clés**
        - PD : Probability of Default (probabilité de défaut)
        - LGD : Loss Given Default (perte en cas de défaut)
        - EAD : Exposure at Default (exposition au moment du défaut)
        - M : Maturity (maturité effective)
        """)

    if st.button("⚠️ Calculer les RWA selon CRR3", type="primary"):
        with st.spinner("Calcul des RWA en cours..."):
            try:
                # Use service layer for RWA computation
                config = DEFAULT_CONFIG
                rwa_results = compute_rwa(positions, config)

                # Use service layer for capital ratios
                capital_ratios = compute_capital(rwa_results)

                st.session_state['advanced_rwa'] = rwa_results
                st.session_state['capital_ratios'] = capital_ratios

                st.success("🎉 RWA calculés avec succès selon CRR3!")

            except Exception as e:
                st.error(f"❌ Erreur lors du calcul des RWA: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
                return

    if 'advanced_rwa' in st.session_state and 'capital_ratios' in st.session_state:
        rwa_results = st.session_state['advanced_rwa']
        capital_ratios = st.session_state['capital_ratios']

        st.markdown("### 📊 Résultats des RWA")

        # Métriques principales
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            total_rwa = capital_ratios['total_rwa']
            st.metric("RWA Total", f"{total_rwa:,.0f} EUR")

        with col2:
            total_ead = rwa_results['ead'].sum()
            avg_density = (total_rwa / total_ead * 100) if total_ead > 0 else 0
            st.metric("Densité RWA", f"{avg_density:.1f}%")

        with col3:
            capital_required = total_rwa * 0.08
            st.metric("Capital Requis (8%)", f"{capital_required:,.0f} EUR")

        with col4:
            cet1_capital = capital_ratios['cet1_capital']
            st.metric("Capital CET1", f"{cet1_capital:,.0f} EUR")

        with col5:
            cet1_ratio = capital_ratios['cet1_ratio']
            st.metric("Ratio CET1", f"{cet1_ratio:.1f}%")

        # Ratios de capital détaillés
        st.markdown("#### 🏛️ Ratios de Capital Réglementaires")

        col1, col2, col3 = st.columns(3)

        with col1:
            cet1_req = capital_ratios['cet1_requirement']
            cet1_surplus = capital_ratios['cet1_surplus']
            color = "normal" if cet1_surplus > 0 else "inverse"
            st.metric("CET1 Ratio", f"{cet1_ratio:.1f}%",
                     delta=f"{cet1_surplus:.1f}% vs exigence ({cet1_req:.1f}%)",
                     delta_color=color)

        with col2:
            tier1_ratio = capital_ratios['tier1_ratio']
            tier1_req = capital_ratios['tier1_requirement']
            tier1_surplus = capital_ratios['tier1_surplus']
            color = "normal" if tier1_surplus > 0 else "inverse"
            st.metric("Tier 1 Ratio", f"{tier1_ratio:.1f}%",
                     delta=f"{tier1_surplus:.1f}% vs exigence ({tier1_req:.1f}%)",
                     delta_color=color)

        with col3:
            total_ratio = capital_ratios['total_capital_ratio']
            total_req = capital_ratios['total_requirement']
            total_surplus = capital_ratios['total_surplus']
            color = "normal" if total_surplus > 0 else "inverse"
            st.metric("Total Capital Ratio", f"{total_ratio:.1f}%",
                     delta=f"{total_surplus:.1f}% vs exigence ({total_req:.1f}%)",
                     delta_color=color)

        # Graphiques d'analyse RWA
        st.markdown("#### 📈 Analyse des RWA")

        col1, col2 = st.columns(2)

        with col1:
            # RWA par classe d'exposition
            rwa_by_class = rwa_results.groupby('exposure_class')['rwa_amount'].sum().reset_index()

            fig = px.bar(rwa_by_class, x='exposure_class', y='rwa_amount',
                       title="RWA par Classe d'Exposition", color='exposure_class')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # RWA par approche
            rwa_by_approach = rwa_results.groupby('approach')['rwa_amount'].sum().reset_index()

            fig = px.pie(rwa_by_approach, values='rwa_amount', names='approach',
                       title="Répartition RWA par Approche")
            st.plotly_chart(fig, use_container_width=True)

        # Densité RWA par entité et classe
        col1, col2 = st.columns(2)

        with col1:
            # RWA par entité
            rwa_by_entity = rwa_results.groupby('entity_id').agg({
                'rwa_amount': 'sum',
                'ead': 'sum'
            }).reset_index()
            rwa_by_entity['rwa_density'] = (rwa_by_entity['rwa_amount'] / rwa_by_entity['ead'] * 100).round(1)

            fig = px.bar(rwa_by_entity, x='entity_id', y='rwa_amount',
                       title="RWA par Entité", color='entity_id')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Densité RWA par classe
            density_by_class = rwa_results.groupby('exposure_class')['rwa_density'].mean().reset_index()

            fig = px.bar(density_by_class, x='exposure_class', y='rwa_density',
                       title="Densité RWA Moyenne par Classe", color='exposure_class')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        # Analyse spécifique des dérivés dans les RWA
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

        # Analyse de sensibilité
        st.markdown("#### 🎯 Analyse de Sensibilité")

        with st.expander("Voir l'impact des variations de paramètres"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Impact d'une augmentation de PD de +50%**")

                # Simulation rapide
                pd_shock = 1.5
                shocked_rwa = total_rwa * pd_shock
                rwa_impact = shocked_rwa - total_rwa

                st.write(f"• RWA après choc: {shocked_rwa:,.0f} EUR")
                st.write(f"• Impact: +{rwa_impact:,.0f} EUR (+{(rwa_impact/total_rwa*100):.1f}%)")

                # Impact sur les ratios
                new_cet1 = (cet1_capital / shocked_rwa * 100)
                cet1_impact = new_cet1 - cet1_ratio
                st.write(f"• Nouveau CET1: {new_cet1:.1f}% ({cet1_impact:+.1f}%)")

            with col2:
                st.markdown("**Impact d'une augmentation de LGD de +25%**")

                lgd_shock = 1.25
                shocked_rwa_lgd = total_rwa * lgd_shock
                rwa_impact_lgd = shocked_rwa_lgd - total_rwa

                st.write(f"• RWA après choc: {shocked_rwa_lgd:,.0f} EUR")
                st.write(f"• Impact: +{rwa_impact_lgd:,.0f} EUR (+{(rwa_impact_lgd/total_rwa*100):.1f}%)")

                new_cet1_lgd = (cet1_capital / shocked_rwa_lgd * 100)
                cet1_impact_lgd = new_cet1_lgd - cet1_ratio
                st.write(f"• Nouveau CET1: {new_cet1_lgd:.1f}% ({cet1_impact_lgd:+.1f}%)")

        # Détail des RWA par entité
        st.markdown("#### 🏢 Détail par Entité")

        entity_detail = rwa_results.groupby(['entity_id', 'exposure_class']).agg({
            'rwa_amount': 'sum',
            'ead': 'sum',
            'rwa_density': 'mean'
        }).reset_index()

        entity_pivot = entity_detail.pivot(index='entity_id',
                                         columns='exposure_class',
                                         values='rwa_amount').fillna(0)

        st.dataframe(entity_pivot, use_container_width=True)

        # Aperçu des RWA détaillés
        st.markdown("### 🔍 Détail des RWA (100 premières positions)")

        display_columns = ['entity_id', 'exposure_class', 'ead',
                          'rwa_amount', 'rwa_density', 'approach']

        # Add optional columns if they exist
        if 'pd' in rwa_results.columns:
            display_columns.append('pd')
        if 'lgd' in rwa_results.columns:
            display_columns.append('lgd')

        st.dataframe(rwa_results[display_columns].head(100), use_container_width=True)

