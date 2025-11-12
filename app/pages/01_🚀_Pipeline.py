"""
Page Pipeline E2E - Orchestration complète avec run_id (I11).
"""
import uuid

import streamlit as st

from app.adapters.legacy_compat import (
    generate_exposures_advanced,
    compute_rwa_from_run_advanced,
    compute_saccr_from_run_advanced,
    compute_lcr_from_run_advanced,
    compute_capital_ratios_from_run_advanced,
    reconcile_ledger_vs_risk_advanced,
    create_corep_finrep_stubs_advanced,
)

st.set_page_config(page_title="Pipeline E2E", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.title("🚀 Pipeline E2E - Orchestration Complète (I11)")
st.markdown(
    "Exécutez le pipeline complet avec **run_id** : **Génération Exposures → Risques → Réconciliation → COREP/FINREP**"
)

# Sidebar : Paramètres
st.sidebar.header("⚙️ Paramètres Pipeline")

# Mode : Legacy ou Run ID
mode = st.sidebar.radio(
    "Mode d'exécution",
    ["Run ID (I11)", "Legacy (I1-I8)"],
    index=0,
    help="Run ID : Nouvelle architecture centrée sur exposures. Legacy : Ancien workflow."
)

if mode == "Run ID (I11)":
    st.sidebar.markdown("### 🆔 Run ID")
    
    # Générer ou saisir run_id
    use_existing_run = st.sidebar.checkbox("Utiliser un run_id existant", value=False)
    
    if use_existing_run:
        run_id = st.sidebar.text_input("Run ID", value="", placeholder="Saisir un UUID")
    else:
        if 'generated_run_id' not in st.session_state:
            st.session_state.generated_run_id = str(uuid.uuid4())
        run_id = st.session_state.generated_run_id
        st.sidebar.info(f"Run ID généré : `{run_id[:8]}...`")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📦 Génération Exposures")
    
    n_loans = st.sidebar.number_input("Nombre de prêts", min_value=0, max_value=50000, value=10000, step=1000)
    n_bonds = st.sidebar.number_input("Nombre d'obligations", min_value=0, max_value=50000, value=5000, step=1000)
    n_deposits = st.sidebar.number_input("Nombre de dépôts", min_value=0, max_value=50000, value=15000, step=1000)
    n_derivatives = st.sidebar.number_input("Nombre de dérivés", min_value=0, max_value=50000, value=3000, step=1000)
    n_off_bs = st.sidebar.number_input("Nombre d'engagements hors-bilan", min_value=0, max_value=50000, value=2000, step=1000)
    n_equities = st.sidebar.number_input("Nombre d'actions", min_value=0, max_value=50000, value=1000, step=1000)
    
    seed = st.sidebar.number_input("Seed (reproductibilité)", min_value=0, max_value=99999, value=42, step=1)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Fonds Propres")
    
    cet1 = st.sidebar.number_input("CET1 (M€)", min_value=0.0, value=1200.0, step=100.0)
    tier1 = st.sidebar.number_input("Tier 1 (M€)", min_value=0.0, value=1500.0, step=100.0)
    total_capital = st.sidebar.number_input("Total Capital (M€)", min_value=0.0, value=2000.0, step=100.0)
    
    use_cache = st.sidebar.checkbox("Utiliser le cache", value=True)
    
    # Bouton d'exécution
    if st.sidebar.button("🚀 Lancer le Pipeline E2E", type="primary"):
        # Validation
        if tier1 < cet1:
            st.error("❌ Tier 1 doit être ≥ CET1")
            st.stop()
        
        if total_capital < tier1:
            st.error("❌ Total Capital doit être ≥ Tier 1")
            st.stop()
        
        if not run_id:
            st.error("❌ Run ID manquant")
            st.stop()
        
        # Configuration
        config = {
            'n_loans': n_loans,
            'n_bonds': n_bonds,
            'n_deposits': n_deposits,
            'n_derivatives': n_derivatives,
            'n_off_bs': n_off_bs,
            'n_equities': n_equities,
            'entities': ['EU', 'US', 'CN'],
            'currencies': ['EUR', 'USD', 'CNY'],
        }
        
        params_capital = {
            'cet1_capital': cet1,
            'tier1_capital': tier1,
            'total_capital': total_capital,
        }
        
        # Exécution du pipeline
        with st.spinner("⏳ Exécution du pipeline E2E en cours..."):
            try:
                # 1. Génération exposures
                st.info("1️⃣ Génération des exposures...")
                df_exp, cache_hit_exp = generate_exposures_advanced(run_id, config, seed, use_cache)
                
                # 2. Calcul RWA
                st.info("2️⃣ Calcul RWA...")
                rwa_result, cache_hit_rwa = compute_rwa_from_run_advanced(run_id, use_cache=use_cache)
                
                # 3. Calcul SA-CCR
                st.info("3️⃣ Calcul SA-CCR...")
                saccr_result, cache_hit_saccr = compute_saccr_from_run_advanced(run_id, use_cache=use_cache)
                
                # 4. Calcul LCR
                st.info("4️⃣ Calcul LCR...")
                lcr_result, cache_hit_lcr = compute_lcr_from_run_advanced(run_id, use_cache=use_cache)
                
                # 5. Calcul ratios de capital
                st.info("5️⃣ Calcul ratios de capital...")
                capital_result, cache_hit_capital = compute_capital_ratios_from_run_advanced(run_id, params_capital, use_cache=use_cache)
                
                # 6. Réconciliation
                st.info("6️⃣ Réconciliation ledger vs risk...")
                recon_result = reconcile_ledger_vs_risk_advanced(run_id)
                
                # 7. Pré-remplissage COREP/FINREP
                st.info("7️⃣ Pré-remplissage COREP/FINREP...")
                corep_finrep = create_corep_finrep_stubs_advanced(run_id)
                
                st.success("✅ Pipeline E2E exécuté avec succès !")
                
                # Afficher les cache hits
                st.markdown("### 📊 Cache Hits")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    icon = "✅" if cache_hit_exp else "❌"
                    st.metric("Exposures", icon, delta="Cache" if cache_hit_exp else "Calcul")
                
                with col2:
                    icon = "✅" if cache_hit_rwa else "❌"
                    st.metric("RWA", icon, delta="Cache" if cache_hit_rwa else "Calcul")
                
                with col3:
                    icon = "✅" if cache_hit_saccr else "❌"
                    st.metric("SA-CCR", icon, delta="Cache" if cache_hit_saccr else "Calcul")
                
                with col4:
                    icon = "✅" if cache_hit_lcr else "❌"
                    st.metric("LCR", icon, delta="Cache" if cache_hit_lcr else "Calcul")
                
                with col5:
                    icon = "✅" if cache_hit_capital else "❌"
                    st.metric("Capital", icon, delta="Cache" if cache_hit_capital else "Calcul")
                
                # Onglets de résultats
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    "📦 Exposures",
                    "💰 RWA",
                    "🔁 SA-CCR",
                    "💧 LCR",
                    "📈 Capital",
                    "🔄 Réconciliation",
                    "📋 COREP/FINREP"
                ])
                
                with tab1:
                    st.subheader("📦 Exposures Générées")
                    st.metric("Total Exposures", f"{len(df_exp):,}")
                    st.metric("Total Notional", f"{df_exp['notional'].sum() / 1e6:.2f} M€")
                    
                    # Breakdown par produit
                    st.markdown("#### Breakdown par Produit")
                    breakdown = df_exp.groupby('product_type').agg({
                        'notional': 'sum',
                        'ead': 'sum',
                    }).reset_index()
                    st.dataframe(breakdown, use_container_width=True)
                    
                    # Aperçu
                    st.markdown("#### Aperçu des Exposures")
                    st.dataframe(df_exp.head(100), use_container_width=True)
                
                with tab2:
                    st.subheader("💰 RWA - Risk-Weighted Assets")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total EAD", f"{rwa_result['total_ead'] / 1e6:.2f} M€")
                    with col2:
                        st.metric("Total RWA", f"{rwa_result['total_rwa'] / 1e6:.2f} M€")
                    with col3:
                        st.metric("RWA Density", f"{rwa_result['rwa_density']:.2%}")
                    
                    st.markdown("#### RWA par Classe d'Exposition")
                    st.json(rwa_result['by_exposure_class'])
                
                with tab3:
                    st.subheader("🔁 SA-CCR - Standardised Approach for Counterparty Credit Risk")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total EAD", f"{saccr_result.get('total_ead', 0) / 1e6:.2f} M€")
                    with col2:
                        st.metric("RC (Replacement Cost)", f"{saccr_result.get('rc', 0) / 1e6:.2f} M€")
                    with col3:
                        st.metric("PFE (Potential Future Exposure)", f"{saccr_result.get('pfe', 0) / 1e6:.2f} M€")
                
                with tab4:
                    st.subheader("💧 LCR - Liquidity Coverage Ratio")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("HQLA", f"{lcr_result['hqla'] / 1e6:.2f} M€")
                    with col2:
                        st.metric("Net Cash Outflows", f"{lcr_result['net_cash_outflows'] / 1e6:.2f} M€")
                    with col3:
                        compliant_icon = "✅" if lcr_result['compliant'] else "❌"
                        st.metric("LCR Ratio", f"{lcr_result['lcr_ratio']:.2f}%", delta=compliant_icon)
                
                with tab5:
                    st.subheader("📈 Ratios de Capital")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        compliant_icon = "✅" if capital_result['cet1_compliant'] else "❌"
                        st.metric("CET1 Ratio", f"{capital_result['cet1_ratio']:.2f}%", delta=compliant_icon)
                    
                    with col2:
                        compliant_icon = "✅" if capital_result['tier1_compliant'] else "❌"
                        st.metric("Tier 1 Ratio", f"{capital_result['tier1_ratio']:.2f}%", delta=compliant_icon)
                    
                    with col3:
                        compliant_icon = "✅" if capital_result['total_compliant'] else "❌"
                        st.metric("Total Ratio", f"{capital_result['total_ratio']:.2f}%", delta=compliant_icon)
                    
                    with col4:
                        compliant_icon = "✅" if capital_result['leverage_compliant'] else "❌"
                        st.metric("Leverage Ratio", f"{capital_result['leverage_ratio']:.2f}%", delta=compliant_icon)
                
                with tab6:
                    st.subheader("🔄 Réconciliation Ledger vs Risk")
                    
                    summary = recon_result['summary']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Ledger", f"{summary['total_ledger'] / 1e6:.2f} M€")
                    with col2:
                        st.metric("Total Risk EAD", f"{summary['total_risk_ead'] / 1e6:.2f} M€")
                    with col3:
                        status_icon = "✅" if summary['reconciliation_status'] == 'OK' else "❌"
                        st.metric("Statut", summary['reconciliation_status'], delta=status_icon)
                    
                    st.markdown("#### Détails des Écarts")
                    st.dataframe(recon_result['details'], use_container_width=True)
                
                with tab7:
                    st.subheader("📋 COREP/FINREP Stubs")
                    
                    # Sous-onglets pour chaque rapport
                    subtab1, subtab2, subtab3, subtab4, subtab5, subtab6, subtab7 = st.tabs([
                        "COREP C34", "COREP C07", "COREP C08", "COREP Leverage", "COREP LCR", "FINREP F01", "FINREP F18"
                    ])
                    
                    with subtab1:
                        st.markdown("##### COREP C34 - Standardised Approach")
                        st.dataframe(corep_finrep['corep_c34'], use_container_width=True)
                    
                    with subtab2:
                        st.markdown("##### COREP C07 - IRB Approach by PD Scale")
                        st.dataframe(corep_finrep['corep_c07'], use_container_width=True)
                    
                    with subtab3:
                        st.markdown("##### COREP C08 - IRB Approach by Portfolio")
                        st.dataframe(corep_finrep['corep_c08'], use_container_width=True)
                    
                    with subtab4:
                        st.markdown("##### COREP Leverage Ratio")
                        st.dataframe(corep_finrep['corep_leverage'], use_container_width=True)
                    
                    with subtab5:
                        st.markdown("##### COREP LCR")
                        st.dataframe(corep_finrep['corep_lcr'], use_container_width=True)
                    
                    with subtab6:
                        st.markdown("##### FINREP F01 - Balance Sheet Assets")
                        st.dataframe(corep_finrep['finrep_f01'], use_container_width=True)
                    
                    with subtab7:
                        st.markdown("##### FINREP F18 - Breakdown of Loans")
                        st.dataframe(corep_finrep['finrep_f18'], use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'exécution du pipeline : {str(e)}")
                st.exception(e)

else:
    # Mode Legacy (I1-I8)
    st.info("Mode Legacy : Utilisez l'ancien workflow I1-I8 (à implémenter si nécessaire)")
    st.markdown("Ce mode utilise l'ancienne architecture sans run_id.")

