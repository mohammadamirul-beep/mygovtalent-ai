import random
import sqlite3
import json
from pathlib import Path

import pandas as pd

DB_NAME = "mygovtalent.db"


# =====================================================
# CONNECTION
# =====================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cur, table, column, column_type="TEXT"):
    """Add a column to an existing SQLite table if it does not exist."""
    existing = {row[1] for row in cur.execute(f'PRAGMA table_info("{table}")').fetchall()}
    if column not in existing:
        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {column_type}')


def migrate_database():
    """Safely migrate existing databases without deleting mygovtalent.db."""
    conn = get_connection()
    cur = conn.cursor()
    _ensure_column(cur, "employee_profiles", "competencies")
    _ensure_column(cur, "employee_profiles", "skills")
    _ensure_column(cur, "vacancies", "competencies")
    _ensure_column(cur, "vacancies", "skills")
    _ensure_column(cur, "vacancies", "myportfolio_filename")
    _ensure_column(cur, "vacancies", "myportfolio_json")
    _ensure_column(cur, "vacancies", "ai_ringkasan_bidang")
    _ensure_column(cur, "vacancies", "ai_sub_bidang")
    _ensure_column(cur, "vacancies", "myportfolio_verified", "INTEGER DEFAULT 0")
    _ensure_column(cur, "vacancies", "vacancy_type", "TEXT DEFAULT 'ADVERTISEMENT'")
    _ensure_column(cur, "applications", "source", "TEXT DEFAULT 'IKLAN'")
    _ensure_column(cur, "applications", "ai_explanation")
    _ensure_column(cur, "applications", "ai_breakdown")
    _ensure_column(cur, "applications", "ai_strengths")
    _ensure_column(cur, "applications", "ai_gaps")
    _ensure_column(cur, "applications", "ai_recommendation")
    _ensure_column(cur, "applications", "ai_updated_at")
    cur.execute("""
        UPDATE vacancies
        SET vacancy_type='TALENT_POOL'
        WHERE myportfolio_verified=1
          AND (vacancy_type IS NULL OR vacancy_type='')
    """)
    cur.execute("""
        UPDATE vacancies
        SET vacancy_type='ADVERTISEMENT'
        WHERE vacancy_type IS NULL OR vacancy_type=''
    """)
    cur.execute("""
        UPDATE applications
        SET source=(
            SELECT CASE
                WHEN v.vacancy_type='TALENT_POOL' THEN 'TALENT_POOL'
                ELSE 'IKLAN'
            END
            FROM vacancies v
            WHERE v.id=applications.vacancy_id
        )
        WHERE source IS NULL OR source=''
    """)
    conn.commit()
    conn.close()


# =====================================================
# TABLES
# =====================================================

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
        competencies TEXT,
        skills TEXT,
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
        competencies TEXT,
        skills TEXT,
        myportfolio_filename TEXT,
        myportfolio_json TEXT,
        ai_ringkasan_bidang TEXT,
        ai_sub_bidang TEXT,
        myportfolio_verified INTEGER DEFAULT 0,
        vacancy_type TEXT DEFAULT 'ADVERTISEMENT',
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
        ai_explanation TEXT,
        ai_breakdown TEXT,
        ai_strengths TEXT,
        ai_gaps TEXT,
        ai_recommendation TEXT,
        ai_updated_at TIMESTAMP,
        source TEXT DEFAULT 'IKLAN',
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
    CREATE TABLE IF NOT EXISTS talent_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vacancy_id INTEGER NOT NULL,
        applicant_email TEXT NOT NULL,
        score REAL DEFAULT 0,
        explanation TEXT,
        recommendation TEXT,
        status TEXT DEFAULT 'Dicadangkan',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(vacancy_id, applicant_email)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS talent_pool_profiles (
        email TEXT PRIMARY KEY,
        work_scope TEXT DEFAULT '',
        states TEXT DEFAULT '',
        districts TEXT DEFAULT '',
        status TEXT DEFAULT 'INACTIVE',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,
        interview_date TEXT,
        interview_time TEXT,
        interview_location TEXT,
        interview_panel TEXT,
        result TEXT,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        kppm_status TEXT,
        kppm_remarks TEXT,
        kppm_signed_by TEXT,
        kppm_signed_at TEXT,
        director_origin_status TEXT,
        director_new_cc TEXT,
        handover_status TEXT,
        report_status TEXT,
        final_remarks TEXT,
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

    conn.commit()
    conn.close()
    migrate_database()
    migrate_kppm_columns()



def migrate_kppm_columns():
    """Add KPPM workflow columns to existing placements table."""
    conn = get_connection()
    cur = conn.cursor()
    columns = {
        "kppm_status": "TEXT",
        "kppm_remarks": "TEXT",
        "kppm_signed_by": "TEXT",
        "kppm_signed_at": "TEXT",
        "director_origin_status": "TEXT",
        "director_new_cc": "TEXT",
        "handover_status": "TEXT",
        "report_status": "TEXT",
        "final_remarks": "TEXT",
        "director_received_at": "TEXT",
    }
    existing = {
        row["name"]
        for row in cur.execute("PRAGMA table_info(placements)").fetchall()
    }
    for name, col_type in columns.items():
        if name not in existing:
            cur.execute(f"ALTER TABLE placements ADD COLUMN {name} {col_type}")
    conn.commit()
    conn.close()


# =====================================================
# SEED USERS / LOGIN
# =====================================================

def seed_users():
    users = [
        ("pemohon@moe.gov.my", "Pemohon Demo", "Applicant", "", "", "Active"),
        ("bpg@moe.gov.my", "Pegawai Bahagian Pendidikan Guru", "Department", "Bahagian Pendidikan Guru (BPG)", "", "Active"),
        ("pengarah.bpg@moe.gov.my", "Pengarah Bahagian Pendidikan Guru", "Director", "Bahagian Pendidikan Guru (BPG)", "", "Active"),
        ("audit@moe.gov.my", "Pegawai Bahagian Audit Dalam", "Department", "Bahagian Audit Dalam", "", "Active"),
        ("pengarah.audit@moe.gov.my", "Pengarah Bahagian Audit Dalam", "Director", "Bahagian Audit Dalam", "", "Active"),
        ("bahagian@moe.gov.my", "Pegawai Bahagian Demo", "Department", "Bahagian Pengurusan Sumber Manusia", "", "Active"),
        ("pengarah@moe.gov.my", "Pengarah Bahagian Demo", "Director", "Bahagian Pengurusan Sumber Manusia", "", "Active"),
        ("bpsm@moe.gov.my", "Admin BPSM Demo", "BPSM", "BPSM", "", "Active"),
        ("kppm@moe.gov.my", "KPPM Demo", "KPPM", "KPPM", "", "Active"),
    ]

    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
    INSERT OR IGNORE INTO users (email, name, role, department, phone, status)
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
    cur.execute("INSERT INTO otp_logs (email, otp) VALUES (?, ?)", (email, otp))
    conn.commit()
    conn.close()


def verify_saved_otp(email, otp):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM otp_logs
    WHERE email=? AND otp=?
    ORDER BY id DESC
    LIMIT 1
    """, (email, otp))
    data = cur.fetchone()
    if data:
        cur.execute("UPDATE otp_logs SET verified=1 WHERE id=?", (data["id"],))
        conn.commit()
    conn.close()
    return data is not None


# =====================================================
# MASTER DATA
# =====================================================

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
        data = [row[0] for row in cur.fetchall() if row[0] not in (None, "")]
    except Exception:
        data = []
    conn.close()
    return data


def get_districts_by_states(states):
    """Return districts belonging to any selected state."""
    results = []
    seen = set()
    for state in states or []:
        for district in get_districts_by_state(state):
            if district not in seen:
                seen.add(district)
                results.append(district)
    return sorted(results)


def get_talent_pool_work_scopes():
    """Return unique AI sub-scopes from active Talent Pool vacancies."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ai_sub_bidang
            FROM vacancies
            WHERE status='Active'
              AND vacancy_type='TALENT_POOL'
              AND ai_sub_bidang IS NOT NULL
              AND TRIM(ai_sub_bidang) <> ''
        """)
        rows = cur.fetchall()
    except Exception:
        rows = []
    conn.close()

    result = []
    seen = set()
    for row in rows:
        raw = row[0]
        try:
            parsed = json.loads(raw)
            items = parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            items = [x.strip() for x in str(raw).split(",") if x.strip()]

        for item in items:
            item = str(item).strip()
            if item and item.casefold() not in seen:
                seen.add(item.casefold())
                result.append(item)

    return sorted(result)


def get_organizations():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        SELECT name FROM organizations
        WHERE status='Active'
        ORDER BY name
        """)
        data = [row[0] for row in cur.fetchall() if row[0]]
    except Exception:
        data = []
    conn.close()
    return data


# =====================================================
# COUNTS
# =====================================================

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


def count_applications():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applications")
    total = cur.fetchone()[0]
    conn.close()
    return total


# =====================================================
# PROFILE
# =====================================================

def save_profile(data):
    conn = get_connection()
    cur = conn.cursor()

    # Current Applicant form supplies 17 values.
    # employee_profiles has 19 columns; competencies and skills are optional
    # for the current form and default to empty strings.
    data = list(data)

    if len(data) == 17:
        data.extend(["", ""])

    if len(data) != 19:
        conn.close()
        raise ValueError(
            f"save_profile memerlukan 19 nilai, tetapi menerima {len(data)}."
        )

    cur.execute("""
    INSERT OR REPLACE INTO employee_profiles (
        email, name, ic, phone, current_department, current_position, grade,
        home_address, state, district, academic, professional, specialization,
        experience, certification, course, language, competencies, skills
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def get_all_employee_profiles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM employee_profiles
        WHERE email IS NOT NULL
          AND TRIM(email) <> ''
        ORDER BY name
    """)
    data = cur.fetchall()
    conn.close()
    return data


def save_talent_match(
    vacancy_id,
    applicant_email,
    score,
    explanation="",
    recommendation="",
    status="Dicadangkan",
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO talent_matches (
            vacancy_id, applicant_email, score,
            explanation, recommendation, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(vacancy_id, applicant_email)
        DO UPDATE SET
            score=excluded.score,
            explanation=excluded.explanation,
            recommendation=excluded.recommendation,
            status=excluded.status,
            created_at=CURRENT_TIMESTAMP
    """, (
        vacancy_id,
        applicant_email,
        score,
        explanation,
        recommendation,
        status,
    ))
    row = cur.execute("""
        SELECT id FROM talent_matches
        WHERE vacancy_id=? AND applicant_email=?
    """, (vacancy_id, applicant_email)).fetchone()
    conn.commit()
    conn.close()
    return row["id"] if row else None


def get_talent_matches_by_vacancy(vacancy_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            tm.*,
            ep.name,
            ep.current_position,
            ep.current_department,
            ep.grade,
            ep.state,
            ep.district
        FROM talent_matches tm
        LEFT JOIN employee_profiles ep
            ON ep.email = tm.applicant_email
        WHERE tm.vacancy_id=?
        ORDER BY tm.score DESC, tm.created_at DESC
    """, (vacancy_id,))
    data = cur.fetchall()
    conn.close()
    return data


def get_talent_alerts(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            tm.*,
            v.title,
            v.department,
            v.state,
            v.district,
            v.ai_ringkasan_bidang,
            v.ai_sub_bidang
        FROM talent_matches tm
        LEFT JOIN vacancies v
            ON v.id = tm.vacancy_id
        WHERE tm.applicant_email=?
          AND tm.status IN ('Talent Alert Dihantar', 'Dilihat')
        ORDER BY tm.created_at DESC
    """, (email,))
    data = cur.fetchall()
    conn.close()
    return data


def update_talent_match_status(match_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE talent_matches SET status=? WHERE id=?",
        (status, match_id),
    )
    conn.commit()
    conn.close()


def get_active_talent_pool_candidates():
    """Return employee profiles whose Talent Pool membership is ACTIVE."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            ep.*,
            tp.work_scope AS talent_work_scope,
            tp.states AS talent_states,
            tp.districts AS talent_districts,
            tp.status AS talent_pool_status
        FROM employee_profiles ep
        INNER JOIN talent_pool_profiles tp
            ON LOWER(TRIM(tp.email)) = LOWER(TRIM(ep.email))
        WHERE tp.status='ACTIVE'
          AND ep.email IS NOT NULL
          AND TRIM(ep.email) <> ''
        ORDER BY ep.name
    """)
    data = cur.fetchall()
    conn.close()
    return data


def get_talent_pool_profile(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM talent_pool_profiles
        WHERE email=?
    """, (email,))
    row = cur.fetchone()
    conn.close()
    return row


def save_talent_pool_profile(
    email,
    work_scope="",
    states="",
    districts="",
    status="ACTIVE",
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO talent_pool_profiles (
            email,
            work_scope,
            states,
            districts,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email)
        DO UPDATE SET
            work_scope=excluded.work_scope,
            states=excluded.states,
            districts=excluded.districts,
            status=excluded.status,
            updated_at=CURRENT_TIMESTAMP
    """, (
        email,
        work_scope,
        states,
        districts,
        status,
    ))
    conn.commit()
    conn.close()


# =====================================================
# VACANCIES
# =====================================================

def add_vacancy(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO vacancies (
        title, department, location, state, district, academic, professional,
        specialization, experience, certification, course, language,
        competencies, skills, closing_date, interview_required, status, created_by
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def get_vacancies_by_department(department):
    """Return only vacancies owned by the logged-in department."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM vacancies WHERE department=? ORDER BY created_at DESC",
        (department,),
    )
    data = cur.fetchall()
    conn.close()
    return data


def get_active_vacancies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM vacancies
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


def get_districts_by_state(state):
    """Return districts belonging to the selected state.
    Supports the common master-data layouts used by the prototype.
    """
    conn = get_connection()
    cur = conn.cursor()
    data = []
    try:
        cols = {row["name"] for row in cur.execute("PRAGMA table_info(districts)").fetchall()}
        district_col = "district" if "district" in cols else ("name" if "name" in cols else None)
        state_col = "state" if "state" in cols else ("state_name" if "state_name" in cols else None)

        if district_col and state_col:
            cur.execute(
                f'SELECT DISTINCT "{district_col}" FROM districts '
                f'WHERE "{state_col}"=? ORDER BY "{district_col}"',
                (state,),
            )
        elif district_col:
            cur.execute(
                f'SELECT DISTINCT "{district_col}" FROM districts '
                f'ORDER BY "{district_col}"'
            )
        else:
            cur.execute("SELECT 1 WHERE 0")

        data = [row[0] for row in cur.fetchall() if row[0]]
    except Exception:
        data = []
    conn.close()
    return data


def save_advertisement_vacancy(
    *,
    title,
    department,
    location,
    state,
    district,
    academic,
    professional,
    experience,
    skills,
    competencies,
    certification,
    language,
    closing_date,
    created_by,
):
    """Save a manually entered vacancy for the advertisement route."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO vacancies (
            title, department, location, state, district,
            academic, professional, specialization, experience,
            certification, course, language, competencies, skills,
            myportfolio_filename, myportfolio_json,
            ai_ringkasan_bidang, ai_sub_bidang, myportfolio_verified,
            vacancy_type, closing_date, interview_required, status, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            department,
            location,
            state,
            district,
            academic or "",
            professional or "",
            "",
            experience or "",
            certification or "",
            "",
            language or "",
            competencies or "",
            skills or "",
            "",
            "",
            "",
            "[]",
            0,
            "ADVERTISEMENT",
            str(closing_date),
            "Ya",
            "Active",
            created_by,
        ),
    )
    vacancy_id = cur.lastrowid
    conn.commit()
    conn.close()
    return vacancy_id


def save_myportfolio_vacancy(
    *,
    title,
    department,
    location,
    state,
    district,
    extraction,
    closing_date=None,
    created_by="",
):
    """Save a verified Cortex MyPortfolio vacancy for the Talent Pool route."""
    conn = get_connection()
    cur = conn.cursor()

    competencies = extraction.get("kompetensi", [])
    skills = extraction.get("kemahiran", [])
    academic = extraction.get("akademik", [])
    professional = extraction.get("ikhtisas")
    specialization = extraction.get("ai_ringkasan_bidang")
    experience = extraction.get("pengalaman")
    certification = extraction.get("pensijilan", [])
    course = extraction.get("fungsi", [])
    language = extraction.get("bahasa", [])

    cur.execute(
        """
        INSERT INTO vacancies (
            title, department, location, state, district,
            academic, professional, specialization, experience,
            certification, course, language, competencies, skills,
            myportfolio_filename, myportfolio_json,
            ai_ringkasan_bidang, ai_sub_bidang, myportfolio_verified,
            vacancy_type, closing_date, interview_required, status, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            department,
            location,
            state,
            district,
            json.dumps(academic, ensure_ascii=False),
            professional or "",
            specialization or "",
            experience or "",
            json.dumps(certification, ensure_ascii=False),
            json.dumps(course, ensure_ascii=False),
            json.dumps(language, ensure_ascii=False),
            json.dumps(competencies, ensure_ascii=False),
            json.dumps(skills, ensure_ascii=False),
            extraction.get("_myportfolio_filename", ""),
            json.dumps(extraction, ensure_ascii=False),
            extraction.get("ai_ringkasan_bidang"),
            json.dumps(extraction.get("ai_sub_bidang", []), ensure_ascii=False),
            1,
            "TALENT_POOL",
            str(closing_date) if closing_date else "",
            "Ya",
            "Active",
            created_by,
        ),
    )
    vacancy_id = cur.lastrowid
    conn.commit()
    conn.close()
    return vacancy_id


# =====================================================
# APPLICATIONS
# =====================================================

def add_application(vacancy_id, applicant_email, score=0, status="Menunggu Kelulusan Pengarah Bahagian Asal"):
    conn = get_connection()
    cur = conn.cursor()

    vacancy_row = cur.execute(
        "SELECT vacancy_type FROM vacancies WHERE id=?",
        (vacancy_id,),
    ).fetchone()
    source = "TALENT_POOL" if vacancy_row and vacancy_row["vacancy_type"] == "TALENT_POOL" else "IKLAN"

    existing = cur.execute("""
        SELECT id FROM applications
        WHERE vacancy_id=? AND applicant_email=?
    """, (vacancy_id, applicant_email)).fetchone()
    if existing:
        conn.close()
        return existing["id"]

    cur.execute("""
    INSERT INTO applications (vacancy_id, applicant_email, score, source, status)
    VALUES (?, ?, ?, ?, ?)
    """, (vacancy_id, applicant_email, score, source, status))
    app_id = cur.lastrowid
    conn.commit()
    conn.close()
    return app_id


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
        a.ai_explanation,
        a.ai_breakdown,
        a.ai_strengths,
        a.ai_gaps,
        a.ai_recommendation,
        a.ai_updated_at,
        a.source,
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
        a.ai_explanation,
        a.ai_breakdown,
        a.ai_strengths,
        a.ai_gaps,
        a.ai_recommendation,
        a.ai_updated_at,
        a.status,
        a.submitted_at,
        v.title,
        v.department AS target_department,
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
        p.language,
        p.competencies,
        p.skills,
        p.state,
        p.district
    FROM applications a
    LEFT JOIN vacancies v ON a.vacancy_id = v.id
    LEFT JOIN employee_profiles p ON a.applicant_email = p.email
    WHERE a.vacancy_id=?
    ORDER BY a.score DESC
    """, (vacancy_id,))
    data = cur.fetchall()
    conn.close()
    return data


def get_all_application_details():
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
        v.title,
        v.department AS target_department,
        p.name,
        p.current_department,
        p.current_position,
        p.grade
    FROM applications a
    LEFT JOIN vacancies v ON a.vacancy_id = v.id
    LEFT JOIN employee_profiles p ON a.applicant_email = p.email
    ORDER BY a.submitted_at DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data


def update_application_status(application_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status=? WHERE id=?", (status, application_id))
    conn.commit()
    conn.close()


def update_application_score(application_id, score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET score=? WHERE id=?", (score, application_id))
    conn.commit()
    conn.close()


def update_ai_snapshot(application_id, score, explanation="", breakdown=None, strengths=None, gaps=None, recommendation=""):
    """Persist the official Cortex AI snapshot.

    The first Cortex run freezes the numeric score for the application.
    Later runs may refresh the explanation/evidence, but never overwrite the
    already-frozen score. This keeps Department → BPSM → KPPM consistent.
    """
    conn = get_connection()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT score, ai_updated_at FROM applications WHERE id=?",
        (application_id,),
    ).fetchone()

    frozen_score = score
    if existing and existing["ai_updated_at"]:
        frozen_score = existing["score"]

    cur.execute("""
        UPDATE applications
        SET score=?, ai_explanation=?, ai_breakdown=?, ai_strengths=?,
            ai_gaps=?, ai_recommendation=?, ai_updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        frozen_score,
        explanation or "",
        json.dumps(breakdown or {}, ensure_ascii=False),
        json.dumps(strengths or [], ensure_ascii=False),
        json.dumps(gaps or [], ensure_ascii=False),
        recommendation or "",
        application_id,
    ))
    conn.commit()
    conn.close()


def _decode_json(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def get_ai_snapshot(application_id):
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute("""
        SELECT score, ai_explanation, ai_breakdown, ai_strengths,
               ai_gaps, ai_recommendation, ai_updated_at
        FROM applications WHERE id=?
    """, (application_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "score": row["score"],
        "explanation": row["ai_explanation"] or "",
        "breakdown": _decode_json(row["ai_breakdown"], {}),
        "strengths": _decode_json(row["ai_strengths"], []),
        "gaps": _decode_json(row["ai_gaps"], []),
        "recommendation": row["ai_recommendation"] or "",
        "updated_at": row["ai_updated_at"],
    }


# =====================================================
# OPEN APPLICATIONS
# =====================================================

def add_open_application(email, status="Menunggu Kekosongan"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO open_applications (applicant_email, status)
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
    INSERT INTO open_applications_preferences (application_id, department, priority)
    VALUES (?, ?, ?)
    """, (application_id, department, priority))
    conn.commit()
    conn.close()


def get_my_open_application(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT * FROM open_applications
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
    SELECT * FROM open_applications_preferences
    WHERE application_id=?
    ORDER BY priority
    """, (application_id,))
    data = cur.fetchall()
    conn.close()
    return data


# =====================================================
# INTERVIEW
# =====================================================

def add_interview(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO interviews (
        application_id, interview_date, interview_time, interview_location,
        interview_panel, result, remarks
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()


def get_interview(application_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interviews WHERE application_id=?", (application_id,))
    data = cur.fetchone()
    conn.close()
    return data


def update_interview_result(application_id, result, remarks):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE interviews
    SET result=?, remarks=?
    WHERE application_id=?
    """, (result, remarks, application_id))
    conn.commit()
    conn.close()


# =====================================================
# PLACEMENTS / BPSM
# =====================================================

def send_to_bpsm(application_id, applicant_email, vacancy_id, department, remarks=""):
    conn = get_connection()
    cur = conn.cursor()

    existing = cur.execute("""
        SELECT id FROM placements WHERE application_id=?
    """, (application_id,)).fetchone()

    if existing:
        cur.execute("""
        UPDATE placements
        SET applicant_email=?, vacancy_id=?, department=?, department_status=?,
            bpsm_status=?, remarks=?
        WHERE application_id=?
        """, (
            applicant_email,
            vacancy_id,
            department,
            "Diperakukan Bahagian",
            "Menunggu Semakan BPSM",
            remarks,
            application_id,
        ))
    else:
        cur.execute("""
        INSERT INTO placements (
            application_id, applicant_email, vacancy_id, department,
            department_status, bpsm_status, placement_order, placement_date, remarks
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
            remarks,
        ))

    cur.execute("UPDATE applications SET status=? WHERE id=?", ("Dihantar ke BPSM", application_id))
    conn.commit()
    conn.close()


def get_placements():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT
        pl.*,
        p.name,
        p.current_position,
        p.grade,
        v.title,
        v.department AS target_department
    FROM placements pl
    LEFT JOIN employee_profiles p ON pl.applicant_email = p.email
    LEFT JOIN vacancies v ON pl.vacancy_id = v.id
    ORDER BY pl.created_at DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data


def update_bpsm_status(placement_id, status, order_no="", placement_date="", remarks=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE placements
    SET bpsm_status=?, placement_order=?, placement_date=?, remarks=?
    WHERE id=?
    """, (status, order_no, placement_date, remarks, placement_id))
    conn.commit()
    conn.close()


# =====================================================
# EXCEL IMPORT / DEMO DATA
# =====================================================


def get_kppm_pending():
    """Return placements recommended by BPSM and waiting for KPPM."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.*,
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
            p.language,
            p.competencies,
            p.skills,
            p.state,
            p.district,
            v.title,
            v.department AS target_department
        FROM placements pl
        LEFT JOIN employee_profiles p ON pl.applicant_email = p.email
        LEFT JOIN vacancies v ON pl.vacancy_id = v.id
        WHERE pl.bpsm_status='Diperakukan BPSM'
          AND (pl.kppm_status IS NULL OR pl.kppm_status='')
        ORDER BY pl.created_at DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data


def get_kppm_history():
    """Return placements already processed by KPPM."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.*,
            p.name,
            v.title,
            v.department AS target_department
        FROM placements pl
        LEFT JOIN employee_profiles p ON pl.applicant_email = p.email
        LEFT JOIN vacancies v ON pl.vacancy_id = v.id
        WHERE pl.kppm_status IS NOT NULL
          AND pl.kppm_status != ''
        ORDER BY pl.created_at DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data


def update_kppm_decision(
    placement_id,
    status,
    remarks="",
    signed_by="",
    signed_at="",
):
    """Persist KPPM decision and mock digital-signature metadata."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE placements
        SET kppm_status=?,
            kppm_remarks=?,
            kppm_signed_by=?,
            kppm_signed_at=?
        WHERE id=?
    """, (
        status,
        remarks,
        signed_by,
        signed_at,
        placement_id,
    ))

    # Keep application status aligned with the workflow.
    row = cur.execute(
        "SELECT application_id FROM placements WHERE id=?",
        (placement_id,),
    ).fetchone()

    if row:
        if status == "Diluluskan KPPM":
            app_status = "Diluluskan KPPM"
        elif status == "Dipulangkan ke BPSM":
            app_status = "Dipulangkan ke BPSM"
        else:
            app_status = status

        cur.execute(
            "UPDATE applications SET status=? WHERE id=?",
            (app_status, row["application_id"]),
        )

    conn.commit()
    conn.close()



def get_post_kppm_pending():
    """Return KPPM-approved placements awaiting BPSM dispatch to directors."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.*,
            p.name,
            p.current_department,
            p.current_position,
            p.grade,
            p.email,
            v.title,
            v.department AS target_department
        FROM placements pl
        LEFT JOIN employee_profiles p
            ON pl.applicant_email = p.email
        LEFT JOIN vacancies v
            ON pl.vacancy_id = v.id
        WHERE pl.kppm_status='Diluluskan KPPM'
          AND (
              pl.director_origin_status IS NULL
              OR pl.director_origin_status=''
          )
        ORDER BY pl.created_at DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data


def get_director_pending():
    """Return KPPM-approved placements sent to the original director."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.*,
            p.name,
            p.current_department,
            p.current_position,
            p.grade,
            p.email,
            v.title,
            v.department AS target_department
        FROM placements pl
        LEFT JOIN employee_profiles p
            ON pl.applicant_email = p.email
        LEFT JOIN vacancies v
            ON pl.vacancy_id = v.id
        WHERE pl.director_origin_status=
              'Dihantar kepada Pengarah Bahagian Asal'
        ORDER BY pl.created_at DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data


def send_kppm_decision_to_directors(
    placement_id,
    new_department="",
):
    """BPSM sends the KPPM-approved decision to the original director
    and records the new director as CC.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE placements
        SET director_origin_status=?,
            director_new_cc=?,
            handover_status=?
        WHERE id=?
          AND kppm_status='Diluluskan KPPM'
    """, (
        "Dihantar kepada Pengarah Bahagian Asal",
        new_department or "",
        "Menunggu Serahan kepada Pegawai",
        placement_id,
    ))

    row = cur.execute(
        "SELECT application_id FROM placements WHERE id=?",
        (placement_id,),
    ).fetchone()

    if row:
        cur.execute(
            "UPDATE applications SET status=? WHERE id=?",
            (
                "Dihantar kepada Pengarah Bahagian Asal",
                row["application_id"],
            ),
        )

    conn.commit()
    conn.close()


def director_handover_to_officer(
    placement_id,
    remarks="",
):
    """Original director records that the decision was handed to the officer."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE placements
        SET handover_status=?,
            report_status=?,
            final_remarks=?
        WHERE id=?
          AND director_origin_status=
              'Dihantar kepada Pengarah Bahagian Asal'
    """, (
        "Diserahkan kepada Pegawai",
        "Menunggu Lapor Diri",
        remarks or "",
        placement_id,
    ))

    row = cur.execute(
        "SELECT application_id FROM placements WHERE id=?",
        (placement_id,),
    ).fetchone()

    if row:
        cur.execute(
            "UPDATE applications SET status=? WHERE id=?",
            (
                "Menunggu Lapor Diri",
                row["application_id"],
            ),
        )

    conn.commit()
    conn.close()


def officer_report_duty(
    placement_id,
    remarks="",
):
    """Officer confirms reporting for duty at the new department."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE placements
        SET report_status=?,
            final_remarks=?
        WHERE id=?
          AND handover_status='Diserahkan kepada Pegawai'
    """, (
        "Lapor Diri Selesai",
        remarks or "",
        placement_id,
    ))

    row = cur.execute(
        "SELECT application_id FROM placements WHERE id=?",
        (placement_id,),
    ).fetchone()

    if row:
        cur.execute(
            "UPDATE applications SET status=? WHERE id=?",
            (
                "Selesai",
                row["application_id"],
            ),
        )

    conn.commit()
    conn.close()



def get_director_placement_orders(department):
    """Return signed placement orders relevant to this director.

    The same Director module is used for:
    - original director: officer is leaving this department;
    - new director: officer is entering this department.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            pl.*,
            p.name,
            p.current_department,
            p.current_position,
            p.grade,
            p.email AS applicant_email,
            v.title,
            v.department AS target_department
        FROM placements pl
        LEFT JOIN employee_profiles p
            ON pl.applicant_email = p.email
        LEFT JOIN vacancies v
            ON pl.vacancy_id = v.id
        WHERE pl.director_origin_status=
              'Dihantar kepada Pengarah Bahagian Asal'
          AND (
              p.current_department=?
              OR v.department=?
          )
        ORDER BY pl.created_at DESC
    """, (department, department))

    data = cur.fetchall()
    conn.close()
    return data


def mark_director_placement_received(placement_id):
    """Record that the director has received the signed placement order."""
    from datetime import datetime

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE placements
        SET director_received_at=?
        WHERE id=?
          AND director_origin_status=
              'Dihantar kepada Pengarah Bahagian Asal'
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        placement_id,
    ))

    conn.commit()
    conn.close()


def _clean_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def import_applicants_excel(file_path):
    df = pd.read_excel(file_path)
    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        email = _clean_value(row.get("email", ""))
        if not email:
            continue

        name = _clean_value(row.get("name", ""))
        phone = _clean_value(row.get("phone", ""))
        current_department = _clean_value(row.get("current_department", ""))

        cur.execute("""
        INSERT OR IGNORE INTO users (email, name, role, department, phone, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (email, name, "Applicant", current_department, phone, "Active"))

        cur.execute("""
        INSERT OR REPLACE INTO employee_profiles (
            email, name, ic, phone, current_department, current_position, grade,
            home_address, state, district, academic, professional, specialization,
            experience, certification, course, language, competencies, skills
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email,
            name,
            _clean_value(row.get("ic", "")),
            phone,
            current_department,
            _clean_value(row.get("current_position", "")),
            _clean_value(row.get("grade", "")),
            _clean_value(row.get("home_address", "")),
            _clean_value(row.get("state", "")),
            _clean_value(row.get("district", "")),
            _clean_value(row.get("academic", "")),
            _clean_value(row.get("professional", "")),
            _clean_value(row.get("specialization", "")),
            int(row.get("experience", 0)) if not pd.isna(row.get("experience", 0)) else 0,
            _clean_value(row.get("certification", "")),
            _clean_value(row.get("course", "")),
            _clean_value(row.get("language", "")),
            _clean_value(row.get("competencies", row.get("competency", ""))),
            _clean_value(row.get("skills", row.get("skill", ""))),
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
            title, department, location, state, district, academic, professional,
            specialization, experience, certification, course, language,
            competencies, skills, closing_date, interview_required, status, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _clean_value(row.get("title", "")),
            _clean_value(row.get("department", "")),
            _clean_value(row.get("location", "")),
            _clean_value(row.get("state", "")),
            _clean_value(row.get("district", "")),
            _clean_value(row.get("academic", "")),
            _clean_value(row.get("professional", "")),
            _clean_value(row.get("specialization", "")),
            int(row.get("experience", 0)) if not pd.isna(row.get("experience", 0)) else 0,
            _clean_value(row.get("certification", "")),
            _clean_value(row.get("course", "")),
            _clean_value(row.get("language", "")),
            _clean_value(row.get("competencies", row.get("competency", ""))),
            _clean_value(row.get("skills", row.get("skill", ""))),
            _clean_value(row.get("closing_date", "")),
            _clean_value(row.get("interview_required", "Tidak")) or "Tidak",
            _clean_value(row.get("status", "Active")) or "Active",
            created_by,
        ))

    conn.commit()
    conn.close()


def auto_generate_dummy_applications(limit_per_applicant=2):
    from utils.ai_engine import calculate_ai_match

    conn = get_connection()
    cur = conn.cursor()

    profiles = cur.execute("""
        SELECT *
        FROM employee_profiles
        WHERE email LIKE 'pemohon%'
    """).fetchall()

    vacancies = cur.execute("""
        SELECT *
        FROM vacancies
        WHERE status='Active'
    """).fetchall()

    if not profiles or not vacancies:
        conn.close()
        return 0

    total_created = 0

    for profile in profiles:
        selected_vacancies = random.sample(vacancies, min(limit_per_applicant, len(vacancies)))

        for vacancy in selected_vacancies:
            existing = cur.execute("""
                SELECT id
                FROM applications
                WHERE applicant_email=? AND vacancy_id=?
            """, (profile["email"], vacancy["id"])).fetchone()

            if existing:
                continue

            score, _, _ = calculate_ai_match(profile, vacancy)

            cur.execute("""
                INSERT INTO applications (vacancy_id, applicant_email, score, status)
                VALUES (?, ?, ?, ?)
            """, (
                vacancy["id"],
                profile["email"],
                score,
                "Menunggu Kelulusan Pengarah Bahagian Asal",
            ))

            total_created += 1

    conn.commit()
    conn.close()
    return total_created


def is_demo_data_empty():
    return count_profiles() == 0 and count_vacancies() == 0


def initialize_demo_data():
    data_dir = Path("data")
    master_file = data_dir / "master_data_v3_FULL.xlsx"
    applicants_file = data_dir / "dummy_pemohon_kpm_300_ALIGNED.xlsx"
    vacancies_file = data_dir / "dummy_iklan_kpm_30_ALIGNED.xlsx"

    if not (master_file.exists() and applicants_file.exists() and vacancies_file.exists()):
        return False

    import_master_data(master_file)
    import_applicants_excel(applicants_file)
    import_vacancies_excel(vacancies_file, "demo@moe.gov.my")
    auto_generate_dummy_applications(limit_per_applicant=2)
    return True


if __name__ == "__main__":
    create_tables()
    seed_users()
    print("===================================")
    print(" MyGovTalent AI Database v4 Ready")
    print("===================================")