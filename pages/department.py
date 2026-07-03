import pandas as pd
import streamlit as st

from database import (
    add_interview,
    add_vacancy,
    get_all_vacancies,
    get_applications_by_vacancy,
    get_dropdown,
    get_organizations,
    get_vacancy,
    send_to_bpsm,
    update_application_score,
    update_application_status,
)
from utils.ai_engine import calculate_ai_match


def safe_df(rows):
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def safe_name(row):
    try:
        return row["name"] if row["name"] else row["applicant_email"]
    except Exception:
        return row.get("name") or row.get("applicant_email", "")


def applications_for_all_vacancies(vacancies):
    all_apps = []
    for v in vacancies:
        all_apps.extend(get_applications_by_vacancy(v["id"]))
    return all_apps


def candidate_row(candidate, vacancy=None, include_detail=True):
    row = {
        "Application ID": candidate["id"],
        "Nama": safe_name(candidate),
        "Email": candidate["applicant_email"],
        "AI Score": candidate["score"],
        "Status": candidate["status"],
    }

    if include_detail:
        row.update({
            "Jawatan": candidate["current_position"],
            "Bahagian Semasa": candidate["current_department"],
            "Bahagian Dipohon": candidate["target_department"],
            "Gred": candidate["grade"],
            "Akademik": candidate["academic"],
            "Ikhtisas": candidate["professional"],
            "Bidang": candidate["specialization"],
            "Pengalaman": candidate["experience"],
            "Pensijilan": candidate["certification"],
            "Kursus": candidate["course"],
            "Negeri": candidate["state"],
            "Daerah": candidate["district"],
        })

    if vacancy is not None:
        score, _, _ = calculate_ai_match(candidate, vacancy)
        row["AI Score"] = score
        try:
            if candidate["score"] != score:
                update_application_score(candidate["id"], score)
        except Exception:
            pass

    return row


def show():
    tabs = st.tabs([
        "🏠 Dashboard",
        "📢 Pengurusan Iklan",
        "📥 Permohonan",
        "🤖 AI Recommendation",
        "🎤 Temuduga",
        "📤 Hantar ke BPSM",
    ])

    with tabs[0]:
        st.title("🏢 Dashboard Bahagian")

        vacancies = get_all_vacancies()
        active = [v for v in vacancies if v["status"] == "Active"]
        all_apps = applications_for_all_vacancies(vacancies)

        pending_director = [a for a in all_apps if a["status"] == "Menunggu Kelulusan Pengarah Bahagian Asal"]
        approved_director = [a for a in all_apps if a["status"] == "Diluluskan Pengarah Bahagian Asal"]
        shortlisted = [a for a in all_apps if a["status"] == "Shortlisted Bahagian"]
        interview_waiting = [a for a in all_apps if a["status"] in ["Menunggu Temuduga", "Temuduga Dijadualkan"]]
        sent_bpsm = [a for a in all_apps if a["status"] == "Dihantar ke BPSM"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📢 Iklan Aktif", len(active))
        c2.metric("📥 Permohonan", len(all_apps))
        c3.metric("✅ Shortlisted", len(shortlisted))
        c4.metric("📤 Ke BPSM", len(sent_bpsm))

        c5, c6, c7 = st.columns(3)
        c5.metric("⏳ Tunggu Pengarah", len(pending_director))
        c6.metric("✔ Lulus Pengarah", len(approved_director))
        c7.metric("🎤 Temuduga", len(interview_waiting))

        st.divider()
        st.info("Dashboard Bahagian memaparkan statistik sebenar daripada permohonan, shortlist, temuduga dan perakuan ke BPSM.")

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
                st.session_state.email,
            ))
            st.success("✅ Iklan berjaya disimpan.")

        st.divider()
        st.subheader("📋 Senarai Iklan")
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
            vacancy_id = options[selected]
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)

            if not applications:
                st.info("Tiada permohonan untuk iklan ini.")
            else:
                rows = [candidate_row(a, vacancy, include_detail=True) | {"Tarikh": a["submitted_at"]} for a in applications]
                df = pd.DataFrame(rows).sort_values(by="AI Score", ascending=False)
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
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)
            approved_apps = [a for a in applications if a["status"] == "Diluluskan Pengarah Bahagian Asal"]

            if not approved_apps:
                st.info("Tiada calon yang telah diluluskan oleh Pengarah Bahagian Asal.")
            else:
                rows = [candidate_row(a, vacancy, include_detail=True) for a in approved_apps]
                df = pd.DataFrame(rows).sort_values(by="AI Score", ascending=False)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.divider()
                st.subheader("🔍 AI Match Explanation")
                selected_explain = st.selectbox(
                    "Pilih calon untuk lihat penerangan AI",
                    df["Application ID"].tolist(),
                    key="explain_app",
                )
                selected_candidate = next((a for a in approved_apps if a["id"] == selected_explain), None)

                if selected_candidate:
                    score, explanation, recommendation = calculate_ai_match(selected_candidate, vacancy)
                    st.metric("AI Match Score", f"{score}%")
                    for item in explanation:
                        st.write(item)
                    st.success(f"Cadangan AI: {recommendation}")

                st.divider()
                selected_app = st.selectbox(
                    "Pilih Application ID untuk Shortlist",
                    df["Application ID"].tolist(),
                    key="shortlist_app",
                )
                if st.button("Shortlist Calon", use_container_width=True):
                    status = "Menunggu Temuduga" if vacancy["interview_required"] == "Ya" else "Shortlisted Bahagian"
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
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)
            interview_apps = [a for a in applications if a["status"] in ["Menunggu Temuduga", "Temuduga Dijadualkan"]]

            if not interview_apps:
                st.info("Tiada calon menunggu temuduga.")
            else:
                df = pd.DataFrame([candidate_row(a, vacancy, include_detail=False) for a in interview_apps]).sort_values(by="AI Score", ascending=False)
                st.dataframe(df, use_container_width=True, hide_index=True)

                selected_app = st.selectbox("Pilih Application ID", df["Application ID"].tolist(), key="interview_app")
                interview_date = st.date_input("Tarikh Temuduga")
                interview_time = st.time_input("Masa Temuduga")
                interview_location = st.text_input("Lokasi Temuduga")
                interview_panel = st.text_input("Panel Temuduga")

                if st.button("Jadualkan Temuduga", use_container_width=True):
                    add_interview((selected_app, str(interview_date), str(interview_time), interview_location, interview_panel, "Dijadualkan", ""))
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
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)
            shortlisted = [a for a in applications if a["status"] == "Shortlisted Bahagian"]

            if not shortlisted:
                st.info("Tiada calon shortlisted untuk dihantar ke BPSM.")
            else:
                df = pd.DataFrame([candidate_row(a, vacancy, include_detail=False) for a in shortlisted]).sort_values(by="AI Score", ascending=False)
                st.dataframe(df, use_container_width=True, hide_index=True)

                selected_app = st.selectbox(
                    "Pilih Application ID untuk dihantar",
                    df["Application ID"].tolist(),
                    key="send_bpsm_app",
                )
                selected_row = df[df["Application ID"] == selected_app].iloc[0]
                remarks = st.text_area("Catatan Bahagian")

                if st.button("Hantar ke BPSM", use_container_width=True):
                    send_to_bpsm(selected_app, selected_row["Email"], vacancy_id, st.session_state.department, remarks)
                    st.success("✅ Calon berjaya dihantar ke BPSM.")
                    st.rerun()
