import json
import requests
import streamlit as st


CORTEX_FLOW_URL = st.secrets["CORTEX_FLOW_URL"]
CORTEX_FLOW_API_KEY = st.secrets["CORTEX_FLOW_API_KEY"]


def extract_myportfolio(uploaded_file):
    if uploaded_file is None:
        raise ValueError("Sila pilih fail MyPortfolio terlebih dahulu.")

    if not uploaded_file.name.lower().endswith(".pdf"):
        raise ValueError("MyPortfolio mesti dalam format PDF.")

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }

    headers = {
        "x-api-key": CORTEX_FLOW_API_KEY
    }

    try:
        response = requests.post(
            CORTEX_FLOW_URL,
            headers=headers,
            files=files,
            timeout=120,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Gagal menghubungi Cortex Flow: {exc}"
        ) from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Cortex Flow gagal. HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        )

    try:
        response_data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Response Cortex bukan JSON yang sah: "
            f"{response.text[:500]}"
        ) from exc

    result = response_data.get("result")

    if result is None:
        raise RuntimeError(
            "Cortex Flow tidak memulangkan field 'result'."
        )

    # -------------------------------------------------
    # Cortex response:
    #
    # {
    #     "result": {
    #         "result": "{ ...JSON... }"
    #     }
    # }
    #
    # Unwrap sehingga mendapat JSON MyPortfolio sebenar.
    # -------------------------------------------------

    if isinstance(result, dict):
        result = result.get("result")

    if result is None:
        raise RuntimeError(
            "Response Cortex mempunyai struktur result yang tidak dijangka."
        )

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Result Cortex bukan JSON yang sah: {exc}"
            ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(
            "Result MyPortfolio daripada Cortex mesti berupa JSON object."
        )

    # Pastikan data yang kita terima memang schema MyPortfolio.
    expected_fields = {
        "jawatan",
        "bahagian",
        "tujuan",
        "fungsi",
        "kompetensi",
        "akademik",
        "ikhtisas",
        "pengalaman",
        "kemahiran",
        "pensijilan",
        "bahasa",
        "ai_ringkasan_bidang",
        "ai_sub_bidang",
    }

    if not expected_fields.intersection(result.keys()):
        raise RuntimeError(
            "Cortex tidak memulangkan field MyPortfolio yang dijangka."
        )

    return result