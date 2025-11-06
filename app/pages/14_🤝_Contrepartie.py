"""
Page Contrepartie - SA-CCR & CVA (I7c).
"""
import json

import numpy as np
import pandas as pd
import streamlit as st

from src.services.risk_service import compute_counterparty_risk

st.set_page_config(page_title="Contrepartie", page_icon="🔁", layout="wide", initial_sidebar_state="expanded")

st.title("🔁 Risque de Contrepartie (SA-CCR & CVA)")
st.markdown(
    "Calcul du **risque de contrepartie** : **SA-CCR** (EAD) + **CVA** (capital BA-CVA + pricing v1)"
)

# Sidebar : Paramètres
st.sidebar.header("⚙️ Paramètres")

# Option 1 : Upload fichier
st.sidebar.subheader("Option 1 : Upload Fichier")
uploaded_file = st.sidebar.file_uploader(
    "Upload trades (CSV/XLSX)", type=["csv", "xlsx"], key="upload_trades"
)

# Option 2 : Génération démo
st.sidebar.subheader("Option 2 : Génération Démo")
num_trades = st.sidebar.number_input(
    "Nombre de trades", min_value=10, max_value=20000, value=100, step=10
)
seed_demo = st.sidebar.number_input("Seed", min_value=0, max_value=99999, value=42, step=1)

# Paramètres SA-CCR
st.sidebar.markdown("---")
st.sidebar.subheader("Paramètres SA-CCR")
alpha = st.sidebar.number_input("Alpha", min_value=1.0, max_value=2.0, value=1.4, step=0.1)

# Paramètres CVA
st.sidebar.markdown("---")
st.sidebar.subheader("Paramètres CVA")
enable_cva_pricing = st.sidebar.checkbox("Activer CVA Pricing v1", value=False)
recovery_rate = st.sidebar.number_input(
    "Recovery Rate", min_value=0.0, max_value=1.0, value=0.4, step=0.1
)
risk_free_rate = st.sidebar.number_input(
    "Taux sans risque", min_value=0.0, max_value=0.1, value=0.02, step=0.01
)

use_cache = st.sidebar.checkbox("Utiliser le cache", value=True)


def generate_demo_trades(num_trades: int, seed: int) -> pd.DataFrame:
    """Génère un portefeuille de trades démo."""
    np.random.seed(seed)

    asset_classes = ["IR", "FX", "Equity", "Commodity", "Credit"]
    maturity_buckets = ["0-1Y", "1-5Y", ">5Y"]
    ratings = ["IG", "HY"]

    trades = []
    for i in range(num_trades):
        asset_class = np.random.choice(asset_classes)

        trade = {
            "trade_id": f"T{i+1:05d}",
            "netting_set": f"NS{np.random.randint(1, 11):02d}",  # 10 netting sets
            "asset_class": asset_class,
            "notional": np.random.uniform(100000, 10000000),
            "maturity_bucket": np.random.choice(maturity_buckets),
            "rating": np.random.choice(ratings),
            "mtm": np.random.uniform(-100000, 100000),
        }

        trades.append(trade)

    return pd.DataFrame(trades)


# Bouton de calcul
if st.sidebar.button("🔁 Calculer Risque Contrepartie", type="primary"):
    # Charger ou générer les trades
    if uploaded_file is not None:
        # Charger depuis fichier
        if uploaded_file.name.endswith(".csv"):
            trades_df = pd.read_csv(uploaded_file)
        else:
            trades_df = pd.read_excel(uploaded_file)

        st.info(f"✅ Fichier chargé : {len(trades_df)} trades")
    else:
        # Générer démo
        trades_df = generate_demo_trades(num_trades, seed_demo)
        st.info(f"✅ Portefeuille démo généré : {len(trades_df)} trades")

    # Validation
    required_cols = ["trade_id", "netting_set", "asset_class", "notional", "mtm"]
    missing_cols = [col for col in required_cols if col not in trades_df.columns]

    if missing_cols:
        st.error(f"❌ Colonnes manquantes : {missing_cols}")
        st.stop()

    # Paramètres
    params = {
        "alpha": alpha,
        "enable_cva_pricing": enable_cva_pricing,
        "cva_params": {
            "recovery_rate": recovery_rate,
            "risk_free_rate": risk_free_rate,
        },
    }

    # Calcul Risque Contrepartie
    with st.spinner("⏳ Calcul du risque de contrepartie en cours..."):
        try:
            result, cache_hit = compute_counterparty_risk(
                trades_df, collateral_df=None, params=params, use_cache=use_cache
            )

            # Afficher le statut du cache
            if cache_hit:
                st.success("✅ Résultats chargés depuis le cache")
            else:
                st.success("✅ Risque de contrepartie calculé avec succès")

            # Métriques globales
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                ead_total = result["saccr"]["ead_df"]["ead_contribution"].sum()
                st.metric("EAD Total", f"{ead_total:,.0f} €")

            with col2:
                rwa_total = result["saccr"]["rwa"]
                st.metric("RWA SA-CCR", f"{rwa_total:,.0f} €")

            with col3:
                k_cva = result["cva_capital"]["k_cva"]
                st.metric("K_CVA (Capital)", f"{k_cva:,.0f} €")

            with col4:
                if result["cva_pricing"] is not None:
                    cva_pricing = result["cva_pricing"]["cva"]
                    st.metric("CVA Pricing", f"{cva_pricing:,.0f} €")
                else:
                    st.metric("CVA Pricing", "N/A")

            with col5:
                cache_icon = "✅" if cache_hit else "❌"
                st.metric("Cache", cache_icon)

            # Onglets de résultats
            tabs = ["📊 SA-CCR", "💰 CVA Capital", "📈 CVA Pricing", "📥 Export"]
            tab_objects = st.tabs(tabs)

            # Onglet 1 : SA-CCR
            with tab_objects[0]:
                st.subheader("SA-CCR (Standardized Approach for Counterparty Credit Risk)")

                # Métriques SA-CCR
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)

                with col_s1:
                    st.metric("RC", f"{result['saccr']['rc']:,.0f} €")

                with col_s2:
                    st.metric("PFE", f"{result['saccr']['pfe']:,.0f} €")

                with col_s3:
                    st.metric("Multiplier", f"{result['saccr']['multiplier']:.4f}")

                with col_s4:
                    st.metric("Alpha", f"{result['saccr']['alpha']:.2f}")

                # EAD par trade
                st.markdown("**EAD par Trade**")
                st.dataframe(result["saccr"]["ead_df"], use_container_width=True)

                # Add-ons PFE
                st.markdown("**Add-ons PFE par Classe d'Actifs**")
                addons = result["saccr"]["pfe_addons"]
                addons_df = pd.DataFrame(
                    {
                        "Classe d'Actifs": list(addons.keys()),
                        "Add-on PFE": list(addons.values()),
                    }
                )
                st.bar_chart(addons_df.set_index("Classe d'Actifs")["Add-on PFE"])

            # Onglet 2 : CVA Capital
            with tab_objects[1]:
                st.subheader("CVA Capital (BA-CVA - Basic Approach)")

                # Métriques CVA Capital
                st.metric("K_CVA (Capital CVA)", f"{result['cva_capital']['k_cva']:,.0f} €")

                # Détails par contrepartie
                st.markdown("**Détails par Contrepartie**")
                st.dataframe(
                    result["cva_capital"]["by_counterparty"], use_container_width=True
                )

                # Formule
                st.markdown("**Formule BA-CVA**")
                st.latex(r"K_{CVA} = 2.33 \times \sqrt{\sum_i (w_i \times M_i \times EAD_i)^2}")

            # Onglet 3 : CVA Pricing
            with tab_objects[2]:
                st.subheader("CVA Pricing v1 (Simplified)")

                if result["cva_pricing"] is not None:
                    # Métriques CVA Pricing
                    st.metric("CVA Pricing", f"{result['cva_pricing']['cva']:,.0f} €")

                    # Détails par bucket
                    st.markdown("**Détails par Bucket de Temps**")
                    st.dataframe(
                        result["cva_pricing"]["by_bucket"], use_container_width=True
                    )

                    # Graphique
                    st.markdown("**CVA Contribution par Bucket**")
                    st.line_chart(
                        result["cva_pricing"]["by_bucket"].set_index("time")[
                            "cva_contribution"
                        ]
                    )

                    # Formule
                    st.markdown("**Formule CVA Pricing**")
                    st.latex(
                        r"CVA \approx (1-R) \times \sum_t DF(t) \times \Delta PD(t) \times EE(t)"
                    )
                else:
                    st.info(
                        "CVA Pricing désactivé. Cochez **Activer CVA Pricing v1** dans la sidebar."
                    )

            # Onglet 4 : Export
            with tab_objects[3]:
                st.subheader("Export Résultats")

                # Export SA-CCR EAD
                st.markdown("**Export SA-CCR EAD (CSV)**")
                csv_ead = result["saccr"]["ead_df"].to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger SA-CCR EAD (CSV)",
                    data=csv_ead,
                    file_name=f"saccr_ead_{len(trades_df)}trades.csv",
                    mime="text/csv",
                )

                # Export CVA Capital
                st.markdown("**Export CVA Capital (CSV)**")
                csv_cva_capital = result["cva_capital"]["by_counterparty"].to_csv(
                    index=False
                )
                st.download_button(
                    label="📥 Télécharger CVA Capital (CSV)",
                    data=csv_cva_capital,
                    file_name=f"cva_capital_{len(trades_df)}trades.csv",
                    mime="text/csv",
                )

                # Export CVA Pricing (si activé)
                if result["cva_pricing"] is not None:
                    st.markdown("**Export CVA Pricing (CSV)**")
                    csv_cva_pricing = result["cva_pricing"]["by_bucket"].to_csv(
                        index=False
                    )
                    st.download_button(
                        label="📥 Télécharger CVA Pricing (CSV)",
                        data=csv_cva_pricing,
                        file_name=f"cva_pricing_{len(trades_df)}trades.csv",
                        mime="text/csv",
                    )

                # Export JSON global
                st.markdown("**Export Résultats Complets (JSON)**")

                # Préparer le dict pour JSON (sans DataFrames)
                export_dict = {
                    "saccr": {
                        "ead_total": float(ead_total),
                        "rc": float(result["saccr"]["rc"]),
                        "pfe": float(result["saccr"]["pfe"]),
                        "multiplier": float(result["saccr"]["multiplier"]),
                        "alpha": float(result["saccr"]["alpha"]),
                        "rwa": float(result["saccr"]["rwa"]),
                        "k": float(result["saccr"]["k"]),
                        "pfe_addons": {
                            k: float(v) for k, v in result["saccr"]["pfe_addons"].items()
                        },
                    },
                    "cva_capital": {"k_cva": float(result["cva_capital"]["k_cva"])},
                    "cva_pricing": (
                        {"cva": float(result["cva_pricing"]["cva"])}
                        if result["cva_pricing"] is not None
                        else None
                    ),
                }

                json_export = json.dumps(export_dict, indent=2)
                st.download_button(
                    label="📥 Télécharger Résultats Complets (JSON)",
                    data=json_export,
                    file_name=f"counterparty_risk_{len(trades_df)}trades.json",
                    mime="application/json",
                )

        except Exception as e:
            st.error(f"❌ Erreur lors du calcul : {e}")
            st.exception(e)
else:
    st.info(
        "👈 Configurez les paramètres dans la barre latérale et cliquez sur **Calculer Risque Contrepartie**"
    )

    # Afficher un exemple de format de fichier
    st.subheader("📋 Format de Fichier Attendu")

    example_df = pd.DataFrame(
        {
            "trade_id": ["T00001", "T00002", "T00003"],
            "netting_set": ["NS01", "NS01", "NS02"],
            "asset_class": ["IR", "FX", "Equity"],
            "notional": [1000000, 500000, 750000],
            "maturity_bucket": ["1-5Y", "0-1Y", ">5Y"],
            "rating": ["IG", "HY", "IG"],
            "mtm": [10000, -5000, 2000],
        }
    )

    st.dataframe(example_df, use_container_width=True)

    st.markdown(
        """
    **Colonnes obligatoires** :
    - `trade_id` : Identifiant unique du trade
    - `netting_set` : Identifiant du netting set (CSA)
    - `asset_class` : Classe d'actifs (`IR`, `FX`, `Equity`, `Commodity`, `Credit`)
    - `notional` : Notionnel du trade
    - `mtm` : Mark-to-Market (positif = créance, négatif = dette)

    **Colonnes optionnelles** :
    - `maturity_bucket` : Bucket de maturité pour IR (`0-1Y`, `1-5Y`, `>5Y`)
    - `rating` : Rating pour Credit (`IG` = Investment Grade, `HY` = High Yield)
    """
    )

