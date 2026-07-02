import streamlit as st
import pandas as pd

from database import (
    get_connection,
    get_active_vacancies,
    get_my_applications,
    get_my_open_application,
    add_open_application,
    add_open_application_preference,
    save_profile,
    get_profile
)


def load_dropdown(table, column):

    conn = get_connection()

    try:
        query = f'SELECT "{column}" FROM "{table}"'
        data = conn.execute(query).fetchall()
        result = [x[0] for x in data if x[0] is not None]

    except Exception:
        result = []

    conn.close()

    return result


def load_organizations():

    conn = get_connection()

    try:
        data = conn.execute("""
            SELECT name
            FROM organizations
            WHERE status='Active'
            ORDER BY name
        """).fetchall()

        result = [x[0] for x in data if x[0] is not None]

    except Exception:
        result = []

    conn.close()

    return result


def show():

    email = st.session_state.email

    tabs = st.tabs(
        [
            "🏠 Dashboard",
            "👤 Profil Saya",
            "📢 Iklan Kekosongan",
            "📬 Permohonan Terbuka",
            "📊 Permohonan Saya"
        ]
    )

    # =====================================================
    # DASHBOARD
    # =====================================================

    with tabs[0]:

        st.title("👤 Dashboard Pemohon")

        my_apps = get_my_applications(email)
        open_app = get_my_open_application(email)
        active_vacancies = get_active_vacancies()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("📢 Iklan Aktif", len(active_vacancies))
        col2.metric("📝 Permohonan Iklan", len(my_apps))
        col3.metric("📬 Permohonan Terbuka", 1 if open_app else 0)
        col4.metric("⏳ Status", "Aktif")

        st.divider()

        st.info(
            "Sila lengkapkan Profil Saya sebelum membuat permohonan pertukaran."
        )

    # =====================================================
    # PROFIL SAYA
    # =====================================================

    with tabs[1]:

        st.title("👤 Profil Pegawai")

        existing = get_profile(email)

        organizations = load_organizations()
        grades = load_dropdown("grades", "grade")
        academic = load_dropdown("academic", "academic")
        professional = load_dropdown("professional", "professional")
        specialization = load_dropdown("specialization", "specialization")
        certification = load_dropdown("certification", "certification")
        course = load_dropdown("course", "course_category")
        language = load_dropdown("language", "language")
        states = load_dropdown("states", "state")

        if not organizations:
            st.warning("Master Data belum diimport. Sila import melalui BPSM → Master Data.")

        with st.form("profile_form"):

            name = st.text_input(
                "Nama",
                value=existing["name"] if existing else ""
            )

            ic = st.text_input(
                "No. Kad Pengenalan",
                value=existing["ic"] if existing else ""
            )

            phone = st.text_input(
                "No. Telefon",
                value=existing["phone"] if existing else ""
            )

            current_department = st.selectbox(
                "Bahagian / Organisasi Semasa",
                organizations,
                index=organizations.index(existing["current_department"])
                if existing and existing["current_department"] in organizations
                else 0
            ) if organizations else st.text_input("Bahagian / Organisasi Semasa")

            current_position = st.text_input(
                "Jawatan Semasa",
                value=existing["current_position"] if existing else ""
            )

            grade = st.selectbox(
                "Gred",
                grades,
                index=grades.index(existing["grade"])
                if existing and existing["grade"] in grades
                else 0
            ) if grades else st.text_input("Gred")

            home_address = st.text_area(
                "Alamat Rumah",
                value=existing["home_address"] if existing else ""
            )

            state = st.selectbox(
                "Negeri",
                states,
                index=states.index(existing["state"])
                if existing and existing["state"] in states
                else 0
            ) if states else st.text_input("Negeri")

            district = st.text_input(
                "Daerah",
                value=existing["district"] if existing else ""
            )

            academic_value = st.selectbox(
                "Akademik",
                academic,
                index=academic.index(existing["academic"])
                if existing and existing["academic"] in academic
                else 0
            ) if academic else st.text_input("Akademik")

            professional_value = st.selectbox(
                "Ikhtisas",
                professional,
                index=professional.index(existing["professional"])
                if existing and existing["professional"] in professional
                else 0
            ) if professional else st.text_input("Ikhtisas")

            specialization_value = st.selectbox(
                "Bidang Pengkhususan",
                specialization,
                index=specialization.index(existing["specialization"])
                if existing and existing["specialization"] in specialization
                else 0
            ) if specialization else st.text_input("Bidang Pengkhususan")

            experience = st.number_input(
                "Pengalaman Berkaitan (Tahun)",
                min_value=0,
                max_value=40,
                value=int(existing["experience"]) if existing and existing["experience"] else 0
            )

            certification_value = st.selectbox(
                "Pensijilan",
                certification,
                index=certification.index(existing["certification"])
                if existing and existing["certification"] in certification
                else 0
            ) if certification else st.text_input("Pensijilan")

            course_value = st.selectbox(
                "Kursus Disertai",
                course,
                index=course.index(existing["course"])
                if existing and existing["course"] in course
                else 0
            ) if course else st.text_input("Kursus Disertai")

            language_value = st.selectbox(
                "Kemahiran Bahasa",
                language,
                index=language.index(existing["language"])
                if existing and existing["language"] in language
                else 0
            ) if language else st.text_input("Kemahiran Bahasa")

            submit = st.form_submit_button("💾 Simpan Profil")

        if submit:

            save_profile(
                (
                    email,
                    name,
                    ic,
                    phone,
                    current_department,
                    current_position,
                    grade,
                    home_address,
                    state,
                    district,
                    academic_value,
                    professional_value,
                    specialization_value,
                    experience,
                    certification_value,
                    course_value,
                    language_value
                )
            )

            st.success("✅ Profil berjaya disimpan.")

    # =====================================================
    # IKLAN KEKOSONGAN
    # =====================================================

    with tabs[2]:

        st.title("📢 Iklan Kekosongan")

        vacancies = get_active_vacancies()

        if len(vacancies) == 0:

            st.info("Tiada iklan aktif buat masa ini.")

        else:

            rows = []

            for v in vacancies:
                rows.append(
                    {
                        "ID": v["id"],
                        "Jawatan": v["title"],
                        "Bahagian": v["department"],
                        "Negeri": v["state"],
                        "Daerah": v["district"],
                        "Tarikh Tutup": v["closing_date"],
                        "Interview": v["interview_required"],
                        "Status": v["status"]
                    }
                )

            df = pd.DataFrame(rows)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.warning(
                "Fungsi mohon iklan akan disambungkan selepas AI scoring siap."
            )

    # =====================================================
    # PERMOHONAN TERBUKA
    # =====================================================

    with tabs[3]:

        st.title("📬 Permohonan Terbuka")

        profile = get_profile(email)

        if not profile:

            st.warning("Sila lengkapkan Profil Saya dahulu.")

        else:

            orgs = load_organizations()

            selected_orgs = st.multiselect(
                "Pilih Bahagian / Organisasi Diminati",
                orgs
            )

            if st.button("Hantar Permohonan Terbuka", use_container_width=True):

                if len(selected_orgs) == 0:

                    st.error("Sila pilih sekurang-kurangnya satu organisasi.")

                else:

                    app_id = add_open_application(
                        email,
                        "Menunggu Kekosongan"
                    )

                    for idx, org in enumerate(selected_orgs, start=1):

                        add_open_application_preference(
                            app_id,
                            org,
                            idx
                        )

                    st.success("✅ Permohonan terbuka berjaya dihantar.")

    # =====================================================
    # PERMOHONAN SAYA
    # =====================================================

    with tabs[4]:

        st.title("📊 Permohonan Saya")

        apps = get_my_applications(email)
        open_app = get_my_open_application(email)

        st.subheader("Permohonan Melalui Iklan")

        if len(apps) == 0:

            st.info("Tiada permohonan iklan.")

        else:

            st.dataframe(
                apps,
                use_container_width=True
            )

        st.divider()

        st.subheader("Permohonan Terbuka")

        if open_app:

            st.success(f"Status: {open_app['status']}")

            conn = get_connection()

            prefs = conn.execute("""
                SELECT *
                FROM open_applications_preferences
                WHERE application_id=?
                ORDER BY priority
            """, (open_app["id"],)).fetchall()

            conn.close()

            if prefs:

                pref_rows = [
                    {
                        "Keutamaan": p["priority"],
                        "Organisasi": p["department"]
                    }
                    for p in prefs
                ]

                st.dataframe(
                    pd.DataFrame(pref_rows),
                    use_container_width=True,
                    hide_index=True
                )

        else:

            st.info("Tiada permohonan terbuka.")