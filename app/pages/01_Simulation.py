"""
Page Simulation - Génération des expositions bancaires.
"""
import uuid

import streamlit as st

from app.adapters.legacy_compat import generate_exposures_advanced

st.set_page_config(
    page_title="Simulation d'Expositions",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎲 Simulation d'Expositions Bancaires")
st.markdown(
    """
    Cette page permet de générer un portefeuille d'expositions bancaires avec tous les paramètres
    configurables. Un identifiant unique (run_id) sera créé pour permettre les calculs de risque
    dans les pages suivantes.
    """
)

# Afficher le run_id actuel si disponible
if 'selected_run_id' in st.session_state:
    st.info(f"ℹ️ Run ID actif : `{st.session_state['selected_run_id'][:16]}...`")

st.markdown("---")

# Formulaire de saisie des paramètres
with st.form("simulation_form"):
    st.subheader("📊 Paramètres de Génération")

    # Section : Run ID
    st.markdown("### 🆔 Identifiant de Simulation")
    col1, col2 = st.columns([2, 1])

    with col1:
        run_id_input = st.text_input(
            "Run ID (laisser vide pour générer automatiquement)",
            value="",
            placeholder="UUID auto-généré si vide",
            help="Identifiant unique pour cette simulation. Si laissé vide, un UUID sera généré automatiquement."
        )

    with col2:
        if st.form_submit_button("🎲 Générer UUID", use_container_width=True):
            st.session_state['temp_run_id'] = str(uuid.uuid4())
            st.rerun()

    # Afficher l'UUID généré temporairement
    if 'temp_run_id' in st.session_state:
        st.info(f"UUID généré : `{st.session_state['temp_run_id']}`")

    st.markdown("---")

    # Section : Composition du portefeuille
    st.markdown("### 📦 Composition du Portefeuille")

    col1, col2, col3 = st.columns(3)

    with col1:
        n_loans = st.number_input(
            "Nombre de prêts",
            min_value=0,
            max_value=100000,
            value=10000,
            step=1000,
            help="Nombre de lignes de prêts à générer"
        )

        n_bonds = st.number_input(
            "Nombre d'obligations",
            min_value=0,
            max_value=100000,
            value=5000,
            step=1000,
            help="Nombre d'obligations à générer"
        )

    with col2:
        n_deposits = st.number_input(
            "Nombre de dépôts",
            min_value=0,
            max_value=100000,
            value=15000,
            step=1000,
            help="Nombre de dépôts à générer"
        )

        n_derivatives = st.number_input(
            "Nombre de dérivés",
            min_value=0,
            max_value=100000,
            value=3000,
            step=1000,
            help="Nombre de contrats dérivés à générer"
        )

    with col3:
        n_off_bs = st.number_input(
            "Engagements hors-bilan",
            min_value=0,
            max_value=100000,
            value=2000,
            step=1000,
            help="Nombre d'engagements hors-bilan (garanties, lignes de crédit)"
        )

        n_equities = st.number_input(
            "Nombre d'actions",
            min_value=0,
            max_value=100000,
            value=1000,
            step=1000,
            help="Nombre de lignes d'actions à générer"
        )

    st.markdown("---")

    # Section : Paramètres de reproductibilité
    st.markdown("### 🔢 Reproductibilité")

    seed = st.number_input(
        "Graine aléatoire (seed)",
        min_value=0,
        max_value=999999,
        value=42,
        step=1,
        help="Graine pour le générateur aléatoire. Utiliser la même graine garantit des résultats identiques."
    )

    st.markdown("---")

    # Section : Fonds propres
    st.markdown("### 💰 Fonds Propres")
    st.markdown("Paramètres de fonds propres pour les calculs de ratios réglementaires.")

    col1, col2, col3 = st.columns(3)

    with col1:
        cet1 = st.number_input(
            "CET1 (M€)",
            min_value=0.0,
            value=1200.0,
            step=100.0,
            help="Common Equity Tier 1 en millions d'euros"
        )

    with col2:
        tier1 = st.number_input(
            "Tier 1 (M€)",
            min_value=0.0,
            value=1500.0,
            step=100.0,
            help="Tier 1 Capital en millions d'euros (doit être ≥ CET1)"
        )

    with col3:
        total_capital = st.number_input(
            "Total Capital (M€)",
            min_value=0.0,
            value=2000.0,
            step=100.0,
            help="Total Capital en millions d'euros (doit être ≥ Tier 1)"
        )

    st.markdown("---")

    # Bouton de soumission
    submitted = st.form_submit_button("🚀 Lancer la Simulation", type="primary", use_container_width=True)

# Traitement de la soumission du formulaire
if submitted:
    # Validation des fonds propres
    if tier1 < cet1:
        st.error("❌ Erreur de validation : Tier 1 doit être supérieur ou égal à CET1")
        st.stop()

    if total_capital < tier1:
        st.error("❌ Erreur de validation : Total Capital doit être supérieur ou égal à Tier 1")
        st.stop()

    # Déterminer le run_id
    if run_id_input:
        run_id = run_id_input
    elif 'temp_run_id' in st.session_state:
        run_id = st.session_state['temp_run_id']
    else:
        run_id = str(uuid.uuid4())

    # Sauvegarder le run_id dans session_state
    st.session_state['generated_run_id'] = run_id
    st.session_state['selected_run_id'] = run_id

    # Nettoyer l'UUID temporaire
    if 'temp_run_id' in st.session_state:
        del st.session_state['temp_run_id']

    # Construire la configuration
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

    # Lancer la génération
    with st.spinner("⏳ Génération des expositions en cours..."):
        try:
            df_exp, cache_hit = generate_exposures_advanced(
                run_id=run_id,
                config=config,
                seed=seed,
                use_cache=False  # Toujours générer pour une nouvelle simulation
            )

            st.success("✅ Simulation terminée avec succès !")

            # Afficher les informations du run
            st.markdown("---")
            st.header("📋 Résumé de la Simulation")

            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Run ID",
                    f"{run_id[:8]}...",
                    help=f"Identifiant complet : {run_id}"
                )

            with col2:
                st.metric(
                    "Total Expositions",
                    f"{len(df_exp):,}"
                )

            with col3:
                st.metric(
                    "Notionnel Total",
                    f"{df_exp['notional'].sum() / 1e6:,.2f} M€"
                )

            with col4:
                cache_icon = "✅" if cache_hit else "🆕"
                st.metric(
                    "Cache",
                    cache_icon,
                    delta="Utilisé" if cache_hit else "Nouveau"
                )

            # Breakdown par type de produit
            st.markdown("---")
            st.subheader("📊 Répartition par Type de Produit")

            breakdown = df_exp.groupby('product_type').agg({
                'notional': 'sum',
                'ead': 'sum',
            }).reset_index()

            breakdown['notional'] = breakdown['notional'].apply(lambda x: f"{x / 1e6:,.2f} M€")
            breakdown['ead'] = breakdown['ead'].apply(lambda x: f"{x / 1e6:,.2f} M€")
            breakdown['count'] = df_exp.groupby('product_type').size().values

            # Renommer les colonnes
            breakdown.columns = ['Type de Produit', 'Notionnel', 'EAD', 'Nombre']

            # Réordonner les colonnes
            breakdown = breakdown[['Type de Produit', 'Nombre', 'Notionnel', 'EAD']]

            st.dataframe(breakdown, use_container_width=True, hide_index=True)

            # Aperçu des expositions
            st.markdown("---")
            st.subheader("👁️ Aperçu des Expositions (100 premières lignes)")

            # Sélectionner les colonnes principales pour l'affichage
            display_columns = [
                'product_type', 'entity', 'currency', 'notional', 'ead',
                'exposure_class', 'counterparty_id', 'maturity_date'
            ]

            # Filtrer les colonnes disponibles
            available_columns = [col for col in display_columns if col in df_exp.columns]

            st.dataframe(df_exp[available_columns].head(100), use_container_width=True)

            # Informations sur la suite
            st.markdown("---")
            st.info(
                f"""
                ✅ **Run ID sauvegardé** : `{run_id}`

                Ce run_id a été enregistré dans votre session et dans la base de données.
                Vous pouvez maintenant l'utiliser dans les autres pages pour :

                - 💰 Calculer les **RWA** (Risk-Weighted Assets)
                - 🔁 Calculer le **SA-CCR** (Standardised Approach for Counterparty Credit Risk)
                - 💧 Calculer le **LCR** (Liquidity Coverage Ratio)
                - 📈 Calculer les **ratios de capital** (CET1, Tier 1, Total Capital, Leverage)
                - 🔄 Effectuer la **réconciliation** ledger vs risk
                - 📋 Générer le **reporting** COREP/FINREP

                Rendez-vous dans les pages correspondantes pour continuer !
                """
            )

        except Exception as e:
            st.error(f"❌ Erreur lors de la génération des expositions : {str(e)}")
            st.exception(e)
