"""
Page Documentation (I7a).
"""
import streamlit as st

st.set_page_config(page_title="Documentation", page_icon="ℹ️", layout="wide", initial_sidebar_state="expanded")

st.title("ℹ️ Documentation Banking Simulator")
st.markdown("Guide complet d'utilisation et référence technique")

# Navigation
tabs = st.tabs([
    "🚀 Démarrage Rapide",
    "📋 Architecture",
    "📊 Méthodologies",
    "🔧 Configuration",
    "⚠️ Limitations",
    "📚 Références"
])

# Tab 1: Démarrage Rapide
with tabs[0]:
    st.markdown("""
    ## 🚀 Démarrage Rapide

    ### 1️⃣ Première utilisation

    Pour commencer avec Banking Simulator :

    1. **Page Pipeline** (🚀 Pipeline)
       - Configurez le nombre de positions (ex: 1000)
       - Définissez un seed pour la reproductibilité (ex: 42)
       - Cliquez sur "Lancer le Pipeline"
       - Téléchargez le rapport Excel complet

    2. **Exploration des résultats**
       - **💰 RWA** : Consultez les actifs pondérés par le risque
       - **💧 Liquidité** : Analysez les ratios LCR et NSFR
       - **🏛️ Capital** : Vérifiez les ratios de capital réglementaires
       - **📈 Reporting** : Visualisez les rapports COREP/FINREP

    ### 2️⃣ Workflow typique

    ```
    Pipeline → RWA → Liquidité → Capital → Reporting → Export
    ```

    ### 3️⃣ Cache intelligent

    - Le système met en cache les résultats basés sur les paramètres
    - Statut cache visible : ✅ (hit) ou ❌ (miss)
    - Gain de performance : jusqu'à 56x plus rapide
    - Stockage : Base de données SQLite/PostgreSQL

    ### 4️⃣ Export des résultats

    - **Format** : Excel multi-onglets (.xlsx)
    - **Contenu** : Positions, RWA, LCR, NSFR, Capital, COREP, FINREP
    - **Téléchargement** : Bouton direct dans chaque page
    """)

# Tab 2: Architecture
with tabs[1]:
    st.markdown("""
    ## 📋 Architecture Technique

    ### 🏗️ Architecture 3-Layer

    ```
    UI Layer (Streamlit)
         ↓
    Services Layer (Orchestration + Cache)
         ↓
    Domain Layer (Logique Métier Pure)
         ↓
    Persistence Layer (SQLite/PostgreSQL)
    ```

    ### 📦 Modules Principaux

    #### Domain Layer (`src/domain/`)
    - **monte_carlo.py** : Génération positions (Monte Carlo)
    - **rwa.py** : Calculs RWA (IRB Foundation + Standardized)
    - **saccr.py** : SA-CCR pour dérivés OTC
    - **lcr.py** : Liquidity Coverage Ratio
    - **nsfr.py** : Net Stable Funding Ratio
    - **capital.py** : Ratios CET1, Tier 1, Total Capital
    - **ifrs9.py** : Expected Credit Loss (ECL)
    - **reporting/corep.py** : Templates COREP (C07, C08, C34)
    - **reporting/finrep.py** : Templates FINREP (F09, F18)

    #### Services Layer (`src/services/`)
    - **simulation_service.py** : Orchestration simulation
    - **risk_service.py** : Orchestration calculs de risque
    - **reporting_service.py** : Génération rapports
    - **persistence_service.py** : Cache + DB
    - **pipeline_service.py** : Pipeline E2E

    #### UI Layer (`app/`)
    - **main.py** : Point d'entrée Streamlit
    - **pages/*.py** : 15 pages multi-page

    ### 🗄️ Base de Données

    **Tables principales :**
    - `exposures` : Positions bancaires (36k+ lignes par run)
    - `rwa_results` : Résultats RWA
    - `lcr_results` : Résultats LCR
    - `nsfr_results` : Résultats NSFR
    - `capital_results` : Ratios de capital
    - `pipeline_runs` : Métadonnées des runs
    - `corep_reports` : Rapports COREP
    - `finrep_reports` : Rapports FINREP

    **Run-ID Architecture :**
    - Chaque exécution = UUID unique (`run_id`)
    - Traçabilité complète : exposures → risques → rapports
    - Audit trail complet
    """)

# Tab 3: Méthodologies
with tabs[2]:
    st.markdown("""
    ## 📊 Méthodologies Réglementaires

    ### 💰 Risk-Weighted Assets (RWA)

    **Approche IRB Foundation** (Retail):
    - Formule Bâle III avec corrélation R(PD)
    - Maturity Adjustment M(PD)
    - Risk Weight = 12.5 × K × M
    - K = [LGD × N((1-R)^-0.5 × G(PD) + (R/(1-R))^0.5 × G(0.999)) - PD × LGD] × (1-1.5×b(PD))^-1

    **Approche Standardisée** (Corporate/Sovereign):
    - Pondérations fixes par classe d'exposition
    - Corporate : 100% (non noté)
    - Sovereign AAA-AA : 0%, A+ à A- : 20%, etc.
    - Retail : 75%

    ### 💧 Liquidité (LCR)

    **Liquidity Coverage Ratio:**
    ```
    LCR = HQLA / Net Cash Outflows (30 jours) × 100%
    Minimum réglementaire : 100%
    ```

    **HQLA (High Quality Liquid Assets):**
    - **Level 1** : Cash, obligations souveraines (haircut 0%)
    - **Level 2A** : Obligations corporate AA+ (haircut 15%)
    - **Level 2B** : Actions, RMBS (haircut 25-50%)

    **Net Cash Outflows:**
    - Dépôts retail : run-off 3-10%
    - Dépôts wholesale : run-off 25-100%
    - Committed facilities : draw-down 30-100%

    ### 🏗️ Liquidité (NSFR)

    **Net Stable Funding Ratio:**
    ```
    NSFR = Available Stable Funding / Required Stable Funding × 100%
    Minimum réglementaire : 100%
    ```

    **ASF Factors:**
    - Capital : 100%
    - Dépôts retail < 1 an : 90-95%
    - Dépôts wholesale < 1 an : 50%

    **RSF Factors:**
    - Cash, Souverains : 0-5%
    - Corporate loans > 1 an : 65%
    - Retail mortgages : 65%

    ### 🏛️ Capital

    **Ratios CRR3:**
    ```
    CET1 Ratio = CET1 Capital / Total RWA × 100%  (Min: 4.5%)
    Tier 1 Ratio = (CET1 + AT1) / Total RWA × 100%  (Min: 6.0%)
    Total Capital Ratio = (Tier 1 + Tier 2) / Total RWA × 100%  (Min: 8.0%)
    Leverage Ratio = Tier 1 / Total Exposure × 100%  (Min: 3.0%)
    ```

    ### 📈 SA-CCR (Dérivés)

    **Standardised Approach for Counterparty Credit Risk:**
    ```
    EAD = Alpha × (RC + PFE)
    Alpha = 1.4
    RC = Replacement Cost (max(V - C, 0))
    PFE = Multiplier × AddOn
    ```

    ### 💵 IFRS 9 ECL

    **Expected Credit Loss (3 stages):**
    - **Stage 1** : 12-month ECL (performing)
    - **Stage 2** : Lifetime ECL (underperforming, SICR)
    - **Stage 3** : Lifetime ECL (non-performing, default)

    **Formule ECL:**
    ```
    ECL = EAD × PD × LGD
    PD : Probability of Default (0-100%)
    LGD : Loss Given Default (0-100%)
    EAD : Exposure At Default
    ```
    """)

# Tab 4: Configuration
with tabs[3]:
    st.markdown("""
    ## 🔧 Configuration

    ### 📁 Fichier .env

    ```bash
    # Base de données
    DATABASE_URL=sqlite:///data/banking_simulator.db
    # Pour PostgreSQL en production :
    # DATABASE_URL=postgresql://user:pass@localhost/banking_sim

    # Stockage des artefacts
    ARTIFACT_STORE=filesystem
    ARTIFACT_PATH=data/artifacts

    # Logging
    LOG_LEVEL=INFO

    # Cache
    CACHE_ENABLED=true
    CACHE_TTL=3600
    ```

    ### ⚙️ Paramètres de Simulation

    **Nombre de positions :**
    - Min : 10
    - Max : 10,000
    - Recommandé : 1,000-2,000 (bon compromis perf/réalisme)

    **Seed :**
    - Valeur fixe = résultats reproductibles
    - Ex: seed=42 produit toujours les mêmes exposures

    **Entités simulées :**
    - ENTITY_A (50% des positions)
    - ENTITY_B (30% des positions)
    - ENTITY_C (20% des positions)

    **Classes d'exposition :**
    - Retail (40%)
    - Corporate (30%)
    - Sovereign (15%)
    - Bank (10%)
    - Equity (5%)

    ### 🚀 Lancement

    ```bash
    # Installation
    pip install -r requirements.txt

    # Initialisation DB
    alembic upgrade head

    # Lancement Streamlit
    streamlit run app/main.py

    # Tests
    pytest tests/
    ```

    ### 📊 Performance

    **Cache activé :**
    - 1ère exécution : ~2-3s (calculs + stockage)
    - Exécutions suivantes : ~0.05s (lecture cache)
    - Speedup : 50-60x

    **Sans cache :**
    - Simulation 1000 positions : ~1s
    - RWA calculation : ~0.5s
    - LCR/NSFR : ~0.5s
    - Total : ~2-3s
    """)

# Tab 5: Limitations
with tabs[4]:
    st.markdown("""
    ## ⚠️ Limitations et Avertissements

    ### 🎓 Usage Éducatif Uniquement

    **⚠️ IMPORTANT : Cette application est destinée à des fins pédagogiques et de démonstration.**

    - ❌ **NE PAS** utiliser pour calculs réglementaires officiels
    - ❌ **NE PAS** soumettre les rapports aux autorités de supervision
    - ❌ **NE PAS** baser des décisions financières sur ces résultats

    ### 📉 Simplifications Méthodologiques

    **Monte Carlo :**
    - Distributions simplifiées (log-normale, beta)
    - Pas de modélisation de dépendances complexes
    - Pas de scénarios de stress avancés

    **RWA :**
    - IRB Foundation uniquement (pas Advanced)
    - Pas de CVA/DVA complet
    - Pas de calibration réelle PD/LGD

    **Liquidité :**
    - Hypothèses simplifiées sur run-off rates
    - Pas de modélisation comportementale avancée
    - ALMM basique (pas ILAAP complet)

    **Capital :**
    - Pas de buffers GSIB/OSII
    - Pas de Pillar 2 requirements
    - Pas de stress testing ICAAP

    ### 🔒 Données et Sécurité

    - Données 100% synthétiques
    - Pas de connexion à systèmes réels
    - Pas de données clients réelles
    - Stockage local uniquement

    ### 🏗️ Architecture

    - SQLite par défaut (limité en production)
    - Pas de multi-threading avancé
    - Cache mémoire limité
    - Pas de scalabilité horizontale

    ### 📋 Conformité

    - Templates COREP/FINREP simplifiés
    - Pas de validation XBRL
    - Pas de contrôles qualité réglementaires
    - Pas de certification superviseur

    ### ✅ Recommandations

    Pour un usage professionnel :
    1. **Valider** les méthodologies avec des experts
    2. **Calibrer** sur données historiques réelles
    3. **Auditer** les calculs par un tiers indépendant
    4. **Certifier** par l'autorité de supervision
    5. **Intégrer** dans un environnement de production sécurisé
    """)

# Tab 6: Références
with tabs[5]:
    st.markdown("""
    ## 📚 Références Réglementaires

    ### 🇪🇺 Textes Européens

    **Capital Requirements Regulation (CRR3):**
    - Règlement (UE) 2024/1623 du 31 mai 2024
    - Entrée en vigueur : 1er janvier 2025
    - Modifications majeures : Output Floor, SA-CCR, CVA

    **Capital Requirements Directive (CRD VI):**
    - Directive (UE) 2024/1619 du 31 mai 2024
    - Transposition nationale avant juin 2026

    **FINREP (Financial Reporting):**
    - Règlement d'exécution (UE) n° 680/2014 (ITS)
    - Dernière version : EBA/ITS/2023/01
    - Fréquence : Trimestrielle (grandes banques)

    **COREP (Common Reporting):**
    - Règlement d'exécution (UE) n° 680/2014 (ITS)
    - Templates : C 07.00, C 08.01, C 34.00, etc.
    - Fréquence : Trimestrielle

    ### 🏛️ Standards Internationaux

    **Bâle III (BCBS):**
    - Basel III: Finalising post-crisis reforms (décembre 2017)
    - Output Floor : 72.5% des RWA standardisés
    - LCR : BCBS 238 (janvier 2013)
    - NSFR : BCBS 295 (octobre 2014)
    - SA-CCR : BCBS 279 (mars 2014)

    **IFRS 9:**
    - Instruments Financiers (depuis 1er janvier 2018)
    - ECL : Expected Credit Loss
    - Stages 1/2/3 : 12m vs Lifetime ECL

    ### 📖 Guidelines EBA

    **Capital:**
    - EBA/GL/2020/06 : Treatment of structural FX
    - EBA/GL/2021/03 : NPL coverage expectations

    **Liquidité:**
    - EBA/GL/2017/01 : LCR disclosure
    - EBA/GL/2016/10 : NSFR disclosure

    **Risque de Crédit:**
    - EBA/GL/2017/16 : PD/LGD estimation
    - EBA/GL/2017/18 : NPE definition

    ### 🔗 Liens Utiles

    **Autorités Européennes:**
    - [EBA](https://www.eba.europa.eu/) - European Banking Authority
    - [BCE/SSM](https://www.bankingsupervision.europa.eu/) - Single Supervisory Mechanism
    - [ESMA](https://www.esma.europa.eu/) - European Securities Markets Authority

    **Autorités Nationales:**
    - [ACPR](https://acpr.banque-france.fr/) - France
    - [BaFin](https://www.bafin.de/) - Allemagne
    - [PRA](https://www.bankofengland.co.uk/pra) - UK

    **Institutions Internationales:**
    - [BIS](https://www.bis.org/) - Bank for International Settlements
    - [BCBS](https://www.bis.org/bcbs/) - Basel Committee
    - [IFRS Foundation](https://www.ifrs.org/) - IFRS Standards

    ### 📊 Documentation Technique

    **GitHub Repository:**
    - [GITMHAROUECH/Banking_simulator](https://github.com/GITMHAROUECH/Banking_simulator)

    **Version :** 0.7.0 (I7a)
    **Dernière mise à jour :** Novembre 2024
    **Licence :** MIT
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.9em;">
    Banking Simulator v0.7.0 (I7a) -
    <a href="https://github.com/GITMHAROUECH/Banking_simulator" target="_blank">GitHub</a> -
    MIT License -
    ⚠️ Usage éducatif uniquement
</div>
""", unsafe_allow_html=True)
