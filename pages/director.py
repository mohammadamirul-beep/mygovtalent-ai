import streamlit as st
import pandas as pd

from database import (
    get_connection,
    update_application_status
)


def get_pending_applications(department):

    conn = get_connection()

    data = conn.execute("""
        SELECT
            a.id,
            a.applicant_email,
            a.score,
            a.status,
            a.submitted_at,
            v.title,
            v.department AS target_department,
            p.name,
            p.current_department,
            p.current_position,
            p.grade
        FROM applications a
        LEFT JOIN vacancies v ON a.vacancy_id = v.id
        LEFT JOIN employee_profiles p ON a.applicant_email = p.email
        WHERE a.status = 'Menunggu Kelulusan Pengarah Bahagian Asal'
        AND p.current_department = ?
        ORDER BY a.submitted_at DESC
    """, (department,)).fetchall()

    conn.close()

    return data


def get_history(department):

    conn = get_connection()

    data = conn.execute("""
        SELECT
            a.id,
            a.applicant_email,
            a.score,
            a.status,
            a.submitted_at,
            v.title,
            v.department AS target_department,
            p.name,
            p.current_department,
            p.current_position,
            p.grade
        FROM applications a
        LEFT JOIN vacancies v ON a.vacancy_id = v.id
        LEFT JOIN employee_profiles p ON a.applicant_email = p.email
        WHERE a.status IN (
            'Diluluskan Pengarah Bahagian Asal',
            'Ditolak Pengarah Bahagian Asal'
        )
        AND p.current_department = ?
        ORDER BY a.submitted_at DESC
    """, (department,)).fetchall()

    conn.close()

    return data


def show():

    department = st.session_state.department

    tabs = st.tabs(
        [
            "🏠 Dashboard",
            "📥 Kelulusan Permohonan",
            "📜 Sejarah Kelulusan"
        ]
    )

    pending = get_pending_applications(department)
    history = get_history(department)

    with tabs[0]:

        st.title("👔 Dashboard Pengarah Bahagian Asal")

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

    with tabs[1]:

        st.title("📥 Kelulusan Permohonan")

        if len(pending) == 0:

            st.info("Tiada permohonan menunggu kelulusan.")

        else:

            for app in pending:

                with st.container(border=True):

                    st.subheader(app["name"])

                    st.write(f"**Jawatan Semasa:** {app['current_position']}")
                    st.write(f"**Gred:** {app['grade']}")
                    st.write(f"**Bahagian Semasa:** {app['current_department']}")
                    st.write(f"**Jawatan Dimohon:** {app['title']}")
                    st.write(f"**Bahagian Dimohon:** {app['target_department']}")
                    st.write(f"**AI Score:** {app['score']}%")
                    st.write(f"**Status:** {app['status']}")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "✅ Lulus",
                            key=f"approve_{app['id']}",
                            use_container_width=True
                        ):
                            update_application_status(
                                app["id"],
                                "Diluluskan Pengarah Bahagian Asal"
                            )
                            st.success("Permohonan diluluskan.")
                            st.rerun()

                    with col2:
                        if st.button(
                            "❌ Tolak",
                            key=f"reject_{app['id']}",
                            use_container_width=True
                        ):
                            update_application_status(
                                app["id"],
                                "Ditolak Pengarah Bahagian Asal"
                            )
                            st.warning("Permohonan ditolak.")
                            st.rerun()

    with tabs[2]:

        st.title("📜 Sejarah Kelulusan")

        if len(history) == 0:

            st.info("Tiada sejarah kelulusan.")

        else:

            rows = []

            for h in history:
                rows.append(
                    {
                        "ID": h["id"],
                        "Nama": h["name"],
                        "Jawatan Dimohon": h["title"],
                        "Bahagian Dimohon": h["target_department"],
                        "AI Score": h["score"],
                        "Status": h["status"],
                        "Tarikh": h["submitted_at"]
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )