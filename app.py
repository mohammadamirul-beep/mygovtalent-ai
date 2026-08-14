import streamlit as st

from database import create_tables, seed_users
from login import login, logout
from pages import applicant, bpsm, department, director, kppm

st.set_page_config(
    page_title="MyGovTalent AI",
    page_icon="🧠",
    layout="wide",
)

create_tables()
seed_users()

if login():
    st.sidebar.title("🧠 MyGovTalent AI")
    st.sidebar.success(st.session_state.name)
    st.sidebar.write(f"Email: {st.session_state.email}")
    st.sidebar.write(f"Role: {st.session_state.role}")
    if st.session_state.department:
        st.sidebar.write(f"Organisasi: {st.session_state.department}")
    st.sidebar.divider()

    if st.sidebar.button("Logout", use_container_width=True):
        logout()

    role = st.session_state.role
    if role == "Applicant":
        applicant.show()
    elif role == "Department":
        department.show()
    elif role == "Director":
        director.show()
    elif role == "BPSM":
        bpsm.show()
    elif role == "KPPM":
        kppm.show()
    else:
        st.error("Role pengguna tidak sah.")
