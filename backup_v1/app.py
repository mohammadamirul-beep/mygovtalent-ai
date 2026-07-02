import streamlit as st

from database import create_tables
from login import login

from pages import applicant
from pages import department
from pages import bpsm

from master import organizations

st.set_page_config(
    page_title="MyGovTalent AI",
    page_icon="🧠",
    layout="wide"
)

create_tables()

if login():

    st.sidebar.title("🧠 MyGovTalent AI")

    st.sidebar.success(st.session_state.email)

    st.sidebar.write(
        f"Role : {st.session_state.role}"
    )

    st.sidebar.markdown("---")

    if st.sidebar.button("Logout"):

        st.session_state.clear()

        st.rerun()

    role = st.session_state.role

    if role == "Applicant":

        applicant.show()

    elif role == "Department":

        department.show()

    elif role == "BPSM":

        menu = st.sidebar.radio(

        "Menu",

        [

            "Dashboard",

            "Master Data"

        ]

    )

    if menu == "Dashboard":

        bpsm.show()

    elif menu == "Master Data":

        submenu = st.sidebar.selectbox(

            "Reference",

            [

                "Organizations"

            ]

        )

        if submenu == "Organizations":

            organizations.show()