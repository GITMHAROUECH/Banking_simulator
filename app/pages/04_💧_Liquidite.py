"""
Page Liquidité - LCR, NSFR, ALMM (I7a).
"""
import streamlit as st

from src.services import run_simulation, compute_liquidity

st.set_page_config(page_title="Liquidité", page_icon="💧", layout="wide", initial_sidebar_state="expanded")

st.title("💧 Liquidité - LCR, NSFR, ALMM")
st.markdown("Calcul des ratios de liquidité réglementaires")

# Sidebar : Paramètres
st.sidebar.header("⚙️ Paramètres")

num_positions = st.sidebar.number_input(
    "Nombre de positions", min_value=10, max_value=10000, value=1000, step=100
)
seed = st.sidebar.number_input(
    "Seed", min_value=0, max_value=99999, value=42, step=1
)
use_cache = st.sidebar.checkbox("Utiliser le cache", value=True)

# Bouton d'exécution
if st.sidebar.button("💧 Calculer Liquidité", type="primary"):
    with st.spinner("⏳ Calcul de liquidité en cours..."):
        try:
            # Générer les positions
            positions_df, cache_hit_sim = run_simulation(
                num_positions=num_positions, seed=seed, use_cache=use_cache
            )

            # Calculer liquidité
            lcr_df, nsfr_df, almm, cache_hit_liq = compute_liquidity(
                positions_df, use_cache=use_cache
            )

            # Statut cache
            if cache_hit_liq:
                st.success("✅ Liquidité chargée depuis le cache")
            else:
                st.success("✅ Liquidité calculée avec succès")

            # Métriques LCR
            st.subheader("📊 Liquidity Coverage Ratio (LCR)")
            col1, col2, col3 = st.columns(3)

            with col1:
                lcr_ratio = lcr_df["lcr_ratio"].iloc[0] if not lcr_df.empty else 0
                st.metric("LCR Ratio", f"{lcr_ratio:.1f}%",
                         delta=f"{lcr_ratio - 100:.1f}% vs min 100%")

            with col2:
                hqla = lcr_df["total_hqla"].iloc[0] if not lcr_df.empty else 0
                st.metric("Total HQLA", f"{hqla:,.0f} M€")

            with col3:
                outflows = lcr_df["net_outflows"].iloc[0] if not lcr_df.empty else 0
                st.metric("Net Outflows 30j", f"{outflows:,.0f} M€")

            # Tableau LCR
            with st.expander("📋 Détail LCR par entité"):
                st.dataframe(lcr_df, use_container_width=True)

            # Métriques NSFR
            st.subheader("🏗️ Net Stable Funding Ratio (NSFR)")
            col1, col2, col3 = st.columns(3)

            with col1:
                nsfr_ratio = nsfr_df["nsfr_ratio"].iloc[0] if not nsfr_df.empty else 0
                st.metric("NSFR Ratio", f"{nsfr_ratio:.1f}%",
                         delta=f"{nsfr_ratio - 100:.1f}% vs min 100%")

            with col2:
                asf = nsfr_df["asf"].iloc[0] if not nsfr_df.empty else 0
                st.metric("ASF", f"{asf:,.0f} M€")

            with col3:
                rsf = nsfr_df["rsf"].iloc[0] if not nsfr_df.empty else 0
                st.metric("RSF", f"{rsf:,.0f} M€")

            # Tableau NSFR
            with st.expander("📋 Détail NSFR par entité"):
                st.dataframe(nsfr_df, use_container_width=True)

            # ALMM
            st.subheader("⏰ Asset Liability Maturity Mismatch (ALMM)")
            if almm is not None and not almm.empty:
                st.dataframe(almm, use_container_width=True)
            else:
                st.info("Données ALMM non disponibles")

        except Exception as e:
            st.error(f"❌ Erreur: {e}")
            import traceback
            st.code(traceback.format_exc())
else:
    st.info("👈 Configurez les paramètres et cliquez sur 'Calculer Liquidité'")
