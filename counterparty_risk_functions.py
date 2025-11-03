import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import math

def safe_dataframe_creation(data_dict):
    """Créer un DataFrame de manière sécurisée"""
    try:
        if isinstance(data_dict, dict):
            # S'assurer que toutes les listes ont la même longueur
            max_len = max(len(v) if isinstance(v, list) else 1 for v in data_dict.values())
            
            for key, value in data_dict.items():
                if not isinstance(value, list):
                    data_dict[key] = [value] * max_len
                elif len(value) < max_len:
                    data_dict[key] = value + [value[-1]] * (max_len - len(value))
            
            return pd.DataFrame(data_dict)
        else:
            return pd.DataFrame(data_dict)
    except Exception as e:
        st.error(f"Erreur création DataFrame: {e}")
        return pd.DataFrame()

def generate_derivatives_portfolio(num_derivatives=500):
    """Générer un portefeuille de produits dérivés"""
    
    derivatives_data = []
    
    # Types de dérivés avec leurs caractéristiques
    derivative_types = {
        'Interest_Rate_Swap': {
            'asset_class': 'Interest Rate',
            'typical_maturity': [1, 2, 3, 5, 7, 10, 15, 20, 30],
            'notional_range': [1000000, 100000000],
            'volatility': 0.15
        },
        'FX_Forward': {
            'asset_class': 'Foreign Exchange',
            'typical_maturity': [0.25, 0.5, 1, 2, 3, 5],
            'notional_range': [500000, 50000000],
            'volatility': 0.12
        },
        'Credit_Default_Swap': {
            'asset_class': 'Credit',
            'typical_maturity': [1, 3, 5, 7, 10],
            'notional_range': [1000000, 25000000],
            'volatility': 0.25
        },
        'Equity_Option': {
            'asset_class': 'Equity',
            'typical_maturity': [0.25, 0.5, 1, 2],
            'notional_range': [100000, 10000000],
            'volatility': 0.30
        },
        'Commodity_Swap': {
            'asset_class': 'Commodity',
            'typical_maturity': [0.5, 1, 2, 3, 5],
            'notional_range': [500000, 20000000],
            'volatility': 0.35
        }
    }
    
    # Contreparties avec ratings
    counterparties = [
        {'name': 'BANK_AAA_01', 'rating': 'AAA', 'pd': 0.0003, 'lgd': 0.45},
        {'name': 'BANK_AA_02', 'rating': 'AA', 'pd': 0.0008, 'lgd': 0.45},
        {'name': 'BANK_A_03', 'rating': 'A', 'pd': 0.0025, 'lgd': 0.45},
        {'name': 'CORP_BBB_04', 'rating': 'BBB', 'pd': 0.0080, 'lgd': 0.60},
        {'name': 'CORP_BB_05', 'rating': 'BB', 'pd': 0.0250, 'lgd': 0.60},
        {'name': 'HEDGE_FUND_06', 'rating': 'B', 'pd': 0.0500, 'lgd': 0.75},
        {'name': 'SOVEREIGN_07', 'rating': 'AA', 'pd': 0.0005, 'lgd': 0.30},
        {'name': 'INSURANCE_08', 'rating': 'A', 'pd': 0.0020, 'lgd': 0.50}
    ]
    
    # Devises
    currencies = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD']
    
    # Entités
    entities = ['EU_SUB', 'US_SUB', 'CN_SUB']
    
    for i in range(num_derivatives):
        # Sélection aléatoire du type de dérivé
        derivative_type = random.choice(list(derivative_types.keys()))
        derivative_info = derivative_types[derivative_type]
        
        # Sélection de la contrepartie
        counterparty = random.choice(counterparties)
        
        # Paramètres de base
        notional = random.uniform(*derivative_info['notional_range'])
        maturity_years = random.choice(derivative_info['typical_maturity'])
        maturity_days = int(maturity_years * 365)
        
        # Calcul de la valeur de marché (MTM)
        # Simulation d'une distribution normale autour de 0
        mtm_volatility = derivative_info['volatility']
        mtm = random.gauss(0, notional * mtm_volatility * 0.1)
        
        # Calcul du PFE (Potential Future Exposure) selon SA-CCR
        pfe = calculate_pfe_sa_ccr(
            derivative_type, 
            notional, 
            maturity_years, 
            derivative_info['volatility']
        )
        
        # Calcul de l'EAD selon SA-CCR
        replacement_cost = max(mtm, 0)  # RC = max(V, 0)
        ead_sa_ccr = 1.4 * (replacement_cost + pfe)  # Alpha = 1.4
        
        # Netting set (groupement par contrepartie)
        netting_set_id = f"NS_{counterparty['name']}"
        
        # Collatéral (pour certains dérivés)
        has_collateral = random.choice([True, False]) if derivative_type in ['Interest_Rate_Swap', 'FX_Forward'] else False
        collateral_amount = random.uniform(0.7, 0.9) * max(mtm, 0) if has_collateral else 0
        
        # Calcul CVA (Credit Valuation Adjustment)
        cva_charge = calculate_cva_charge(
            ead_sa_ccr, 
            counterparty['pd'], 
            counterparty['lgd'], 
            maturity_years
        )
        
        derivative_record = {
            'derivative_id': f"DRV_{i+1:05d}",
            'entity_id': random.choice(entities),
            'derivative_type': derivative_type,
            'asset_class': derivative_info['asset_class'],
            'counterparty_name': counterparty['name'],
            'counterparty_rating': counterparty['rating'],
            'counterparty_pd': counterparty['pd'],
            'counterparty_lgd': counterparty['lgd'],
            
            # Caractéristiques du contrat
            'notional_amount': notional,
            'currency': random.choice(currencies),
            'maturity_years': maturity_years,
            'maturity_days': maturity_days,
            'trade_date': (datetime.now() - timedelta(days=random.randint(1, 1095))).strftime('%Y-%m-%d'),
            'maturity_date': (datetime.now() + timedelta(days=maturity_days)).strftime('%Y-%m-%d'),
            
            # Valorisation
            'mtm_value': mtm,
            'replacement_cost': replacement_cost,
            'pfe_amount': pfe,
            'ead_sa_ccr': ead_sa_ccr,
            
            # Netting et collatéral
            'netting_set_id': netting_set_id,
            'has_collateral': has_collateral,
            'collateral_amount': collateral_amount,
            'net_exposure': max(0, ead_sa_ccr - collateral_amount),
            
            # Ajustements de valorisation
            'cva_charge': cva_charge,
            'dva_charge': cva_charge * 0.3,  # DVA = 30% de CVA (approximation)
            'fva_charge': cva_charge * 0.2,  # FVA = 20% de CVA (approximation)
            
            # Classification réglementaire
            'cleared': random.choice([True, False]) if derivative_type != 'Equity_Option' else False,
            'margined': has_collateral,
            'regulatory_capital_treatment': 'Trading Book' if maturity_years <= 1 else 'Banking Book',
            
            # Facteurs de risque
            'delta_equivalent': random.uniform(-1, 1) * notional * 0.01,
            'gamma_equivalent': random.uniform(0, 1) * notional * 0.0001,
            'vega_equivalent': random.uniform(0, 1) * notional * 0.001,
            
            # Métriques de risque
            'var_1d_99': abs(random.gauss(0, notional * 0.02)),
            'expected_shortfall': abs(random.gauss(0, notional * 0.025)),
            'stress_loss': abs(random.gauss(0, notional * 0.05))
        }
        
        derivatives_data.append(derivative_record)
    
    return safe_dataframe_creation(derivatives_data)

def calculate_pfe_sa_ccr(derivative_type, notional, maturity, volatility):
    """Calculer le PFE selon l'approche SA-CCR"""
    
    # Facteurs de supervisory delta selon le type de dérivé
    supervisory_factors = {
        'Interest_Rate_Swap': {'delta': 0.5, 'correlation': 0.99},
        'FX_Forward': {'delta': 0.8, 'correlation': 0.60},
        'Credit_Default_Swap': {'delta': 0.38, 'correlation': 0.80},
        'Equity_Option': {'delta': 0.75, 'correlation': 0.50},
        'Commodity_Swap': {'delta': 0.40, 'correlation': 0.40}
    }
    
    # Facteur de maturité
    maturity_factor = min(1, math.sqrt(maturity / 1))  # M = min(1, sqrt(T))
    
    # Facteur supervisory
    supervisory_delta = supervisory_factors.get(derivative_type, {'delta': 0.5})['delta']
    
    # Calcul du PFE
    # PFE = supervisory_delta * notional * supervisory_factor * maturity_factor * volatility
    supervisory_factor = 0.15  # Facteur standard pour la plupart des classes d'actifs
    
    pfe = supervisory_delta * notional * supervisory_factor * maturity_factor * volatility
    
    return max(pfe, 0)

def calculate_cva_charge(ead, pd, lgd, maturity):
    """Calculer la charge CVA"""
    
    # Formule simplifiée CVA = EAD * PD * LGD * sqrt(maturity)
    # Avec ajustement pour la courbe de survie
    survival_probability = math.exp(-pd * maturity)
    default_probability = 1 - survival_probability
    
    cva = ead * default_probability * lgd * math.sqrt(maturity)
    
    return max(cva, 0)

def calculate_counterparty_risk_metrics(derivatives_df):
    """Calculer les métriques de risque de contrepartie"""
    
    # Agrégation par netting set
    netting_analysis = derivatives_df.groupby(['netting_set_id', 'counterparty_name']).agg({
        'notional_amount': 'sum',
        'mtm_value': 'sum',
        'ead_sa_ccr': 'sum',
        'net_exposure': 'sum',
        'cva_charge': 'sum',
        'counterparty_pd': 'first',
        'counterparty_lgd': 'first',
        'counterparty_rating': 'first'
    }).reset_index()
    
    # Calcul des métriques globales
    total_notional = derivatives_df['notional_amount'].sum()
    total_gross_mtm = derivatives_df['mtm_value'].sum()
    total_ead = derivatives_df['ead_sa_ccr'].sum()
    total_net_exposure = derivatives_df['net_exposure'].sum()
    total_cva = derivatives_df['cva_charge'].sum()
    
    # Netting benefit
    gross_exposure = derivatives_df['ead_sa_ccr'].sum()
    net_exposure_total = derivatives_df['net_exposure'].sum()
    netting_benefit = (gross_exposure - net_exposure_total) / gross_exposure if gross_exposure > 0 else 0
    
    # Collateral coverage
    collateralized_trades = derivatives_df[derivatives_df['has_collateral'] == True]
    collateral_coverage = len(collateralized_trades) / len(derivatives_df) if len(derivatives_df) > 0 else 0
    
    # Concentration par contrepartie
    counterparty_concentration = derivatives_df.groupby('counterparty_name')['net_exposure'].sum().sort_values(ascending=False)
    top_5_concentration = counterparty_concentration.head(5).sum() / total_net_exposure if total_net_exposure > 0 else 0
    
    # Wrong-way risk (approximation)
    high_risk_counterparties = derivatives_df[derivatives_df['counterparty_pd'] > 0.01]
    wrong_way_risk_exposure = high_risk_counterparties['net_exposure'].sum()
    
    summary_metrics = {
        'total_notional': total_notional,
        'total_gross_mtm': total_gross_mtm,
        'total_ead_sa_ccr': total_ead,
        'total_net_exposure': total_net_exposure,
        'total_cva_charge': total_cva,
        'netting_benefit_pct': netting_benefit * 100,
        'collateral_coverage_pct': collateral_coverage * 100,
        'top_5_concentration_pct': top_5_concentration * 100,
        'wrong_way_risk_exposure': wrong_way_risk_exposure,
        'num_counterparties': derivatives_df['counterparty_name'].nunique(),
        'num_netting_sets': derivatives_df['netting_set_id'].nunique(),
        'avg_maturity': derivatives_df['maturity_years'].mean()
    }
    
    return netting_analysis, summary_metrics

def calculate_sa_ccr_capital(derivatives_df):
    """Calculer les exigences de capital selon SA-CCR"""
    
    capital_results = []
    
    # Grouper par netting set pour les calculs SA-CCR
    for netting_set, group in derivatives_df.groupby('netting_set_id'):
        
        # Replacement Cost (RC) au niveau du netting set
        net_mtm = group['mtm_value'].sum()
        replacement_cost = max(net_mtm, 0)
        
        # Potential Future Exposure (PFE) au niveau du netting set
        # Agrégation avec corrélations
        total_pfe = 0
        for asset_class in group['asset_class'].unique():
            class_group = group[group['asset_class'] == asset_class]
            class_pfe = class_group['pfe_amount'].sum()
            total_pfe += class_pfe  # Simplification sans corrélations croisées
        
        # EAD SA-CCR
        alpha = 1.4  # Facteur alpha réglementaire
        ead_sa_ccr = alpha * (replacement_cost + total_pfe)
        
        # Ajustement pour collatéral
        collateral_adjustment = group['collateral_amount'].sum()
        net_ead = max(0, ead_sa_ccr - collateral_adjustment)
        
        # Risk Weight selon le rating de la contrepartie
        counterparty_rating = group['counterparty_rating'].iloc[0]
        risk_weight = get_counterparty_risk_weight(counterparty_rating)
        
        # RWA
        rwa_amount = net_ead * risk_weight
        
        # Capital requis (8%)
        capital_required = rwa_amount * 0.08
        
        capital_result = {
            'netting_set_id': netting_set,
            'counterparty_name': group['counterparty_name'].iloc[0],
            'counterparty_rating': counterparty_rating,
            'num_trades': len(group),
            'gross_notional': group['notional_amount'].sum(),
            'net_mtm': net_mtm,
            'replacement_cost': replacement_cost,
            'pfe_amount': total_pfe,
            'ead_sa_ccr': ead_sa_ccr,
            'collateral_amount': collateral_adjustment,
            'net_ead': net_ead,
            'risk_weight': risk_weight,
            'rwa_amount': rwa_amount,
            'capital_required': capital_required
        }
        
        capital_results.append(capital_result)
    
    return safe_dataframe_creation(capital_results)

def get_counterparty_risk_weight(rating):
    """Obtenir le risk weight selon le rating de la contrepartie"""
    
    risk_weights = {
        'AAA': 0.20,
        'AA': 0.20,
        'A': 0.50,
        'BBB': 1.00,
        'BB': 1.00,
        'B': 1.50,
        'CCC': 1.50,
        'Unrated': 1.00
    }
    
    return risk_weights.get(rating, 1.00)

def show_counterparty_risk_advanced():
    """Page de calcul du risque de contrepartie sur dérivés"""
    st.markdown("## ⚡ Risque de Contrepartie - Produits Dérivés")
    
    st.markdown("""
    Cette section calcule le **risque de contrepartie sur les produits dérivés** selon les dernières 
    réglementations CRR3, incluant :
    
    - **SA-CCR** (Standardised Approach for Counterparty Credit Risk)
    - **CVA** (Credit Valuation Adjustment) et charges de capital
    - **Netting** et bénéfices de compensation
    - **Collatéral** et réduction des expositions
    - **Wrong-way risk** et concentration des contreparties
    """)
    
    # Configuration des paramètres
    st.markdown("### ⚙️ Configuration du Portefeuille de Dérivés")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_derivatives = st.slider("Nombre de Dérivés", 100, 2000, 500)
    
    with col2:
        include_exotic = st.checkbox("Inclure Produits Exotiques", value=False)
    
    with col3:
        stress_scenario = st.selectbox("Scénario de Stress", 
                                     ["Baseline", "Adverse", "Severely Adverse"])
    
    # Génération du portefeuille
    if st.button("🔄 Générer Portefeuille de Dérivés", type="primary"):
        with st.spinner("Génération du portefeuille de dérivés..."):
            derivatives_portfolio = generate_derivatives_portfolio(num_derivatives)
            st.session_state['derivatives_portfolio'] = derivatives_portfolio
            
            st.success(f"✅ Portefeuille de {len(derivatives_portfolio)} dérivés généré avec succès !")
    
    if 'derivatives_portfolio' in st.session_state:
        derivatives_portfolio = st.session_state['derivatives_portfolio']
        
        # Vue d'ensemble du portefeuille
        st.markdown("### 📊 Vue d'Ensemble du Portefeuille")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_notional = derivatives_portfolio['notional_amount'].sum()
            st.metric("Notionnel Total", f"{total_notional/1e9:.1f} Mrd EUR")
        
        with col2:
            total_mtm = derivatives_portfolio['mtm_value'].sum()
            st.metric("MTM Total", f"{total_mtm/1e6:.1f} M EUR")
        
        with col3:
            num_counterparties = derivatives_portfolio['counterparty_name'].nunique()
            st.metric("Nb Contreparties", num_counterparties)
        
        with col4:
            avg_maturity = derivatives_portfolio['maturity_years'].mean()
            st.metric("Maturité Moyenne", f"{avg_maturity:.1f} ans")
        
        with col5:
            collateral_rate = (derivatives_portfolio['has_collateral'].sum() / 
                             len(derivatives_portfolio) * 100)
            st.metric("Taux Collatéral", f"{collateral_rate:.1f}%")
        
        # Analyse par type de dérivé
        st.markdown("#### 📈 Répartition par Type de Dérivé")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Répartition par type
            type_analysis = derivatives_portfolio.groupby('derivative_type').agg({
                'notional_amount': 'sum',
                'ead_sa_ccr': 'sum',
                'derivative_id': 'count'
            }).reset_index()
            
            type_analysis.columns = ['Type', 'Notionnel', 'EAD SA-CCR', 'Nombre']
            
            fig = px.pie(type_analysis, values='Notionnel', names='Type',
                       title="Répartition du Notionnel par Type")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Répartition par classe d'actif
            asset_analysis = derivatives_portfolio.groupby('asset_class').agg({
                'ead_sa_ccr': 'sum',
                'cva_charge': 'sum'
            }).reset_index()
            
            fig = px.bar(asset_analysis, x='asset_class', y='ead_sa_ccr',
                       title="EAD SA-CCR par Classe d'Actif")
            fig.update_layout(xaxis_title="Classe d'Actif")
            fig.update_layout(yaxis_title="EAD SA-CCR (EUR)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Calcul des métriques de risque de contrepartie
        if st.button("⚡ Calculer Risque de Contrepartie", type="secondary"):
            with st.spinner("Calcul des métriques de risque de contrepartie..."):
                netting_analysis, summary_metrics = calculate_counterparty_risk_metrics(derivatives_portfolio)
                capital_results = calculate_sa_ccr_capital(derivatives_portfolio)
                
                st.session_state['netting_analysis'] = netting_analysis
                st.session_state['counterparty_summary'] = summary_metrics
                st.session_state['sa_ccr_capital'] = capital_results
                
                st.success("✅ Calculs de risque de contrepartie terminés !")
        
        if 'counterparty_summary' in st.session_state:
            summary_metrics = st.session_state['counterparty_summary']
            netting_analysis = st.session_state['netting_analysis']
            capital_results = st.session_state['sa_ccr_capital']
            
            # Métriques de risque de contrepartie
            st.markdown("### ⚡ Métriques de Risque de Contrepartie")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("EAD SA-CCR Total", f"{summary_metrics['total_ead_sa_ccr']/1e6:.1f} M EUR")
            
            with col2:
                st.metric("Exposition Nette", f"{summary_metrics['total_net_exposure']/1e6:.1f} M EUR")
            
            with col3:
                st.metric("Bénéfice Netting", f"{summary_metrics['netting_benefit_pct']:.1f}%")
            
            with col4:
                st.metric("Couverture Collatéral", f"{summary_metrics['collateral_coverage_pct']:.1f}%")
            
            with col5:
                st.metric("Charge CVA Totale", f"{summary_metrics['total_cva_charge']/1e6:.1f} M EUR")
            
            # Analyse par netting set
            st.markdown("#### 🔗 Analyse par Netting Set")
            
            # Top 10 des expositions
            top_netting_sets = netting_analysis.nlargest(10, 'net_exposure')
            
            fig = px.bar(top_netting_sets, x='counterparty_name', y='net_exposure',
                       color='counterparty_rating',
                       title="Top 10 des Expositions Nettes par Contrepartie")
            fig.update_layout(xaxis_tickangle=-45)
            fig.update_layout(xaxis_title="Contrepartie")
            fig.update_layout(yaxis_title="Exposition Nette (EUR)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé des netting sets
            with st.expander("📋 Détail des Netting Sets"):
                display_netting = netting_analysis.copy()
                display_netting['notional_amount'] = display_netting['notional_amount'].round(0)
                display_netting['net_exposure'] = display_netting['net_exposure'].round(0)
                display_netting['cva_charge'] = display_netting['cva_charge'].round(0)
                
                display_netting.columns = [
                    'Netting Set ID', 'Contrepartie', 'Notionnel', 'MTM', 
                    'EAD SA-CCR', 'Exposition Nette', 'Charge CVA', 
                    'PD', 'LGD', 'Rating'
                ]
                
                st.dataframe(display_netting, use_container_width=True)
            
            # Calculs de capital SA-CCR
            st.markdown("#### 💰 Exigences de Capital SA-CCR")
            
            total_rwa = capital_results['rwa_amount'].sum()
            total_capital = capital_results['capital_required'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("RWA Total", f"{total_rwa/1e6:.1f} M EUR")
            
            with col2:
                st.metric("Capital Requis", f"{total_capital/1e6:.1f} M EUR")
            
            with col3:
                capital_ratio = (total_capital / total_rwa * 100) if total_rwa > 0 else 0
                st.metric("Ratio Capital", f"{capital_ratio:.1f}%")
            
            with col4:
                avg_risk_weight = (total_rwa / summary_metrics['total_net_exposure']) if summary_metrics['total_net_exposure'] > 0 else 0
                st.metric("Risk Weight Moyen", f"{avg_risk_weight:.1%}")
            
            # Répartition du capital par rating
            capital_by_rating = capital_results.groupby('counterparty_rating').agg({
                'capital_required': 'sum',
                'rwa_amount': 'sum',
                'net_ead': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(capital_by_rating, values='capital_required', names='counterparty_rating',
                           title="Répartition du Capital par Rating")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(capital_by_rating, x='counterparty_rating', y='rwa_amount',
                           title="RWA par Rating de Contrepartie")
                fig.update_layout(xaxis_title="Rating")
                fig.update_layout(yaxis_title="RWA (EUR)")
                st.plotly_chart(fig, use_container_width=True)
            
            # Analyse des concentrations
            st.markdown("#### 🎯 Analyse des Concentrations")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Top 5 Concentration", f"{summary_metrics['top_5_concentration_pct']:.1f}%")
            
            with col2:
                st.metric("Nb Contreparties", summary_metrics['num_counterparties'])
            
            with col3:
                st.metric("Wrong-Way Risk", f"{summary_metrics['wrong_way_risk_exposure']/1e6:.1f} M EUR")
            
            # Heatmap des expositions par contrepartie et type
            st.markdown("#### 🔥 Heatmap des Expositions")
            
            heatmap_data = derivatives_portfolio.pivot_table(
                values='net_exposure',
                index='counterparty_name',
                columns='asset_class',
                aggfunc='sum',
                fill_value=0
            )
            
            fig = px.imshow(heatmap_data.values,
                          x=heatmap_data.columns,
                          y=heatmap_data.index,
                          title="Expositions par Contrepartie et Classe d'Actif",
                          color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
            
            # Stress testing
            st.markdown("#### 📈 Stress Testing")
            
            if stress_scenario != "Baseline":
                stress_multiplier = 1.5 if stress_scenario == "Adverse" else 2.0
                
                stressed_cva = summary_metrics['total_cva_charge'] * stress_multiplier
                stressed_capital = total_capital * stress_multiplier
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("CVA Stressée", f"{stressed_cva/1e6:.1f} M EUR", 
                             delta=f"+{(stressed_cva - summary_metrics['total_cva_charge'])/1e6:.1f} M EUR")
                
                with col2:
                    st.metric("Capital Stressé", f"{stressed_capital/1e6:.1f} M EUR",
                             delta=f"+{(stressed_capital - total_capital)/1e6:.1f} M EUR")
                
                with col3:
                    impact_pct = ((stressed_capital - total_capital) / total_capital * 100) if total_capital > 0 else 0
                    st.metric("Impact Stress", f"+{impact_pct:.1f}%")
            
            # Sauvegarde pour export
            st.session_state['counterparty_risk_complete'] = {
                'derivatives_portfolio': derivatives_portfolio,
                'netting_analysis': netting_analysis,
                'capital_results': capital_results,
                'summary_metrics': summary_metrics
            }
            
            # Export
            st.markdown("#### 📥 Export des Résultats")
            
            if st.button("📊 Exporter Analyse Risque Contrepartie"):
                # Créer un rapport de synthèse
                report_data = {
                    'Métrique': [
                        'Nombre de Dérivés',
                        'Notionnel Total (M EUR)',
                        'EAD SA-CCR Total (M EUR)',
                        'Exposition Nette (M EUR)',
                        'RWA Total (M EUR)',
                        'Capital Requis (M EUR)',
                        'Charge CVA (M EUR)',
                        'Bénéfice Netting (%)',
                        'Couverture Collatéral (%)',
                        'Top 5 Concentration (%)'
                    ],
                    'Valeur': [
                        len(derivatives_portfolio),
                        f"{summary_metrics['total_notional']/1e6:.1f}",
                        f"{summary_metrics['total_ead_sa_ccr']/1e6:.1f}",
                        f"{summary_metrics['total_net_exposure']/1e6:.1f}",
                        f"{total_rwa/1e6:.1f}",
                        f"{total_capital/1e6:.1f}",
                        f"{summary_metrics['total_cva_charge']/1e6:.1f}",
                        f"{summary_metrics['netting_benefit_pct']:.1f}",
                        f"{summary_metrics['collateral_coverage_pct']:.1f}",
                        f"{summary_metrics['top_5_concentration_pct']:.1f}"
                    ]
                }
                
                report_df = safe_dataframe_creation(report_data)
                
                # Convertir en CSV pour téléchargement
                csv_data = report_df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger Rapport Risque Contrepartie",
                    data=csv_data,
                    file_name=f"counterparty_risk_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
                st.success("✅ Rapport de risque de contrepartie prêt au téléchargement !")
