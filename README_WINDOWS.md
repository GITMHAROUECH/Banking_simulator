# Banking Simulation & CRR3 Reporting - Version Windows

## 🏦 Application de simulation bancaire et reporting réglementaire

Cette application permet de simuler des positions bancaires réalistes et de calculer les indicateurs réglementaires selon CRR3 (Capital Requirements Regulation).

## 🚀 Installation rapide sur Windows

### Prérequis
- **Python 3.8+** (recommandé : Python 3.11)
- Connexion Internet pour l'installation des dépendances

### Étapes d'installation

1. **Télécharger Python** (si pas déjà installé)
   - Aller sur https://python.org/downloads/
   - Télécharger la dernière version Python 3.11
   - **Important** : Cocher "Add Python to PATH" lors de l'installation

2. **Extraire l'application**
   - Extraire tous les fichiers dans un dossier (ex: `C:\BankingApp\`)

3. **Installation automatique**
   - Double-cliquer sur `install_windows.bat`
   - Attendre la fin de l'installation des dépendances

4. **Lancement de l'application**
   - Double-cliquer sur `run_banking_app.bat`
   - L'application s'ouvre automatiquement dans votre navigateur

## 🎯 Utilisation

### Interface web
- **Adresse** : http://localhost:8501
- **Navigation** : Menu latéral gauche
- **Compatible** : Chrome, Firefox, Edge, Safari

### Workflow recommandé
1. **Configuration** : Paramétrer le scénario de simulation
2. **Simulation** : Générer 1000+ positions bancaires
3. **Risque de crédit** : Calculer les RWA selon CRR3
4. **Liquidité** : Analyser les ratios LCR et NSFR
5. **Reporting** : Générer le rapport de synthèse
6. **Export Excel** : Télécharger les résultats

## 📊 Fonctionnalités

### Simulation bancaire
- **Entités** : 3 filiales (EU, US, CN)
- **Produits** : Prêts, dépôts, obligations
- **Paramètres** : PD, LGD, maturités réalistes
- **Stages IFRS 9** : Classification automatique

### Calculs réglementaires
- **RWA** : Approches IRB et standardisée CRR3
- **Ratios de capital** : CET1, Tier 1, Total
- **LCR** : Liquidity Coverage Ratio (30 jours)
- **NSFR** : Net Stable Funding Ratio (1 an)

### Visualisations
- **Graphiques interactifs** : Plotly
- **Tableaux détaillés** : Pandas
- **Métriques** : Temps réel
- **Export** : Excel multi-feuilles

## 🔧 Dépannage

### Problèmes courants

**Python non trouvé**
```
Solution : Réinstaller Python en cochant "Add to PATH"
Vérification : Ouvrir cmd et taper "python --version"
```

**Erreur d'installation des dépendances**
```
Solution : Ouvrir cmd en tant qu'administrateur
Commande : pip install --upgrade pip
Puis : pip install streamlit pandas numpy plotly openpyxl
```

**Port 8501 occupé**
```
Solution : Modifier run_banking_app.bat
Remplacer : streamlit run banking_demo.py
Par : streamlit run banking_demo.py --server.port 8502
```

**Application ne se charge pas**
```
Solution : Vérifier le navigateur
Aller manuellement sur : http://localhost:8501
Essayer un autre navigateur
```

### Installation manuelle

Si les fichiers .bat ne fonctionnent pas :

```cmd
# Ouvrir une invite de commande (cmd)
cd C:\BankingApp

# Installer les dépendances
pip install streamlit pandas numpy plotly openpyxl

# Lancer l'application
streamlit run banking_demo.py
```

## 📁 Structure des fichiers

```
BankingApp/
├── banking_demo.py          # Application principale
├── install_windows.bat      # Installation automatique
├── run_banking_app.bat      # Lancement automatique
├── README_WINDOWS.md        # Ce fichier
└── banking_app_complete.zip # Version complète (optionnel)
```

## ⚠️ Avertissements

**Application de démonstration uniquement**
- Destinée à l'éducation et la formation
- Ne pas utiliser pour des calculs réglementaires réels
- Données fictives générées aléatoirement
- Modèles simplifiés par rapport à la réalité bancaire

## 📚 Documentation

### Références réglementaires
- **CRR3** : Règlement (UE) 2024/1623
- **Bâle III** : Standards internationaux
- **IFRS 9** : Provisions sur pertes de crédit

### Liens utiles
- [EBA Guidelines](https://www.eba.europa.eu/)
- [Banque de France](https://acpr.banque-france.fr/)
- [Documentation Streamlit](https://docs.streamlit.io/)

## 🆘 Support

### En cas de problème
1. Vérifier que Python 3.8+ est installé
2. Vérifier que les dépendances sont installées
3. Redémarrer l'application
4. Consulter la documentation intégrée (section ℹ️)

### Fonctionnalités avancées
- La version complète inclut la comptabilité IFRS
- Consolidation multi-devises disponible
- Templates d'import/export personnalisés
- Tests unitaires complets

---

**Développé pour l'éducation financière et la compréhension des réglementations bancaires.**

*Compatible Windows 10/11, macOS, Linux*
