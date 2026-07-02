import streamlit as st

from master import organizations


def show():

    menu = st.tabs(

        [

            "🏠 Dashboard",

            "🏢 Master Data",

            "📄 Arahan Penempatan",

            "📊 Analytics"

        ]

    )

    # ==========================
    # DASHBOARD
    # ==========================

    with menu[0]:

        st.title("🏛️ Dashboard BPSM")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("📥 Permohonan", 38)
        col2.metric("📄 Arahan Penempatan", 14)
        col3.metric("✅ Selesai", 9)
        col4.metric("⏳ Dalam Proses", 5)

        st.divider()

        st.subheader("Pengurusan")

        st.button(
            "📥 Semakan Perakuan",
            use_container_width=True
        )

        st.button(
            "📄 Arahan Penempatan",
            use_container_width=True
        )

        st.button(
            "📊 Laporan",
            use_container_width=True
        )

    # ==========================
    # MASTER DATA
    # ==========================

    with menu[1]:

        organizations.show()

    # ==========================
    # ARAHAN PENEMPATAN
    # ==========================

    with menu[2]:

        st.header("📄 Arahan Penempatan")

        st.info("Dalam pembangunan")

    # ==========================
    # ANALYTICS
    # ==========================

    with menu[3]:

        st.header("📊 Analytics")

        st.info("Dalam pembangunan")