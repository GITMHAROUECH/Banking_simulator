# Banking Simulation & CRR3 Reporting Application

## 🏦 Vue d'ensemble

Cette application de simulation bancaire permet de générer des données réalistes pour un groupe bancaire multi-entités et de produire les rapports réglementaires conformes à CRR3. Elle couvre l'ensemble de la chaîne de traitement depuis la simulation des positions jusqu'à la génération des rapports FINREP, COREP et RUBA.

## 🎯 Objectifs

- **Simulation** : Générer des positions bancaires réalistes avec des paramètres de risque cohérents
- **Comptabilité** : Calculer les états financiers selon les normes IFRS simplifiées
- **Consolidation** : Agréger les données multi-devises au niveau groupe
- **Risque de crédit** : Calculer les RWA selon les approches IRB et standardisée CRR3
- **Liquidité** : Évaluer les ratios LCR, NSFR et ALMM
- **Reporting** : Générer les rapports réglementaires européens

## 🏭️ Architecture

### Architecture en couches (refactorisée)

```
banking_app/
├── app/
│   ├── streamlit_app.py          # Application principale Streamlit
│   ├── core/                     # Moteurs de calcul (legacy)
│   │   ├── simulation.py         # Simulation Monte Carlo
│   │   ├── accounting.py         # Comptabilité IFRS
│   │   ├── consolidation.py      # Consolidation groupe
│   │   ├── credit_risk.py        # Risque de crédit CRR3 (legacy)
│   │   ├── liquidity.py          # Ratios de liquidité
│   │   └── reporting.py          # Rapports réglementaires
│   ├── io/                       # Import/Export
│   │   ├── readers.py            # Lecture Excel
│   │   ├── writers.py            # Écriture Excel
│   │   └── excel_templates.py    # Génération templates
│   └── config/                   # Configuration
│       ├── schemas.py            # Schémas de données
│       └── defaults.py           # Paramètres par défaut
├── src/                          # ✨ Architecture refactorisée
│   ├── domain/                   # Logique métier pure
│   │   └── credit_risk/
│   │       ├── standardized.py   # Approche standardisée RWA
│   │       ├── irb.py            # Approche IRB RWA
│   │       └── capital.py        # Ratios de capital
│   ├── services/                 # Orchestration
│   │   └── credit_risk_service.py
│   └── ui/                       # Pages UI Streamlit
│       └── pages/
│           ├── credit_risk.py    # Page Risque de Crédit
│           └── capital.py        # Page Ratios de Capital
├── tests/                        # ✨ Tests unitaires (91% coverage)
│   └── unit/
│       └── credit_risk/
│           ├── test_standardized.py
│           ├── test_irb.py
│           └── test_capital.py
├── data/                         # Données (créé automatiquement)
├── regulatory_docs/              # Documents réglementaires
├── requirements.txt              # Dépendances Python
├── README.md                     # Cette documentation
└── REFACTORING_CREDIT_RISK.md   # ✨ Documentation refactorisation
```

### Couches de l'architecture

- **Domain Layer** (`src/domain/`) : Logique métier pure, sans dépendances externes
- **Service Layer** (`src/services/`) : Orchestration entre domain et UI
- **UI Layer** (`src/ui/`) : Pages Streamlit, présentation uniquement
- **Tests** (`tests/unit/`) : Tests unitaires avec 91% de couverture

## 🚀 Installation et démarrage

### Prérequis

- Python 3.11+
- pip

### Installation

```bash
# Cloner ou télécharger le projet
cd banking_app

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app/streamlit_app.py
```

L'application sera accessible à l'adresse : http://localhost:8501

## 📋 Guide d'utilisation

### 1. Configuration

- Accéder à la section "⚙️ Configuration"
- Définir les paramètres du scénario (graine, dates, devise de base)
- Configurer les entités (EU, US, CN) avec leurs devises et pourcentages de détention
- Sélectionner les produits financiers à inclure
- Sauvegarder la configuration

### 2. Simulation

- Accéder à la section "📊 Simulation"
- Lancer la simulation avec les paramètres configurés
- Examiner les résultats : positions, flux de trésorerie, dérivés
- Télécharger les données générées

### 3. Comptabilité

- Accéder à la section "📋 Comptabilité"
- Calculer les états comptables par entité
- Examiner les balances, bilans et comptes de résultat
- Analyser les provisions IFRS 9

### 4. Consolidation

- Accéder à la section "🔄 Consolidation"
- Effectuer la consolidation avec conversion de devises
- Examiner la balance consolidée et les états groupe
- Vérifier les éliminations et intérêts minoritaires

### 5. Risque de crédit

- Accéder à la section "⚠️ Risque de Crédit"
- Calculer les RWA selon CRR3
- Examiner les ratios de capital (CET1, Tier 1, Total)
- Analyser la répartition par classe d'exposition

### 6. Liquidité

- Accéder à la section "💧 Liquidité"
- Calculer les ratios LCR, NSFR et ALMM
- Examiner les gaps de liquidité
- Vérifier la conformité aux seuils réglementaires

### 7. Reporting

- Accéder à la section "📈 Reporting"
- Générer les rapports FINREP, COREP et RUBA
- Examiner les templates remplis
- Valider la cohérence des données

### 8. Export

- Accéder à la section "📥 Import/Export"
- Sélectionner les données à exporter
- Générer les fichiers Excel formatés
- Télécharger individuellement ou en archive ZIP

## 🔧 Fonctionnalités techniques

### Moteur de simulation

- **Méthode** : Monte Carlo avec graine fixe pour la reproductibilité
- **Entités** : Support multi-devises (EUR, USD, CNY)
- **Produits** : 12+ types de produits bancaires
- **Paramètres** : PD, LGD, CCF selon les standards de l'industrie
- **Stages ECL** : Classification IFRS 9 automatique

### Comptabilité IFRS

- **Plan comptable** : Structure bancaire simplifiée
- **Provisions** : Calcul ECL selon IFRS 9
- **Équilibrage** : Automatique des balances
- **Multi-devises** : Support des devises locales

### Consolidation

- **Méthode** : Intégration globale
- **Conversion** : Taux de clôture et taux moyens
- **Éliminations** : Transactions intercompagnies
- **Minoritaires** : Calcul automatique

### Risque de crédit CRR3

- **IRB** : Formules réglementaires pour le retail
- **Standardisé** : Pondérations CRR3 pour le non-retail
- **Corrélations** : Selon le type de produit
- **Maturités** : Effectives par produit

### Liquidité

- **LCR** : Horizon 30 jours, classification HQLA
- **NSFR** : Facteurs ASF/RSF réglementaires
- **ALMM** : Buckets de maturité standard

## 📊 Données générées

### Positions

- **Volume** : 1000+ positions par défaut
- **Attributs** : EAD, PD, LGD, maturité, stage, provisions
- **Granularité** : Par entité, produit et classe d'exposition

### Flux de trésorerie

- **Types** : Intérêts, principal, commissions, provisions
- **Fréquence** : Mensuelle sur l'année
- **Devises** : Locale et EUR

### États financiers

- **Balances** : Par entité en devise locale
- **Consolidé** : Groupe en EUR
- **Provisions** : Détail par stage IFRS 9

### Rapports réglementaires

- **FINREP** : États financiers harmonisés
- **COREP** : Fonds propres et ratios prudentiels
- **RUBA** : Utilisation des notations internes

## ⚠️ Limitations et avertissements

### Limitations techniques

- **Simulation** : Données fictives générées aléatoirement
- **Simplifications** : Modèles simplifiés par rapport à la réalité
- **Périmètre** : Limité aux principaux risques (crédit, liquidité)
- **Validation** : Aucune validation réglementaire officielle

### Avertissements d'usage

⚠️ **Cette application est destinée uniquement à des fins éducatives et de démonstration.**

- Ne pas utiliser pour des calculs réglementaires réels
- Les résultats ne sont pas auditables
- Les méthodologies sont simplifiées
- Aucune garantie de conformité réglementaire

## 🧪 Tests

### Exécution des tests

```bash
# Tests unitaires du module Credit Risk (refactorisé)
python -m pytest tests/unit/credit_risk -v

# Avec couverture de code
python -m pytest tests/unit/credit_risk --cov=src/domain/credit_risk --cov-report=term

# Générer un rapport HTML
python -m pytest tests/unit/credit_risk --cov=src/domain/credit_risk --cov-report=html
```

### Couverture des tests

#### Module Credit Risk (refactorisé) : **91% de couverture** ✅

- **test_standardized.py** (17 tests) : Approche standardisée RWA
  - Calcul EAD avec/sans CCF
  - Pondérations de risque par classe d'exposition
  - Calcul RWA total et densité
  - Gestion des cas limites

- **test_irb.py** (21 tests) : Approche IRB RWA
  - Corrélations par type de produit
  - Ajustements de maturité
  - Formule IRB CRR3 complète
  - Gestion des valeurs extrêmes

- **test_capital.py** (17 tests) : Ratios de capital
  - CET1, Tier 1, Total Capital ratios
  - Exigences avec buffers réglementaires
  - Ratio de levier
  - Calcul des surplus/déficits

#### Autres modules (legacy)

- Moteur de simulation
- Génération des entités et positions
- Calculs de provisions
- Cohérence des flux de trésorerie
- Reproductibilité des résultats

## 📚 Références réglementaires

### Textes européens

- **CRR3** : Règlement (UE) 2024/1623 (Capital Requirements Regulation)
- **CRD VI** : Directive (UE) 2024/1619 (Capital Requirements Directive)
- **FINREP** : Templates EBA pour le reporting financier
- **COREP** : Templates EBA pour le reporting prudentiel

### Standards internationaux

- **Bâle III** : Accords du Comité de Bâle sur le contrôle bancaire
- **IFRS 9** : Norme comptable internationale sur les instruments financiers
- **LCR** : Liquidity Coverage Ratio (Bâle III)
- **NSFR** : Net Stable Funding Ratio (Bâle III)

## 🔗 Liens utiles

- [EBA Guidelines](https://www.eba.europa.eu/)
- [ECB Banking Supervision](https://www.bankingsupervision.europa.eu/)
- [ACPR](https://acpr.banque-france.fr/)
- [BIS Basel Framework](https://www.bis.org/basel_framework/)

## 📝 Changelog

### Version 1.1.0 (2025-10-25) ✨

- ✅ **Refactorisation module Credit Risk** : Architecture en couches (Domain/Service/UI)
- ✅ **Tests unitaires** : 55 tests avec 91% de couverture
- ✅ **Séparation des responsabilités** : Logique métier isolée de l'UI
- ✅ **Maintenabilité** : Code modulaire et testable
- ✅ **Documentation** : REFACTORING_CREDIT_RISK.md détaillé
- ✅ **Compatibilité** : Fallback vers l'implémentation legacy

### Version 1.0.0 (2024-10-09)

- ✅ Moteur de simulation Monte Carlo
- ✅ Comptabilité IFRS simplifiée
- ✅ Consolidation multi-devises
- ✅ Calculs RWA selon CRR3
- ✅ Ratios de liquidité (LCR, NSFR, ALMM)
- ✅ Rapports réglementaires (FINREP, COREP, RUBA)
- ✅ Interface Streamlit complète
- ✅ Export Excel formaté
- ✅ Templates d'import/export
- ✅ Tests unitaires
- ✅ Documentation complète

## 📞 Support

Cette application a été développée à des fins éducatives et de démonstration des capacités de simulation bancaire et de reporting réglementaire.

Pour toute question technique ou suggestion d'amélioration, veuillez consulter la documentation intégrée dans l'application (section "ℹ️ Documentation").

## 📄 Licence

Application développée pour démonstration des capacités de simulation bancaire et de reporting CRR3.

---

**Développé avec ❤️ pour l'éducation financière et la compréhension des réglementations bancaires.**
