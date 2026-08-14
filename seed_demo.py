import sqlite3

from seed_demo import main as seed_base
from database import DB_NAME, add_application

BPG = "Bahagian Pendidikan Guru (BPG)"
BPG_EMAIL = "bpg@moe.gov.my"
RELEASED = "Diluluskan Pengarah Bahagian Asal"

# Demo profiles from seed_demo_DG_only.py.
CROSS_DEPARTMENT_EMAILS = [
    "demo.nur.aina@moe.gov.my",          # Audit Dalam
    "demo.muhammad.hakim@moe.gov.my",    # JPN Selangor
    "demo.siti.hajar@moe.gov.my",        # JPN Negeri Sembilan
    "demo.farhan.ismail@moe.gov.my",     # BPPDP
    "demo.nur.syafiqah@moe.gov.my",      # JPN Selangor
    "demo.amirul.hakim@moe.gov.my",      # JPN Perak
    "demo.nor.izzati@moe.gov.my",        # JPN Melaka
    "demo.daniel.wong@moe.gov.my",       # JPN Pulau Pinang
    "demo.aisyah.rahman@moe.gov.my",     # JPN Sabah
]


def get_bpg_talent_pool_vacancy():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT *
        FROM vacancies
        WHERE created_by=?
          AND vacancy_type='TALENT_POOL'
        ORDER BY id DESC
        LIMIT 1
        """,
        (BPG_EMAIL,),
    ).fetchone()
    conn.close()

    if not row:
        raise RuntimeError(
            "Talent Pool BPG tidak ditemui. Pastikan seed_demo_DG_only.py "
            "berjaya dijalankan."
        )

    return row


def prepare_released_candidates():
    vacancy = get_bpg_talent_pool_vacancy()

    # Remove any previous demo applications for this vacancy only.
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "DELETE FROM applications WHERE vacancy_id=?",
        (vacancy["id"],),
    )
    conn.commit()
    conn.close()

    created = []

    for email in CROSS_DEPARTMENT_EMAILS:
        app_id = add_application(
            vacancy_id=vacancy["id"],
            applicant_email=email,
            score=0,
            status=RELEASED,
        )
        created.append((app_id, email))

    return vacancy, created


def main():
    # 1. Reset/recreate the base DG-only demo.
    seed_base()

    # 2. Prepare released cross-Bahagian candidates.
    vacancy, released = prepare_released_candidates()

    print()
    print("======================================================")
    print("✅ DEMO DATA — READY UNTUK TOP 5")
    print("======================================================")
    print(f"🟢 Jawatan Talent Pool : {vacancy['title']}")
    print(f"🏢 Bahagian            : {vacancy['department']}")
    print(f"🆔 Vacancy ID          : {vacancy['id']}")
    print()
    print(f"✔ Calon cross-Bahagian telah dilepaskan: {len(released)}")
    for _, email in released:
        print(f"   - {email}")
    print()
    print("👤 Calon BPG sendiri tidak dimasukkan sebagai")
    print("   permohonan pelepasan kerana berada dalam")
    print("   Bahagian yang sama.")
    print()
    print("Sekarang boleh terus:")
    print("  1. streamlit run app.py")
    print("  2. Login BPG")
    print("  3. Talent Discovery")
    print("  4. Pilih jawatan Talent Pool BPG")
    print("  5. Jalankan / buka bahagian AI Recommendation Top 5")
    print("  6. Tekan 'Jalankan Cortex AI Recommendation Top 5'")
    print()
    print("⚠ Status release demo menggunakan status sedia ada")
    print("  sistem: 'Diluluskan Pengarah Bahagian Asal'.")
    print("  Ini hanya untuk dataset demo; esok kita boleh uji")
    print("  flow pelepasan sebenar end-to-end.")
    print("======================================================")


if __name__ == "__main__":
    main()