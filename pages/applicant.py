import pandas as pd
import streamlit as st

from database import (
    add_application,
    add_open_application,
    add_open_application_preference,
    get_active_vacancies,
    get_dropdown,
    get_my_applications,
    get_my_open_application,
    get_open_preferences,
    get_organizations,
    get_profile,
    get_vacancy,
    save_profile,
)
from utils.ai_engine import calculate_ai_match


def safe_index(options, value):
    return options.index(value) if value in options else 0


def valid_multiselect_defaults(saved_value, options):
    if not saved_value:
        return []
    return [x.strip() for x in str(saved_value).split(",") if x.strip() in options]


def show():
    email = st.session_state.email

    tabs = st.tabs([
        "🏠 Dashboard",
        "👤 Profil Saya",
        "📢 Iklan Kekosongan",
        "📬 Permohonan Terbuka",
        "📊 Permohonan Saya",
    ])

    with tabs[0]:
        st.title("👤 Dashboard Pemohon")
        profile = get_profile(email)
        vacancies = get_active_vacancies()
        applications = get_my_applications(email)
        open_application = get_my_open_application(email)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📢 Iklan Aktif", len(vacancies))
        c2.metric("📝 Permohonan Iklan", len(applications))
        c3.metric("📬 Permohonan Terbuka", 1 if open_application else 0)
        c4.metric("👤 Profil", "Lengkap" if profile else "Belum Lengkap")

        st.divider()
        if not profile:
            st.warning("Sila lengkapkan Profil Saya sebelum membuat permohonan.")
        else:
            st.success("Profil pegawai telah dilengkapkan.")

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
            name = st.text_input("Nama", value=existing["name"] if existing else "")
            ic = st.text_input("No. Kad Pengenalan", value=existing["ic"] if existing else "")
            phone = st.text_input("No. Telefon", value=existing["phone"] if existing else "")

            current_department = (
                st.selectbox(
                    "Bahagian / Organisasi Semasa",
                    organizations,
                    index=safe_index(organizations, existing["current_department"] if existing else ""),
                )
                if organizations
                else st.text_input("Bahagian / Organisasi Semasa")
            )

            current_position = st.text_input("Jawatan Semasa", value=existing["current_position"] if existing else "")
            grade = st.selectbox("Gred", grades, index=safe_index(grades, existing["grade"] if existing else "")) if grades else st.text_input("Gred")
            home_address = st.text_area("Alamat Rumah", value=existing["home_address"] if existing else "")
            state = st.selectbox("Negeri", states, index=safe_index(states, existing["state"] if existing else "")) if states else st.text_input("Negeri")
            district = st.text_input("Daerah", value=existing["district"] if existing else "")
            academic_value = st.selectbox("Akademik", academic, index=safe_index(academic, existing["academic"] if existing else "")) if academic else st.text_input("Akademik")
            professional_value = st.selectbox("Ikhtisas", professional, index=safe_index(professional, existing["professional"] if existing else "")) if professional else st.text_input("Ikhtisas")
            specialization_value = st.selectbox("Bidang Pengkhususan", specialization, index=safe_index(specialization, existing["specialization"] if existing else "")) if specialization else st.text_input("Bidang Pengkhususan")
            experience = st.number_input("Pengalaman Berkaitan (Tahun)", min_value=0, max_value=40, value=int(existing["experience"]) if existing and existing["experience"] else 0)

            certification_value = (
                st.multiselect(
                    "Pensijilan",
                    certification,
                    default=valid_multiselect_defaults(existing["certification"] if existing else "", certification),
                )
                if certification
                else []
            )
            course_value = (
                st.multiselect(
                    "Kursus Disertai",
                    course,
                    default=valid_multiselect_defaults(existing["course"] if existing else "", course),
                )
                if course
                else []
            )
            language_value = (
                st.multiselect(
                    "Kemahiran Bahasa",
                    language,
                    default=valid_multiselect_defaults(existing["language"] if existing else "", language),
                )
                if language
                else []
            )

            submit_profile = st.form_submit_button("💾 Simpan Profil")

        if submit_profile:
            save_profile((
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
                ",".join(language_value),
            ))
            st.success("✅ Profil berjaya disimpan.")
            st.rerun()

    with tabs[2]:
        st.title("📢 Iklan Kekosongan")
        profile = get_profile(email)
        vacancies = get_active_vacancies()

        if not profile:
            st.warning("Sila lengkapkan Profil Saya dahulu sebelum memohon iklan.")
        elif len(vacancies) == 0:
            st.info("Tiada iklan aktif buat masa ini.")
        else:
            df = pd.DataFrame([
                {
                    "ID": v["id"],
                    "Jawatan": v["title"],
                    "Bahagian": v["department"],
                    "Negeri": v["state"],
                    "Daerah": v["district"],
                    "Tarikh Tutup": v["closing_date"],
                    "Interview": v["interview_required"],
                    "Status": v["status"],
                }
                for v in vacancies
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            vacancy_options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected_vacancy = st.selectbox("Pilih iklan untuk dimohon", list(vacancy_options.keys()))
            vacancy_id = vacancy_options[selected_vacancy]
            vacancy = get_vacancy(vacancy_id)
            score, explanation, recommendation = calculate_ai_match(profile, vacancy)

            st.metric("Anggaran AI Match Score", f"{score}%")
            with st.expander("Lihat penerangan AI"):
                for item in explanation:
                    st.write(item)
                st.success(f"Cadangan AI: {recommendation}")

            if st.button("Hantar Permohonan Iklan", use_container_width=True):
                add_application(vacancy_id, email, score, "Menunggu Kelulusan Pengarah Bahagian Asal")
                st.success("✅ Permohonan berjaya dihantar.")

    with tabs[3]:
        st.title("📬 Permohonan Terbuka")
        profile = get_profile(email)
        if not profile:
            st.warning("Sila lengkapkan Profil Saya dahulu.")
        else:
            organizations = get_organizations()
            selected_orgs = st.multiselect("Pilih Bahagian / Organisasi Diminati", organizations)
            if st.button("Hantar Permohonan Terbuka", use_container_width=True):
                if not selected_orgs:
                    st.error("Sila pilih sekurang-kurangnya satu organisasi.")
                else:
                    open_id = add_open_application(email, "Menunggu Kekosongan")
                    for index, org in enumerate(selected_orgs, start=1):
                        add_open_application_preference(open_id, org, index)
                    st.success("✅ Permohonan terbuka berjaya dihantar.")

    with tabs[4]:
        st.title("📊 Permohonan Saya")
        apps = get_my_applications(email)
        open_app = get_my_open_application(email)

        st.subheader("Permohonan Melalui Iklan")
        if not apps:
            st.info("Tiada permohonan melalui iklan.")
        else:
            rows = [
                {
                    "ID": a["id"],
                    "Jawatan": a["title"],
                    "Bahagian": a["department"],
                    "AI Score": a["score"],
                    "Status": a["status"],
                    "Tarikh": a["submitted_at"],
                }
                for a in apps
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Permohonan Terbuka")
        if not open_app:
            st.info("Tiada permohonan terbuka.")
        else:
            st.success(f"Status: {open_app['status']}")
            prefs = get_open_preferences(open_app["id"])
            pref_rows = [{"Keutamaan": p["priority"], "Organisasi": p["department"]} for p in prefs]
            st.dataframe(pd.DataFrame(pref_rows), use_container_width=True, hide_index=True)
