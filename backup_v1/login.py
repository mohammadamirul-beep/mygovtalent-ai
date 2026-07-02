import streamlit as st
from utils.otp import generate_otp, verify_otp

# ===========================
# LOGIN PAGE
# ===========================

def login():

    st.title("🧠 MyGovTalent AI")

    st.caption("Kementerian Pendidikan Malaysia")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "otp" not in st.session_state:
        st.session_state.otp = ""

    if "email" not in st.session_state:
        st.session_state.email = ""

    if "role" not in st.session_state:
        st.session_state.role = ""

    if st.session_state.logged_in:
        return True

    email = st.text_input(
        "Email Rasmi KPM (@moe.gov.my)"
    )

    role = st.selectbox(
        "Login Sebagai",
        [
            "Applicant",
            "Department",
            "BPSM"
        ]
    )

    if st.button("Hantar OTP"):

        if not email.endswith("@moe.gov.my"):

            st.error("Gunakan emel rasmi KPM.")

        else:

            otp = generate_otp()

            st.session_state.otp = otp
            st.session_state.email = email
            st.session_state.role = role

            # Simulasi OTP
            st.success(f"OTP Simulasi: {otp}")

    if st.session_state.otp != "":

        input_otp = st.text_input(
            "Masukkan OTP"
        )

        if st.button("Login"):

            if verify_otp(
                input_otp,
                st.session_state.otp
            ):

                st.session_state.logged_in = True

                st.success("Login Berjaya")

                st.rerun()

            else:

                st.error("OTP tidak sah.")

    return st.session_state.logged_in