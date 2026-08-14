import json
import pandas as pd
import streamlit as st

from utils.placement_order import generate_placement_order_pdf

from database import (
    get_placements,
    get_vacancy,
    get_applications_by_vacancy,
    get_profile,
    update_bpsm_status,
    update_application_status,
    get_post_kppm_pending,
    send_kppm_decision_to_directors,
)


def _row_value(row, key, default=""):
    if row is None:
        return default
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        try:
            value = row.get(key, default)
        except AttributeError:
            value = default
    return default if value is None else value


def _get_application(placement):
    vacancy_id = _row_value(placement, "vacancy_id")
    application_id = _row_value(placement, "application_id")
    if not vacancy_id or not application_id:
        return None

    for app in get_applications_by_vacancy(vacancy_id):
        if _row_value(app, "id") == application_id:
            return app
    return None


def _decode(value, default):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _show_profile(application, vacancy):
    st.subheader("👤 Profil Pegawai")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nama", _row_value(application, "name", "-"))
    c2.metric("Gred", _row_value(application, "grade", "-"))
    c3.metric(
        "Jawatan Semasa",
        _row_value(application, "current_position", "-"),
    )

    c1, c2 = st.columns(2)
    c1.write(
        f"**Bahagian Asal:** "
        f"{_row_value(application, 'current_department', '-')}"
    )
    c2.write(
        f"**Email:** "
        f"{_row_value(application, 'applicant_email', '-')}"
    )

    st.divider()
    st.subheader("🎯 Jawatan Diperakukan")

    c1, c2 = st.columns(2)
    c1.write(f"**Jawatan:** {_row_value(vacancy, 'title', '-')}")
    c2.write(
        f"**Bahagian Baharu:** "
        f"{_row_value(vacancy, 'department', '-')}"
    )

    c1, c2 = st.columns(2)
    c1.write(
        f"**Pengalaman Minimum:** "
        f"{_row_value(vacancy, 'experience', 0)} tahun"
    )
    c2.write(
        f"**Pengalaman Pegawai:** "
        f"{_row_value(application, 'experience', 0)} tahun"
    )

    st.divider()
    st.subheader("📋 Perbandingan Keperluan")

    rows = [
        ("Akademik", "academic"),
        ("Ikhtisas", "professional"),
        ("Pengkhususan", "specialization"),
        ("Pensijilan", "certification"),
        ("Kursus", "course"),
        ("Bahasa", "language"),
        ("Kompetensi", "competencies"),
        ("Kemahiran", "skills"),
    ]

    data = []
    for label, key in rows:
        data.append({
            "Faktor": label,
            "Profil Pegawai": _row_value(application, key, "-"),
            "Keperluan Jawatan": _row_value(vacancy, key, "-"),
        })

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True,
    )


def _show_ai(application):
    st.subheader("🤖 AI Matching")

    score = _row_value(application, "score", 0)
    explanation = _decode(
        _row_value(application, "ai_explanation", ""),
        _row_value(application, "ai_explanation", ""),
    )
    breakdown = _decode(
        _row_value(application, "ai_breakdown", ""),
        {},
    )
    strengths = _decode(
        _row_value(application, "ai_strengths", ""),
        [],
    )
    gaps = _decode(
        _row_value(application, "ai_gaps", ""),
        [],
    )
    recommendation = _row_value(
        application,
        "ai_recommendation",
        "Tiada cadangan AI direkodkan.",
    )

    c1, c2 = st.columns([1, 2])
    c1.metric("AI Match Score", f"{score}/100")
    c2.info(f"**Cadangan AI:** {recommendation}")

    st.caption(
        "🔒 Snapshot rasmi Cortex AI. BPSM tidak mengira semula skor."
    )

    st.subheader("📊 Score Breakdown")
    if isinstance(breakdown, dict) and breakdown:
        for factor, value in breakdown.items():
            st.write(
                f"**{str(factor).replace('_', ' ').title()}:** {value}"
            )
    elif isinstance(breakdown, list) and breakdown:
        for item in breakdown:
            st.write(item)
    else:
        st.info("Tiada score breakdown direkodkan.")

    if strengths:
        st.subheader("💪 Kekuatan Calon")
        for item in strengths if isinstance(strengths, list) else [strengths]:
            st.write(f"✔ {item}")

    if gaps:
        st.subheader("⚠️ Jurang / Perkara Perlu Semakan")
        for item in gaps if isinstance(gaps, list) else [gaps]:
            st.write(f"• {item}")

    if explanation:
        st.subheader("🧠 AI Explanation")
        if isinstance(explanation, list):
            for item in explanation:
                st.write(item)
        elif isinstance(explanation, dict):
            for key, value in explanation.items():
                st.write(f"**{key}:** {value}")
        else:
            st.write(explanation)


def _candidate_tabs(placement, application, vacancy):
    score = _row_value(application, "score", 0)
    tab_profile, tab_ai, tab_order, tab_decision = st.tabs([
        "👤 Profil & Keperluan",
        "🤖 AI Matching",
        "📄 Arahan Penempatan",
        "⚖️ Keputusan BPSM",
    ])

    with tab_profile:
        _show_profile(application, vacancy)

    with tab_ai:
        _show_ai(application)

    with tab_order:
        st.subheader("📄 Draf Arahan Penempatan")
        st.caption(
            "Draf ini disediakan BPSM untuk semakan sebelum dihantar "
            "kepada KPPM. Belum mempunyai tandatangan digital KPPM."
        )

        profile = get_profile(
            _row_value(placement, "applicant_email", "")
        )

        draft_pdf = generate_placement_order_pdf(
            placement=placement,
            profile=profile,
            vacancy=vacancy,
        )

        st.download_button(
            "📄 Lihat / Muat Turun Draf Arahan Penempatan",
            data=draft_pdf,
            file_name=(
                f"Arahan_Penempatan_Draf_"
                f"{_row_value(placement, 'name', 'Calon').replace(' ', '_')}.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            key=f"draft_placement_{_row_value(placement, 'id')}",
        )

    with tab_decision:
        st.subheader("⚖️ Keputusan BPSM")

        remarks = st.text_area(
            "Ulasan / catatan BPSM",
            key=f"bpsm_remarks_{_row_value(placement, 'id')}",
            placeholder="Masukkan ulasan semakan dan perakuan BPSM...",
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "↩️ Pulangkan kepada Bahagian",
                use_container_width=True,
                key=f"return_bpsm_{_row_value(placement, 'id')}",
            ):
                update_bpsm_status(
                    _row_value(placement, "id"),
                    "Dipulangkan ke Bahagian",
                    remarks=remarks,
                )
                update_application_status(
                    _row_value(placement, "application_id"),
                    "Dipulangkan ke Bahagian",
                )
                st.warning("Perakuan telah dipulangkan kepada Bahagian.")
                st.rerun()

        with c2:
            if st.button(
                "✅ Peraku kepada KPPM",
                use_container_width=True,
                type="primary",
                key=f"recommend_kppm_{_row_value(placement, 'id')}",
            ):
                update_bpsm_status(
                    _row_value(placement, "id"),
                    "Diperakukan BPSM",
                    remarks=remarks,
                )
                update_application_status(
                    _row_value(placement, "application_id"),
                    "Diperakukan BPSM",
                )
                st.success(
                    f"✅ Calon diperakukan kepada KPPM "
                    f"(AI Match Score: {score}/100)."
                )
                st.rerun()


def _post_kppm_tab():
    post_kppm = get_post_kppm_pending()

    if not post_kppm:
        st.success("Tiada keputusan KPPM yang menunggu penghantaran.")
        return

    rows = []
    for p in post_kppm:
        rows.append({
            "ID": _row_value(p, "id"),
            "Nama": _row_value(p, "name", "-"),
            "Jawatan": _row_value(p, "title", "-"),
            "Bahagian Asal": _row_value(p, "current_department", "-"),
            "Bahagian Baharu": _row_value(p, "target_department", "-"),
            "KPPM": _row_value(p, "kppm_signed_by", "-"),
            "Tarikh Sign": _row_value(p, "kppm_signed_at", "-"),
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    options = {
        (
            f"{_row_value(p, 'id')} — "
            f"{_row_value(p, 'name', 'Calon')} — "
            f"{_row_value(p, 'title', 'Jawatan')}"
        ): _row_value(p, "id")
        for p in post_kppm
    }

    label = st.selectbox(
        "Pilih keputusan KPPM",
        list(options.keys()),
        key="bpsm_post_kppm_selection",
    )
    selected_id = options[label]
    selected = next(
        (p for p in post_kppm if _row_value(p, "id") == selected_id),
        None,
    )

    if not selected:
        return

    st.success("✅ KPPM telah meluluskan dan menandatangani keputusan ini.")

    tab_pdf, tab_dispatch = st.tabs([
        "📄 Dokumen Ditandatangani",
        "📤 Penghantaran",
    ])

    with tab_pdf:
        st.subheader("📄 Arahan Penempatan Ditandatangani KPPM")

        final_pdf = generate_placement_order_pdf(
            placement=selected,
            profile=selected,
            vacancy=selected,
            signed_by=_row_value(
                selected,
                "kppm_signed_by",
                "KPPM",
            ),
            signed_at=_row_value(
                selected,
                "kppm_signed_at",
                "",
            ),
        )

        st.download_button(
            "📄 Lihat / Muat Turun Arahan Penempatan Ditandatangani",
            data=final_pdf,
            file_name=(
                f"Arahan_Penempatan_FINAL_"
                f"{_row_value(selected, 'name', 'Calon').replace(' ', '_')}.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            key=f"bpsm_final_pdf_{selected_id}",
        )

    with tab_dispatch:
        st.subheader("📤 Hantar kepada Pengarah")

        c1, c2 = st.columns(2)
        c1.write(
            f"**Pengarah Bahagian Asal:** "
            f"{_row_value(selected, 'current_department', '-')}"
        )
        c2.write(
            f"**Bahagian Baharu:** "
            f"{_row_value(selected, 'target_department', '-')}"
        )

        st.info(
            "Arahan Penempatan yang telah ditandatangani KPPM akan dihantar "
            "kepada Pengarah Bahagian Asal dengan salinan kepada Pengarah "
            "Bahagian Baharu."
        )

        if st.button(
            "📤 Hantar kepada Pengarah Bahagian Asal + CC Bahagian Baharu",
            use_container_width=True,
            type="primary",
            key=f"dispatch_directors_{selected_id}",
        ):
            send_kppm_decision_to_directors(
                selected_id,
                _row_value(selected, "target_department", ""),
            )
            st.success(
                "✅ Arahan Penempatan ditandatangani telah dihantar "
                "kepada Pengarah Bahagian Asal dan CC Pengarah Bahagian Baharu."
            )
            st.rerun()


def show():
    st.title("🏛️ BPSM")
    st.caption(
        "Semakan, perakuan dan pengurusan Arahan Penempatan."
    )

    placements = get_placements()

    pending = [
        p for p in placements
        if _row_value(p, "bpsm_status") == "Menunggu Semakan BPSM"
    ]
    recommended = [
        p for p in placements
        if _row_value(p, "bpsm_status") == "Diperakukan BPSM"
    ]
    returned = [
        p for p in placements
        if _row_value(p, "bpsm_status") == "Dipulangkan ke Bahagian"
    ]

    c1, c2, c3 = st.columns(3)
    c1.metric("⏳ Menunggu Semakan", len(pending))
    c2.metric("✅ Diperakukan", len(recommended))
    c3.metric("↩️ Dipulangkan", len(returned))

    tab_review, tab_post, tab_history = st.tabs([
        "📥 Semakan BPSM",
        "📜 Selepas KPPM",
        "📚 Rekod",
    ])

    with tab_review:
        if not pending:
            st.success("Tiada calon menunggu semakan BPSM.")
        else:
            table_rows = []
            for p in pending:
                table_rows.append({
                    "ID": _row_value(p, "id"),
                    "Nama": _row_value(p, "name", "-"),
                    "Jawatan": _row_value(p, "title", "-"),
                    "Bahagian Baharu": _row_value(
                        p, "target_department", "-"
                    ),
                    "Status": _row_value(p, "bpsm_status", "-"),
                })

            st.dataframe(
                pd.DataFrame(table_rows),
                use_container_width=True,
                hide_index=True,
            )

            options = {
                (
                    f"{_row_value(p, 'id')} — "
                    f"{_row_value(p, 'name', 'Calon')} — "
                    f"{_row_value(p, 'title', 'Jawatan')}"
                ): _row_value(p, "id")
                for p in pending
            }

            selected_label = st.selectbox(
                "Pilih calon untuk semakan",
                list(options.keys()),
                key="bpsm_review_selection",
            )

            selected_id = options[selected_label]
            selected = next(
                (p for p in pending if _row_value(p, "id") == selected_id),
                None,
            )

            if selected:
                application = _get_application(selected)
                vacancy = get_vacancy(
                    _row_value(selected, "vacancy_id")
                )

                if application is None:
                    st.error("Rekod permohonan calon tidak dapat ditemui.")
                elif vacancy is None:
                    st.error("Rekod jawatan/kekosongan tidak dapat ditemui.")
                else:
                    _candidate_tabs(
                        selected,
                        application,
                        vacancy,
                    )

    with tab_post:
        _post_kppm_tab()

    with tab_history:
        history = [
            p for p in placements
            if _row_value(p, "bpsm_status") in [
                "Diperakukan BPSM",
                "Dipulangkan ke Bahagian",
                "Tidak Diperakukan BPSM",
            ]
        ]

        if history:
            rows = []
            for p in history:
                rows.append({
                    "Nama": _row_value(p, "name", "-"),
                    "Jawatan": _row_value(p, "title", "-"),
                    "Bahagian Baharu": _row_value(
                        p, "target_department", "-"
                    ),
                    "Status": _row_value(p, "bpsm_status", "-"),
                    "Catatan": _row_value(p, "remarks", ""),
                })
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Belum ada rekod keputusan BPSM.")