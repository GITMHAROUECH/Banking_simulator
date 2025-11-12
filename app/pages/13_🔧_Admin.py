"""Page Admin (I8b) - Historique exports."""
import streamlit as st

st.set_page_config(page_title="Admin", page_icon="🔧", layout="wide", initial_sidebar_state="expanded")
st.title("🔧 Admin - Historique des Exports")
try:
    from app.adapters.legacy_compat import list_artifacts_advanced
    artifacts_df = list_artifacts_advanced(limit=50)
    if not artifacts_df.empty:
        st.dataframe(artifacts_df, use_container_width=True)
    else:
        st.info("Aucun artifact trouvé")
except Exception as e:
    st.error(f"Erreur: {e}")
