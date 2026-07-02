import sqlite3
import pandas as pd

DB_NAME = "mygovtalent.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        role TEXT,
        department TEXT,
        phone TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employee_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        ic TEXT,
        phone TEXT,
        current_department TEXT,
        current_position TEXT,
        grade TEXT,
        home_address TEXT,
        state TEXT,
        district TEXT,
        academic TEXT,
        professional TEXT,
        specialization TEXT,
        experience INTEGER,
        certification TEXT,
        course TEXT,
        language TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vacancies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        department TEXT,
        location TEXT,
        state TEXT,
        district TEXT,
        academic TEXT,
        professional TEXT,
        specialization TEXT,
        experience INTEGER,
        certification TEXT,
        course TEXT,
        language TEXT,
        closing_date TEXT,
        interview_required TEXT,
        status TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vacancy_id INTEGER,
        applicant_email TEXT,
        score REAL DEFAULT 0,
        status TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS open_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_email TEXT,
        status TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS open_applications_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,
        department TEXT,
        priority INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS placements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,
        applicant_email TEXT,
        vacancy_id INTEGER,
        department TEXT,
        department_status TEXT,
        bpsm_status TEXT,
        placement_order TEXT,
        placement_date TEXT,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS otp_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        otp TEXT,
        verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS interviews(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    application_id INTEGER,

    interview_date TEXT,

    interview_time TEXT,

    interview_location TEXT,

    interview_panel TEXT,

    result TEXT,

    remarks TEXT
    )
    """)

    conn.commit()
    conn.close()


def seed_users():
    users = [
        ("pemohon@moe.gov.my", "Pemohon Demo", "Applicant", "", "", "Active"),
        ("bahagian@moe.gov.my", "Pegawai Bahagian Baru", "Department", "Bahagian Baru", "", "Active"),
        ("bpsm@moe.gov.my", "Admin BPSM Demo", "BPSM", "BPSM", "", "Active"),
        ("pengarah@moe.gov.my","Pengarah Bahagian Asal","Director","Bahagian Pengurusan Sumber Manusia","","Active"),
    ]

    conn = get_connection()
    cur = conn.cursor()

    cur.executemany("""
    INSERT OR IGNORE INTO users (
        email, name, role, department, phone, status
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, users)

    conn.commit()
    conn.close()


def get_user(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    conn.close()
    return user


def save_otp(email, otp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO otp_logs (email, otp) VALUES (?, ?)",
        (email, otp)
    )
    conn.commit()
    conn.close()


def verify_saved_otp(email, otp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT *
    FROM otp_logs
    WHERE email=? AND otp=?
    ORDER BY id DESC
    LIMIT 1
    """, (email, otp))
    data = cur.fetchone()

    if data:
        cur.execute(
            "UPDATE otp_logs SET verified=1 WHERE id=?",
            (data["id"],)
        )
        conn.commit()

    conn.close()
    return data is not None


def import_master_data(file_path):
    conn = get_connection()

    sheets = {
        "Organizations": "organizations",
        "Grades": "grades",
        "Academic": "academic",
        "Professional": "professional",
        "Specialization": "specialization",
        "Certification": "certification",
        "Course": "course",
        "Language": "language",
        "States": "states",
        "Districts": "districts",
    }

    for sheet, table in sheets.items():
        df = pd.read_excel(file_path, sheet_name=sheet)
        df.to_sql(table, conn, if_exists="replace", index=False)

    conn.close()


def get_dropdown(table, column):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY "{column}"')
        data = [row[0] for row in cur.fetchall() if row[0] is not None]
    except Exception:
        data = []

    conn.close()
    return data


def get_organizations():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
        SELECT name
        FROM organizations
        WHERE status='Active'
        ORDER BY name
        """)
        data = [row[0] for row in cur.fetchall()]
    except Exception:
        data = []

    conn.close()
    return data


def save_profile(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO employee_profiles (
        email,
        name,
        ic,
        phone,
        current_department,
        current_position,
        grade,
        home_address,
        state,
        district,
        academic,
        professional,
        specialization,
        experience,
        certification,
        course,
        language
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()


def get_profile(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employee_profiles WHERE email=?", (email,))
    data = cur.fetchone()
    conn.close()
    return data


def add_vacancy(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO vacancies (
        title,
        department,
        location,
        state,
        district,
        academic,
        professional,
        specialization,
        experience,
        certification,
        course,
        language,
        closing_date,
        interview_required,
        status,
        created_by
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()


def get_all_vacancies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vacancies ORDER BY created_at DESC")
    data = cur.fetchall()
    conn.close()
    return data


def get_active_vacancies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT *
    FROM vacancies
    WHERE status='Active'
    ORDER BY closing_date
    """)
    data = cur.fetchall()
    conn.close()
    return data


def get_vacancy(vacancy_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vacancies WHERE id=?", (vacancy_id,))
    data = cur.fetchone()
    conn.close()
    return data


def add_application(vacancy_id, applicant_email, score=0, status="Menunggu Kelulusan Pengarah"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO applications (
        vacancy_id,
        applicant_email,
        score,
        status
    )
    VALUES (?, ?, ?, ?)
    """, (vacancy_id, applicant_email, score, status))

    conn.commit()
    conn.close()


def get_my_applications(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        a.id,
        a.vacancy_id,
        v.title,
        v.department,
        a.score,
        a.status,
        a.submitted_at
    FROM applications a
    LEFT JOIN vacancies v ON a.vacancy_id = v.id
    WHERE a.applicant_email=?
    ORDER BY a.submitted_at DESC
    """, (email,))

    data = cur.fetchall()
    conn.close()
    return data


def get_applications_by_vacancy(vacancy_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        a.id,
        a.vacancy_id,
        a.applicant_email,
        a.score,
        a.status,
        a.submitted_at,
        p.name,
        p.current_department,
        p.current_position,
        p.grade,
        p.academic,
        p.professional,
        p.specialization,
        p.experience,
        p.certification,
        p.course,
        p.state,
        p.district
    FROM applications a
    LEFT JOIN employee_profiles p ON a.applicant_email = p.email
    WHERE a.vacancy_id=?
    ORDER BY a.score DESC
    """, (vacancy_id,))

    data = cur.fetchall()
    conn.close()
    return data


def update_application_score(application_id, score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE applications SET score=? WHERE id=?",
        (score, application_id)
    )
    conn.commit()
    conn.close()


def update_application_status(application_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE applications SET status=? WHERE id=?",
        (status, application_id)
    )
    conn.commit()
    conn.close()


def add_open_application(email, status="Menunggu Kekosongan"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO open_applications (
        applicant_email,
        status
    )
    VALUES (?, ?)
    """, (email, status))

    app_id = cur.lastrowid

    conn.commit()
    conn.close()
    return app_id


def add_open_application_preference(application_id, department, priority):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO open_applications_preferences (
        application_id,
        department,
        priority
    )
    VALUES (?, ?, ?)
    """, (application_id, department, priority))

    conn.commit()
    conn.close()


def get_my_open_application(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM open_applications
    WHERE applicant_email=?
    ORDER BY submitted_at DESC
    LIMIT 1
    """, (email,))

    data = cur.fetchone()
    conn.close()
    return data


def get_open_preferences(application_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM open_applications_preferences
    WHERE application_id=?
    ORDER BY priority
    """, (application_id,))

    data = cur.fetchall()
    conn.close()
    return data


def send_to_bpsm(application_id, applicant_email, vacancy_id, department, remarks=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO placements (
        application_id,
        applicant_email,
        vacancy_id,
        department,
        department_status,
        bpsm_status,
        placement_order,
        placement_date,
        remarks
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        application_id,
        applicant_email,
        vacancy_id,
        department,
        "Diperakukan Bahagian",
        "Menunggu Semakan BPSM",
        "",
        "",
        remarks
    ))

    cur.execute(
        "UPDATE applications SET status=? WHERE id=?",
        ("Dihantar ke BPSM", application_id)
    )

    conn.commit()
    conn.close()


def get_placements():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM placements
    ORDER BY created_at DESC
    """)

    data = cur.fetchall()
    conn.close()
    return data


def update_bpsm_status(placement_id, status, order_no="", placement_date="", remarks=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE placements
    SET
        bpsm_status=?,
        placement_order=?,
        placement_date=?,
        remarks=?
    WHERE id=?
    """, (status, order_no, placement_date, remarks, placement_id))

    conn.commit()
    conn.close()

def add_interview(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO interviews(

        application_id,
        interview_date,
        interview_time,
        interview_location,
        interview_panel,
        result,
        remarks

    )

    VALUES(?,?,?,?,?,?,?)

    """, data)

    conn.commit()
    conn.close()

def get_interview(application_id):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""

    SELECT *

    FROM interviews

    WHERE application_id=?

    """,(application_id,))

    data = cur.fetchone()

    conn.close()

    return data

def update_interview_result(application_id,result,remarks):

    conn=get_connection()

    cur=conn.cursor()

    cur.execute("""

    UPDATE interviews

    SET

    result=?,
    remarks=?

    WHERE application_id=?

    """,(result,remarks,application_id))

    conn.commit()

    conn.close()

def import_applicants_excel(file_path):
    df = pd.read_excel(file_path)

    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        email = str(row.get("email", "")).strip()

        if email == "":
            continue

        cur.execute("""
        INSERT OR IGNORE INTO users (
            email, name, role, department, phone, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            email,
            row.get("name", ""),
            "Applicant",
            row.get("current_department", ""),
            row.get("phone", ""),
            "Active"
        ))

        cur.execute("""
        INSERT OR REPLACE INTO employee_profiles (
            email,
            name,
            ic,
            phone,
            current_department,
            current_position,
            grade,
            home_address,
            state,
            district,
            academic,
            professional,
            specialization,
            experience,
            certification,
            course,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email,
            row.get("name", ""),
            row.get("ic", ""),
            row.get("phone", ""),
            row.get("current_department", ""),
            row.get("current_position", ""),
            row.get("grade", ""),
            row.get("home_address", ""),
            row.get("state", ""),
            row.get("district", ""),
            row.get("academic", ""),
            row.get("professional", ""),
            row.get("specialization", ""),
            int(row.get("experience", 0)),
            row.get("certification", ""),
            row.get("course", ""),
            row.get("language", "")
        ))

    conn.commit()
    conn.close()


def import_vacancies_excel(file_path, created_by="system"):
    df = pd.read_excel(file_path)

    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
        INSERT INTO vacancies (
            title,
            department,
            location,
            state,
            district,
            academic,
            professional,
            specialization,
            experience,
            certification,
            course,
            language,
            closing_date,
            interview_required,
            status,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("title", ""),
            row.get("department", ""),
            row.get("location", ""),
            row.get("state", ""),
            row.get("district", ""),
            row.get("academic", ""),
            row.get("professional", ""),
            row.get("specialization", ""),
            int(row.get("experience", 0)),
            row.get("certification", ""),
            row.get("course", ""),
            row.get("language", ""),
            str(row.get("closing_date", "")),
            row.get("interview_required", "Tidak"),
            row.get("status", "Active"),
            created_by
        ))

    conn.commit()
    conn.close()

def count_profiles():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM employee_profiles")

    total = cur.fetchone()[0]

    conn.close()

    return total


def count_vacancies():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM vacancies")

    total = cur.fetchone()[0]

    conn.close()

    return total

def auto_generate_dummy_applications(limit_per_applicant=2):
    import random

    conn = get_connection()
    cur = conn.cursor()

    profiles = cur.execute("""
        SELECT email, academic, specialization, experience, certification, course
        FROM employee_profiles
        WHERE email LIKE 'pemohon%'
    """).fetchall()

    vacancies = cur.execute("""
        SELECT id
        FROM vacancies
        WHERE status='Active'
    """).fetchall()

    if not profiles or not vacancies:
        conn.close()
        return 0

    total_created = 0

    for profile in profiles:
        selected_vacancies = random.sample(
            vacancies,
            min(limit_per_applicant, len(vacancies))
        )

        for vacancy in selected_vacancies:
            existing = cur.execute("""
                SELECT id
                FROM applications
                WHERE applicant_email=? AND vacancy_id=?
            """, (profile["email"], vacancy["id"])).fetchone()

            if existing:
                continue

            score = random.randint(60, 98)

            cur.execute("""
                INSERT INTO applications (
                    vacancy_id,
                    applicant_email,
                    score,
                    status
                )
                VALUES (?, ?, ?, ?)
            """, (
                vacancy["id"],
                profile["email"],
                score,
                "Menunggu Kelulusan Pengarah Bahagian Asal"
            ))

            total_created += 1

    conn.commit()
    conn.close()

    return total_created

if __name__ == "__main__":
    create_tables()
    seed_users()

    print("===================================")
    print(" MyGovTalent AI Database v2 Ready")
    print("===================================")