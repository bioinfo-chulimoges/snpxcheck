"""Main application module.

This module contains the Streamlit application interface and main logic
for the SNPXPlex identity verification system.
"""

import streamlit as st
import pandas as pd
from src.services.identity_vigilance import IdentityVigilanceService
from src.visualization.plots import (
    highlight_status,
    insert_blank_rows_between_groups,
)
from src.utils.models import SessionState
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Initialize the service
service = IdentityVigilanceService()


def render_intra_comparison(df_intra: pd.DataFrame, error_count: int):
    """Render the intra-patient comparison section.

    Args:
        df_intra (pd.DataFrame): DataFrame containing intra-patient comparison results.
        error_count (int): Number of errors found in the comparison.

    Returns:
        pd.DataFrame: DataFrame with status information for display.
    """
    st.subheader("Comparaison intra-patient", divider="grey")
    if error_count > 0:
        st.error(f"Erreur : {error_count} échantillon(s) incohérent(s) détecté(s).")
    else:
        st.success("Tous les échantillons sont cohérents.")

    styled_df = df_intra.style.apply(highlight_status, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    return df_intra[
        ["Patient", "Sample Name", "Genre", "status_description", "status_type"]
    ].copy()


def render_inter_comparison(df_inter: pd.DataFrame):
    """Render the inter-patient comparison section.

    Args:
        df_inter (pd.DataFrame): DataFrame containing inter-patient comparison results.
    """
    st.subheader("Comparaison inter-patient", divider="grey")
    if df_inter.empty:
        st.success("Tous les échantillons sont cohérents.")
    else:
        df_display = insert_blank_rows_between_groups(df_inter, "signature_hash")
        st.error("Incohérence(s) détectée(s) entre les échantillons.")
        st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_heatmap(heatmap):
    """Render the heatmap section.

    Args:
        heatmap: Plotly figure containing the heatmap visualization.
    """
    st.subheader(
        "Matrice de comparaison des patients (% allèles en commun) :", divider="grey"
    )
    if heatmap is not None:
        st.plotly_chart(heatmap, use_container_width=True)
    else:
        st.warning("Aucune donnée à afficher.")


def generate_pdf_report(session_state: SessionState) -> Path:
    """Generate and download the PDF report.

    Args:
        session_state (SessionState): Current session state containing analysis results.

    Returns:
        Path: Path to the generated PDF file.
    """
    if not session_state.comparison_result:
        st.error("Aucune donnée ou graphique disponible pour générer le rapport.")
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
        service.generate_pdf_report(
            df_intra=session_state.comparison_result.df_intra,
            df_inter=session_state.comparison_result.df_inter,
            heatmap=session_state.comparison_result.heatmap,
            metadata=session_state.metadata.__dict__,
            errors_intra=session_state.comparison_result.errors_intra,
            errors_inter=session_state.comparison_result.errors_inter,
            output_path=pdf_file.name,
        )

        with open(pdf_file.name, "rb") as f:
            st.download_button(
                "Télécharger le rapport PDF",
                f,
                file_name="rapport_identitovigilance.pdf",
            )

        return Path(pdf_file.name)


def main():
    """Main application function.

    This function sets up the Streamlit interface and handles the main application logic,
    including file upload, data processing, analysis, and report generation.
    """
    # Configure the Streamlit app
    st.set_page_config(
        page_title="Identitovigilence SNPXPlex",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state if not already done
    if "comparison_result" not in st.session_state:
        st.session_state.comparison_result = None

    with st.sidebar:
        st.subheader("Identitovigilance - contrôle d'extraction", divider="rainbow")

        # File upload
        uploaded_file = st.file_uploader(
            "Choisissez un fichier GeneMapper", type=["txt"]
        )

        interpreter = st.text_input("Interprétateur :", "")
        extraction_week = st.text_input("Semaine d'extraction :", "")
        comment = st.text_area("Commentaire :", "")
        serie = st.selectbox(
            "Série validée ?",
            ("Oui", "Non"),
            index=None,
            placeholder="",
        )

        # Add a separator
        st.divider()

    if uploaded_file is not None:
        # Load and validate file
        df, error = service.load_and_validate_file(uploaded_file)
        if error:
            st.error(error)
            return

        # Prepare data
        prepared_data = service.prepare_data(df)

        # Perform comparisons
        df_intra, errors_intra = service.perform_intra_comparison(prepared_data)
        df_inter, errors_inter = service.perform_inter_comparison(prepared_data)

        # Generate heatmap
        heatmap = service.generate_heatmap(prepared_data)

        # Store results in session state
        st.session_state.comparison_result = {
            "df_intra": df_intra,
            "df_inter": df_inter,
            "heatmap": heatmap,
            "errors_intra": errors_intra,
            "errors_inter": errors_inter,
        }

        # Display results
        st.subheader("Résultats de l'analyse")

        # Intra-patient comparison
        render_intra_comparison(df_intra, errors_intra)

        # Inter-patient comparison
        render_inter_comparison(df_inter)

        # Display heatmap
        render_heatmap(heatmap)

        # Add the PDF report generation button in the sidebar
        with st.sidebar:
            if st.button("Générer rapport PDF", type="primary"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    # Get current date and time
                    current_datetime = datetime.now()
                    formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M")

                    metadata = {
                        "date": formatted_date,
                        "filename": uploaded_file.name,
                        "interpreter": interpreter,
                        "week": extraction_week,
                        "comment": comment,
                        "serie": serie,
                    }
                    service.generate_pdf_report(
                        df_intra=st.session_state.comparison_result["df_intra"],
                        df_inter=st.session_state.comparison_result["df_inter"],
                        heatmap=st.session_state.comparison_result["heatmap"],
                        metadata=metadata,
                        errors_intra=st.session_state.comparison_result["errors_intra"],
                        errors_inter=st.session_state.comparison_result["errors_inter"],
                        output_path=tmp.name,
                    )

                    # Read the PDF file
                    with open(tmp.name, "rb") as f:
                        pdf_data = f.read()

                    # Create download button that opens the PDF directly
                    st.download_button(
                        label="Ouvrir le rapport PDF",
                        data=pdf_data,
                        file_name="rapport_identite.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

                    # Clean up
                    os.unlink(tmp.name)


if __name__ == "__main__":
    main()
