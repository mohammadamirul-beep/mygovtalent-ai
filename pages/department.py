import streamlit as st
import pandas as pd

from database import (
    get_dropdown,
    get_organizations,
    add_vacancy,
    get_all_vacancies,
    get_applications_by_vacancy,
    get_vacancy,
    update_application_status,
    send_to_bpsm,
    add_interview
)


def safe_df(rows):
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def show():
    tabs = st.tabs([
        "🏠 Dashboard",
        "📢 Pengurusan Iklan",
        "📥 Permohonan",
        "🤖 AI Recommendation",
        "🎤 Temuduga",
        "📤 Hantar ke BPSM"
    ])

    with tabs[0]:
        st.title("🏢 Dashboard Bahagian")
        vacancies = get_all_vacancies()
        active = [v for v in vacancies if v["status"] == "Active"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📢 Iklan Aktif", len(active))
        c2.metric("📋 Jumlah Iklan", len(vacancies))
        c3.metric("✅ Shortlisted", 0)
        c4.metric("📤 Ke BPSM", 0)

    with tabs[1]:
        st.title("📢 Pengurusan Iklan")

        organizations = get_organizations()
        states = get_dropdown("states", "state")
        academic = get_dropdown("academic", "academic")
        professional = get_dropdown("professional", "professional")
        specialization = get_dropdown("specialization", "specialization")
        certification = get_dropdown("certification", "certification")
        course = get_dropdown("course", "course_category")
        language = get_dropdown("language", "language")

        with st.form("vacancy_form"):
            title = st.text_input("Jawatan / Peranan")
            department = st.selectbox("Bahagian / Organisasi", organizations) if organizations else st.text_input("Bahagian / Organisasi")
            location = st.text_area("Alamat Tempat Bertugas")
            state = st.selectbox("Negeri", states) if states else st.text_input("Negeri")
            district = st.text_input("Daerah")
            academic_value = st.selectbox("Akademik", academic) if academic else st.text_input("Akademik")
            professional_value = st.selectbox("Ikhtisas", professional) if professional else st.text_input("Ikhtisas")
            specialization_value = st.selectbox("Bidang Pengkhususan", specialization) if specialization else st.text_input("Bidang Pengkhususan")
            experience = st.number_input("Pengalaman Minimum (Tahun)", min_value=0, max_value=40, value=0)
            certification_value = st.multiselect("Pensijilan", certification) if certification else []
            course_value = st.multiselect("Kategori Kursus", course) if course else []
            language_value = st.multiselect("Kemahiran Bahasa", language) if language else []
            closing_date = st.date_input("Tarikh Tutup")
            interview_required = st.selectbox("Perlu Interview?", ["Ya", "Tidak"])
            submit = st.form_submit_button("💾 Simpan Iklan")

        if submit:
            add_vacancy((
                title,
                department,
                location,
                state,
                district,
                academic_value,
                professional_value,
                specialization_value,
                experience,
                ",".join(certification_value),
                ",".join(course_value),
                ",".join(language_value),
                str(closing_date),
                interview_required,
                "Active",
                st.session_state.email
            ))
            st.success("✅ Iklan berjaya disimpan.")

        st.divider()
        st.subheader("Senarai Iklan")
        df = safe_df(get_all_vacancies())
        if df.empty:
            st.info("Tiada iklan direkodkan.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.title("📥 Permohonan Mengikut Iklan")
        vacancies = get_all_vacancies()

        if not vacancies:
            st.info("Tiada iklan.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Iklan", list(options.keys()), key="permohonan_vacancy")
            applications = get_applications_by_vacancy(options[selected])
            df = safe_df(applications)

            if df.empty:
                st.info("Tiada permohonan untuk iklan ini.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[3]:
        st.title("🤖 AI Recommendation")
        vacancies = get_all_vacancies()

        if not vacancies:
            st.info("Tiada iklan untuk diproses.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Iklan untuk AI Ranking", list(options.keys()), key="ai_vacancy")
            vacancy_id = options[selected]
            applications = get_applications_by_vacancy(vacancy_id)

            approved_apps = [
                a for a in applications
                if a["status"] == "Diluluskan Pengarah Bahagian Asal"
            ]

            if not approved_apps:
                st.info("Tiada calon yang telah diluluskan oleh Pengarah Bahagian Asal.")
            else:
                df = pd.DataFrame([{
                    "Application ID": a["id"],
                    "Nama": a["name"],
                    "Email": a["applicant_email"],
                    "Jawatan": a["current_position"],
                    "Bahagian Semasa": a["current_department"],
                    "Gred": a["grade"],
                    "Akademik": a["academic"],
                    "Ikhtisas": a["professional"],
                    "Bidang": a["specialization"],
                    "Pengalaman": a["experience"],
                    "Pensijilan": a["certification"],
                    "Kursus": a["course"],
                    "Negeri": a["state"],
                    "AI Score": a["score"],
                    "Status": a["status"]
                } for a in approved_apps]).sort_values(by="AI Score", ascending=False)

                st.dataframe(df, use_container_width=True, hide_index=True)

                selected_app = st.selectbox(
                    "Pilih Application ID untuk Shortlist",
                    df["Application ID"].tolist(),
                    key="shortlist_app"
                )

                if st.button("Shortlist Calon", use_container_width=True):
                    vacancy = get_vacancy(vacancy_id)

                    if vacancy["interview_required"] == "Ya":
                        status = "Menunggu Temuduga"
                    else:
                        status = "Shortlisted Bahagian"

                    update_application_status(selected_app, status)
                    st.success(f"✅ Status calon dikemaskini kepada: {status}")
                    st.rerun()

    with tabs[4]:
        st.title("🎤 Temuduga")
        vacancies = get_all_vacancies()

        if not vacancies:
            st.info("Tiada iklan.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Iklan", list(options.keys()), key="interview_vacancy")
            vacancy_id = options[selected]
            applications = get_applications_by_vacancy(vacancy_id)

            interview_apps = [
                a for a in applications
                if a["status"] in ["Menunggu Temuduga", "Temuduga Dijadualkan"]
            ]

            if not interview_apps:
                st.info("Tiada calon menunggu temuduga.")
            else:
                df = pd.DataFrame([{
                    "Application ID": a["id"],
                    "Nama": a["name"],
                    "Email": a["applicant_email"],
                    "AI Score": a["score"],
                    "Status": a["status"]
                } for a in interview_apps])

                st.dataframe(df, use_container_width=True, hide_index=True)

                selected_app = st.selectbox(
                    "Pilih Application ID",
                    df["Application ID"].tolist(),
                    key="interview_app"
                )

                interview_date = st.date_input("Tarikh Temuduga")
                interview_time = st.time_input("Masa Temuduga")
                interview_location = st.text_input("Lokasi Temuduga")
                interview_panel = st.text_input("Panel Temuduga")

                if st.button("Jadualkan Temuduga", use_container_width=True):
                    add_interview((
                        selected_app,
                        str(interview_date),
                        str(interview_time),
                        interview_location,
                        interview_panel,
                        "Dijadualkan",
                        ""
                    ))
                    update_application_status(selected_app, "Temuduga Dijadualkan")
                    st.success("✅ Temuduga berjaya dijadualkan.")
                    st.rerun()

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Lulus Temuduga", use_container_width=True):
                        update_application_status(selected_app, "Shortlisted Bahagian")
                        st.success("✅ Calon lulus temuduga.")
                        st.rerun()

                with col2:
                    if st.button("❌ Gagal Temuduga", use_container_width=True):
                        update_application_status(selected_app, "Gagal Temuduga")
                        st.warning("Calon gagal temuduga.")
                        st.rerun()

    with tabs[5]:
        st.title("📤 Hantar ke BPSM")
        vacancies = get_all_vacancies()

        if not vacancies:
            st.info("Tiada iklan.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Iklan", list(options.keys()), key="bpsm_vacancy")
            vacancy_id = options[selected]
            applications = get_applications_by_vacancy(vacancy_id)

            shortlisted = [
                a for a in applications
                if a["status"] == "Shortlisted Bahagian"
            ]

            if not shortlisted:
                st.info("Tiada calon shortlisted untuk dihantar ke BPSM.")
            else:
                df = pd.DataFrame([{
                    "Application ID": a["id"],
                    "Nama": a["name"],
                    "Email": a["applicant_email"],
                    "AI Score": a["score"],
                    "Status": a["status"]
                } for a in shortlisted])

                st.dataframe(df, use_container_width=True, hide_index=True)

                selected_app = st.selectbox(
                    "Pilih Application ID untuk dihantar",
                    df["Application ID"].tolist(),
                    key="send_bpsm_app"
                )

                selected_row = df[df["Application ID"] == selected_app].iloc[0]
                remarks = st.text_area("Catatan Bahagian")

                if st.button("Hantar ke BPSM", use_container_width=True):
                    send_to_bpsm(
                        selected_app,
                        selected_row["Email"],
                        vacancy_id,
                        st.session_state.department,
                        remarks
                    )
                    st.success("✅ Calon berjaya dihantar ke BPSM.")
                    st.rerun()