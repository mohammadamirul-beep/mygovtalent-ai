import streamlit as st
import pandas as pd

from database import (
    get_dropdown,
    get_organizations,
    save_profile,
    get_profile,
    get_active_vacancies,
    get_vacancy,
    add_application,
    get_my_applications,
    add_open_application,
    add_open_application_preference,
    get_my_open_application,
    get_open_preferences
)


def safe_index(options, value):
    if value in options:
        return options.index(value)
    return 0


def match_multi(profile_value, vacancy_value):

    profile_items = [
        x.strip().lower()
        for x in str(profile_value).split(",")
        if x.strip()
    ]

    vacancy_items = [
        x.strip().lower()
        for x in str(vacancy_value).split(",")
        if x.strip()
    ]

    if not vacancy_items:
        return 0

    matched = 0

    for item in vacancy_items:
        if item in profile_items:
            matched += 1

    return matched / len(vacancy_items)


def calculate_preview_score(profile, vacancy):

    if profile is None or vacancy is None:
        return 0

    score = 0

    if profile["academic"] == vacancy["academic"]:
        score += 20

    if profile["specialization"] == vacancy["specialization"]:
        score += 25

    if profile["experience"] and vacancy["experience"]:
        if int(profile["experience"]) >= int(vacancy["experience"]):
            score += 25

    score += match_multi(
        profile["certification"],
        vacancy["certification"]
    ) * 10

    score += match_multi(
        profile["course"],
        vacancy["course"]
    ) * 15

    if profile["state"] == vacancy["state"]:
        score += 5

    return round(score)


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

        profile = get_profile(email)
        vacancies = get_active_vacancies()
        applications = get_my_applications(email)
        open_application = get_my_open_application(email)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("📢 Iklan Aktif", len(vacancies))
        col2.metric("📝 Permohonan Iklan", len(applications))
        col3.metric("📬 Permohonan Terbuka", 1 if open_application else 0)
        col4.metric("👤 Profil", "Lengkap" if profile else "Belum Lengkap")

        st.divider()

        if not profile:
            st.warning("Sila lengkapkan Profil Saya sebelum membuat permohonan.")
        else:
            st.success("Profil pegawai telah dilengkapkan.")

    # =====================================================
    # PROFIL SAYA
    # =====================================================

    with tabs[1]:

        st.title("👤 Profil Pegawai")

        existing = get_profile(email)

        organizations = get_organizations()
        grades = get_dropdown("grades", "grade")
        academic = get_dropdown("academic", "academic")
        professional = get_dropdown("professional", "professional")
        specialization = get_dropdown("specialization", "specialization")
        certification = get_dropdown("certification", "certification")
        course = get_dropdown("course", "course_category")
        language = get_dropdown("language", "language")
        states = get_dropdown("states", "state")

        if not organizations:
            st.warning("Master Data belum diimport. Login BPSM dan upload master_data_v3_FULL.xlsx dahulu.")

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
                index=safe_index(
                    organizations,
                    existing["current_department"] if existing else ""
                )
            ) if organizations else st.text_input("Bahagian / Organisasi Semasa")

            current_position = st.text_input(
                "Jawatan Semasa",
                value=existing["current_position"] if existing else ""
            )

            grade = st.selectbox(
                "Gred",
                grades,
                index=safe_index(
                    grades,
                    existing["grade"] if existing else ""
                )
            ) if grades else st.text_input("Gred")

            home_address = st.text_area(
                "Alamat Rumah",
                value=existing["home_address"] if existing else ""
            )

            state = st.selectbox(
                "Negeri",
                states,
                index=safe_index(
                    states,
                    existing["state"] if existing else ""
                )
            ) if states else st.text_input("Negeri")

            district = st.text_input(
                "Daerah",
                value=existing["district"] if existing else ""
            )

            academic_value = st.selectbox(
                "Akademik",
                academic,
                index=safe_index(
                    academic,
                    existing["academic"] if existing else ""
                )
            ) if academic else st.text_input("Akademik")

            professional_value = st.selectbox(
                "Ikhtisas",
                professional,
                index=safe_index(
                    professional,
                    existing["professional"] if existing else ""
                )
            ) if professional else st.text_input("Ikhtisas")

            specialization_value = st.selectbox(
                "Bidang Pengkhususan",
                specialization,
                index=safe_index(
                    specialization,
                    existing["specialization"] if existing else ""
                )
            ) if specialization else st.text_input("Bidang Pengkhususan")

            experience = st.number_input(
                "Pengalaman Berkaitan (Tahun)",
                min_value=0,
                max_value=40,
                value=int(existing["experience"]) if existing and existing["experience"] else 0
            )

            certification_value = st.multiselect(
                "Pensijilan",
                certification,
                default=existing["certification"].split(",") if existing and existing["certification"] else []
            ) if certification else []

            course_value = st.multiselect(
                "Kursus Disertai",
                course,
                default=existing["course"].split(",") if existing and existing["course"] else []
            ) if course else []

            language_value = st.multiselect(
                "Kemahiran Bahasa",
                language,
                default=existing["language"].split(",") if existing and existing["language"] else []
            ) if language else []
            
            submit_profile = st.form_submit_button("💾 Simpan Profil")

        if submit_profile:
            st.write("DEBUG: Butang ditekan")
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
                    ",".join(certification_value),
                    ",".join(course_value),
                    ",".join(language_value)
                )
            )

            st.success("✅ Profil berjaya disimpan.")
            st.rerun()

    # =====================================================
    # IKLAN KEKOSONGAN
    # =====================================================

    with tabs[2]:

        st.title("📢 Iklan Kekosongan")

        profile = get_profile(email)
        vacancies = get_active_vacancies()

        if not profile:

            st.warning("Sila lengkapkan Profil Saya dahulu sebelum memohon iklan.")

        elif len(vacancies) == 0:

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

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            vacancy_options = {
                f"{v['id']} - {v['title']} ({v['department']})": v["id"]
                for v in vacancies
            }

            selected_vacancy = st.selectbox(
                "Pilih iklan untuk dimohon",
                list(vacancy_options.keys())
            )

            vacancy_id = vacancy_options[selected_vacancy]
            vacancy = get_vacancy(vacancy_id)

            score = calculate_preview_score(profile, vacancy)

            st.metric("Anggaran AI Match Score", f"{score}%")

            if st.button("Hantar Permohonan Iklan", use_container_width=True):

                add_application(
                    vacancy_id,
                    email,
                    score,
                    "Menunggu Kelulusan Pengarah Bahagian Asal"
                )

                st.success("✅ Permohonan berjaya dihantar.")

    # =====================================================
    # PERMOHONAN TERBUKA
    # =====================================================

    with tabs[3]:

        st.title("📬 Permohonan Terbuka")

        profile = get_profile(email)

        if not profile:

            st.warning("Sila lengkapkan Profil Saya dahulu.")

        else:

            organizations = get_organizations()

            selected_orgs = st.multiselect(
                "Pilih Bahagian / Organisasi Diminati",
                organizations
            )

            if st.button("Hantar Permohonan Terbuka", use_container_width=True):

                if len(selected_orgs) == 0:

                    st.error("Sila pilih sekurang-kurangnya satu organisasi.")

                else:

                    open_id = add_open_application(
                        email,
                        "Menunggu Kekosongan"
                    )

                    for index, org in enumerate(selected_orgs, start=1):

                        add_open_application_preference(
                            open_id,
                            org,
                            index
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

            st.info("Tiada permohonan melalui iklan.")

        else:

            rows = []

            for a in apps:

                rows.append(
                    {
                        "ID": a["id"],
                        "Jawatan": a["title"],
                        "Bahagian": a["department"],
                        "AI Score": a["score"],
                        "Status": a["status"],
                        "Tarikh": a["submitted_at"]
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        st.subheader("Permohonan Terbuka")

        if not open_app:

            st.info("Tiada permohonan terbuka.")

        else:

            st.success(f"Status: {open_app['status']}")

            prefs = get_open_preferences(open_app["id"])

            pref_rows = []

            for p in prefs:

                pref_rows.append(
                    {
                        "Keutamaan": p["priority"],
                        "Organisasi": p["department"]
                    }
                )

            st.dataframe(
                pd.DataFrame(pref_rows),
                use_container_width=True,
                hide_index=True
            )