import streamlit as st
import pandas as pd

from database import (
    import_master_data,
    get_connection
)


def show():

    st.title("🏢 Master Data KPM")

    st.info(
        "Upload fail master_data_v3_FULL.xlsx untuk import data rujukan ke SQLite."
    )

    uploaded_file = st.file_uploader(
        "Upload Master Data Excel",
        type=["xlsx"]
    )

    if uploaded_file is not None:

        with open("temp_master_data.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())

        import_master_data("temp_master_data.xlsx")

        st.success("✅ Master Data berjaya diimport ke database.")

    st.divider()

    tables = [
        "organizations",
        "grades",
        "academic",
        "professional",
        "specialization",
        "certification",
        "course",
        "language",
        "states",
        "districts"
    ]

    selected_table = st.selectbox(
        "Pilih jadual untuk semakan",
        tables
    )

    conn = get_connection()

    try:

        df = pd.read_sql(
            f"SELECT * FROM {selected_table}",
            conn
        )

        st.metric("Jumlah Rekod", len(df))

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:

        st.error(f"Ralat membaca data: {e}")

    conn.close()