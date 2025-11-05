# Journal d'Arbitrages Techniques - Itération 3

## 1. Point d'entrée : app/main.py vs Banking_Simulator.py

**Décision** : Créer `app/main.py` comme nouveau point d'entrée.

**Justification** :
- **Séparation** : app/main.py = architecture refactorisée, Banking_Simulator.py = legacy
- **Coexistence** : Les deux points d'entrée peuvent coexister pendant la transition
- **Migration progressive** : Permet de tester la nouvelle architecture sans casser l'existant

**Implémentation** :
- app/main.py reprend la navigation sidebar de Banking_Simulator.py
- Utilise les adaptateurs pour appeler Domain/Services
- Pages legacy appelées via import direct

## 2. Adaptateurs : Placement dans app/ vs src/

**Décision** : Adaptateurs dans `app/adapters/`.

**Justification** :
- **Logique** : Les adaptateurs font partie de la couche application (app/)
- **Séparation** : src/ contient uniquement Domain et Services (logique métier)
- **Clarté** : app/ = UI + adaptateurs + configuration

## 3. Smoke tests : Tests unitaires vs Tests d'intégration

**Décision** : Smoke tests dans `tests/ui_smoke/`.

**Justification** :
- **Objectif** : Vérifier que l'application démarre et les adaptateurs fonctionnent
- **Rapidité** : Tests légers, pas de vérification exhaustive
- **Complémentarité** : Les tests unitaires (domain, services) sont dans tests/domain/ et tests/services/

**Implémentation** :
- 7 tests smoke : imports, adaptateurs, pipeline complet
- Pas de vérification UI visuelle (headless)
- Validation des contrats d'interface

## 4. Navigation : Pages refactorisées vs Pages legacy

**Décision** : Routage mixte dans app/main.py.

**Justification** :
- **Pragmatisme** : Seules les pages Credit Risk et Capital sont refactorisées (I1-I2)
- **Coexistence** : Les autres pages (Consolidation, Réconciliation, etc.) restent legacy
- **Migration progressive** : Refactorisation UI complète en I7

**Implémentation** :
```python
if page_choice == "Simulation Monte Carlo":
    # Utilise les adaptateurs (Domain/Services via legacy_compat)
    from app.adapters.legacy_compat import generate_positions_advanced
    positions_df = generate_positions_advanced(num_positions, seed)
elif page_choice == "Consolidation IFRS":
    # Appelle la page legacy directement
    from consolidation_complete import show_consolidation_complete
    show_consolidation_complete()
```

## 5. Streamlit headless : Timeout vs Vérification manuelle

**Décision** : Timeout 5s pour les smoke tests.

**Justification** :
- **Automatisation** : Permet de valider le démarrage sans intervention manuelle
- **CI/CD** : Compatible avec les pipelines automatisés
- **Suffisant** : 5s suffisent pour détecter les erreurs de démarrage

**Implémentation** :
```bash
timeout 5 streamlit run app/main.py --server.headless true
```

## Conclusion

Les arbitrages techniques de l'Itération 3 privilégient :
- **Coexistence** : Nouveau point d'entrée + legacy
- **Migration progressive** : Refactorisation par étapes
- **Pragmatisme** : Smoke tests légers, routage mixte
- **Automatisation** : Tests headless pour CI/CD

**Prochaine étape** : Itération 4 (Domain Consolidation & Réconciliation)

