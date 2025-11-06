"""
Page ECL (IFRS 9) - I12.
Calcul Expected Credit Loss avec staging S1/S2/S3.
"""
import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="ECL (IFRS 9)",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Expected Credit Loss (IFRS 9)")
st.markdown("Calcul ECL avancé avec staging S1/S2/S3, PD term structures et LGD downturn.")

# ============================================================================
# Imports des services
# ============================================================================

try:
    from app.adapters.legacy_compat import (
        generate_exposures_advanced,
        list_scenario_overlays_advanced,
        compute_ecl_advanced_wrapper,
        create_scenario_overlay_advanced,
    )
except ImportError:
    st.error("❌ Erreur d'import des adaptateurs I12. Vérifiez que les modules sont installés.")
    st.stop()

# ============================================================================
# Sidebar - Configuration
# ============================================================================

st.sidebar.header("⚙️ Configuration ECL")

# 1. Sélection Run ID
run_id = st.sidebar.text_input(
    "Run ID",
    value="run_20251103_001",
    help="Identifiant du run d'expositions"
)

# 2. Sélection Scénario
st.sidebar.subheader("Scénario Overlay")

# Lister les scénarios existants
try:
    df_scenarios = list_scenario_overlays_advanced()
    
    if len(df_scenarios) > 0:
        scenario_options = df_scenarios['scenario_id'].tolist()
        scenario_id = st.sidebar.selectbox(
            "Scénario",
            options=scenario_options,
            help="Scénario de stress pour ECL"
        )
        
        # Afficher détails du scénario sélectionné
        scenario_row = df_scenarios[df_scenarios['scenario_id'] == scenario_id].iloc[0]
        st.sidebar.info(f"""
**{scenario_row['name']}**

{scenario_row.get('description', '')}

- PD Shift: {scenario_row.get('pd_shift', 0):.0f} bps
- Horizon: {scenario_row.get('horizon_months', 12)} mois
        """)
    else:
        st.sidebar.warning("Aucun scénario trouvé. Créez-en un ci-dessous.")
        scenario_id = "baseline"

except Exception as e:
    st.sidebar.error(f"Erreur lors du chargement des scénarios : {e}")
    scenario_id = "baseline"

# 3. Créer un nouveau scénario
with st.sidebar.expander("➕ Créer un nouveau scénario"):
    new_scenario_id = st.text_input("Scenario ID", value="stress_2025")
    new_scenario_name = st.text_input("Nom", value="Stress 2025")
    new_scenario_desc = st.text_area("Description", value="Scénario de stress macroéconomique 2025")
    
    col1, col2 = st.columns(2)
    with col1:
        pd_shift = st.number_input("PD Shift (bps)", value=50.0, step=10.0)
        sicr_abs = st.number_input("SICR Abs (bps)", value=100.0, step=10.0)
    with col2:
        horizon = st.number_input("Horizon (mois)", value=12, step=1, min_value=1, max_value=60)
        discount_rate = st.number_input("Taux Discount (%)", value=5.0, step=0.5)
    
    if st.button("Créer Scénario"):
        try:
            create_scenario_overlay_advanced(
                scenario_id=new_scenario_id,
                name=new_scenario_name,
                description=new_scenario_desc,
                pd_shift=pd_shift,
                sicr_threshold_abs=sicr_abs,
                horizon_months=horizon,
                discount_rate_value=discount_rate,
            )
            st.success(f"✅ Scénario '{new_scenario_name}' créé !")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

# 4. Paramètres avancés
with st.sidebar.expander("🔧 Paramètres Avancés"):
    use_cache = st.checkbox("Utiliser le cache", value=True)

# ============================================================================
# Main - Calcul ECL
# ============================================================================

st.header("📊 Calcul ECL")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(f"""
**Run ID** : `{run_id}`  
**Scénario** : `{scenario_id}`
    """)

with col2:
    if st.button("🚀 Calculer ECL", type="primary", use_container_width=True):
        st.session_state['ecl_calculated'] = True

# ============================================================================
# Résultats
# ============================================================================

if st.session_state.get('ecl_calculated', False):
    with st.spinner("⏳ Calcul ECL en cours..."):
        try:
            # Calculer ECL
            ecl_result, cache_hit = compute_ecl_advanced_wrapper(
                run_id=run_id,
                scenario_id=scenario_id,
                use_cache=use_cache,
            )
            
            # Badge cache
            if cache_hit:
                st.success("✅ Résultats chargés depuis le cache")
            else:
                st.info("🔄 Calcul effectué (résultats mis en cache)")
            
            # ================================================================
            # Onglets de résultats
            # ================================================================
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Vue d'ensemble",
                "📋 Par Exposition",
                "📈 Par Segment",
                "💾 Export"
            ])
            
            # ============================================================
            # Tab 1 : Vue d'ensemble
            # ============================================================
            with tab1:
                st.subheader("KPIs Globaux")
                
                df_totals = ecl_result['totals']
                stage_mix = ecl_result['stage_mix']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Total ECL",
                        f"{df_totals['Total ECL'].iloc[0]:,.2f} M€"
                    )
                
                with col2:
                    st.metric(
                        "Total EAD",
                        f"{df_totals['Total EAD'].iloc[0]:,.2f} M€"
                    )
                
                with col3:
                    st.metric(
                        "ECL Rate",
                        f"{df_totals['ECL Rate (%)'].iloc[0]:.2f}%"
                    )
                
                st.divider()
                
                # Stage Mix
                st.subheader("Distribution par Stage")
                
                col1, col2, col3 = st.columns(3)
                
                for i, (stage, data) in enumerate(sorted(stage_mix.items())):
                    col = [col1, col2, col3][i]
                    with col:
                        st.metric(
                            f"Stage {stage}",
                            f"{data['count']} expositions ({data['percentage']:.1f}%)",
                            delta=f"ECL: {data['ecl_amount']:,.2f} M€"
                        )
            
            # ============================================================
            # Tab 2 : Par Exposition
            # ============================================================
            with tab2:
                st.subheader("Résultats par Exposition")
                
                df_exp = ecl_result['by_exposure']
                
                st.dataframe(
                    df_exp[[
                        'exposure_id', 'stage', 'pd_12m', 'pd_lifetime',
                        'lgd', 'ead', 'ecl_amount', 'segment_id'
                    ]].head(100),
                    use_container_width=True,
                )
                
                st.caption(f"Affichage des 100 premières lignes sur {len(df_exp)} expositions.")
            
            # ============================================================
            # Tab 3 : Par Segment
            # ============================================================
            with tab3:
                st.subheader("Résultats par Segment")
                
                df_segment = ecl_result['by_segment']
                
                st.dataframe(
                    df_segment,
                    use_container_width=True,
                )
                
                # Graphique
                import plotly.express as px
                
                fig = px.bar(
                    df_segment,
                    x='segment_id',
                    y='ecl_amount',
                    color='stage',
                    title="ECL par Segment et Stage",
                    labels={'ecl_amount': 'ECL (M€)', 'segment_id': 'Segment'},
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # ============================================================
            # Tab 4 : Export
            # ============================================================
            with tab4:
                st.subheader("Export des Résultats")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export CSV
                    csv_exp = ecl_result['by_exposure'].to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV (Expositions)",
                        data=csv_exp,
                        file_name=f"ecl_exposures_{run_id}_{scenario_id}.csv",
                        mime="text/csv",
                    )
                
                with col2:
                    # Export CSV Segments
                    csv_seg = ecl_result['by_segment'].to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV (Segments)",
                        data=csv_seg,
                        file_name=f"ecl_segments_{run_id}_{scenario_id}.csv",
                        mime="text/csv",
                    )
        
        except Exception as e:
            st.error(f"❌ Erreur lors du calcul ECL : {e}")
            import traceback
            st.code(traceback.format_exc())

else:
    st.info("👆 Cliquez sur 'Calculer ECL' pour démarrer le calcul.")

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("💰 ECL (IFRS 9) - Banking Simulator v0.12.0")

