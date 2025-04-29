import streamlit as st
import pandas as pd
import utils
import plotly
import numpy as np
import tempfile
from natsort import natsorted


def generate_report():
    # Placeholder for the report generation logic
    st.success("Rapport généré avec succès !")


def read_file(file) -> pd.DataFrame:
    """
    Read the uploaded file and return a DataFrame.

    Args:
        file (UploadedFile): The uploaded file containing Genemapper data.
    Returns:
        pd.DataFrame: A DataFrame containing the loaded Genemapper data.
    """
    try:
        df = utils.load_genemapper_data(file)
        return df
    except Exception as e:
        st.error(str(e))


def highlight_status(row):
    """Highlight rows based on the status_type column.

    Args:
        row (pd.Series): A row of the DataFrame.

    Returns:
        list: A list of styles for each cell in the row.
    """
    color = {
        "success": "#ffffff",  # green clair
        "error": "#f8d7da",  # red clair
        "info": "#d1ecf1",  # blue clair
        "warning": "#fff3cd",  # yellow clair
    }.get(row["status_type"], "white")

    return [f"background-color: {color}"] * len(row)


def insert_blank_rows_between_groups(df, group_col="Patient"):
    """Insert blank rows between groups in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        group_col (str): The column name to group by.

    Returns:
        pd.DataFrame: A new DataFrame with blank rows inserted.
    """
    df = df.sort_values(group_col)
    rows = []

    # Create an empty row with compatible values for the columns
    def create_empty_row(columns):
        return {col: "" for col in columns}

    previous_value = None
    for _, row in df.iterrows():
        if previous_value is not None and row[group_col] != previous_value:
            # Add an empty row before adding the next row
            rows.append(create_empty_row(df))
        rows.append(row.to_dict())  # Convert the row to a dictionary
        previous_value = row[group_col]

    df_with_blanks = pd.DataFrame(rows).reset_index(drop=True)
    return df_with_blanks


def create_plotly_heatmap(comparison_matrix):
    """Create a heatmap using Plotly.

    Args:
        comparison_matrix (pd.DataFrame): The matrix to visualize.

    Returns:
        plotly.graph_objects.Figure: The heatmap figure.
    """
    # Sort patient by natural sort
    sorted_patients = natsorted(comparison_matrix.index.tolist())
    comparison_matrix = comparison_matrix.loc[sorted_patients, sorted_patients]

    # Mask the upper triangle of the matrix due to symmetry
    masked_matrix = comparison_matrix.where(
        np.tril(np.ones(comparison_matrix.shape)).astype(bool)
    )

    n = len(sorted_patients) / 2  # nombre d'échantillons

    # Taille dynamique : chaque case fait environ 30 pixels
    cell_size = 30
    fig_size = n * cell_size

    fig = plotly.graph_objects.Figure(
        data=plotly.graph_objects.Heatmap(
            z=masked_matrix.values,
            x=masked_matrix.columns,
            y=masked_matrix.index,
            colorscale=plotly.colors.sequential.Viridis.reverse(),  # ou 'Cividis', 'Inferno', etc.
            coloraxis="coloraxis",
            zmin=0,
            zmax=100,
            hovertemplate=(
                "<b>Patient 1:</b> %{y}<br>"
                "<b>Patient 2:</b> %{x}<br>"
                "<b>Identité:</b> %{z:.2f}<extra>%</extra>"
            ),
        )
    )
    fig.update_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        xaxis_title=None,
        yaxis_title=None,
        width=fig_size,
        height=fig_size,
        template="plotly_white",
        xaxis_scaleanchor="y",  # squared tiles
        xaxis_side="bottom",
        coloraxis=dict(
            colorbar=dict(
                title="Identité (%)",
                lenmode="fraction",
                len=0.8,
                yanchor="middle",
                y=0.5,
            )
        ),
        margin=dict(t=0, b=10, l=10, r=10),
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(masked_matrix.columns),
        ticktext=list(masked_matrix.columns),
        # tickangle=45,
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=list(masked_matrix.index),
        ticktext=list(masked_matrix.index),
        autorange="reversed",
    )

    return fig


def render_app(df: pd.DataFrame):
    """Render the Streamlit app with the provided DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to display.
    """
    data = utils.prepare_data(df)

    # Intra-patient Comparison
    df_intra = utils.intra_comparison(data)
    df_intra = utils.merge_genotypes(df_intra)
    print(df_intra)
    # count samples with errors
    error_count = df_intra["status_type"].value_counts().get("error", 0)
    st.session_state["errors_intra"] = error_count

    # Reorder columns
    alleles_columns = [str(col) for col in df_intra.columns if col.startswith("Locus")]
    intra_column_order = (
        [
            "Patient",
            "Sample Name",
            "Genre",
            "status_description",
        ]
        + alleles_columns
        + ["status_type"]
    )
    df_display = df_intra[intra_column_order]

    # Highlight the rows based on status_type
    styled_df = df_display.style.apply(highlight_status, axis=1)

    st.subheader("Comparaison intra-patient", divider="grey")
    if error_count > 0:
        st.error(f"Erreur : {error_count} échantillon(s) incohérent(s) détecté(s).")
    else:
        st.success("Tous les échantillons sont cohérents.")
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Copy the dataframe for the pdf report
    df_intra_report = df_display[
        ["Patient", "Sample Name", "Genre", "status_description", "status_type"]
    ].copy()
    df_intra_report = df_intra_report.style.apply(highlight_status, axis=1).hide(
        axis="index"
    )
    st.session_state["df_intra"] = df_intra_report

    # Inter-Patient Comparison
    df_inter = utils.inter_comparison(data)

    st.subheader("Comparaison inter-patient", divider="grey")
    if df_inter.empty:
        st.success("Tous les échantillons sont cohérents.")
    else:
        df_inter = utils.merge_genotypes(df_inter)
        locus_columns = [
            str(col) for col in df_inter.columns if col.startswith("Locus")
        ]
        inter_column_order = (
            [
                "Patient",
                "Sample Name",
                "Genre",
            ]
            + locus_columns
            + ["signature_hash"]
        )
        df_display = df_inter[inter_column_order]
        df_display = insert_blank_rows_between_groups(df_display, "signature_hash")
        st.error("Incohérence(s) détectée(s) entre les échantillons.")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.session_state["df_inter"] = df_inter
    st.session_state["errors_inter"] = len(df_inter)

    # Plot the heatmap
    comparison_matrix = utils.sample_heatmap(data)
    st.subheader(
        "Matrice de comparaison des patients (% allèles en commun) :",
        divider="grey",
    )
    if not comparison_matrix.empty:
        fig = create_plotly_heatmap(comparison_matrix)
        fig.update_traces(colorscale="Viridis")
        st.plotly_chart(fig, use_container_width=True)
        st.session_state["heatmap"] = fig
    else:
        st.warning("Aucune donnée à afficher.")


def main():
    # Configure the Streamlit app
    st.set_page_config(
        page_title="Identitovigilence SNPXPlex",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:

        st.subheader("Identitovigilance - contrôle d'extraction", divider="rainbow")
        # Genemapper file uploader
        genemapper_file = st.file_uploader(
            "Insérer les donnés patients :",
            type=["txt", "csv"],
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
        st.session_state["metadata"] = {
            "interpreter": interpreter,
            "week": extraction_week,
            "comment": comment,
            "serie": serie,
        }

        if st.button("Générer un rapport PDF"):
            with st.spinner("Génération du rapport..."):
                fig = st.session_state.get("heatmap")
                df_intra = st.session_state.get("df_intra")
                df_inter = st.session_state.get("df_inter")
                metadata = st.session_state.get("metadata", {})
                errors_intra = st.session_state.get("errors_intra", 0)
                errors_inter = st.session_state.get("errors_inter", 0)

                if fig and df_intra is not None and df_inter is not None:
                    heatmap_path = utils.save_heatmap_as_image(fig)
                    heatmap_path = f"file://{heatmap_path}"
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as pdf_file:
                        utils.generate_pdf_report_custom(
                            df_intra=df_intra,
                            df_inter=df_inter,
                            figure_path=heatmap_path,
                            metadata=metadata,
                            errors_intra=errors_intra,
                            errors_inter=errors_inter,
                            output_path=pdf_file.name,
                        )
                        with open(pdf_file.name, "rb") as f:
                            st.download_button(
                                "Télécharger le rapport PDF",
                                f,
                                file_name="rapport_identitovigilance.pdf",
                            )
                else:
                    st.error(
                        "Aucune donnée ou graphique disponible pour générer le rapport."
                    )

    if genemapper_file is not None:
        df = read_file(genemapper_file)
        if df is not None:
            missing_colmuns = utils.validate_file_format(df)
            if missing_colmuns:
                st.error(
                    f"Le fichier ne semble pas au bon format.\n\nColonnes manquantes : {missing_colmuns}"
                )
            else:
                render_app(df)


if __name__ == "__main__":
    main()
