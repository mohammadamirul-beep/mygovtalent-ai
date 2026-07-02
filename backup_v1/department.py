import streamlit as st

from database import (
    add_vacancy,
    get_all_vacancies,
    get_connection
)


def dropdown(table, column):

    conn = get_connection()

    query = f'SELECT "{column}" FROM "{table}"'

    data = conn.execute(query).fetchall()

    conn.close()

    return [x[0] for x in data]


def show():

    tabs = st.tabs(
        [
            "🏠 Dashboard",
            "📢 Pengurusan Iklan",
            "📥 Permohonan",
            "🤖 AI Recommendation",
            "📤 Hantar ke BPSM"
        ]
    )

    # =====================================================
    # DASHBOARD
    # =====================================================

    with tabs[0]:

        st.title("Dashboard Bahagian")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Iklan Aktif", 0)
        c2.metric("Permohonan", 0)
        c3.metric("Shortlist", 0)
        c4.metric("Ke BPSM", 0)

    # =====================================================
    # PENGURUSAN IKLAN
    # =====================================================

    with tabs[1]:

        st.header("Cipta Iklan")

        academic = load_dropdown("academic", "academic")

        professional = load_dropdown("professional", "professional")

        specialization = load_dropdown("specialization", "specialization")

        certification = load_dropdown("certification", "certification")

        course = load_dropdown("course", "course_category")

        language = load_dropdown("language", "language")

        state = load_dropdown("states", "state")

        conn = get_connection()

        dept = conn.execute("""
            SELECT name
            FROM organizations
            ORDER BY name
        """).fetchall()

        conn.close()

        dept = [x[0] for x in dept]

        with st.form("vacancy"):

            title = st.text_input("Jawatan")

            department = st.selectbox(
                "Bahagian",
                dept
            )

            location = st.text_input(
                "Alamat Tempat Bertugas"
            )

            negeri = st.selectbox(
                "Negeri",
                state
            )

            district = st.text_input(
                "Daerah"
            )

            akademik = st.selectbox(
                "Akademik",
                academic
            )

            ikhtisas = st.selectbox(
                "Ikhtisas",
                professional
            )

            bidang = st.selectbox(
                "Bidang Pengkhususan",
                specialization
            )

            pengalaman = st.number_input(
                "Minimum Pengalaman",
                0,
                40
            )

            sijil = st.selectbox(
                "Pensijilan",
                certification
            )

            kursus = st.selectbox(
                "Kategori Kursus",
                course
            )

            bahasa = st.selectbox(
                "Bahasa",
                language
            )

            closing = st.date_input(
                "Tarikh Tutup"
            )

            interview = st.selectbox(
                "Interview",
                ["Ya", "Tidak"]
            )

            submit = st.form_submit_button(
                "Simpan Iklan"
            )

        if submit:

            add_vacancy(

                (
                    title,
                    department,
                    location,
                    negeri,
                    district,
                    akademik,
                    ikhtisas,
                    bidang,
                    pengalaman,
                    sijil,
                    kursus,
                    bahasa,
                    str(closing),
                    interview,
                    "Active",
                    st.session_state.email
                )

            )

            st.success("Iklan berjaya disimpan.")

        st.subheader("Senarai Iklan")

        st.dataframe(
            get_all_vacancies(),
            use_container_width=True
        )

    # =====================================================
    # PERMOHONAN
    # =====================================================

    with tabs[2]:

        st.header("Permohonan")

        st.info("Akan dipaparkan mengikut iklan.")

    # =====================================================
    # AI
    # =====================================================

    with tabs[3]:

        st.header("AI Recommendation")

        st.info("Scoring AI akan dibina pada langkah seterusnya.")

    # =====================================================
    # BPSM
    # =====================================================

    with tabs[4]:

        st.header("Hantar ke BPSM")

        st.info("Calon yang diluluskan akan dihantar ke BPSM.")