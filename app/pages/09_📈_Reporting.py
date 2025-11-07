"""
Page Reporting - COREP/FINREP (I7a).
"""
import streamlit as st
import pandas as pd

from src.services import run_simulation, compute_rwa

st.set_page_config(page_title="Reporting", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.title("📈 Reporting Réglementaire")
st.markdown("Rapports COREP et FINREP conformes aux normes EBA")

# Info section
st.info("""
**Rapports disponibles :**
- **COREP C07** : Expositions de crédit (Approche Standard)
- **COREP C08** : RWA par approche (STD/IRB)
- **COREP C34** : SA-CCR (Risque de contrepartie)
- **FINREP F09** : Impairment IFRS 9 (ECL par stage)
- **FINREP F18** : Loans and Advances

Pour générer des rapports, utilisez la page **🚀 Pipeline**.
""")

# Sidebar : Génération rapide
st.sidebar.header("⚙️ Génération Rapide")

st.sidebar.markdown("Générer des données pour visualiser les rapports :")

num_positions = st.sidebar.number_input(
    "Nombre de positions", min_value=10, max_value=10000, value=500, step=100
)
seed = st.sidebar.number_input(
    "Seed", min_value=0, max_value=99999, value=42, step=1
)

if st.sidebar.button("📊 Générer Données", type="primary"):
    with st.spinner("⏳ Génération en cours..."):
        try:
            # Générer positions et RWA
            positions_df, _ = run_simulation(num_positions=num_positions, seed=seed)
            rwa_df, _ = compute_rwa(positions_df, use_cache=False)

            st.session_state["reporting_positions"] = positions_df
            st.session_state["reporting_rwa"] = rwa_df

            st.success("✅ Données générées avec succès")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erreur: {e}")

# Affichage des rapports
if "reporting_positions" in st.session_state and "reporting_rwa" in st.session_state:
    positions_df = st.session_state["reporting_positions"]
    rwa_df = st.session_state["reporting_rwa"]

    tabs = st.tabs(["📊 COREP C07", "📊 COREP C08", "📋 FINREP F18", "📈 Statistiques"])

    with tabs[0]:
        st.subheader("COREP C07 - Expositions de crédit (Approche Standard)")

        # Agrégation par classe d'exposition
        corep_c07 = rwa_df.groupby("exposure_class").agg({
            "ead": "sum",
            "rwa_amount": "sum"
        }).reset_index()
        corep_c07["risk_weight_pct"] = (corep_c07["rwa_amount"] / corep_c07["ead"] * 100).round(2)
        corep_c07["own_funds_req"] = (corep_c07["rwa_amount"] * 0.08).round(2)

        corep_c07.columns = ["Exposure Class", "EAD (M€)", "RWEA (M€)", "Risk Weight (%)", "Own Funds Req (M€)"]

        st.dataframe(corep_c07, use_container_width=True)

        # Métriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total EAD", f"{corep_c07['EAD (M€)'].sum():,.0f} M€")
        with col2:
            st.metric("Total RWEA", f"{corep_c07['RWEA (M€)'].sum():,.0f} M€")
        with col3:
            st.metric("Avg Risk Weight", f"{(corep_c07['RWEA (M€)'].sum() / corep_c07['EAD (M€)'].sum() * 100):.1f}%")

    with tabs[1]:
        st.subheader("COREP C08 - RWA par approche")

        # Agrégation par approche
        corep_c08 = rwa_df.groupby("approach").agg({
            "ead": "sum",
            "rwa_amount": "sum"
        }).reset_index()
        corep_c08["capital_req"] = (corep_c08["rwa_amount"] * 0.08).round(2)
        corep_c08["risk_density_pct"] = (corep_c08["rwa_amount"] / corep_c08["ead"] * 100).round(2)

        corep_c08.columns = ["Approach", "EAD (M€)", "RWEA (M€)", "Capital Req (M€)", "Risk Density (%)"]

        st.dataframe(corep_c08, use_container_width=True)

        # Graphique
        import plotly.express as px
        fig = px.pie(corep_c08, values="RWEA (M€)", names="Approach",
                    title="Répartition RWEA par approche")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("FINREP F18 - Loans and Advances")

        # Agrégation par classe d'exposition
        finrep_f18 = positions_df.groupby("exposure_class").agg({
            "notional": "sum"
        }).reset_index()

        finrep_f18.columns = ["Exposure Class", "Total Loans (M€)"]

        st.dataframe(finrep_f18, use_container_width=True)

        # Graphique
        fig = px.bar(finrep_f18, x="Exposure Class", y="Total Loans (M€)",
                    title="Prêts par classe d'exposition")
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.subheader("📈 Statistiques Globales")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Positions", f"{len(positions_df):,}")

        with col2:
            st.metric("Entités", f"{positions_df['entity_id'].nunique()}")

        with col3:
            st.metric("Classes Expo", f"{positions_df['exposure_class'].nunique()}")

        with col4:
            st.metric("Total Notional", f"{positions_df['notional'].sum():,.0f} M€")

        # Détails par entité
        st.markdown("### Par Entité")
        entity_stats = positions_df.groupby("entity_id").agg({
            "position_id": "count",
            "notional": "sum"
        }).reset_index()
        entity_stats.columns = ["Entity", "Positions", "Notional (M€)"]

        st.dataframe(entity_stats, use_container_width=True)

else:
    st.warning("⚠️ Aucune donnée disponible. Utilisez la génération rapide ou exécutez le Pipeline.")

    st.markdown("""
    ### 📖 Guide d'utilisation

    **Option 1 : Génération rapide (sidebar)**
    1. Configurez le nombre de positions et le seed
    2. Cliquez sur "Générer Données"
    3. Les rapports COREP/FINREP s'affichent automatiquement

    **Option 2 : Pipeline complet**
    1. Allez sur la page **🚀 Pipeline**
    2. Exécutez le pipeline E2E
    3. Les rapports complets (COREP C07/C08/C34, FINREP F09/F18) seront disponibles

    ### 📋 Templates disponibles
    - **COREP C07** : Expositions par classe, pondérations de risque
    - **COREP C08** : RWA par approche (Standardized/IRB)
    - **COREP C34** : SA-CCR pour dérivés OTC
    - **FINREP F09** : Impairment ECL par stage IFRS 9
    - **FINREP F18** : Loans par maturité et garantie
    """)
