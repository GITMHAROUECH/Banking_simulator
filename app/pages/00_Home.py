"""
Page d'accueil - Gestion des simulations.
"""
import streamlit as st

from app.adapters.legacy_compat import list_runs_advanced

st.set_page_config(
    page_title="Accueil - Banking Simulator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏠 Banking Simulator - Accueil")
st.markdown(
    """
    Bienvenue dans le simulateur bancaire. Cette application permet de générer
    des portefeuilles d'expositions bancaires et de calculer les risques associés.
    """
)

# Section : Démarrer une nouvelle simulation
st.markdown("---")
st.header("🆕 Démarrer une nouvelle simulation")
st.markdown(
    """
    Pour créer un nouveau portefeuille d'expositions, utilisez la page **01_Simulation**.
    Vous pourrez y configurer tous les paramètres de génération (nombre de prêts, obligations,
    dérivés, etc.) et obtenir un identifiant unique (run_id) pour vos calculs ultérieurs.
    """
)

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("➕ Nouvelle Simulation", type="primary", use_container_width=True):
        st.switch_page("pages/01_Simulation.py")

# Section : Simulations existantes
st.markdown("---")
st.header("📚 Simulations existantes")

try:
    df_runs = list_runs_advanced(limit=100)

    if len(df_runs) == 0:
        st.info("Aucune simulation disponible. Commencez par créer une nouvelle simulation.")
    else:
        st.markdown(f"**{len(df_runs)} simulation(s) disponible(s)**")

        # Options d'affichage
        col1, col2 = st.columns([1, 3])
        with col1:
            show_all = st.checkbox("Afficher tous les détails", value=False)

        # Formater les données pour l'affichage
        df_display = df_runs.copy()
        df_display['run_date'] = df_display['run_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_display['total_notional'] = df_display['total_notional'].apply(
            lambda x: f"{x / 1e6:,.2f} M€" if x else "N/A"
        )
        df_display['total_exposures'] = df_display['total_exposures'].apply(
            lambda x: f"{x:,}" if x else "N/A"
        )

        # Colonnes à afficher
        if show_all:
            columns_to_show = ['run_id', 'run_date', 'status', 'total_exposures', 'total_notional']
        else:
            columns_to_show = ['run_id', 'run_date', 'total_exposures', 'total_notional']

        # Renommer les colonnes pour l'affichage
        column_config = {
            'run_id': st.column_config.TextColumn('Run ID', width="medium"),
            'run_date': st.column_config.TextColumn('Date', width="medium"),
            'status': st.column_config.TextColumn('Statut', width="small"),
            'total_exposures': st.column_config.TextColumn('Nb Expositions', width="small"),
            'total_notional': st.column_config.TextColumn('Notionnel Total', width="small"),
        }

        # Afficher le tableau
        st.dataframe(
            df_display[columns_to_show],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
        )

        # Section : Sélectionner un run
        st.markdown("---")
        st.subheader("🔍 Sélectionner une simulation")

        # Créer une liste des run_ids avec informations
        run_options = [
            f"{row['run_id'][:8]}... ({row['run_date'].strftime('%Y-%m-%d %H:%M')} - {row['total_exposures']:,} exp.)"
            for _, row in df_runs.iterrows()
        ]

        selected_index = st.selectbox(
            "Choisir un run_id pour les calculs de risque",
            range(len(run_options)),
            format_func=lambda i: run_options[i],
            key="selected_run_index"
        )

        if selected_index is not None:
            selected_run_id = df_runs.iloc[selected_index]['run_id']

            # Sauvegarder dans session_state
            if st.button("✅ Utiliser ce run_id", type="primary"):
                st.session_state['selected_run_id'] = selected_run_id
                st.success(f"Run ID sélectionné : `{selected_run_id[:16]}...`")
                st.info(
                    """
                    Vous pouvez maintenant utiliser ce run_id dans les autres pages pour calculer :
                    - **RWA** (Risk-Weighted Assets)
                    - **SA-CCR** (Standardised Approach for Counterparty Credit Risk)
                    - **LCR** (Liquidity Coverage Ratio)
                    - **Ratios de capital** (CET1, Tier 1, Total Capital)
                    - **Réconciliation** ledger vs risk
                    - **Reporting** COREP/FINREP
                    """
                )

except Exception as e:
    st.error(f"❌ Erreur lors du chargement des simulations : {str(e)}")
    st.exception(e)

# Informations sur le run_id actuel
if 'selected_run_id' in st.session_state:
    st.sidebar.success(f"✅ Run ID actif : `{st.session_state['selected_run_id'][:16]}...`")

    if st.sidebar.button("🗑️ Désélectionner"):
        del st.session_state['selected_run_id']
        st.rerun()
else:
    st.sidebar.info("Aucun run_id sélectionné")
