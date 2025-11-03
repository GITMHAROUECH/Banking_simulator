import streamlit as st
import base64
from pathlib import Path

def get_image_base64(image_path):
    """Convertir une image en base64 pour l'affichage dans Streamlit"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def show_updated_home():
    """Afficher la page d'accueil mise à jour avec les icônes Picasso"""
    
    # CSS personnalisé pour la page d'accueil
    st.markdown("""
    <style>
        .main-title {
            font-size: 3.5rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(135deg, #1f4e79, #2c5aa0, #4a90e2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .subtitle {
            font-size: 1.5rem;
            text-align: center;
            color: #666;
            margin-bottom: 3rem;
            font-style: italic;
        }
        
        .feature-card {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-left: 5px solid #1f4e79;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 35px rgba(0,0,0,0.15);
        }
        
        .feature-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 1rem auto;
            display: block;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .feature-title {
            font-size: 1.3rem;
            font-weight: bold;
            color: #1f4e79;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .feature-description {
            color: #555;
            text-align: center;
            line-height: 1.6;
            font-size: 0.95rem;
        }
        
        .stats-container {
            background: linear-gradient(135deg, #1f4e79, #2c5aa0);
            border-radius: 15px;
            padding: 2rem;
            margin: 2rem 0;
            color: white;
            text-align: center;
        }
        
        .stat-item {
            margin: 1rem 0;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            display: block;
        }
        
        .stat-label {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        .tech-stack {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 2rem 0;
            border: 2px dashed #dee2e6;
        }
        
        .cta-button {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 1rem 2rem;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
            display: inline-block;
            margin: 1rem;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .cta-button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.4);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Titre principal
    st.markdown('<h1 class="main-title">🏦 Banking Simulation & CRR3 Reporting</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Plateforme Complète de Simulation Bancaire et Reporting Réglementaire</p>', unsafe_allow_html=True)
    
    # Description générale
    st.markdown("""
    <div style="text-align: center; font-size: 1.1rem; color: #666; margin-bottom: 3rem; max-width: 800px; margin-left: auto; margin-right: auto;">
        Une application avancée de simulation Monte Carlo pour la modélisation des portefeuilles bancaires, 
        le calcul des exigences réglementaires CRR3, et la génération de rapports financiers conformes aux standards internationaux.
        Intégrant les dernières innovations en matière de risque de contrepartie, consolidation IFRS, et analyse drill-down.
    </div>
    """, unsafe_allow_html=True)
    
    # Statistiques clés
    st.markdown("""
    <div class="stats-container">
        <h3 style="margin-bottom: 2rem;">🎯 Capacités de la Plateforme</h3>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div class="stat-item">
                <span class="stat-number">10,000+</span>
                <span class="stat-label">Positions Simulées</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">15+</span>
                <span class="stat-label">Modules Intégrés</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">100%</span>
                <span class="stat-label">Conforme CRR3</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Real-time</span>
                <span class="stat-label">Calculs & Rapports</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fonctionnalités principales avec icônes Picasso
    st.markdown("## 🚀 Fonctionnalités Principales")
    
    # Première ligne de fonctionnalités
    col1, col2, col3 = st.columns(3)
    
    with col1:
        simulation_icon = get_image_base64("/home/ubuntu/banking_app/icons/simulation_icon.png")
        if simulation_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{simulation_icon}" class="feature-icon">
                <div class="feature-title">Simulation Monte Carlo Avancée</div>
                <div class="feature-description">
                    Génération de portefeuilles réalistes avec paramètres de risque sophistiqués. 
                    Support multi-entités, multi-devises avec scénarios de stress personnalisables.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Icône simulation non trouvée")
    
    with col2:
        portfolio_icon = get_image_base64("/home/ubuntu/banking_app/icons/portfolio_icon.png")
        if portfolio_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{portfolio_icon}" class="feature-icon">
                <div class="feature-title">Gestion de Portefeuille</div>
                <div class="feature-description">
                    Analyse complète des expositions par classe, entité et produit. 
                    Calcul automatique des provisions IFRS 9 avec classification par stages.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        risk_icon = get_image_base64("/home/ubuntu/banking_app/icons/risk_icon.png")
        if risk_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{risk_icon}" class="feature-icon">
                <div class="feature-title">Risque de Crédit (RWA)</div>
                <div class="feature-description">
                    Calculs RWA conformes CRR3 avec approches IRB-Foundation et Standardisée. 
                    Formules réglementaires complètes avec ajustements de maturité.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Deuxième ligne de fonctionnalités
    col1, col2, col3 = st.columns(3)
    
    with col1:
        capital_icon = get_image_base64("/home/ubuntu/banking_app/icons/capital_icon.png")
        if capital_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{capital_icon}" class="feature-icon">
                <div class="feature-title">Ratios de Capital</div>
                <div class="feature-description">
                    Calcul et monitoring des ratios CET1, Tier 1 et Total Capital. 
                    Comparaison automatique avec les exigences réglementaires et buffers.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        liquidity_icon = get_image_base64("/home/ubuntu/banking_app/icons/liquidity_icon.png")
        if liquidity_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{liquidity_icon}" class="feature-icon">
                <div class="feature-title">Risque de Liquidité</div>
                <div class="feature-description">
                    Calculs LCR, NSFR et ALMM avec classification HQLA détaillée. 
                    Analyse des gaps de maturité et stress tests de liquidité.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        derivatives_icon = get_image_base64("/home/ubuntu/banking_app/icons/derivatives_icon.png")
        if derivatives_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{derivatives_icon}" class="feature-icon">
                <div class="feature-title">Produits Dérivés & CVA</div>
                <div class="feature-description">
                    Module complet de risque de contrepartie avec calculs SA-CCR. 
                    Évaluation CVA/DVA et analyse des expositions futures potentielles.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Troisième ligne de fonctionnalités
    col1, col2, col3 = st.columns(3)
    
    with col1:
        consolidation_icon = get_image_base64("/home/ubuntu/banking_app/icons/consolidation_icon.png")
        if consolidation_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{consolidation_icon}" class="feature-icon">
                <div class="feature-title">Consolidation IFRS</div>
                <div class="feature-description">
                    Processus complet de consolidation avec éliminations intragroupes. 
                    Conversion multi-devises et calcul des intérêts minoritaires.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        reconciliation_icon = get_image_base64("/home/ubuntu/banking_app/icons/reconciliation_icon.png")
        if reconciliation_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{reconciliation_icon}" class="feature-icon">
                <div class="feature-title">Réconciliation Compta-Risque</div>
                <div class="feature-description">
                    Détection et analyse des écarts entre données comptables et de risque. 
                    Outils de justification et de résolution des divergences.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        reporting_icon = get_image_base64("/home/ubuntu/banking_app/icons/reporting_icon.png")
        if reporting_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{reporting_icon}" class="feature-icon">
                <div class="feature-title">Reporting Réglementaire</div>
                <div class="feature-description">
                    Génération automatique des rapports FINREP, COREP et RUBA. 
                    Templates conformes aux standards EBA et BCE.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Fonctionnalité drill-down
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        drilldown_icon = get_image_base64("/home/ubuntu/banking_app/icons/drilldown_icon.png")
        if drilldown_icon:
            st.markdown(f"""
            <div class="feature-card">
                <img src="data:image/png;base64,{drilldown_icon}" class="feature-icon">
                <div class="feature-title">🔍 Analyse Drill-Down Avancée</div>
                <div class="feature-description">
                    Exploration interactive des données avec filtres dynamiques par entité, classe d'exposition et stage IFRS 9. 
                    Tableaux paginés, graphiques de corrélation et métriques en temps réel pour une analyse approfondie.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Stack technologique
    st.markdown("## 🛠️ Stack Technologique")
    st.markdown("""
    <div class="tech-stack">
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; align-items: center;">
            <div style="text-align: center; margin: 1rem;">
                <strong>Frontend</strong><br>
                Streamlit • Plotly • HTML/CSS
            </div>
            <div style="text-align: center; margin: 1rem;">
                <strong>Backend</strong><br>
                Python • Pandas • NumPy
            </div>
            <div style="text-align: center; margin: 1rem;">
                <strong>Calculs</strong><br>
                Monte Carlo • IRB • SA-CCR
            </div>
            <div style="text-align: center; margin: 1rem;">
                <strong>Standards</strong><br>
                CRR3 • IFRS 9 • Bâle III
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h3>🎯 Prêt à Explorer ?</h3>
        <p style="font-size: 1.1rem; color: #666; margin-bottom: 2rem;">
            Découvrez toutes les capacités de simulation et d'analyse de notre plateforme bancaire.
        </p>
        <div>
            <button class="cta-button">🚀 Commencer la Simulation</button>
            <button class="cta-button">📊 Explorer les Rapports</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Avertissement
    st.markdown("---")
    st.warning("""
    ⚠️ **Avertissement Important** : Cette application est destinée uniquement à des fins éducatives et de démonstration. 
    Les données générées sont fictives et les calculs, bien que basés sur les réglementations réelles, 
    sont simplifiés et ne doivent pas être utilisés pour des rapports réglementaires officiels.
    """)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px;">
        <p style="color: #666; margin: 0;">
            <strong>Banking Simulation & CRR3 Reporting Platform</strong><br>
            Développé avec ❤️ pour l'éducation financière et la compréhension des réglementations bancaires
        </p>
    </div>
    """, unsafe_allow_html=True)
