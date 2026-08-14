import base64
import io
from pathlib import Path

import pandas as pd
import streamlit as st

from database import (
    get_connection,
    update_application_status,
    get_director_placement_orders,
    director_handover_to_officer,
)


def _fetch_applications(department, statuses):
    conn = get_connection()
    placeholders = ",".join(["?"] * len(statuses))

    data = conn.execute(
        f"""
        SELECT
            a.id,
            a.applicant_email,
            a.status,
            a.submitted_at,
            a.source,
            v.title,
            v.department AS target_department,
            p.name,
            p.current_department,
            p.current_position,
            p.grade
        FROM applications a
        LEFT JOIN vacancies v
            ON a.vacancy_id = v.id
        LEFT JOIN employee_profiles p
            ON a.applicant_email = p.email
        WHERE a.status IN ({placeholders})
          AND p.current_department = ?
        ORDER BY a.submitted_at DESC
        """,
        (*statuses, department),
    ).fetchall()

    conn.close()
    return data


def get_pending_applications(department):
    return _fetch_applications(
        department,
        ["Menunggu Kelulusan Pengarah Bahagian Asal"],
    )


def get_history(department):
    return _fetch_applications(
        department,
        [
            "Diluluskan Pengarah Bahagian Asal",
            "Ditolak Pengarah Bahagian Asal",
        ],
    )




def _placement_pdf_bytes(order):
    """
    Return PDF bytes for the signed placement order.

    If placement_order contains a real PDF path or base64-encoded PDF,
    use that existing document. Otherwise generate a demo copy from the
    signed KPPM metadata already stored with the placement.
    """
    stored = order["placement_order"]

    # Existing PDF file path.
    if stored:
        try:
            candidate = Path(str(stored))
            if candidate.exists() and candidate.is_file():
                data = candidate.read_bytes()
                if data.startswith(b"%PDF"):
                    return data
        except Exception:
            pass

        # Base64-encoded PDF.
        try:
            raw = base64.b64decode(str(stored), validate=True)
            if raw.startswith(b"%PDF"):
                return raw
        except Exception:
            pass

    # Fallback: generate a demo AP from the signed KPPM metadata.
    # This keeps the Director view functional even when the database stores
    # only the placement-order reference/number rather than PDF bytes.
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib import colors

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title="Arahan Penempatan",
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "PlacementTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=14,
            leading=18,
            spaceAfter=8,
        )

        body_style = ParagraphStyle(
            "PlacementBody",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
        )

        story = []

        story.append(
            Paragraph(
                "ARAHAN PENEMPATAN",
                title_style,
            )
        )

        story.append(
            Paragraph(
                "Dokumen penempatan yang telah diluluskan dan "
                "ditandatangani secara digital oleh KPPM.",
                body_style,
            )
        )

        story.append(Spacer(1, 8))

        rows = [
            ["Nama Pegawai", order["name"] or order["applicant_email"]],
            ["Jawatan", order["title"] or "-"],
            ["Bahagian Asal", order["current_department"] or "-"],
            ["Bahagian Baharu", order["target_department"] or "-"],
            ["No. Arahan", order["placement_order"] or "-"],
            ["Tarikh Penempatan", order["placement_date"] or "-"],
            ["KPPM", order["kppm_signed_by"] or "-"],
            ["Tarikh / Masa Tandatangan", order["kppm_signed_at"] or "-"],
        ]

        table = Table(
            rows,
            colWidths=[55 * mm, 105 * mm],
            repeatRows=0,
        )

        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 16))

        story.append(
            Paragraph(
                "<b>STATUS TANDATANGAN DIGITAL</b>",
                body_style,
            )
        )

        story.append(
            Paragraph(
                f"Keputusan: Diluluskan KPPM<br/>"
                f"Ditandatangani oleh: {order['kppm_signed_by'] or '-'}<br/>"
                f"Tarikh / Masa: {order['kppm_signed_at'] or '-'}",
                body_style,
            )
        )

        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "Dokumen ini dipaparkan sebagai salinan Arahan "
                "Penempatan untuk rujukan Pengarah Bahagian.",
                body_style,
            )
        )

        doc.build(story)

        return buffer.getvalue()

    except Exception:
        return None


def _show_pdf_viewer(order):
    pdf_bytes = _placement_pdf_bytes(order)

    if not pdf_bytes:
        st.warning(
            "PDF Arahan Penempatan belum tersedia untuk rekod ini."
        )
        return

    st.success(
        "📄 Salinan Arahan Penempatan telah ditandatangani KPPM."
    )

    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    st.components.v1.html(
        f"""
        <iframe
            src="data:application/pdf;base64,{pdf_b64}"
            width="100%"
            height="700"
            style="border: 1px solid #ddd; border-radius: 8px;"
        ></iframe>
        """,
        height=720,
        scrolling=True,
    )

    st.download_button(
        "⬇️ Muat Turun Arahan Penempatan",
        data=pdf_bytes,
        file_name=f"arahan_penempatan_{order['id']}.pdf",
        mime="application/pdf",
        key=f"download_ap_{order['id']}",
        use_container_width=True,
    )


def _show_placement_orders(department):
    """Role-aware placement inbox using the same Director module."""
    st.title("📥 Arahan Penempatan")

    st.caption(
        "Arahan Penempatan yang telah ditandatangani KPPM dan dihantar "
        "oleh BPSM. Fungsi dipaparkan mengikut kedudukan Pengarah "
        "sebagai Bahagian Asal atau Bahagian Baharu."
    )

    orders = get_director_placement_orders(department)

    if not orders:
        st.info("Tiada Arahan Penempatan untuk bahagian ini.")
        return

    for order in orders:
        is_origin = (
            order["current_department"] == department
        )
        is_destination = (
            order["target_department"] == department
        )

        with st.container(border=True):
            st.subheader(
                order["name"] or order["applicant_email"]
            )

            c1, c2 = st.columns(2)

            with c1:
                st.write(
                    f"**Jawatan:** {order['title'] or '-'}"
                )
                st.write(
                    f"**Bahagian Asal:** "
                    f"{order['current_department'] or '-'}"
                )
                st.write(
                    f"**Bahagian Baharu:** "
                    f"{order['target_department'] or '-'}"
                )

            with c2:
                st.write(
                    f"**KPPM:** "
                    f"{order['kppm_signed_by'] or '-'}"
                )
                st.write(
                    f"**Tarikh Tandatangan:** "
                    f"{order['kppm_signed_at'] or '-'}"
                )
                st.write(
                    f"**Status:** "
                    f"{order['handover_status'] or 'Menunggu tindakan'}"
                )

            if is_origin:
                st.info(
                    "📤 **Peranan Pengarah Bahagian Asal:** "
                    "Arahan ini melibatkan pegawai di bahagian tuan/puan "
                    "yang akan berpindah ke bahagian baharu."
                )

                remarks = st.text_area(
                    "Catatan serahan kepada pegawai",
                    key=f"director_handover_remarks_{order['id']}",
                    placeholder="Catatan jika diperlukan...",
                )

                if order["handover_status"] == "Diserahkan kepada Pegawai":
                    st.success(
                        "✅ Arahan Penempatan telah diserahkan kepada pegawai."
                    )
                elif order["report_status"] == "Lapor Diri Selesai":
                    st.success(
                        "✅ Pegawai telah selesai lapor diri."
                    )
                else:
                    if st.button(
                        "📤 Serah Arahan kepada Pegawai",
                        key=f"handover_{order['id']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        director_handover_to_officer(
                            order["id"],
                            remarks,
                        )
                        st.success(
                            "✅ Arahan Penempatan telah diserahkan kepada pegawai."
                        )
                        st.rerun()

            if is_destination:
                st.info(
                    "📥 **Peranan Pengarah Bahagian Baharu:** "
                    "Arahan ini adalah makluman penempatan pegawai "
                    "ke bahagian tuan/puan. Tiada kelulusan kedua diperlukan."
                )

                st.success(
                    "✅ Pengarah Bahagian Baharu menerima salinan "
                    "Arahan Penempatan."
                )

            if st.button(
                "📄 Lihat Arahan Penempatan",
                key=f"view_ap_{order['id']}",
                use_container_width=True,
            ):
                _show_pdf_viewer(order)

            st.divider()

            st.caption(
                "Dokumen: Arahan Penempatan yang telah ditandatangani KPPM."
            )


def show():
    department = st.session_state.department

    tabs = st.tabs(
        [
            "🏠 Dashboard",
            "📤 Pegawai Keluar",
            "📥 Arahan Penempatan",
            "📜 Sejarah Kelulusan",
        ]
    )

    pending = get_pending_applications(department)
    history = get_history(department)

    # =====================================================
    # DASHBOARD
    # =====================================================

    with tabs[0]:
        st.title("👔 Dashboard Pengarah Bahagian Asal")
        st.caption("Semakan pelepasan pegawai merangkumi permohonan melalui Iklan dan Talent Pool.")

        approved = [
            x for x in history
            if x["status"] == "Diluluskan Pengarah Bahagian Asal"
        ]

        rejected = [
            x for x in history
            if x["status"] == "Ditolak Pengarah Bahagian Asal"
        ]

        c1, c2, c3 = st.columns(3)

        c1.metric("Menunggu Kelulusan", len(pending))
        c2.metric("Diluluskan", len(approved))
        c3.metric("Ditolak", len(rejected))

    # =====================================================
    # KELULUSAN PERMOHONAN
    # =====================================================

    with tabs[1]:
        st.title("📤 Pegawai Keluar")

        st.caption(
            "Pengarah Bahagian Asal membuat keputusan pelepasan awal "
            "permohonan. AI Matching dan shortlist dilaksanakan pada "
            "peringkat Bahagian selepas permohonan diluluskan."
        )

        if not pending:
            st.info("Tiada permohonan menunggu kelulusan.")
        else:
            for app in pending:
                with st.container(border=True):
                    st.subheader(
                        app["name"] or app["applicant_email"]
                    )

                    st.write(f"**Email:** {app['applicant_email']}")
                    st.write(f"**Jawatan Semasa:** {app['current_position']}")
                    st.write(f"**Gred:** {app['grade']}")
                    st.write(f"**Bahagian Semasa:** {app['current_department']}")
                    st.write(f"**Jawatan Dimohon:** {app['title']}")
                    st.write(f"**Bahagian Dimohon:** {app['target_department']}")
                    st.write(
                        "**Jenis Permohonan:** "
                        + (
                            "🟢 Talent Pool"
                            if app["source"] == "TALENT_POOL"
                            else "🟦 Iklan"
                        )
                    )

                    st.divider()

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "✅ Lulus",
                            key=f"approve_{app['id']}",
                            use_container_width=True,
                            type="primary",
                        ):
                            update_application_status(
                                app["id"],
                                "Diluluskan Pengarah Bahagian Asal",
                            )
                            st.success(
                                "Permohonan diluluskan dan "
                                "dilepaskan ke proses Bahagian."
                            )
                            st.rerun()

                    with col2:
                        if st.button(
                            "❌ Tolak",
                            key=f"reject_{app['id']}",
                            use_container_width=True,
                        ):
                            update_application_status(
                                app["id"],
                                "Ditolak Pengarah Bahagian Asal",
                            )
                            st.warning("Permohonan ditolak.")
                            st.rerun()

    # =====================================================
    # ARAHAN PENEMPATAN
    # =====================================================

    with tabs[2]:
        _show_placement_orders(department)

    # =====================================================
    # SEJARAH KELULUSAN
    # =====================================================

    with tabs[3]:
        st.title("📜 Sejarah Kelulusan")

        if not history:
            st.info("Tiada sejarah kelulusan.")
        else:
            rows = []

            for h in history:
                rows.append(
                    {
                        "ID": h["id"],
                        "Nama": h["name"] or h["applicant_email"],
                        "Email": h["applicant_email"],
                        "Jawatan Dimohon": h["title"],
                        "Bahagian Dimohon": h["target_department"],
                        "Jenis Permohonan": (
                            "🟢 Talent Pool"
                            if h["source"] == "TALENT_POOL"
                            else "🟦 Iklan"
                        ),
                        "Status": h["status"],
                        "Tarikh": h["submitted_at"],
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )