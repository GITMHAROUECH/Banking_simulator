"""
Page Monte Carlo - Simulation de positions (I7a).
"""
import streamlit as st

from src.services import run_simulation

st.set_page_config(page_title="Monte Carlo", page_icon="🎲", layout="wide", initial_sidebar_state="expanded")

st.title("🎲 Simulation Monte Carlo")
st.markdown("Génération de positions bancaires avec paramètres avancés")

# Sidebar : Paramètres
st.sidebar.header("⚙️ Paramètres Simulation")

num_positions = st.sidebar.number_input(
    "Nombre de positions", min_value=10, max_value=10000, value=1000, step=100
)

seed = st.sidebar.number_input(
    "Seed (reproductibilité)", min_value=0, max_value=99999, value=42, step=1
)

use_cache = st.sidebar.checkbox("Utiliser le cache", value=True)

# Bouton d'exécution
if st.sidebar.button("🎲 Générer Positions", type="primary"):
    with st.spinner("⏳ Génération des positions en cours..."):
        try:
            positions_df, cache_hit = run_simulation(
                num_positions=num_positions, seed=seed, use_cache=use_cache
            )

            # Afficher le statut du cache
            if cache_hit:
                st.success("✅ Positions chargées depuis le cache")
            else:
                st.success("✅ Positions générées avec succès")

            # Métriques
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Nombre de positions", len(positions_df))

            with col2:
                total_ead = positions_df["ead"].sum()
                st.metric("EAD Total", f"{total_ead:,.0f} M€")

            with col3:
                avg_pd = positions_df["pd"].mean() * 100
                st.metric("PD Moyenne", f"{avg_pd:.2f}%")

            with col4:
                cache_icon = "✅" if cache_hit else "❌"
                st.metric("Cache", cache_icon)

            # Afficher les positions
            st.subheader("📊 Positions Générées")
            st.dataframe(positions_df, use_container_width=True)

            # Statistiques
            st.subheader("📈 Statistiques")
            col_s1, col_s2 = st.columns(2)

            with col_s1:
                st.markdown("**Distribution par Classe d'Exposition**")
                expo_dist = positions_df["exposure_class"].value_counts()
                st.bar_chart(expo_dist)

            with col_s2:
                st.markdown("**Distribution par Stage**")
                stage_dist = positions_df["stage"].value_counts()
                st.bar_chart(stage_dist)

        except Exception as e:
            st.error(f"❌ Erreur lors de la génération : {e}")
            st.exception(e)
else:
    st.info("👈 Configurez les paramètres dans la barre latérale et cliquez sur **Générer Positions**")

