"""
Page de gestion avancée des runs (I13).
6 onglets: Liste, Détails, Comparaison, Clonage, Export/Import, Maintenance.
"""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.services.run_management_service import (
    cleanup_old_runs,
    clone_run,
    compare_runs,
    compute_checksum,
    delete_run,
    export_run,
    get_run_details,
    import_run,
    list_comparisons,
    list_runs,
    save_comparison,
    toggle_favorite,
    update_notes,
    update_tags,
    validate_run,
)

st.set_page_config(page_title="Run Management", page_icon="🔧", layout="wide")

st.title("🔧 Gestion Avancée des Runs")
st.markdown("**Itération I13** : Interface complète de gestion des runs de simulation")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Liste des Runs",
    "🔍 Détails",
    "📊 Comparaison",
    "📋 Clonage",
    "💾 Export/Import",
    "🧹 Maintenance"
])

# ============================================================================
# TAB 1: Liste des Runs
# ============================================================================
with tab1:
    st.header("📋 Liste des Runs")

    # Filtres
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Statut",
            options=["Tous", "completed", "pending", "failed"],
            index=0
        )
        status_filter = None if status_filter == "Tous" else status_filter

    with col2:
        favorites_only = st.checkbox("Favoris uniquement")

    with col3:
        days_filter = st.selectbox(
            "Période",
            options=["Tous", "7 derniers jours", "30 derniers jours", "90 derniers jours"],
            index=0
        )

    with col4:
        limit = st.number_input("Résultats par page", min_value=10, max_value=100, value=20, step=10)

    # Calculer date_from selon filtre
    date_from = None
    if days_filter == "7 derniers jours":
        date_from = datetime.now() - timedelta(days=7)
    elif days_filter == "30 derniers jours":
        date_from = datetime.now() - timedelta(days=30)
    elif days_filter == "90 derniers jours":
        date_from = datetime.now() - timedelta(days=90)

    # Récupérer les runs
    try:
        runs_list, total_count = list_runs(
            status_filter=status_filter,
            favorites_only=favorites_only,
            date_from=date_from,
            limit=limit,
            offset=0,
        )

        st.info(f"**{total_count}** runs trouvés")

        if runs_list:
            # Convertir en DataFrame pour affichage
            df_runs = pd.DataFrame(runs_list)

            # Formater les colonnes
            df_runs['run_date'] = pd.to_datetime(df_runs['run_date']).dt.strftime('%Y-%m-%d %H:%M')
            df_runs['duration'] = df_runs['duration_seconds'].apply(
                lambda x: f"{x:.1f}s" if pd.notna(x) else "N/A"
            )
            df_runs['favorite'] = df_runs['is_favorite'].apply(lambda x: "⭐" if x else "")

            # Sélectionner colonnes à afficher
            display_cols = ['run_id', 'run_date', 'status', 'total_exposures', 'duration', 'favorite']
            df_display = df_runs[display_cols].copy()
            df_display.columns = ['Run ID', 'Date', 'Statut', 'Exposures', 'Durée', 'Fav']

            st.dataframe(df_display, use_container_width=True, height=400)

            # Actions sur les runs
            st.subheader("Actions")

            col_action1, col_action2, col_action3 = st.columns(3)

            with col_action1:
                selected_run = st.selectbox(
                    "Sélectionner un run",
                    options=[r['run_id'] for r in runs_list],
                    key="select_run_list"
                )

            with col_action2:
                if st.button("⭐ Toggle Favori"):
                    try:
                        new_status = toggle_favorite(selected_run)
                        st.success(f"Favori: {'✅' if new_status else '❌'}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

            with col_action3:
                if st.button("🗑️ Supprimer", type="secondary"):
                    if st.session_state.get('confirm_delete') == selected_run:
                        try:
                            delete_run(selected_run)
                            st.success(f"Run {selected_run} supprimé")
                            st.session_state['confirm_delete'] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                    else:
                        st.session_state['confirm_delete'] = selected_run
                        st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")

        else:
            st.warning("Aucun run trouvé avec ces filtres")

    except Exception as e:
        st.error(f"Erreur lors de la récupération des runs: {e}")

# ============================================================================
# TAB 2: Détails d'un Run
# ============================================================================
with tab2:
    st.header("🔍 Détails d'un Run")

    # Sélection du run
    try:
        runs_list_details, _ = list_runs(limit=100)
        run_ids_details = [r['run_id'] for r in runs_list_details]

        if run_ids_details:
            selected_run_details = st.selectbox(
                "Sélectionner un run",
                options=run_ids_details,
                key="select_run_details"
            )

            if st.button("🔄 Rafraîchir les détails"):
                st.rerun()

            # Récupérer les détails
            details = get_run_details(selected_run_details)

            if details:
                # Métadonnées
                st.subheader("📋 Métadonnées")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Run ID", details['run_id'])
                    st.metric("Statut", details['status'])

                with col2:
                    st.metric("Date", details['run_date'].strftime('%Y-%m-%d %H:%M'))
                    st.metric("Durée", f"{details['duration_seconds']:.1f}s" if details['duration_seconds'] else "N/A")

                with col3:
                    st.metric("Exposures", f"{details['total_exposures']:,}")
                    st.metric("Notional Total", f"{details['total_notional']:,.0f}" if details['total_notional'] else "N/A")

                with col4:
                    st.metric("Favori", "⭐ Oui" if details['is_favorite'] else "Non")
                    st.metric("Parent Run", details['parent_run_id'] or "Aucun")

                # Checksum
                if details['checksum']:
                    st.code(f"Checksum: {details['checksum']}", language="text")

                # Tags
                st.subheader("🏷️ Tags")
                current_tags = details['tags']
                new_tags = st.text_input(
                    "Tags (séparés par des virgules)",
                    value=", ".join(current_tags) if current_tags else "",
                    key="tags_input"
                )

                if st.button("💾 Sauvegarder les tags"):
                    tags_list = [t.strip() for t in new_tags.split(",") if t.strip()]
                    try:
                        update_tags(selected_run_details, tags_list)
                        st.success("Tags mis à jour")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

                # Notes
                st.subheader("📝 Notes")
                current_notes = details['notes'] or ""
                new_notes = st.text_area(
                    "Notes",
                    value=current_notes,
                    height=100,
                    key="notes_input"
                )

                if st.button("💾 Sauvegarder les notes"):
                    try:
                        update_notes(selected_run_details, new_notes)
                        st.success("Notes mises à jour")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

                # Statistiques par produit
                st.subheader("📊 Statistiques par Produit")

                if details['stats_by_product']:
                    df_stats = pd.DataFrame(details['stats_by_product'])

                    # Graphique
                    fig = px.bar(
                        df_stats,
                        x='product_type',
                        y='count',
                        title="Nombre d'exposures par produit",
                        labels={'product_type': 'Produit', 'count': 'Nombre'},
                        color='total_ead',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Table
                    st.dataframe(df_stats, use_container_width=True)

                # Logs
                st.subheader("📜 Logs d'exécution")

                if details['logs']:
                    df_logs = pd.DataFrame(details['logs'])
                    df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    st.dataframe(df_logs, use_container_width=True, height=300)
                else:
                    st.info("Aucun log disponible")

                # Validation
                st.subheader("✅ Validation")

                if st.button("🔍 Valider l'intégrité"):
                    with st.spinner("Validation en cours..."):
                        validation = validate_run(selected_run_details)

                        if validation['valid']:
                            st.success("✅ Run valide")
                        else:
                            st.error("❌ Run invalide")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Count Valid",
                                "✅" if validation['count_valid'] else "❌",
                                f"{validation['actual_count']} / {validation['expected_count']}"
                            )

                        with col2:
                            st.metric(
                                "Checksum Valid",
                                "✅" if validation['checksum_valid'] else "❌"
                            )

                        with col3:
                            st.metric(
                                "Données nulles",
                                f"EAD: {validation['null_ead_count']}, PD: {validation['null_pd_count']}"
                            )

            else:
                st.warning("Run non trouvé")

        else:
            st.warning("Aucun run disponible")

    except Exception as e:
        st.error(f"Erreur: {e}")




# ============================================================================
# TAB 3: Comparaison de Runs
# ============================================================================
with tab3:
    st.header("📊 Comparaison de Runs")

    try:
        runs_list_comp, _ = list_runs(limit=100)
        run_ids_comp = [r['run_id'] for r in runs_list_comp]

        if len(run_ids_comp) >= 2:
            selected_runs_comp = st.multiselect(
                "Sélectionner 2-4 runs à comparer",
                options=run_ids_comp,
                max_selections=4,
                key="select_runs_comparison"
            )

            if len(selected_runs_comp) >= 2:
                if st.button("📊 Comparer"):
                    with st.spinner("Comparaison en cours..."):
                        comparison = compare_runs(selected_runs_comp)

                        # Métadonnées comparatives
                        st.subheader("📋 Métadonnées")
                        df_meta = pd.DataFrame(comparison['runs_metadata'])
                        df_meta['run_date'] = pd.to_datetime(df_meta['run_date']).dt.strftime('%Y-%m-%d %H:%M')
                        st.dataframe(df_meta, use_container_width=True)

                        # Graphiques comparatifs
                        st.subheader("📊 Métriques Comparatives")

                        col1, col2 = st.columns(2)

                        with col1:
                            # Graphique exposures
                            fig1 = go.Figure()
                            fig1.add_trace(go.Bar(
                                x=df_meta['run_id'],
                                y=df_meta['total_exposures'],
                                name='Total Exposures',
                                marker_color='lightblue'
                            ))
                            fig1.update_layout(title="Nombre d'Exposures", xaxis_title="Run ID", yaxis_title="Count")
                            st.plotly_chart(fig1, use_container_width=True)

                        with col2:
                            # Graphique EAD
                            fig2 = go.Figure()
                            fig2.add_trace(go.Bar(
                                x=df_meta['run_id'],
                                y=df_meta['total_ead'],
                                name='Total EAD',
                                marker_color='lightgreen'
                            ))
                            fig2.update_layout(title="Total EAD", xaxis_title="Run ID", yaxis_title="EAD")
                            st.plotly_chart(fig2, use_container_width=True)

                        # Comparaison par produit
                        st.subheader("📦 Comparaison par Produit")

                        # Construire DataFrame pour comparaison
                        product_comparison = []
                        for run_id, products in comparison['exposures_comparison'].items():
                            for product_type, stats in products.items():
                                product_comparison.append({
                                    'run_id': run_id,
                                    'product_type': product_type,
                                    'count': stats['count'],
                                    'total_ead': stats['total_ead'],
                                })

                        if product_comparison:
                            df_prod_comp = pd.DataFrame(product_comparison)

                            # Graphique groupé
                            fig3 = px.bar(
                                df_prod_comp,
                                x='product_type',
                                y='count',
                                color='run_id',
                                barmode='group',
                                title="Nombre d'exposures par produit et par run"
                            )
                            st.plotly_chart(fig3, use_container_width=True)

                            # Table pivot
                            pivot_table = df_prod_comp.pivot_table(
                                index='product_type',
                                columns='run_id',
                                values='count',
                                fill_value=0
                            )
                            st.dataframe(pivot_table, use_container_width=True)

                        # Sauvegarder la comparaison
                        st.subheader("💾 Sauvegarder cette comparaison")

                        comp_name = st.text_input("Nom de la comparaison", key="comp_name")
                        comp_notes = st.text_area("Notes", key="comp_notes")

                        if st.button("💾 Sauvegarder"):
                            if comp_name:
                                try:
                                    comp_id = save_comparison(comp_name, selected_runs_comp, comp_notes)
                                    st.success(f"Comparaison sauvegardée: {comp_id}")
                                except Exception as e:
                                    st.error(f"Erreur: {e}")
                            else:
                                st.warning("Veuillez entrer un nom")
            else:
                st.info("Sélectionnez au moins 2 runs pour comparer")

        else:
            st.warning("Au moins 2 runs sont nécessaires pour la comparaison")

        # Liste des comparaisons sauvegardées
        st.subheader("📚 Comparaisons Sauvegardées")

        saved_comps = list_comparisons()
        if saved_comps:
            df_saved = pd.DataFrame(saved_comps)
            df_saved['created_at'] = pd.to_datetime(df_saved['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            df_saved['run_ids_str'] = df_saved['run_ids'].apply(lambda x: ", ".join(x[:2]) + "..." if len(x) > 2 else ", ".join(x))
            st.dataframe(df_saved[['name', 'run_ids_str', 'created_at', 'notes']], use_container_width=True)
        else:
            st.info("Aucune comparaison sauvegardée")

    except Exception as e:
        st.error(f"Erreur: {e}")

# ============================================================================
# TAB 4: Clonage
# ============================================================================
with tab4:
    st.header("📋 Clonage de Run")

    try:
        runs_list_clone, _ = list_runs(limit=100)
        run_ids_clone = [r['run_id'] for r in runs_list_clone]

        if run_ids_clone:
            source_run = st.selectbox(
                "Sélectionner le run source",
                options=run_ids_clone,
                key="select_run_clone"
            )

            st.subheader("🔧 Modifications")

            col1, col2 = st.columns(2)

            with col1:
                modify_seed = st.checkbox("Modifier le seed")
                if modify_seed:
                    new_seed = st.number_input("Nouveau seed", min_value=0, value=42, key="new_seed")
                else:
                    new_seed = None

            with col2:
                modify_exposures = st.checkbox("Modifier le nombre d'exposures")
                if modify_exposures:
                    new_num_exposures = st.number_input("Nombre d'exposures", min_value=100, value=10000, step=1000, key="new_num_exp")
                else:
                    new_num_exposures = None

            if st.button("📋 Cloner le Run"):
                modifications = {}
                if new_seed is not None:
                    modifications['seed'] = new_seed
                if new_num_exposures is not None:
                    modifications['num_exposures'] = new_num_exposures

                with st.spinner("Clonage en cours..."):
                    try:
                        new_run_id = clone_run(source_run, modifications)
                        st.success(f"✅ Run cloné avec succès: {new_run_id}")
                        st.info("⚠️ Note: Les exposures ne sont pas générées automatiquement. Allez dans la page Pipeline pour générer les données.")
                    except Exception as e:
                        st.error(f"Erreur lors du clonage: {e}")

        else:
            st.warning("Aucun run disponible pour clonage")

    except Exception as e:
        st.error(f"Erreur: {e}")

# ============================================================================
# TAB 5: Export/Import
# ============================================================================
with tab5:
    st.header("💾 Export/Import de Runs")

    # Export
    st.subheader("📤 Export")

    try:
        runs_list_export, _ = list_runs(limit=100)
        run_ids_export = [r['run_id'] for r in runs_list_export]

        if run_ids_export:
            col1, col2 = st.columns(2)

            with col1:
                run_to_export = st.selectbox(
                    "Sélectionner un run",
                    options=run_ids_export,
                    key="select_run_export"
                )

            with col2:
                export_format = st.selectbox(
                    "Format",
                    options=["json", "parquet"],
                    key="export_format"
                )

            if st.button("📤 Exporter"):
                with st.spinner("Export en cours..."):
                    try:
                        data_bytes, filename = export_run(run_to_export, export_format)

                        st.download_button(
                            label=f"⬇️ Télécharger {filename}",
                            data=data_bytes,
                            file_name=filename,
                            mime="application/octet-stream"
                        )

                        st.success(f"✅ Export réussi: {filename}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'export: {e}")

        else:
            st.warning("Aucun run disponible pour export")

    except Exception as e:
        st.error(f"Erreur: {e}")

    st.divider()

    # Import
    st.subheader("📥 Import")

    uploaded_file = st.file_uploader(
        "Sélectionner un fichier JSON",
        type=["json"],
        key="import_file"
    )

    if uploaded_file is not None:
        if st.button("📥 Importer"):
            with st.spinner("Import en cours..."):
                try:
                    # Sauvegarder temporairement
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    # Importer
                    new_run_id = import_run(tmp_path)

                    st.success(f"✅ Run importé avec succès: {new_run_id}")

                    # Nettoyer
                    import os
                    os.unlink(tmp_path)

                except Exception as e:
                    st.error(f"Erreur lors de l'import: {e}")

# ============================================================================
# TAB 6: Maintenance
# ============================================================================
with tab6:
    st.header("🧹 Maintenance")

    # Nettoyage automatique
    st.subheader("🗑️ Nettoyage Automatique")

    col1, col2 = st.columns(2)

    with col1:
        days_threshold = st.number_input(
            "Supprimer les runs non favoris plus anciens que (jours)",
            min_value=7,
            max_value=365,
            value=30,
            step=7,
            key="days_threshold"
        )

    with col2:
        dry_run = st.checkbox("Mode simulation (ne supprime pas réellement)", value=True, key="dry_run")

    if st.button("🧹 Lancer le nettoyage"):
        with st.spinner("Nettoyage en cours..."):
            try:
                stats = cleanup_old_runs(days_threshold, dry_run)

                st.subheader("📊 Résultats")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Runs trouvés", stats['runs_found'])

                with col2:
                    st.metric("Runs supprimés", stats['runs_deleted'])

                with col3:
                    st.metric("Exposures supprimées", stats['exposures_deleted'])

                if stats['run_ids']:
                    st.write("**Runs concernés:**")
                    for run_id in stats['run_ids']:
                        st.code(run_id)

                if dry_run:
                    st.info("ℹ️ Mode simulation activé. Aucune suppression réelle n'a été effectuée.")
                else:
                    st.success("✅ Nettoyage terminé")

            except Exception as e:
                st.error(f"Erreur lors du nettoyage: {e}")

    st.divider()

    # Recalcul des checksums
    st.subheader("🔐 Recalcul des Checksums")

    try:
        runs_list_checksum, _ = list_runs(limit=100)
        run_ids_checksum = [r['run_id'] for r in runs_list_checksum]

        if run_ids_checksum:
            run_checksum = st.selectbox(
                "Sélectionner un run",
                options=run_ids_checksum,
                key="select_run_checksum"
            )

            if st.button("🔐 Recalculer le checksum"):
                with st.spinner("Calcul en cours..."):
                    try:
                        checksum = compute_checksum(run_checksum)
                        st.success("✅ Checksum calculé")
                        st.code(checksum)
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        else:
            st.warning("Aucun run disponible")

    except Exception as e:
        st.error(f"Erreur: {e}")

