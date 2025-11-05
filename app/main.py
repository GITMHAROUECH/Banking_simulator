"""
Point d'entrée principal de l'application Banking Simulator (I7a).

Ce module affiche la page d'accueil. Les autres pages sont dans app/pages/
et sont automatiquement détectées par Streamlit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# -- garantir la visibilité runtime des modules du projet --
ROOT = Path(__file__).resolve().parents[1]  # .../<racine_projet>
SRC = ROOT / "src"
for p in (ROOT, SRC):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


# Configuration de la page
st.set_page_config(
    page_title="Banking Simulator",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Page d'accueil principale."""
    st.title("🏦 Banking Simulator - v0.7.0 (I7a)")
    
    st.markdown(
        """
    ## Bienvenue dans Banking Simulator

    Cette application permet de simuler et analyser des portefeuilles bancaires
    selon les normes réglementaires **CRR3**.

    ### 🚀 Nouveautés I7a

    - **Pipeline E2E** : Orchestration complète Simulation → RWA → Liquidité → Capital → Export
    - **Cache intelligent** : Affichage du statut cache (✅/❌) dans toutes les pages
    - **13 pages Streamlit** : Navigation améliorée via la sidebar
    - **UX optimisée** : Spinners, toasts, validations de saisie

    ### 📋 Fonctionnalités disponibles

    Utilisez la **sidebar** pour naviguer entre les pages :

    1. **🚀 Pipeline** : Exécution complète du pipeline E2E
    2. **🎲 Monte Carlo** : Génération de positions bancaires
    3. **💰 RWA** : Risk-Weighted Assets (IRB + Standardisé)
    4. **💧 Liquidité** : LCR, NSFR, ALMM
    5. **📈 Capital** : Ratios CET1, Tier 1, Total Capital, Leverage
    6. **📥 Export** : Export Excel multi-onglets
    7. **🏦 Consolidation** : IFRS 10/11
    8. **📊 Analyse Portfolio** : Visualisations avancées
    9. **📋 Reporting** : Tableaux de bord
    10. **⚙️ Configuration** : Paramètres globaux
    11. **📖 Documentation** : Guide utilisateur
    12. **ℹ️ About** : À propos de l'application
    13. **🔧 Admin** : Administration

    ### 🏗️ Architecture refactorisée (I1-I7a)

    - ✅ **Domain Layer** : Logique métier pure
    - ✅ **Services Layer** : Orchestration + Cache (I6)
    - ✅ **Persistence Layer** : SQLite/PostgreSQL (I6)
    - ✅ **UI Layer** : 13 pages Streamlit (I7a)
    - ✅ **Tests** : 166 tests, couverture 96% (Domain), 87% (Services)
    - ✅ **Performance** : Cache 56x plus rapide (I6)

    ### 🎯 Commencez ici !

    1. Cliquez sur **🚀 Pipeline** dans la sidebar
    2. Configurez les paramètres (nombre de positions, seed, fonds propres)
    3. Cliquez sur **Lancer le Pipeline**
    4. Observez le statut du cache (✅/❌) pour chaque étape
    5. Téléchargez le rapport Excel complet

    ---

    **Version** : 0.7.0 (I7a)  
    **Date** : 28 octobre 2025  
    **Statut** : ✅ Opérationnel
    """
    )

    # Métriques globales
    st.subheader("📊 Métriques Globales")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pages", "13")

    with col2:
        st.metric("Tests", "166")

    with col3:
        st.metric("Couverture", "87%")

    with col4:
        st.metric("Gain Cache", "56x")


if __name__ == "__main__":
    main()

