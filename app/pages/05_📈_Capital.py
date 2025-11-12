"""Page Capital (I8b) - Calcul des ratios de capital."""

import streamlit as st

st.set_page_config(
    page_title="Capital",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 Ratios de Capital")

st.markdown(
    """
Calcul des ratios de capital réglementaires (CET1, Tier 1, Total Capital, Leverage).
"""
)

# Formulaire own_funds
st.subheader("1️⃣ Fonds Propres")

col1, col2 = st.columns(2)

with col1:
    cet1 = st.number_input(
        "CET1 (€M)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        help="Common Equity Tier 1 Capital",
    )

    tier1 = st.number_input(
        "Tier 1 (€M)",
        min_value=0.0,
        value=1200.0,
        step=100.0,
        help="Tier 1 Capital (CET1 + AT1)",
    )

with col2:
    total_capital = st.number_input(
        "Total Capital (€M)",
        min_value=0.0,
        value=1500.0,
        step=100.0,
        help="Total Regulatory Capital (Tier 1 + Tier 2)",
    )

    leverage_exposure = st.number_input(
        "Leverage Exposure (€M)",
        min_value=0.0,
        value=10000.0,
        step=1000.0,
        help="Total Exposure for Leverage Ratio",
    )

# RWA
st.subheader("2️⃣ RWA (Risk-Weighted Assets)")

total_rwa = st.number_input(
    "Total RWA (€M)",
    min_value=0.0,
    value=8000.0,
    step=500.0,
    help="Total Risk-Weighted Assets",
)

# Bouton de calcul
if st.button("🚀 Calculer les Ratios", type="primary", use_container_width=True):
    with st.spinner("Calcul des ratios en cours..."):
        try:
            # Préparer les fonds propres
            own_funds = {
                "cet1": cet1,
                "tier1": tier1,
                "total": total_capital,
                "leverage_exposure": leverage_exposure,
            }

            # Préparer les RWA (DataFrame minimal)
            import pandas as pd

            rwa_df = pd.DataFrame(
                {
                    "exposure_class": ["Corporate"],
                    "rwa": [total_rwa],
                }
            )

            # Appeler compute_capital via adaptateurs
            from app.adapters.legacy_compat import compute_capital_ratios_advanced

            ratios, cache_hit = compute_capital_ratios_advanced(rwa_df, own_funds)

            # Afficher le badge cache
            if cache_hit:
                st.success("✅ Résultats chargés depuis le cache")
            else:
                st.info("🔄 Calcul effectué (résultats sauvegardés en cache)")

            # Afficher les ratios
            st.subheader("3️⃣ Résultats")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                cet1_ratio = ratios.get("cet1_ratio", 0.0)
                st.metric(
                    "CET1 Ratio",
                    f"{cet1_ratio * 100:.2f}%",
                    delta="Seuil: 4.5%",
                    delta_color="normal" if cet1_ratio >= 0.045 else "inverse",
                )

            with col2:
                tier1_ratio = ratios.get("tier1_ratio", 0.0)
                st.metric(
                    "Tier 1 Ratio",
                    f"{tier1_ratio * 100:.2f}%",
                    delta="Seuil: 6.0%",
                    delta_color="normal" if tier1_ratio >= 0.06 else "inverse",
                )

            with col3:
                total_capital_ratio = ratios.get("total_capital_ratio", 0.0)
                st.metric(
                    "Total Capital Ratio",
                    f"{total_capital_ratio * 100:.2f}%",
                    delta="Seuil: 8.0%",
                    delta_color="normal" if total_capital_ratio >= 0.08 else "inverse",
                )

            with col4:
                leverage_ratio = ratios.get("leverage_ratio", 0.0)
                st.metric(
                    "Leverage Ratio",
                    f"{leverage_ratio * 100:.2f}%",
                    delta="Seuil: 3.0%",
                    delta_color="normal" if leverage_ratio >= 0.03 else "inverse",
                )

            # Détails
            st.subheader("4️⃣ Détails")

            details_df = pd.DataFrame(
                {
                    "Métrique": [
                        "CET1",
                        "Tier 1",
                        "Total Capital",
                        "Total RWA",
                        "Leverage Exposure",
                        "CET1 Ratio",
                        "Tier 1 Ratio",
                        "Total Capital Ratio",
                        "Leverage Ratio",
                    ],
                    "Valeur": [
                        f"{cet1:.2f} €M",
                        f"{tier1:.2f} €M",
                        f"{total_capital:.2f} €M",
                        f"{total_rwa:.2f} €M",
                        f"{leverage_exposure:.2f} €M",
                        f"{cet1_ratio * 100:.2f}%",
                        f"{tier1_ratio * 100:.2f}%",
                        f"{total_capital_ratio * 100:.2f}%",
                        f"{leverage_ratio * 100:.2f}%",
                    ],
                }
            )

            st.dataframe(details_df, use_container_width=True, hide_index=True)

        except KeyError as e:
            st.error(f"❌ Erreur : Clé manquante dans own_funds : {e}")
            st.info(
                """
**Valeurs d'exemple** :
- CET1 : 1000 €M
- Tier 1 : 1200 €M
- Total Capital : 1500 €M
- Leverage Exposure : 10000 €M
"""
            )
        except Exception as e:
            st.error(f"❌ Erreur lors du calcul des ratios : {e}")
            st.exception(e)

# Documentation
st.subheader("📖 Documentation")

st.markdown(
    """
### Formules

**CET1 Ratio** :
```
CET1 Ratio = CET1 / Total RWA
```

**Tier 1 Ratio** :
```
Tier 1 Ratio = Tier 1 / Total RWA
```

**Total Capital Ratio** :
```
Total Capital Ratio = Total Capital / Total RWA
```

**Leverage Ratio** :
```
Leverage Ratio = Tier 1 / Leverage Exposure
```

### Seuils Réglementaires (CRR3)

| Ratio | Seuil Minimum | Seuil Recommandé |
|-------|---------------|------------------|
| **CET1 Ratio** | 4.5% | 7.0% (avec buffers) |
| **Tier 1 Ratio** | 6.0% | 8.5% (avec buffers) |
| **Total Capital Ratio** | 8.0% | 10.5% (avec buffers) |
| **Leverage Ratio** | 3.0% | 3.0% |

### Exemples

**Exemple 1 : Banque bien capitalisée**
- CET1 : 1000 €M
- Tier 1 : 1200 €M
- Total Capital : 1500 €M
- Total RWA : 8000 €M
- Leverage Exposure : 10000 €M

**Résultats** :
- CET1 Ratio : 12.5% ✅
- Tier 1 Ratio : 15.0% ✅
- Total Capital Ratio : 18.75% ✅
- Leverage Ratio : 12.0% ✅

**Exemple 2 : Banque sous-capitalisée**
- CET1 : 300 €M
- Tier 1 : 400 €M
- Total Capital : 600 €M
- Total RWA : 8000 €M
- Leverage Exposure : 10000 €M

**Résultats** :
- CET1 Ratio : 3.75% ❌ (< 4.5%)
- Tier 1 Ratio : 5.0% ❌ (< 6.0%)
- Total Capital Ratio : 7.5% ❌ (< 8.0%)
- Leverage Ratio : 4.0% ✅
"""
)

