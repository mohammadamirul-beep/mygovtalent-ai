import html
import json
import pandas as pd
import streamlit as st
import time

from database import (
    add_interview,
    add_application,
    add_vacancy,
    get_all_vacancies,
    get_vacancies_by_department,
    get_all_employee_profiles,
    get_active_talent_pool_candidates,
    get_applications_by_vacancy,
    save_talent_match,
    get_talent_matches_by_vacancy,
    get_districts_by_state,
    get_dropdown,
    get_vacancy,
    save_advertisement_vacancy,
    save_myportfolio_vacancy,
    send_to_bpsm,
    update_ai_snapshot,
    update_application_status,
)
from utils.cortex_matching import match_candidates
from cortex import extract_myportfolio

def safe_df(rows):
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


def department_vacancies():
    """Only show vacancies owned by the logged-in department."""
    return get_vacancies_by_department(
        st.session_state.get("department", "")
    )


def _readonly_card(label, value, multiline=False):
    """Render extracted Cortex data as a consistent read-only card."""
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value or "Tidak dikenal pasti"))
    value_html = safe_value.replace("\n", "<br>") if multiline else safe_value
    st.markdown(
        f"""
        <div style="
            border:1px solid #e1e5ea;
            border-radius:12px;
            padding:14px 16px;
            margin-bottom:14px;
            background:#ffffff;
        ">
            <div style="font-size:13px;color:#7a8088;margin-bottom:7px;">{safe_label}</div>
            <div style="font-size:16px;color:#343841;line-height:1.55;">{value_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _readonly_list_card(label, values):
    """Render an extracted array field using the same read-only card style."""
    values = values or []
    safe_label = html.escape(str(label))
    if values:
        items = "".join(
            f'<div style="margin:0 0 8px 0;">• {html.escape(str(item))}</div>'
            for item in values
        )
    else:
        items = '<div style="color:#8a9098;">Tidak dikenal pasti</div>'

    st.markdown(
        f"""
        <div style="
            border:1px solid #e1e5ea;
            border-radius:12px;
            padding:14px 16px;
            margin-bottom:14px;
            background:#ffffff;
        ">
            <div style="font-size:13px;color:#7a8088;margin-bottom:9px;">{safe_label}</div>
            <div style="font-size:16px;color:#343841;line-height:1.55;">{items}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def _prepare_demo_top5_release(vacancy, max_candidates=9):
    """
    Demo-only helper:
    create applications for cross-Bahagian Talent Pool profiles and mark them
    as already released, so the Top 5 button can be tested immediately.
    """
    profiles = get_active_talent_pool_candidates()
    vacancy_department = str(vacancy["department"] or "").strip().lower()

    created = 0
    for profile in profiles:
        email = str(profile["email"] or "").strip()
        current_department = str(
            profile["current_department"] or ""
        ).strip().lower()

        # Same-Bahagian candidate is treated as internal and does not need
        # the "Pengarah Bahagian Asal" release demo status.
        if not email or current_department == vacancy_department:
            continue

        add_application(
            vacancy_id=vacancy["id"],
            applicant_email=email,
            score=0,
            status="Diluluskan Pengarah Bahagian Asal",
        )
        created += 1

        if created >= max_candidates:
            break

    return created


def _app_value(row, key, default=""):
    try:
        value = row[key]
    except Exception:
        try:
            value = row.get(key, default)
        except Exception:
            value = default
    return default if value is None else value


def _find_application_for_cortex_candidate(candidate, applications):
    candidate_email = str(
        candidate.get("applicant_email")
        or candidate.get("email")
        or candidate.get("emel")
        or ""
    ).strip().lower()
    candidate_name = str(
        candidate.get("nama")
        or candidate.get("name")
        or ""
    ).strip().lower()

    # Prefer a stable email match; fall back to exact name for legacy/demo data.
    for app in applications:
        app_email = str(_app_value(app, "applicant_email", "")).strip().lower()
        if candidate_email and app_email and candidate_email == app_email:
            return app

    for app in applications:
        app_name = str(_app_value(app, "name", "")).strip().lower()
        if candidate_name and app_name and candidate_name == app_name:
            return app

    return None


def _official_score(candidate, applications):
    app = _find_application_for_cortex_candidate(candidate, applications)
    if app is not None:
        stored = _app_value(app, "score", None)
        if stored is not None and stored != "":
            return stored
    return candidate.get("match_score", 0)



def _typewriter_explanation(text, speed=0.012):
    """Display Cortex AI's explanation progressively, like a chat response."""
    if not text:
        st.info("Tiada penerangan tersedia.")
        return

    placeholder = st.empty()
    rendered = ""

    for char in str(text):
        rendered += char
        placeholder.markdown(
            f'<div class="ai-typewriter">{rendered}▌</div>',
            unsafe_allow_html=True,
        )
        time.sleep(speed)

    placeholder.markdown(
        f'<div class="ai-typewriter">{rendered}</div>',
        unsafe_allow_html=True,
    )


def _is_generic_ai_explanation(text):
    """Detect the generic technical explanation that is not useful to reviewers."""
    if not text:
        return True

    normalized = str(text).strip().lower()

    generic_markers = [
        "dikira secara deterministik",
        "dihitung secara deterministik",
        "ai tidak menentukan markah",
        "ai tidak menentukan skor",
        "weighted scoring",
        "scoring engine",
        "scoring engine.",
    ]

    return any(marker in normalized for marker in generic_markers)


def _build_rich_ai_explanation(candidate, run_no=1):
    """
    Fallback explanation only when Cortex does not return an explanation.

    The preferred path is to display Cortex AI's own `explanation` field
    directly. This fallback uses returned evidence without rotating or
    pretending that a Python template is an AI-generated explanation.
    """
    score = candidate.get("match_score", 0)
    recommendation = candidate.get("recommendation", "Tiada cadangan")

    strengths = candidate.get(
        "key_strengths",
        candidate.get("strengths", []),
    ) or []

    gaps = candidate.get(
        "key_gaps",
        candidate.get("gaps", []),
    ) or []

    parts = [
        f"Skor padanan: {score}/100.",
        f"Cadangan Cortex AI: {recommendation}.",
    ]

    if strengths:
        parts.append(
            "Kekuatan utama: " + "; ".join(str(x) for x in strengths[:3]) + "."
        )

    if gaps:
        parts.append(
            "Perkara untuk semakan: " + "; ".join(str(x) for x in gaps[:3]) + "."
        )

    return " ".join(parts)

def _explanation_for_candidate(candidate):
    """
    Prefer the explanation returned by Cortex AI.

    Only use the deterministic evidence-based fallback if Cortex did not
    return a usable explanation.
    """
    existing = candidate.get("explanation", "")

    if existing and not _is_generic_ai_explanation(existing):
        return existing

    return _build_rich_ai_explanation(candidate)

def _save_cortex_snapshot(ranking, applications):
    saved = 0
    for candidate in ranking or []:
        app = _find_application_for_cortex_candidate(candidate, applications)
        if app is None:
            continue

        score = candidate.get("match_score")
        if score is None:
            continue

        update_ai_snapshot(
            app["id"],
            score,
            explanation=_explanation_for_candidate(candidate),
            breakdown=candidate.get("score_breakdown", {}),
            strengths=candidate.get(
                "key_strengths", candidate.get("strengths", [])
            ),
            gaps=candidate.get("key_gaps", candidate.get("gaps", [])),
            recommendation=candidate.get("recommendation", ""),
        )
        saved += 1

    return saved


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
            "Skop Kerja": candidate["specialization"],
            "Pengalaman": candidate["experience"],
            "Pensijilan": candidate["certification"],
            "Kursus": candidate["course"],
            "Negeri": candidate["state"],
            "Daerah": candidate["district"],
        })

    return row


def show():
    tabs = st.tabs([
        "🏠 Dashboard",
        "🗂️ Pengurusan Jawatan",
        "🎯 Talent Discovery",
        "📥 Permohonan",
        "🤖 AI Recommendation",
        "🎤 Temuduga",
        "📤 Hantar ke BPSM",
    ])

    with tabs[0]:
        st.title("🏢 Dashboard Bahagian")

        vacancies = department_vacancies()
        active = [v for v in vacancies if v["status"] == "Active"]
        all_apps = applications_for_all_vacancies(vacancies)

        pending_director = [a for a in all_apps if a["status"] == "Menunggu Kelulusan Pengarah Bahagian Asal"]
        approved_director = [a for a in all_apps if a["status"] == "Diluluskan Pengarah Bahagian Asal"]
        shortlisted = [a for a in all_apps if a["status"] == "Berjaya Temuduga"]
        interview_waiting = [a for a in all_apps if a["status"] in ["Menunggu Temuduga", "Temuduga Dijadualkan"]]
        sent_bpsm = [a for a in all_apps if a["status"] == "Dihantar ke BPSM"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📌 Jawatan Aktif", len(active))
        c2.metric("📥 Permohonan", len(all_apps))
        c3.metric("✅ Shortlisted", len(shortlisted))
        c4.metric("📤 Ke BPSM", len(sent_bpsm))

        c5, c6, c7 = st.columns(3)
        c5.metric("⏳ Tunggu Pengarah", len(pending_director))
        c6.metric("✔ Lulus Pengarah", len(approved_director))
        c7.metric("🎤 Temuduga", len(interview_waiting))

        st.divider()
        st.info("Dashboard hanya memaparkan jawatan milik bahagian yang sedang log masuk serta status permohonan berkaitan.")

    with tabs[1]:
        st.title("🗂️ Pengurusan Jawatan")
        st.caption(
            f"Bahagian: {st.session_state.get('department', 'Tidak ditetapkan')} "
            "— Bahagian tidak perlu dipilih kerana ia datang daripada akaun log masuk."
        )

        route = st.radio(
            "Pilih kaedah pengisian jawatan",
            ["🟦 Permohonan Melalui Iklan", "🟢 Talent Pool / Terbuka"],
            horizontal=True,
            key="vacancy_route",
        )

        st.divider()

        # =================================================
        # ROUTE A — ADVERTISEMENT
        # =================================================
        if route == "🟦 Permohonan Melalui Iklan":
            st.subheader("🟦 Permohonan Melalui Iklan")
            st.caption("Bahagian mengisi sendiri maklumat keperluan jawatan.")

            states = get_dropdown("states", "state")

            with st.form("advertisement_vacancy_form"):
                title = st.text_input("Nama Jawatan *")

                c1, c2 = st.columns(2)
                with c1:
                    state = (
                        st.selectbox("Negeri *", states)
                        if states
                        else st.text_input("Negeri *")
                    )
                with c2:
                    districts = get_districts_by_state(state) if state else []
                    district = (
                        st.selectbox("Daerah *", districts)
                        if districts
                        else st.text_input("Daerah *")
                    )

                location = st.text_area("Alamat / Lokasi Bertugas")

                c1, c2 = st.columns(2)
                with c1:
                    competencies = st.text_area(
                        "Kompetensi",
                        help="Satu kompetensi bagi setiap baris.",
                    )
                    academic = st.text_area("Akademik")
                    professional = st.text_input("Ikhtisas")
                    experience = st.text_input("Pengalaman")
                with c2:
                    skills = st.text_area("Kemahiran")
                    certification = st.text_area("Pensijilan")
                    language = st.text_area("Bahasa")

                closing_date = st.date_input("Tarikh Tutup *")

                submitted = st.form_submit_button(
                    "📢 Simpan & Terbitkan Iklan",
                    use_container_width=True,
                    type="primary",
                )

            if submitted:
                if not title.strip():
                    st.error("Sila isi Nama Jawatan.")
                elif not state:
                    st.error("Sila pilih Negeri.")
                elif not district:
                    st.error("Sila pilih Daerah.")
                else:
                    try:
                        vacancy_id = save_advertisement_vacancy(
                            title=title.strip(),
                            department=st.session_state.department,
                            location=location.strip(),
                            state=state,
                            district=district,
                            academic=academic.strip(),
                            professional=professional.strip(),
                            experience=experience.strip(),
                            skills=skills.strip(),
                            competencies=competencies.strip(),
                            certification=certification.strip(),
                            language=language.strip(),
                            closing_date=closing_date,
                            created_by=st.session_state.email,
                        )
                        st.success(
                            f"🎉 Iklan berjaya diterbitkan. ID Jawatan: {vacancy_id}"
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"❌ Gagal menyimpan iklan: {exc}")

        # =================================================
        # ROUTE B — TALENT POOL
        # =================================================
        else:
            st.subheader("🟢 Talent Pool / Terbuka")
            st.caption(
                "Bahagian hanya perlu memuat naik MyPortfolio. "
                "Cortex akan mengekstrak jawatan dan menganalisis Skop Kerja "
                "untuk digunakan oleh Talent Discovery."
            )

            uploaded_file = st.file_uploader(
                "Upload MyPortfolio",
                type=["pdf"],
                key="myportfolio_upload",
                help="Satu fail PDF MyPortfolio pada satu masa.",
            )

            if st.button(
                "🤖 Analisis Dengan Cortex AI",
                use_container_width=True,
                type="primary",
                disabled=uploaded_file is None,
                key="extract_myportfolio",
            ):
                try:
                    with st.spinner(
                        "Cortex sedang membaca keseluruhan MyPortfolio..."
                    ):
                        extraction = extract_myportfolio(uploaded_file)

                    extraction["_myportfolio_filename"] = uploaded_file.name
                    st.session_state["myportfolio_extraction"] = extraction
                    st.success("✅ MyPortfolio berjaya dianalisis oleh Cortex AI.")
                except Exception as exc:
                    st.error(f"❌ Ekstraksi MyPortfolio gagal: {exc}")

            extraction = st.session_state.get("myportfolio_extraction")

            if extraction:
                st.divider()
                st.subheader("🔎 Hasil Cortex MyPortfolio")
                st.info(
                    "Maklumat di bawah datang daripada extraction Cortex. "
                    "AI Ringkasan Skop Kerja dan Fokus Kerja ialah hasil "
                    "analisis AI berdasarkan kandungan MyPortfolio."
                )

                left, right = st.columns(2)

                with left:
                    _readonly_card("Jawatan", extraction.get("jawatan"))
                    _readonly_card(
                        "Bahagian daripada MyPortfolio",
                        extraction.get("bahagian"),
                    )
                    _readonly_card(
                        "Tujuan",
                        extraction.get("tujuan"),
                        multiline=True,
                    )
                    _readonly_list_card("Fungsi", extraction.get("fungsi"))
                    _readonly_list_card(
                        "Kompetensi",
                        extraction.get("kompetensi"),
                    )

                with right:
                    _readonly_list_card(
                        "Akademik",
                        extraction.get("akademik"),
                    )
                    _readonly_card(
                        "Ikhtisas",
                        extraction.get("ikhtisas"),
                        multiline=True,
                    )
                    _readonly_card(
                        "Pengalaman",
                        extraction.get("pengalaman"),
                        multiline=True,
                    )
                    _readonly_list_card(
                        "Kemahiran",
                        extraction.get("kemahiran"),
                    )
                    _readonly_list_card(
                        "Pensijilan",
                        extraction.get("pensijilan"),
                    )
                    _readonly_list_card(
                        "Bahasa",
                        extraction.get("bahasa"),
                    )

                st.divider()
                st.subheader("🧠 AI Analisis Skop Kerja")

                _readonly_card(
                    "AI RINGKASAN SKOP KERJA",
                    extraction.get("ai_ringkasan_bidang"),
                    multiline=True,
                )

                _readonly_list_card(
                    "FOKUS KERJA",
                    extraction.get("ai_sub_bidang", []),
                )

                st.divider()
                st.subheader("✅ Pengesahan Bahagian")
                st.caption(
                    "Semak hasil extraction dan analisis AI. "
                    "Akaun ini akan direkodkan sebagai pemilik jawatan. "
                    "Tiada pilihan Bahagian diperlukan."
                )

                confirm = st.checkbox(
                    "Saya telah menyemak dan mengesahkan maklumat MyPortfolio "
                    "serta AI Ringkasan Skop Kerja / Fokus Kerja.",
                    key="myportfolio_confirm",
                )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(
                        "💾 Sahkan & Aktifkan Talent Pool",
                        use_container_width=True,
                        type="primary",
                        disabled=not confirm,
                        key="save_myportfolio_vacancy",
                    ):
                        title = extraction.get("jawatan") or "Jawatan Tanpa Nama"
                        try:
                            vacancy_id = save_myportfolio_vacancy(
                                title=title,
                                department=st.session_state.department,
                                location="",
                                state="",
                                district="",
                                extraction=extraction,
                                closing_date=None,
                                created_by=st.session_state.email,
                            )
                            st.session_state.pop("myportfolio_extraction", None)
                            st.session_state.pop("myportfolio_confirm", None)
                            st.success(
                                f"🎉 Jawatan berjaya dimasukkan ke Talent Pool. "
                                f"ID Jawatan: {vacancy_id}"
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(f"❌ Gagal menyimpan Talent Pool: {exc}")

                with c2:
                    if st.button(
                        "🗑️ Buang Hasil Extraction",
                        use_container_width=True,
                        key="discard_myportfolio_extraction",
                    ):
                        st.session_state.pop("myportfolio_extraction", None)
                        st.session_state.pop("myportfolio_confirm", None)
                        st.rerun()

        # =================================================
        # SAVED VACANCIES
        # =================================================
        st.divider()
        st.subheader("📋 Jawatan Milik Bahagian Ini")
        df = safe_df(department_vacancies())

        if df.empty:
            st.info("Tiada jawatan direkodkan untuk bahagian ini.")
        else:
            display_cols = [
                c for c in [
                    "id",
                    "title",
                    "vacancy_type",
                    "state",
                    "district",
                    "ai_ringkasan_bidang",
                    "closing_date",
                    "status",
                    "myportfolio_verified",
                ]
                if c in df.columns
            ]

            if "vacancy_type" in df.columns:
                df["vacancy_type"] = df["vacancy_type"].map(
                    {
                        "ADVERTISEMENT": "🟦 Iklan",
                        "TALENT_POOL": "🟢 Talent Pool",
                    }
                ).fillna(df["vacancy_type"])

            st.dataframe(
                df[display_cols] if display_cols else df,
                use_container_width=True,
                hide_index=True,
            )

    with tabs[2]:
        st.title("🎯 Talent Discovery")
        st.caption(
            "AI mengenal pasti pegawai yang berpotensi untuk jawatan Talent Pool "
            "berdasarkan profil kompetensi. Penemuan ini tidak mencipta "
            "permohonan secara automatik."
        )

        talent_vacancies = [
            v for v in department_vacancies()
            if v["status"] == "Active"
            and v["vacancy_type"] == "TALENT_POOL"
        ]

        if not talent_vacancies:
            st.info(
                "Tiada jawatan Talent Pool aktif untuk Talent Discovery."
            )
        else:
            options = {
                f"{v['id']} — {v['title']}": v["id"]
                for v in talent_vacancies
            }
            selected = st.selectbox(
                "Pilih Jawatan",
                list(options.keys()),
                key="talent_discovery_vacancy",
            )
            vacancy_id = options[selected]
            vacancy = get_vacancy(vacancy_id)

            with st.container(border=True):
                st.markdown(f"### {vacancy['title']}")
                st.write(f"**Bahagian:** {vacancy['department']}")
                st.write(
                    f"**Skop Kerja:** "
                    f"{vacancy['ai_ringkasan_bidang'] or vacancy['specialization'] or '-'}"
                )

                try:
                    subfields = json.loads(vacancy["ai_sub_bidang"] or "[]")
                except Exception:
                    subfields = []

                if subfields:
                    st.write("**Sub-skop:**")
                    for item in subfields:
                        st.write(f"• {item}")

            profiles = get_active_talent_pool_candidates()
            existing_apps = get_applications_by_vacancy(vacancy_id)
            existing_emails = {
                str(a["applicant_email"]).strip().lower()
                for a in existing_apps
                if a["applicant_email"]
            }

            st.divider()
            st.subheader("🔎 AI Candidate Discovery")

            if not profiles:
                st.info("Tiada profil pegawai tersedia.")
            else:
                st.caption(
                    f"{len(profiles)} pegawai aktif dalam Talent Pool • "
                    f"{len(existing_emails)} telah memohon jawatan ini"
                )

                if st.button(
                    "🚀 Jalankan Talent Discovery",
                    use_container_width=True,
                    type="primary",
                    key="run_talent_discovery",
                ):
                    # Build the eligible pool first so an empty pool is handled
                    # before calling Cortex.
                    eligible_profiles = [
                        profile
                        for profile in profiles
                        if str(profile["email"] or "").strip().lower()
                        not in existing_emails
                    ]

                    if not eligible_profiles:
                        st.session_state.pop("talent_discovery_results", None)
                        st.session_state["talent_discovery_vacancy_id"] = vacancy_id
                        st.warning(
                            "⚠️ Tiada pegawai Talent Pool yang layak untuk "
                            "Talent Discovery bagi jawatan ini."
                        )
                    else:
                        with st.spinner(
                            f"Cortex AI sedang membandingkan {len(eligible_profiles)} "
                            "profil Talent Pool dengan jawatan..."
                        ):
                            try:
                                # ALL eligible profiles are sent together.
                                # Cortex determines the ranking and recommendation.
                                cortex_result = match_candidates(
                                    vacancy,
                                    eligible_profiles,
                                )

                                if not isinstance(cortex_result, dict):
                                    raise RuntimeError(
                                        "Cortex memulangkan response yang tidak sah."
                                    )

                                cortex_ranking = cortex_result.get("ranking", [])

                                if not isinstance(cortex_ranking, list):
                                    raise RuntimeError(
                                        "Cortex tidak memulangkan 'ranking' dalam "
                                        "format senarai."
                                    )

                                if not cortex_ranking:
                                    st.session_state.pop(
                                        "talent_discovery_results",
                                        None,
                                    )
                                    st.error(
                                        "❌ Cortex tidak memulangkan sebarang calon "
                                        "daripada Talent Pool."
                                    )
                                    st.caption(
                                        f"{len(eligible_profiles)} profil telah "
                                        "dihantar untuk analisis. Semak konfigurasi "
                                        "Cortex Matching jika keadaan ini berterusan."
                                    )
                                else:
                                    results = []

                                    for item in cortex_ranking:
                                        email = str(
                                            item.get("email")
                                            or item.get("applicant_email")
                                            or ""
                                        ).strip()

                                        source_profile = next(
                                            (
                                                p for p in eligible_profiles
                                                if str(p["email"] or "").strip().lower()
                                                == email.lower()
                                            ),
                                            None,
                                        )

                                        if source_profile is None:
                                            continue

                                        results.append({
                                            "email": email,
                                            "name": item.get("nama")
                                            or source_profile["name"]
                                            or email,
                                            "current_position": source_profile["current_position"] or "-",
                                            "current_department": source_profile["current_department"] or "-",
                                            "grade": source_profile["grade"] or "-",
                                            "state": source_profile["state"] or "-",
                                            "district": source_profile["district"] or "-",
                                            "academic": source_profile["academic"] or "-",
                                            "professional": source_profile["professional"] or "-",
                                            "specialization": source_profile["specialization"] or "-",
                                            "experience": source_profile["experience"] or 0,
                                            "talent_work_scope": source_profile["talent_work_scope"] or "",
                                            "talent_states": source_profile["talent_states"] or "",
                                            "talent_districts": source_profile["talent_districts"] or "",
                                            # Score is Cortex output only.
                                            "score": item.get("match_score", 0),
                                            "match_score": item.get("match_score", 0),
                                            "explanation": item.get("explanation", ""),
                                            "recommendation": item.get("recommendation", ""),
                                            "key_strengths": item.get(
                                                "key_strengths",
                                                item.get("strengths", []),
                                            ),
                                            "key_gaps": item.get(
                                                "key_gaps",
                                                item.get("gaps", []),
                                            ),
                                            "score_breakdown": item.get(
                                                "score_breakdown",
                                                {},
                                            ),
                                            "rank": item.get("rank"),
                                        })

                                    if not results:
                                        st.error(
                                            "❌ Cortex memulangkan ranking tetapi "
                                            "tiada calon dapat dipadankan semula "
                                            "dengan profil Talent Pool."
                                        )
                                    else:
                                        st.session_state[
                                            "talent_discovery_results"
                                        ] = results
                                        st.session_state[
                                            "talent_discovery_vacancy_id"
                                        ] = vacancy_id

                                        st.success(
                                            f"✅ Cortex berjaya menganalisis "
                                            f"{len(eligible_profiles)} profil dan "
                                            f"memulangkan {len(results)} calon."
                                        )

                            except Exception as e:
                                st.error(
                                    f"❌ Talent Discovery Cortex gagal: {str(e)}"
                                )

                results = st.session_state.get(
                    "talent_discovery_results", []
                )
                result_vacancy_id = st.session_state.get(
                    "talent_discovery_vacancy_id"
                )

                if results and result_vacancy_id == vacancy_id:
                    st.success(
                        f"✅ {len(results)} calon berpotensi ditemui."
                    )

                    ranking_rows = []
                    for rank, candidate in enumerate(results, start=1):
                        ranking_rows.append({
                            "Kedudukan": candidate.get("rank") or rank,
                            "Nama": candidate["name"],
                            "Jawatan Semasa": candidate["current_position"],
                            "Bahagian Semasa": candidate["current_department"],
                            "Gred": candidate["grade"],
                            "Cadangan AI": candidate.get("recommendation") or "-",
                            "Negeri": candidate["state"],
                        })

                    st.dataframe(
                        pd.DataFrame(ranking_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.divider()

                    labels = [
                        f"{i+1} — {c['name']}"
                        for i, c in enumerate(results)
                    ]
                    selected_label = st.selectbox(
                        "Pilih calon untuk lihat analisis",
                        labels,
                        key="talent_discovery_candidate",
                    )
                    idx = labels.index(selected_label)
                    candidate = results[idx]

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Cadangan AI", "Semak")
                    c2.metric("Gred", candidate["grade"])
                    c3.metric(
                        "Pengalaman",
                        f"{candidate['experience']} tahun",
                    )

                    st.markdown(
                        f"**{candidate['name']}**  \n"
                        f"{candidate['current_position']} • "
                        f"{candidate['current_department']}"
                    )

                    with st.expander(
                        "📄 Profil Ringkas",
                        expanded=True,
                    ):
                        st.write(
                            f"**Akademik:** {candidate['academic']}"
                        )
                        st.write(
                            f"**Ikhtisas:** {candidate['professional']}"
                        )
                        st.write(
                            f"**Pengkhususan:** {candidate['specialization']}"
                        )
                        st.write(
                            f"**Lokasi:** {candidate['district']}, "
                            f"{candidate['state']}"
                        )

                    st.subheader("🤖 Cortex AI Recommendation")
                    recommendation_text = str(
                        candidate.get("recommendation") or ""
                    ).strip()
                    while recommendation_text.lower().startswith("cadangan ai:"):
                        recommendation_text = recommendation_text[len("cadangan ai:"):].strip()

                    st.info(
                        f"**Cadangan AI**\n\n{recommendation_text}"
                        if recommendation_text
                        else "Tiada cadangan AI tersedia."
                    )
                    st.caption(
                        "Cadangan ini menerangkan kesesuaian berdasarkan "
                        "keutamaan Talent Pool, lokasi dan maklumat profil yang tersedia."
                    )

                    # Always initialise the explanation before the button.
                    # The previous version only assigned it inside the detail
                    # rendering path, which caused UnboundLocalError when the
                    # Talent Alert button was clicked.
                    explanation = str(
                        candidate.get("explanation")
                        or candidate.get("recommendation")
                        or "Tiada penerangan AI tersedia."
                    )

                    if st.button(
                        "📨 Hantar Talent Alert kepada Pegawai",
                        use_container_width=True,
                        type="primary",
                        key="send_talent_alert",
                    ):
                        save_talent_match(
                            vacancy_id=vacancy_id,
                            applicant_email=candidate["email"],
                            score=candidate["score"],
                            explanation=explanation,
                            recommendation=str(
                                candidate.get("recommendation") or ""
                            ),
                            status="Talent Alert Dihantar",
                        )
                        st.success(
                            f"📨 Talent Alert dihantar kepada "
                            f"{candidate['name']}. "
                            "Pegawai masih perlu memilih sendiri "
                            "untuk memohon."
                        )

                    st.caption(
                        "AI mencadangkan calon; pegawai kekal mempunyai "
                        "pilihan untuk menerima atau tidak."
                    )

                alerts = get_talent_matches_by_vacancy(vacancy_id)
                if alerts:
                    st.divider()
                    st.subheader("📬 Talent Alert")
                    alert_rows = [
                        {
                            "Nama": a["name"] or a["applicant_email"],
                            "Cadangan AI": a["recommendation"] or "-",
                            "Jawatan Semasa": a["current_position"] or "-",
                            "Bahagian Semasa": a["current_department"] or "-",
                            "Status": a["status"],
                        }
                        for a in alerts
                    ]
                    st.dataframe(
                        pd.DataFrame(alert_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

    with tabs[3]:
        st.title("📥 Permohonan Mengikut Iklan")
        vacancies = department_vacancies()

        if not vacancies:
            st.info("Tiada jawatan.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Jawatan", list(options.keys()), key="permohonan_vacancy")
            vacancy_id = options[selected]
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)

            if not applications:
                st.info("Tiada permohonan untuk iklan ini.")
            else:
                rows = [candidate_row(a, vacancy, include_detail=True) | {"Tarikh": a["submitted_at"]} for a in applications]
                df = pd.DataFrame(rows).sort_values(by="AI Score", ascending=False)
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.title("🤖 AI Recommendation")
        st.caption(
            "AI Recommendation menerangkan kesesuaian calon dengan jawatan. "
            "Skor digunakan sebagai analisis dalaman; paparan ini menekankan "
            "penerangan seperti respons ChatGPT."
        )

        vacancies = department_vacancies()

        if not vacancies:
            st.info("Tiada jawatan untuk diproses.")
        else:
            options = {
                f"{v['id']} - {v['title']} ({v['department']})": v["id"]
                for v in vacancies
            }

            selected = st.selectbox(
                "Pilih Jawatan",
                list(options.keys()),
                key="ai_vacancy",
            )

            vacancy_id = options[selected]
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)

            pending_apps = [
                a for a in applications
                if a["status"] == "Menunggu Kelulusan Pengarah Bahagian Asal"
            ]

            approved_apps = [
                a for a in applications
                if a["status"] == "Diluluskan Pengarah Bahagian Asal"
            ]

            # ============================================================
            # STAGE 1 — BEFORE DIRECTOR RELEASE
            # Compare EACH applicant against the vacancy.
            # ============================================================
            if pending_apps:
                st.divider()
                st.subheader("📝 AI Recommendation — Pemohon vs Jawatan")
                st.info(
                    f"{len(pending_apps)} pemohon masih menunggu pelepasan "
                    "Pengarah Bahagian Asal."
                )

                pending_options = {
                    f"{i + 1}. {_app_value(a, 'name', '') or _app_value(a, 'applicant_email', '')}":
                    a
                    for i, a in enumerate(pending_apps)
                }

                selected_pending_label = st.selectbox(
                    "Pilih pemohon untuk melihat perbandingan",
                    list(pending_options.keys()),
                    key="ai_pending_candidate",
                )
                selected_pending = pending_options[selected_pending_label]

                if st.button(
                    "✨ Jana AI Recommendation",
                    use_container_width=True,
                    type="primary",
                    key="generate_pending_recommendation",
                ):
                    with st.spinner("AI sedang membandingkan pemohon dengan jawatan..."):
                        try:
                            pending_result = match_candidates(
                                vacancy,
                                [selected_pending],
                            )
                            pending_ranking = pending_result.get("ranking", [])
                            if pending_ranking:
                                pending_candidate = pending_ranking[0]
                                pending_explanation = _explanation_for_candidate(
                                    pending_candidate
                                )
                                st.session_state["pending_ai_recommendation"] = (
                                    pending_explanation
                                )
                                st.session_state["pending_ai_candidate_id"] = (
                                    selected_pending["id"]
                                )
                            else:
                                st.session_state["pending_ai_recommendation"] = (
                                    "AI tidak dapat menghasilkan perbandingan "
                                    "untuk pemohon ini."
                                )
                        except Exception as e:
                            st.error(f"❌ AI Recommendation gagal: {str(e)}")

                pending_explanation = st.session_state.get(
                    "pending_ai_recommendation"
                )
                if pending_explanation:
                    st.subheader("🤖 AI Recommendation")
                    _typewriter_explanation(
                        pending_explanation,
                        speed=0.008,
                    )
                    st.caption(
                        "Perbandingan ini membantu semakan awal. "
                        "Pelepasan calon tetap merupakan keputusan Pengarah "
                        "Bahagian Asal."
                    )

            # ============================================================
            # STAGE 2 — AFTER DIRECTOR RELEASE
            # Compare the TOP 5 released applicants against each other.
            # ============================================================
            # ============================================================
            # STAGE 2 — AFTER DIRECTOR RELEASE
            # Always render this stage after a vacancy is selected.
            # Demo data can be prepared here so the Top 5 button is immediately
            # usable without running the real release workflow tonight.
            # ============================================================
            st.divider()
            st.subheader("🏆 AI Scoring & Ranking — Top 5 Pemohon")

            if not approved_apps:
                st.warning(
                    "Tiada pemohon berstatus 'Diluluskan Pengarah Bahagian Asal' "
                    "untuk jawatan ini."
                )
                st.caption(
                    "Untuk demo Top 5, sediakan dahulu data demo. "
                    "Ini hanya shortcut demo dan tidak mengubah flow pelepasan sebenar."
                )

                if st.button(
                    "🧪 Sediakan Data Demo — Calon Telah Dilepaskan",
                    use_container_width=True,
                    type="secondary",
                    key="prepare_demo_top5_release",
                ):
                    try:
                        created = _prepare_demo_top5_release(vacancy)
                        if created:
                            st.success(
                                f"✅ {created} calon cross-Bahagian telah disediakan "
                                "sebagai calon yang telah menerima pelepasan."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "❌ Tiada calon cross-Bahagian ditemui dalam Talent Pool."
                            )
                    except Exception as e:
                        st.error(f"❌ Gagal menyediakan data demo Top 5: {str(e)}")

            approved_apps = get_applications_by_vacancy(vacancy_id)
            approved_apps = [
                a for a in approved_apps
                if a["status"] == "Diluluskan Pengarah Bahagian Asal"
            ]

            if approved_apps:
                st.info(
                    f"{len(approved_apps)} pemohon telah menerima pelepasan. "
                    "Cortex AI akan membandingkan semua calon yang telah dilepaskan, "
                    "memberi AI scoring, menyusun ranking dan memaparkan Top 5."
                )

                if st.button(
                    "🚀 Jalankan AI Scoring & Ranking Top 5",
                    use_container_width=True,
                    type="primary",
                    key="run_top5_ai_recommendation",
                ):
                    with st.spinner(
                        "AI sedang membandingkan calon yang telah dilepaskan..."
                    ):
                        try:
                            top5_result = match_candidates(
                                vacancy,
                                approved_apps,
                            )
                            top5_ranking = top5_result.get("ranking", [])[:5]

                            # Persist the official AI snapshot for all released
                            # candidates, while the recommendation UI focuses on
                            # the top five.
                            _save_cortex_snapshot(
                                top5_result.get("ranking", []),
                                approved_apps,
                            )

                            st.session_state["top5_ai_result"] = top5_result
                            st.session_state["top5_ai_vacancy_id"] = vacancy_id
                        except Exception as e:
                            st.error(
                                f"❌ AI Scoring & Ranking Top 5 gagal: {str(e)}"
                            )

                top5_result = st.session_state.get("top5_ai_result")
                if (
                    top5_result
                    and st.session_state.get("top5_ai_vacancy_id") == vacancy_id
                ):
                    top5_ranking = top5_result.get("ranking", [])[:5]

                    if not top5_ranking:
                        st.warning("Tiada calon diterima untuk perbandingan AI.")
                    else:
                        # Keep the ranking table concise and hide raw score from
                        # the recommendation narrative.
                        top5_rows = []
                        for item in top5_ranking:
                            strengths = item.get(
                                "key_strengths",
                                item.get("strengths", []),
                            ) or []
                            gaps = item.get(
                                "key_gaps",
                                item.get("gaps", []),
                            ) or []

                            top5_rows.append({
                                "Kedudukan": item.get("rank"),
                                "Nama": item.get("nama"),
                                "AI Score": item.get("match_score", "-"),
                                "Kekuatan": "; ".join(
                                    str(x) for x in strengths[:2]
                                ) or "-",
                                "Jurang": "; ".join(
                                    str(x) for x in gaps[:2]
                                ) or "-",
                                "Cadangan": item.get(
                                    "recommendation",
                                    "Perlu semakan lanjut",
                                ),
                            })

                        st.dataframe(
                            pd.DataFrame(top5_rows),
                            use_container_width=True,
                            hide_index=True,
                        )

                        # TOP 5 REVIEW — show evidence, strengths, gaps and
                        # factor-level analysis returned by Cortex. This is
                        # intentionally different from the earlier Talent
                        # Discovery view: the question here is "why did this
                        # released candidate rank above/below the other released
                        # candidates?"
                        st.subheader("🤖 Cortex AI — Strength, Gap & Recommendation")

                        st.caption(
                            "Analisis ini membandingkan calon yang telah menerima "
                            "pelepasan. Cortex menilai kekuatan, jurang dan faktor "
                            "kesesuaian setiap calon sebelum menyusun ranking Top 5."
                        )

                        for item in top5_ranking:
                            rank = item.get("rank", "")
                            name = item.get("nama", "Calon")
                            score = item.get("match_score", "-")

                            st.markdown(
                                f"### {rank}. {name}  ·  AI Score: {score}/100"
                            )

                            recommendation = str(
                                item.get("recommendation") or ""
                            ).strip()
                            explanation = str(
                                item.get("explanation") or ""
                            ).strip()

                            while recommendation.lower().startswith("cadangan ai:"):
                                recommendation = recommendation[
                                    len("cadangan ai:"):
                                ].strip()

                            if recommendation:
                                st.info(
                                    f"**Cadangan AI:** {recommendation}"
                                )

                            # Evidence from Cortex — do not invent strengths
                            # or gaps in Python.
                            strengths = item.get(
                                "key_strengths",
                                item.get("strengths", []),
                            ) or []
                            gaps = item.get(
                                "key_gaps",
                                item.get("gaps", []),
                            ) or []

                            c_strength, c_gap = st.columns(2)

                            with c_strength:
                                st.markdown("**💪 Kekuatan Utama**")
                                if strengths:
                                    for strength in strengths[:5]:
                                        st.markdown(
                                            f"- {str(strength).strip()}"
                                        )
                                else:
                                    st.caption(
                                        "Tiada kekuatan khusus dinyatakan oleh Cortex."
                                    )

                            with c_gap:
                                st.markdown("**⚠️ Jurang / Perkara untuk Semakan**")
                                if gaps:
                                    for gap in gaps[:5]:
                                        st.markdown(
                                            f"- {str(gap).strip()}"
                                        )
                                else:
                                    st.caption(
                                        "Tiada jurang khusus dinyatakan oleh Cortex."
                                    )

                            if explanation:
                                st.markdown("**🧠 Analisis Cortex**")
                                _typewriter_explanation(
                                    explanation,
                                    speed=0.008,
                                )

                            breakdown = item.get("score_breakdown", {}) or {}
                            if breakdown:
                                st.markdown("**📊 Faktor Kesesuaian**")
                                factor_labels = {
                                    "skop_kerja": "Skop Kerja",
                                    "lokasi": "Lokasi",
                                    "kompetensi": "Kompetensi",
                                    "pengalaman": "Pengalaman",
                                    "akademik": "Akademik",
                                    "ikhtisas": "Ikhtisas",
                                    "kemahiran": "Kemahiran",
                                    "pensijilan": "Pensijilan",
                                    "bahasa": "Bahasa",
                                }
                                factor_rows = []
                                for key, value in breakdown.items():
                                    label = factor_labels.get(
                                        key,
                                        str(key).replace("_", " ").title(),
                                    )
                                    factor_rows.append(
                                        {
                                            "Faktor": label,
                                            "Cortex Assessment": value,
                                        }
                                    )

                                if factor_rows:
                                    st.dataframe(
                                        pd.DataFrame(factor_rows),
                                        use_container_width=True,
                                        hide_index=True,
                                    )

                            st.divider()

                        st.caption(
                            "AI Score, strength, gap, factor assessment dan "
                            "recommendation di atas adalah output Cortex AI. "
                            "Paparan ini adalah untuk semakan dalaman Bahagian; "
                            "AI Score tidak dipaparkan kepada pegawai melalui Talent Alert."
                        )

                        # Individual explanations remain available when the
                        # reviewer wants to understand a particular candidate.
                        st.divider()
                        st.subheader("🔎 Analisis Individu Top 5")

                        top5_labels = [
                            f"{item.get('rank')} - {item.get('nama')}"
                            for item in top5_ranking
                        ]
                        selected_top5_label = st.selectbox(
                            "Pilih calon",
                            top5_labels,
                            key="top5_candidate_detail",
                        )
                        selected_top5 = next(
                            (
                                item for item in top5_ranking
                                if f"{item.get('rank')} - {item.get('nama')}"
                                == selected_top5_label
                            ),
                            None,
                        )

                        if selected_top5:
                            individual_explanation = _explanation_for_candidate(
                                selected_top5
                            )
                            _typewriter_explanation(
                                individual_explanation,
                                speed=0.008,
                            )

                        st.divider()

                        # =====================================================
                        # HUMAN DECISION
                        # =====================================================
                        st.subheader("👤 Human Review")
                        shortlist_options = [
                            f"{c.get('rank')} - {c.get('nama')}"
                            for c in top5_ranking
                        ]

                        selected_shortlist = st.selectbox(
                            "Pilih calon untuk shortlist",
                            shortlist_options,
                            key="cortex_shortlist_candidate",
                        )

                        selected_for_shortlist = next(
                            (
                                c for c in top5_ranking
                                if f"{c.get('rank')} - {c.get('nama')}"
                                == selected_shortlist
                            ),
                            None,
                        )

                        if selected_for_shortlist:
                            if st.button(
                                "✅ Shortlist Calon",
                                use_container_width=True,
                                key="shortlist_top5_candidate",
                            ):
                                selected_name = selected_for_shortlist.get("nama")
                                matched_application = None

                                for app in approved_apps:
                                    app_name = (
                                        _app_value(app, "name", "")
                                        or _app_value(
                                            app,
                                            "applicant_email",
                                            "",
                                        )
                                    )
                                    if app_name == selected_name:
                                        matched_application = app
                                        break

                                if matched_application:
                                    update_application_status(
                                        matched_application["id"],
                                        "Menunggu Temuduga",
                                    )
                                    st.success(
                                        f"✅ {selected_name} berjaya disenarai pendek."
                                    )
                                    st.rerun()
                                else:
                                    st.error(
                                        "Calon tidak dapat dipadankan "
                                        "dengan rekod permohonan."
                                    )

    with tabs[5]:
        st.title("🎤 Temuduga")
        vacancies = department_vacancies()

        if not vacancies:
            st.info("Tiada jawatan.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Jawatan", list(options.keys()), key="interview_vacancy")
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
                        update_application_status(selected_app, "Berjaya Temuduga")
                        st.success(
                            "🎉 Tahniah! Calon berjaya dalam sesi temuduga."
                        )
                        st.rerun()
                with col2:
                    if st.button("❌ Gagal Temuduga", use_container_width=True):
                        update_application_status(selected_app, "Gagal Temuduga")
                        st.warning("Calon gagal temuduga.")
                        st.rerun()

    with tabs[6]:
        st.title("📤 Hantar ke BPSM")
        vacancies = department_vacancies()

        if not vacancies:
            st.info("Tiada jawatan.")
        else:
            options = {f"{v['id']} - {v['title']} ({v['department']})": v["id"] for v in vacancies}
            selected = st.selectbox("Pilih Jawatan", list(options.keys()), key="bpsm_vacancy")
            vacancy_id = options[selected]
            vacancy = get_vacancy(vacancy_id)
            applications = get_applications_by_vacancy(vacancy_id)
            shortlisted = [a for a in applications if a["status"] == "Berjaya Temuduga"]

            if not shortlisted:
                st.info("Tiada calon yang berjaya temuduga untuk dihantar ke BPSM.")
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