"""
Page RWA - Calcul des Risk-Weighted Assets (I7a).
"""
import streamlit as st

from src.services import compute_rwa, run_simulation

st.set_page_config(page_title="RWA", page_icon="💰", layout="wide", initial_sidebar_state="expanded")

st.title("💰 Risk-Weighted Assets (RWA)")
st.markdown("Calcul des actifs pondérés par le risque (IRB Foundation & Standardized)")

# Sidebar : Paramètres
st.sidebar.header("⚙️ Paramètres")

# Option 1 : Générer de nouvelles positions
st.sidebar.subheader("Option 1 : Générer Positions")
num_positions = st.sidebar.number_input(
    "Nombre de positions", min_value=10, max_value=10000, value=1000, step=100
)
seed = st.sidebar.number_input(
    "Seed", min_value=0, max_value=99999, value=42, step=1
)

use_cache = st.sidebar.checkbox("Utiliser le cache", value=True)

# Bouton d'exécution
if st.sidebar.button("💰 Calculer RWA", type="primary"):
    with st.spinner("⏳ Calcul des RWA en cours..."):
        try:
            # Générer les positions
            positions_df, cache_hit_sim = run_simulation(
                num_positions=num_positions, seed=seed, use_cache=use_cache
            )

            # Calculer RWA
            rwa_df, cache_hit_rwa = compute_rwa(positions_df, use_cache=use_cache)

            # Afficher le statut du cache
            if cache_hit_rwa:
                st.success("✅ RWA chargés depuis le cache")
            else:
                st.success("✅ RWA calculés avec succès")

            # Métriques
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_rwa = rwa_df["rwa_amount"].sum()
                st.metric("RWA Total", f"{total_rwa:,.0f} M€")

            with col2:
                avg_density = rwa_df["rwa_density"].mean() * 100
                st.metric("Densité Moyenne", f"{avg_density:.1f}%")

            with col3:
                irb_count = (rwa_df["approach"] == "IRB Foundation").sum()
                st.metric("Positions IRB", irb_count)

            with col4:
                cache_icon = "✅" if cache_hit_rwa else "❌"
                st.metric("Cache", cache_icon)

            # Afficher les RWA
            st.subheader("📊 RWA par Position")
            st.dataframe(rwa_df, use_container_width=True)

            # Statistiques
            st.subheader("📈 Analyse")
            col_a1, col_a2 = st.columns(2)

            with col_a1:
                st.markdown("**RWA par Classe d'Exposition**")
                rwa_by_class = rwa_df.groupby("exposure_class")["rwa_amount"].sum()
                st.bar_chart(rwa_by_class)

            with col_a2:
                st.markdown("**Distribution Densité RWA**")
                st.bar_chart(rwa_df["rwa_density"])

        except Exception as e:
            st.error(f"❌ Erreur lors du calcul : {e}")
            st.exception(e)
else:
    st.info("👈 Configurez les paramètres dans la barre latérale et cliquez sur **Calculer RWA**")

