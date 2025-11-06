"""Page Export (I8) - Export avancé multi-formats avec stubs COREP/LE/LCR."""

import streamlit as st

st.set_page_config(page_title="Export", page_icon="📥", layout="wide", initial_sidebar_state="expanded")

st.title("📥 Export Avancé (I8)")

st.markdown(
    """
Export multi-formats avec stubs COREP/LE/LCR.

Formats supportés : **XLSX**, **Parquet**, **CSV**, **JSON**
"""
)

# Paramètres du pipeline
st.subheader("1️⃣ Paramètres du Pipeline")

col1, col2 = st.columns(2)

with col1:
    num_positions = st.number_input(
        "Nombre de positions",
        min_value=10,
        max_value=100000,
        value=1000,
        step=100,
        help="Nombre de positions à générer via Monte Carlo",
    )

    seed = st.number_input(
        "Seed aléatoire",
        min_value=0,
        max_value=999999,
        value=42,
        step=1,
        help="Graine pour reproductibilité",
    )

with col2:
    cet1 = st.number_input(
        "CET1 (€M)",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        help="Common Equity Tier 1",
    )

    tier1 = st.number_input(
        "Tier 1 (€M)",
        min_value=0.0,
        value=1200.0,
        step=100.0,
        help="Tier 1 Capital",
    )

total_capital = st.number_input(
    "Total Capital (€M)",
    min_value=0.0,
    value=1500.0,
    step=100.0,
    help="Total Regulatory Capital",
)

leverage_exposure = st.number_input(
    "Leverage Exposure (€M)",
    min_value=0.0,
    value=10000.0,
    step=1000.0,
    help="Total Exposure for Leverage Ratio",
)

# Options d'export
st.subheader("2️⃣ Options d'Export")

col1, col2, col3 = st.columns(3)

with col1:
    export_format = st.selectbox(
        "Format",
        options=["xlsx", "parquet", "csv", "json"],
        index=0,
        help="Format d'export",
    )

with col2:
    compress = st.checkbox(
        "Compression",
        value=False,
        help="Activer la compression (gzip pour JSON, zip pour CSV)",
    )

with col3:
    include_corep_stubs = st.checkbox(
        "Inclure stubs COREP/LE/LCR",
        value=True,
        help="Inclure les templates réglementaires COREP/LE/LCR",
    )

# Bouton d'export
if st.button("🚀 Générer l'Export", type="primary", use_container_width=True):
    with st.spinner("Génération de l'export en cours..."):
        try:
            from app.adapters.legacy_compat import create_pipeline_export_advanced

            # Préparer les fonds propres
            own_funds = {
                "cet1": cet1,
                "tier1": tier1,
                "total": total_capital,
                "leverage_exposure": leverage_exposure,
            }

            # Générer l'export
            export_bytes = create_pipeline_export_advanced(
                num_positions=num_positions,
                seed=seed,
                own_funds=own_funds,
                config=None,
                format=export_format,
                compress=compress,
                include_corep_stubs=include_corep_stubs,
            )

            # Déterminer l'extension et le MIME type
            if export_format == "xlsx":
                file_ext = "xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif export_format == "parquet":
                file_ext = "parquet"
                mime_type = "application/octet-stream"
            elif export_format == "csv":
                file_ext = "zip" if compress else "csv"
                mime_type = "application/zip" if compress else "text/csv"
            elif export_format == "json":
                file_ext = "json.gz" if compress else "json"
                mime_type = "application/gzip" if compress else "application/json"
            else:
                file_ext = "bin"
                mime_type = "application/octet-stream"

            # Nom du fichier
            filename = f"banking_export_{export_format}"
            if include_corep_stubs:
                filename += "_corep"
            filename += f".{file_ext}"

            # Afficher les métriques
            st.success("✅ Export généré avec succès !")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Taille", f"{len(export_bytes) / 1024:.2f} KB")

            with col2:
                st.metric("Format", export_format.upper())

            with col3:
                st.metric("Compression", "Oui" if compress else "Non")

            # Bouton de téléchargement
            st.download_button(
                label=f"📥 Télécharger {filename}",
                data=export_bytes,
                file_name=filename,
                mime=mime_type,
                use_container_width=True,
            )

            # Informations supplémentaires
            st.info(
                f"""
**Détails de l'export** :
- **Positions** : {num_positions}
- **Seed** : {seed}
- **Format** : {export_format.upper()}
- **Compression** : {"Oui" if compress else "Non"}
- **Stubs COREP/LE/LCR** : {"Oui" if include_corep_stubs else "Non"}
"""
            )

        except Exception as e:
            st.error(f"❌ Erreur lors de la génération de l'export : {e}")
            st.exception(e)

# Documentation
st.subheader("📖 Documentation")

st.markdown(
    """
### Formats supportés

| Format | Description | Compression | Stubs COREP |
|--------|-------------|-------------|-------------|
| **XLSX** | Excel multi-onglets | Non | Oui |
| **Parquet** | Format colonnaire (Apache Arrow) | Gzip | Non |
| **CSV** | CSV simple ou ZIP multi-fichiers | ZIP | Oui (si ZIP) |
| **JSON** | JSON structuré | Gzip | Oui |

### Stubs COREP/LE/LCR

Les stubs réglementaires suivants sont inclus (si activé) :

- **COREP C34** : SA-CCR (contrepartie)
- **COREP C07** : Crédit (expositions)
- **COREP C08** : Crédit (RWA)
- **Leverage** : Leverage Ratio
- **LCR** : Liquidity Coverage Ratio

### Exemples d'utilisation

**Export Excel complet avec stubs COREP** :
1. Format : XLSX
2. Compression : Non
3. Stubs COREP : Oui
4. Cliquer sur "Générer l'Export"

**Export Parquet compressé pour analyse Big Data** :
1. Format : Parquet
2. Compression : Oui (gzip)
3. Stubs COREP : Non (non supporté en Parquet)
4. Cliquer sur "Générer l'Export"

**Export JSON complet pour API** :
1. Format : JSON
2. Compression : Oui (gzip)
3. Stubs COREP : Oui
4. Cliquer sur "Générer l'Export"
"""
)

