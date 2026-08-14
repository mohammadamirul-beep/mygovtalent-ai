import json
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.placement_order import generate_placement_order_pdf

from database import (
    get_kppm_pending,
    get_kppm_history,
    get_ai_snapshot,
    update_kppm_decision,
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


def _decode(value, default):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _show_profile(row):
    st.subheader("👤 Profil Pegawai")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nama", _row_value(row, "name", "-"))
    c2.metric("Gred", _row_value(row, "grade", "-"))
    c3.metric("Jawatan Semasa", _row_value(row, "current_position", "-"))

    c1, c2 = st.columns(2)
    c1.write(f"**Bahagian Asal:** {_row_value(row, 'current_department', '-')}")
    c2.write(f"**Email:** {_row_value(row, 'applicant_email', '-')}")

    st.divider()
    st.subheader("🎯 Jawatan Diperakukan")

    c1, c2 = st.columns(2)
    c1.write(f"**Jawatan:** {_row_value(row, 'title', '-')}")
    c2.write(
        f"**Bahagian Baharu:** {_row_value(row, 'target_department', '-')}"
    )

    c1, c2 = st.columns(2)
    c1.write(f"**Pengalaman:** {_row_value(row, 'experience', 0)} tahun")
    c2.write(f"**Negeri:** {_row_value(row, 'state', '-')}")

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

    st.dataframe(
        pd.DataFrame([
            {
                "Faktor": label,
                "Profil Pegawai": _row_value(row, key, "-"),
                "Keperluan Jawatan": _row_value(row, key, "-"),
            }
            for label, key in rows
        ]),
        use_container_width=True,
        hide_index=True,
    )


def _show_ai(application_id):
    st.subheader("🤖 AI Matching")

    snapshot = get_ai_snapshot(application_id)

    if not snapshot:
        st.warning("Tiada AI snapshot direkodkan untuk calon ini.")
        return 0

    score = snapshot.get("score", 0)
    recommendation = snapshot.get(
        "recommendation",
        "Tiada cadangan AI direkodkan.",
    )
    explanation = snapshot.get("explanation", "")
    breakdown = snapshot.get("breakdown", {})
    strengths = snapshot.get("strengths", [])
    gaps = snapshot.get("gaps", [])

    c1, c2 = st.columns([1, 2])
    c1.metric("AI Match Score", f"{score}/100")
    c2.info(f"**Cadangan AI:** {recommendation}")

    st.caption(
        "🔒 Snapshot rasmi Cortex AI. KPPM tidak mengira semula skor."
    )

    if breakdown:
        st.subheader("📊 Score Breakdown")
        if isinstance(breakdown, dict):
            for key, value in breakdown.items():
                st.write(
                    f"**{str(key).replace('_', ' ').title()}:** {value}"
                )
        else:
            st.write(breakdown)

    if strengths:
        st.subheader("💪 Kekuatan")
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

    return score


def _candidate_tabs(selected):
    tab_profile, tab_ai, tab_draft, tab_decision = st.tabs([
        "👤 Profil & Keperluan",
        "🤖 AI Matching",
        "📄 Draf Arahan",
        "✍️ Keputusan & Signature",
    ])

    with tab_profile:
        _show_profile(selected)

    with tab_ai:
        score = _show_ai(
            _row_value(selected, "application_id")
        )

    with tab_draft:
        st.subheader("📄 Draf Arahan Penempatan")
        st.caption(
            "Semak draf Arahan Penempatan sebelum membuat keputusan KPPM."
        )

        draft_pdf = generate_placement_order_pdf(
            placement=selected,
            profile=selected,
            vacancy=selected,
        )

        st.download_button(
            "📄 Lihat / Muat Turun Draf Arahan Penempatan",
            data=draft_pdf,
            file_name=(
                f"Arahan_Penempatan_Draf_"
                f"{_row_value(selected, 'name', 'Calon').replace(' ', '_')}.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            key=f"kppm_draft_pdf_{_row_value(selected, 'id')}",
        )

        st.divider()
        st.subheader("📄 Perakuan BPSM")

        remarks = _row_value(selected, "remarks", "")
        if remarks:
            st.info(remarks)
        else:
            st.info("Tiada catatan tambahan direkodkan.")

    with tab_decision:
        selected_id = _row_value(selected, "id")
        st.subheader("⚖️ Keputusan KPPM")

        decision_remarks = st.text_area(
            "Ulasan / keputusan KPPM",
            key=f"kppm_remarks_{selected_id}",
            placeholder="Masukkan ulasan keputusan KPPM...",
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "↩️ Pulangkan kepada BPSM",
                use_container_width=True,
                key=f"kppm_return_{selected_id}",
            ):
                update_kppm_decision(
                    selected_id,
                    "Dipulangkan ke BPSM",
                    remarks=decision_remarks,
                )
                st.warning("Perakuan dipulangkan kepada BPSM.")
                st.rerun()

        with c2:
            if st.button(
                "✅ Bersetuju — Teruskan Tandatangan",
                use_container_width=True,
                type="primary",
                key=f"kppm_approve_{selected_id}",
            ):
                st.session_state[f"kppm_sign_{selected_id}"] = True

        if st.session_state.get(f"kppm_sign_{selected_id}", False):
            st.divider()
            st.subheader("✍️ Digital Signature KPPM")
            st.info(
                "Demo: tandatangan digital ini merekodkan nama, tarikh "
                "dan masa kelulusan KPPM."
            )

            signer = st.text_input(
                "Nama KPPM",
                value="Ketua Pengarah KPPM",
                key=f"kppm_signer_{selected_id}",
            )

            agree = st.checkbox(
                "Saya mengesahkan keputusan ini dan bersetuju menandatangani secara digital.",
                key=f"kppm_agree_{selected_id}",
            )

            if st.button(
                "🔐 Tandatangan & Luluskan",
                use_container_width=True,
                type="primary",
                key=f"kppm_sign_confirm_{selected_id}",
            ):
                if not agree:
                    st.error(
                        "Sila sahkan persetujuan sebelum menandatangani."
                    )
                elif not signer.strip():
                    st.error("Nama KPPM diperlukan.")
                else:
                    signed_at = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    update_kppm_decision(
                        selected_id,
                        "Diluluskan KPPM",
                        remarks=decision_remarks,
                        signed_by=signer.strip(),
                        signed_at=signed_at,
                    )

                    final_pdf = generate_placement_order_pdf(
                        placement=selected,
                        profile=selected,
                        vacancy=selected,
                        signed_by=signer.strip(),
                        signed_at=signed_at,
                    )

                    # Save the generated PDF bytes in session state so it
                    # can be downloaded immediately after signing without
                    # relying on the next rerun's selected row.
                    st.session_state[
                        f"kppm_final_pdf_{selected_id}"
                    ] = final_pdf
                    st.session_state[
                        f"kppm_final_pdf_name_{selected_id}"
                    ] = (
                        f"Arahan_Penempatan_FINAL_"
                        f"{_row_value(selected, 'name', 'Calon').replace(' ', '_')}.pdf"
                    )

                    st.session_state.pop(
                        f"kppm_sign_{selected_id}",
                        None,
                    )

                    st.success(
                        f"✅ Keputusan KPPM diluluskan dan ditandatangani. "
                        f"AI Match Score kekal {score}/100."
                    )

        final_pdf = st.session_state.get(
            f"kppm_final_pdf_{selected_id}"
        )
        if final_pdf:
            st.divider()
            st.subheader("📄 Arahan Penempatan Ditandatangani")
            st.download_button(
                "📄 Lihat / Muat Turun Arahan Penempatan Ditandatangani KPPM",
                data=final_pdf,
                file_name=st.session_state.get(
                    f"kppm_final_pdf_name_{selected_id}",
                    "Arahan_Penempatan_FINAL.pdf",
                ),
                mime="application/pdf",
                use_container_width=True,
                key=f"kppm_final_download_{selected_id}",
            )


def show():
    st.title("🏛️ KPPM")
    st.caption(
        "Semakan perakuan BPSM, draf Arahan Penempatan dan "
        "kelulusan dengan tandatangan digital."
    )

    pending = get_kppm_pending()
    history = get_kppm_history()

    c1, c2 = st.columns(2)
    c1.metric("⏳ Menunggu Keputusan", len(pending))
    c2.metric("📚 Telah Diproses", len(history))

    tab_inbox, tab_history = st.tabs([
        "📥 Perakuan BPSM",
        "📚 Rekod Keputusan",
    ])

    with tab_inbox:
        if not pending:
            st.success("Tiada perakuan BPSM yang menunggu keputusan KPPM.")
        else:
            rows = []
            for p in pending:
                rows.append({
                    "ID": _row_value(p, "id"),
                    "Nama": _row_value(p, "name", "-"),
                    "Jawatan": _row_value(p, "title", "-"),
                    "Bahagian Baharu": _row_value(
                        p, "target_department", "-"
                    ),
                    "AI Score": _row_value(p, "score", "-"),
                    "Status": _row_value(p, "bpsm_status", "-"),
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
                for p in pending
            }

            label = st.selectbox(
                "Pilih calon untuk semakan",
                list(options.keys()),
                key="kppm_review_selection",
            )

            selected_id = options[label]
            selected = next(
                (p for p in pending if _row_value(p, "id") == selected_id),
                None,
            )

            if selected:
                _candidate_tabs(selected)

    with tab_history:
        if not history:
            st.info("Belum ada keputusan KPPM.")
        else:
            rows = []
            for p in history:
                rows.append({
                    "Nama": _row_value(p, "name", "-"),
                    "Jawatan": _row_value(p, "title", "-"),
                    "Bahagian Baharu": _row_value(
                        p, "target_department", "-"
                    ),
                    "Status KPPM": _row_value(
                        p, "kppm_status", "-"
                    ),
                    "Ditandatangani Oleh": _row_value(
                        p, "kppm_signed_by", "-"
                    ),
                    "Tarikh Tandatangan": _row_value(
                        p, "kppm_signed_at", "-"
                    ),
                    "Catatan": _row_value(
                        p, "kppm_remarks", "-"
                    ),
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )