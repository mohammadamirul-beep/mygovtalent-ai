import streamlit as st
import pandas as pd

from master import organizations

from database import (
    get_placements,
    update_bpsm_status,
    import_applicants_excel,
    import_vacancies_excel,
    count_profiles, 
    count_vacancies,
    auto_generate_dummy_applications
)


def show():

    tabs = st.tabs([
        "🏠 Dashboard",
        "🏢 Master Data",
        "📥 Semakan",
        "📄 Arahan Penempatan",
        "📊 Laporan"
    ])

    with tabs[0]:
        st.title("🏛️ Dashboard BPSM")

        placements = get_placements()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("👥 Profil Pegawai", count_profiles())
        col2.metric("📢 Iklan", count_vacancies())
        col3.metric("📄 Arahan Penempatan", 0)
        col4.metric("✅ Selesai", 0)

        st.divider()
        st.info("Dashboard BPSM memaparkan permohonan yang dihantar oleh Bahagian untuk proses arahan penempatan.")

    with tabs[1]:
        st.title("🏢 Master Data")

        organizations.show()

        st.divider()
        st.subheader("📥 Import Data Dummy")

        dummy_applicants = st.file_uploader(
            "Upload Dummy Pemohon Excel",
            type=["xlsx"],
            key="dummy_applicants"
        )

        if dummy_applicants is not None:
            with open("temp_dummy_applicants.xlsx", "wb") as f:
                f.write(dummy_applicants.getbuffer())

            import_applicants_excel("temp_dummy_applicants.xlsx")
            st.success("✅ Dummy pemohon berjaya diimport.")

        dummy_vacancies = st.file_uploader(
            "Upload Dummy Iklan Excel",
            type=["xlsx"],
            key="dummy_vacancies"
        )

        if dummy_vacancies is not None:
            with open("temp_dummy_vacancies.xlsx", "wb") as f:
                f.write(dummy_vacancies.getbuffer())

            import_vacancies_excel(
                "temp_dummy_vacancies.xlsx",
                st.session_state.email
            )

            st.success("✅ Dummy iklan berjaya diimport.")

        st.divider()

        st.subheader("🧪 Generate Dummy Applications")

        if st.button("Generate Dummy Applications", use_container_width=True):

            total = auto_generate_dummy_applications(
                limit_per_applicant=2
            )

            st.success(f"✅ {total} permohonan dummy berjaya dijana.")

    with tabs[2]:
        st.title("📥 Semakan Perakuan Bahagian")

        placements = get_placements()

        if len(placements) == 0:
            st.info("Tiada perakuan diterima daripada Bahagian.")
        else:
            rows = []

            for p in placements:
                rows.append({
                    "ID": p["id"],
                    "Application ID": p["application_id"],
                    "Pemohon": p["applicant_email"],
                    "Bahagian": p["department"],
                    "Status Bahagian": p["department_status"],
                    "Status BPSM": p["bpsm_status"],
                    "Tarikh": p["created_at"]
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

    with tabs[3]:
        st.title("📄 Arahan Penempatan")

        placements = get_placements()

        if len(placements) == 0:
            st.info("Tiada rekod untuk arahan penempatan.")
        else:
            placement_options = {
                f"{p['id']} - {p['applicant_email']}": p["id"]
                for p in placements
            }

            selected = st.selectbox(
                "Pilih Rekod",
                list(placement_options.keys())
            )

            placement_id = placement_options[selected]

            order_no = st.text_input("No. Arahan Penempatan")
            placement_date = st.date_input("Tarikh Arahan")
            remarks = st.text_area("Catatan")

            if st.button("Jana Arahan Penempatan", use_container_width=True):
                update_bpsm_status(
                    placement_id,
                    "Arahan Penempatan Dikeluarkan",
                    order_no,
                    str(placement_date),
                    remarks
                )

                st.success("✅ Arahan penempatan berjaya dikemaskini.")

    with tabs[4]:
        st.title("📊 Laporan BPSM")

        placements = get_placements()

        if len(placements) == 0:
            st.info("Tiada data laporan.")
        else:
            df = pd.DataFrame([
                {
                    "Pemohon": p["applicant_email"],
                    "Bahagian": p["department"],
                    "Status BPSM": p["bpsm_status"],
                    "Tarikh": p["created_at"]
                }
                for p in placements
            ])

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )