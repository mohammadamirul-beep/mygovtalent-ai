import random
import streamlit as st

from database import get_user, save_otp, verify_saved_otp


def generate_otp():
    return str(random.randint(100000, 999999))


def init_session():
    defaults = {
        "logged_in": False,
        "email": "",
        "role": "",
        "name": "",
        "department": "",
        "otp_sent": False,
        "email_pending": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login():
    init_session()

    if st.session_state.logged_in:
        return True

    st.title("🧠 MyGovTalent AI")
    st.caption("Sistem Padanan Pertukaran dan Penempatan Pegawai KPM")
    st.divider()

    email = st.text_input("Email Rasmi KPM", placeholder="contoh: bpsm@moe.gov.my")

    if st.button("Hantar OTP", use_container_width=True):
        if not email.endswith("@moe.gov.my"):
            st.error("Sila gunakan emel rasmi @moe.gov.my")
        else:
            user = get_user(email)
            if user is None:
                st.error("Emel belum didaftarkan. Guna bpsm@moe.gov.my / bahagian@moe.gov.my / pengarah@moe.gov.my / pemohon@moe.gov.my")
            else:
                otp = generate_otp()
                save_otp(email, otp)
                st.session_state.otp_sent = True
                st.session_state.email_pending = email
                st.success(f"OTP simulasi: {otp}")

    if st.session_state.otp_sent:
        otp_input = st.text_input("Masukkan OTP")
        if st.button("Login", use_container_width=True):
            email_pending = st.session_state.email_pending
            if verify_saved_otp(email_pending, otp_input):
                user = get_user(email_pending)
                st.session_state.logged_in = True
                st.session_state.email = user["email"]
                st.session_state.role = user["role"]
                st.session_state.name = user["name"]
                st.session_state.department = user["department"]
                st.rerun()
            else:
                st.error("OTP tidak sah.")

    return False


def logout():
    st.session_state.clear()
    st.rerun()
