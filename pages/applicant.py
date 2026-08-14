import pandas as pd
import streamlit as st

from database import (
    add_application,
    add_open_application,
    add_open_application_preference,
    get_active_vacancies,
    get_dropdown,
    get_districts_by_states,
    get_my_applications,
    get_my_open_application,
    get_open_preferences,
    get_talent_alerts,
    update_talent_match_status,
    get_talent_pool_profile,
    save_talent_pool_profile,
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
        "🔔 Talent Alert",
        "📊 Permohonan Saya",
    ])

    with tabs[0]:
        st.title("👤 Dashboard Pemohon")
        profile = get_profile(email)
        vacancies = get_active_vacancies()
        advertisement_vacancies = [
            v for v in vacancies
            if (v["vacancy_type"] or "ADVERTISEMENT") == "ADVERTISEMENT"
        ]
        talent_pool_vacancies = [
            v for v in vacancies
            if v["vacancy_type"] == "TALENT_POOL"
        ]
        applications = get_my_applications(email)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📢 Iklan Aktif", len(advertisement_vacancies))
        talent_alerts = get_talent_alerts(email)
        c2.metric("🔔 Talent Alert", len(talent_alerts))
        c3.metric("📝 Permohonan Saya", len(applications))
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
        work_scopes = [
            "Teknologi Pendidikan & Digital",
            "Latihan & Pembangunan Profesional Guru",
            "Pembangunan Profesionalisme / Kompetensi",
            "Pengurusan Sekolah",
            "Kepimpinan & Pengurusan Pendidikan",
            "Pemantauan & Penyeliaan Pendidikan",
            "Perancangan & Dasar Pendidikan",
            "Pembangunan Program Pendidikan",
            "Analisis Data & Statistik Pendidikan",
            "Jaminan Kualiti Pendidikan",
            "Penyelidikan & Inovasi Pendidikan",
            "Pengurusan Peperiksaan",
            "Pembangunan Bakat",
            "Pengurusan Institusi Pendidikan",
        ]

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

        st.divider()
        st.subheader("🟢 Talent Pool")

        talent_profile = get_talent_pool_profile(email)
        talent_active = bool(
            talent_profile and talent_profile["status"] == "ACTIVE"
        )

        if not talent_active:
            st.info(
                "Sertai Talent Pool untuk membolehkan profil anda "
                "dipertimbangkan oleh Bahagian melalui Talent Discovery. "
                "Ini bukan permohonan jawatan."
            )

            if st.button(
                "🟢 Sertai Talent Pool",
                use_container_width=True,
                type="primary",
                key="join_talent_pool",
            ):
                st.session_state["show_talent_pool_form"] = True

        if talent_active or st.session_state.get(
            "show_talent_pool_form",
            False,
        ):
            saved_scopes = (
                str(talent_profile["work_scope"])
                if talent_profile and talent_profile["work_scope"]
                else ""
            )
            saved_states = (
                str(talent_profile["states"])
                if talent_profile and talent_profile["states"]
                else ""
            )
            saved_districts = (
                str(talent_profile["districts"])
                if talent_profile and talent_profile["districts"]
                else ""
            )

            st.markdown("**Skop Kerja Yang Diminati**")
            if not work_scopes:
                st.warning(
                    "Belum ada pilihan Skop Kerja. Pilihan akan muncul "
                    "selepas Bahagian menerbitkan jawatan Talent Pool."
                )
                selected_scopes = []
            else:
                saved_scope_values = valid_multiselect_defaults(
                    saved_scopes,
                    work_scopes,
                )
                selected_scopes = []
                scope_cols = st.columns(2)
                for i, scope in enumerate(work_scopes):
                    with scope_cols[i % 2]:
                        if st.checkbox(
                            scope,
                            value=scope in saved_scope_values,
                            key=f"talent_scope_{i}",
                        ):
                            selected_scopes.append(scope)

            st.markdown("**Lokasi Pilihan**")

            state_options = ["Sedia ditempatkan di mana-mana"] + states
            saved_state = (
                saved_states
                if saved_states and saved_states != "ANY"
                else "Sedia ditempatkan di mana-mana"
            )

            selected_state = st.selectbox(
                "Negeri",
                state_options,
                index=(
                    state_options.index(saved_state)
                    if saved_state in state_options
                    else 0
                ),
                key="talent_state",
            )

            if selected_state == "Sedia ditempatkan di mana-mana":
                selected_states = ["ANY"]
                selected_districts = ["ANY"]
                st.info(
                    "Anda bersedia ditempatkan di mana-mana negeri dan "
                    "mana-mana daerah."
                )
            else:
                selected_states = [selected_state]

                district_options = [
                    "Sedia ditempatkan di mana-mana daerah"
                ] + get_districts_by_states([selected_state])

                saved_district = (
                    saved_districts
                    if saved_districts and saved_districts != "ANY"
                    else "Sedia ditempatkan di mana-mana daerah"
                )

                selected_district = st.selectbox(
                    "Daerah",
                    district_options,
                    index=(
                        district_options.index(saved_district)
                        if saved_district in district_options
                        else 0
                    ),
                    key="talent_district",
                )

                selected_districts = (
                    ["ANY"]
                    if selected_district == "Sedia ditempatkan di mana-mana daerah"
                    else [selected_district]
                )

            if st.button(
                "💾 Simpan & Sertai Talent Pool",
                use_container_width=True,
                type="primary",
                key="save_talent_pool",
            ):
                if not selected_scopes:
                    st.error(
                        "Sila pilih sekurang-kurangnya satu Skop Kerja."
                    )
                elif not selected_states:
                    st.error("Sila pilih Negeri.")
                elif not selected_districts:
                    st.error("Sila pilih Daerah.")
                else:
                    save_talent_pool_profile(
                        email=email,
                        work_scope=",".join(selected_scopes),
                        states=",".join(selected_states),
                        districts=",".join(selected_districts),
                        status="ACTIVE",
                    )
                    st.session_state["show_talent_pool_form"] = False
                    st.success(
                        "✅ Profil anda telah disertai ke Talent Pool. "
                        "Bahagian kini boleh mempertimbangkan profil anda "
                        "melalui Talent Discovery."
                    )
                    st.rerun()

            if talent_active:
                st.caption(
                    "🟢 Status Talent Pool: Aktif. "
                    "Anda masih perlu menekan Mohon Jawatan jika menerima "
                    "Talent Alert."
                )

    with tabs[2]:
        st.title("📢 Iklan Kekosongan")
        profile = get_profile(email)
        vacancies = [
            v for v in get_active_vacancies()
            if (v["vacancy_type"] or "ADVERTISEMENT") == "ADVERTISEMENT"
        ]

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
                    "Temuduga": "WAJIB" if (v["interview_required"] or "Ya") == "Ya" else v["interview_required"],
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

            st.info(
                "🤖 Penilaian AI akan dijalankan selepas permohonan dihantar "
                "dan digunakan sebagai sokongan kepada proses semakan dalaman."
            )

            if st.button("Hantar Permohonan Iklan", use_container_width=True):
                # AI score is deliberately not shown to the applicant.
                # The actual AI matching is handled by the Department workflow.
                add_application(
                    vacancy_id,
                    email,
                    0,
                    "Menunggu Kelulusan Pengarah Bahagian Asal",
                )
                st.success(
                    "✅ Permohonan berjaya dihantar. "
                    "Penilaian kesesuaian akan dibuat melalui proses semakan."
                )

    with tabs[3]:
        st.title("🔔 Talent Alert")
        st.caption(
            "AI mengenal pasti jawatan yang berpotensi sesuai dengan profil anda. "
            "Talent Alert bukan permohonan automatik."
        )

        alerts = get_talent_alerts(email)

        if not alerts:
            st.info(
                "Tiada Talent Alert baharu buat masa ini."
            )
        else:
            for alert in alerts:
                with st.container(border=True):
                    st.markdown(f"### {alert['title']}")
                    st.write(
                        f"**Bahagian:** {alert['department']}  \n"
                        f"**Lokasi:** {alert['district'] or '-'}, "
                        f"{alert['state'] or '-'}"
                    )

                    c1, c2 = st.columns(2)
                    c1.metric("Status", "Talent Alert")
                    c2.write("")

                    if alert["ai_ringkasan_bidang"]:
                        st.write(
                            f"**Skop Kerja:** "
                            f"{alert['ai_ringkasan_bidang']}"
                        )

                    recommendation_text = (
                        alert["explanation"]
                        or alert["recommendation"]
                        or ""
                    )

                    # Remove duplicated labels from legacy saved alerts.
                    recommendation_text = str(recommendation_text).strip()
                    while recommendation_text.lower().startswith("cadangan ai:"):
                        recommendation_text = recommendation_text[len("cadangan ai:"):].strip()

                    if recommendation_text:
                        st.write("**Kenapa anda dicadangkan:**")
                        st.info(
                            f"🤖 **Cadangan AI**\n\n{recommendation_text}"
                        )

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button(
                            "🟢 Mohon Jawatan",
                            use_container_width=True,
                            type="primary",
                            key=f"apply_talent_alert_{alert['id']}",
                        ):
                            add_application(
                                alert["vacancy_id"],
                                email,
                                0,
                                "Menunggu Kelulusan Pengarah Bahagian Asal",
                            )
                            update_talent_match_status(
                                alert["id"],
                                "Diluluskan untuk Permohonan",
                            )
                            st.success(
                                "✅ Permohonan berjaya dihantar. "
                                "Ia melalui proses semakan seperti permohonan biasa."
                            )
                            st.rerun()

                    with c2:
                        if st.button(
                            "Lihat Kemudian",
                            use_container_width=True,
                            key=f"later_talent_alert_{alert['id']}",
                        ):
                            update_talent_match_status(
                                alert["id"],
                                "Dilihat",
                            )
                            st.rerun()

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
                    "Jenis": (
                        "🟢 Talent Pool"
                        if a["source"] == "TALENT_POOL"
                        else "🟦 Iklan"
                    ),
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