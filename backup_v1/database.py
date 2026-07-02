import sqlite3
import pandas as pd

DB_NAME = "mygovtalent.db"


# =====================================================
# CONNECTION
# =====================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# =====================================================
# IMPORT MASTER DATA
# =====================================================

def import_master_data(file_path):

    conn = get_connection()

    sheets = [
        "Organizations",
        "Grades",
        "Academic",
        "Professional",
        "Specialization",
        "Certification",
        "Course",
        "Language",
        "States",
        "Districts"
    ]

    for sheet in sheets:

        df = pd.read_excel(
            file_path,
            sheet_name=sheet
        )

        table = sheet.lower()

        df.to_sql(
            table,
            conn,
            if_exists="replace",
            index=False
        )

    conn.close()
    
# =====================================================
# CREATE TABLES
# =====================================================

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================================
    # USERS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        email TEXT UNIQUE,

        name TEXT,

        role TEXT,

        department TEXT,

        phone TEXT,

        status TEXT

    )
    """)

    # =====================================================
    # EMPLOYEE PROFILE
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_profiles(

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

    # =====================================================
    # VACANCIES
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vacancies(

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

    # =====================================================
    # APPLICATIONS (IKLAN)
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        vacancy_id INTEGER,

        applicant_email TEXT,

        score REAL,

        status TEXT,

        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================================================
    # OPEN APPLICATIONS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS open_applications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        applicant_email TEXT,

        status TEXT,

        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================================================
    # OPEN APPLICATIONS PREFERENCES
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS open_applications_preferences(

        application_id INTEGER,

        department TEXT,

        priority INTEGER
    )
    """)

    # =====================================================
    # INTERVIEWS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        application_id INTEGER,

        interview_required TEXT,

        interview_date TEXT,

        interview_result TEXT,

        remarks TEXT

    )
    """)

    # =====================================================
    # PLACEMENTS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS placements(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        application_id INTEGER,

        department_status TEXT,

        bpsm_status TEXT,

        placement_order TEXT,

        placement_date TEXT,

        remarks TEXT

    )
    """)

    # =====================================================
    # OTP LOGS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        email TEXT,

        otp TEXT,

        verified INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================================================
    # ACTIVITY LOGS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        email TEXT,

        module TEXT,

        action TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================================================
    # ORGANIZATIONS
    # =====================================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parent_id INTEGER,

        code TEXT UNIQUE,

        name TEXT,

        type TEXT,

        state TEXT,

        district TEXT,

        address TEXT,

        status TEXT

    )
    """)

    conn.commit()
    conn.close()

# =====================================================
# USERS
# =====================================================

def add_user(email, name, role, department="", phone="", status="Active"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT OR IGNORE INTO users(

        email,
        name,
        role,
        department,
        phone,
        status

    )

    VALUES(

        ?,?,?,?,?,?

    )

    """, (

        email,
        name,
        role,
        department,
        phone,
        status

    ))

    conn.commit()
    conn.close()


def get_user(email):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM users WHERE email=?",

        (email,)

    )

    user = cursor.fetchone()

    conn.close()

    return user


def get_all_users():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM users

    ORDER BY name

    """)

    users = cursor.fetchall()

    conn.close()

    return users


# =====================================================
# EMPLOYEE PROFILE
# =====================================================

def save_profile(data):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT OR REPLACE INTO employee_profiles(

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

    VALUES(

        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?

    )

    """, data)

    conn.commit()

    conn.close()


def get_profile(email):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM employee_profiles

    WHERE email=?

    """, (email,))

    profile = cursor.fetchone()

    conn.close()

    return profile


def profile_exists(email):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        """

        SELECT COUNT(*)

        FROM employee_profiles

        WHERE email=?

        """,

        (email,)

    )

    exists = cursor.fetchone()[0]

    conn.close()

    return exists > 0


def update_profile(data):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE employee_profiles

    SET

        name=?,
        ic=?,
        phone=?,
        current_department=?,
        current_position=?,
        grade=?,
        home_address=?,
        state=?,
        district=?,
        academic=?,
        professional=?,
        specialization=?,
        experience=?,
        certification=?,
        course=?,
        language=?,
        updated_at=CURRENT_TIMESTAMP

    WHERE email=?

    """, (

        data[1],
        data[2],
        data[3],
        data[4],
        data[5],
        data[6],
        data[7],
        data[8],
        data[9],
        data[10],
        data[11],
        data[12],
        data[13],
        data[14],
        data[15],
        data[16],
        data[0]

    ))

    conn.commit()

    conn.close()


def get_profiles_by_department(department):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM employee_profiles

    WHERE current_department=?

    ORDER BY name

    """, (department,))

    profiles = cursor.fetchall()

    conn.close()

    return profiles

    # =====================================================
# VACANCIES
# =====================================================

def add_vacancy(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO vacancies(

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

    VALUES(

        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?

    )

    """, data)

    conn.commit()
    conn.close()


def get_all_vacancies():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM vacancies

    ORDER BY created_at DESC

    """)

    data = cursor.fetchall()

    conn.close()

    return data


def get_active_vacancies():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM vacancies

    WHERE status='Active'

    ORDER BY closing_date

    """)

    data = cursor.fetchall()

    conn.close()

    return data


def get_vacancy(vacancy_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM vacancies WHERE id=?",

        (vacancy_id,)

    )

    vacancy = cursor.fetchone()

    conn.close()

    return vacancy


def close_vacancy(vacancy_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    UPDATE vacancies

    SET status='Closed'

    WHERE id=?

    """, (vacancy_id,))

    conn.commit()
    conn.close()


# =====================================================
# APPLICATIONS (IKLAN)
# =====================================================

def add_application(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO applications(

        vacancy_id,
        applicant_email,
        score,
        status

    )

    VALUES(

        ?,?,?,?

    )

    """, data)

    conn.commit()
    conn.close()


def get_my_applications(email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM applications

    WHERE applicant_email=?

    ORDER BY submitted_at DESC

    """, (email,))

    data = cursor.fetchall()

    conn.close()

    return data


def get_applications_by_vacancy(vacancy_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM applications

    WHERE vacancy_id=?

    ORDER BY score DESC

    """, (vacancy_id,))

    data = cursor.fetchall()

    conn.close()

    return data


def update_application_status(application_id, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    UPDATE applications

    SET status=?

    WHERE id=?

    """, (status, application_id))

    conn.commit()
    conn.close()


# =====================================================
# OPEN APPLICATIONS
# =====================================================

def add_open_application(email, status="Submitted"):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO open_applications(

        applicant_email,
        status

    )

    VALUES(

        ?,?

    )

    """, (

        email,
        status

    ))

    application_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return application_id

def add_open_application_preference(

    application_id,
    department,
    priority

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO open_applications_preferences(

        application_id,
        department,
        priority

    )

    VALUES(

        ?,?,?

    )

    """, (

        application_id,
        department,
        priority

    ))

    conn.commit()

    conn.close()

def get_open_applications_preferences(application_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM open_applications_preferences

    WHERE application_id=?

    ORDER BY priority

    """, (application_id,))

    data = cursor.fetchall()

    conn.close()

    return data

def get_open_applications():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM open_applications

    ORDER BY submitted_at DESC

    """)

    data = cursor.fetchall()

    conn.close()

    return data


def get_my_open_application(email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM open_applications

    WHERE applicant_email=?

    ORDER BY submitted_at DESC

    LIMIT 1

    """, (email,))

    data = cursor.fetchone()

    conn.close()

    return data

    # =====================================================
# INTERVIEWS
# =====================================================

def add_interview(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO interviews(

        application_id,
        interview_required,
        interview_date,
        interview_result,
        remarks

    )

    VALUES(

        ?,?,?,?,?

    )

    """, data)

    conn.commit()
    conn.close()


def get_interview(application_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM interviews

    WHERE application_id=?

    """, (application_id,))

    data = cursor.fetchone()

    conn.close()

    return data


def update_interview_result(application_id, result, remarks):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    UPDATE interviews

    SET

        interview_result=?,
        remarks=?

    WHERE application_id=?

    """, (

        result,
        remarks,
        application_id

    ))

    conn.commit()
    conn.close()


# =====================================================
# PLACEMENTS
# =====================================================

def add_placement(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO placements(

        application_id,
        department_status,
        bpsm_status,
        placement_order,
        placement_date,
        remarks

    )

    VALUES(

        ?,?,?,?,?,?

    )

    """, data)

    conn.commit()
    conn.close()


def get_placements():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM placements

    ORDER BY id DESC

    """)

    data = cursor.fetchall()

    conn.close()

    return data


def update_bpsm_status(application_id, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    UPDATE placements

    SET bpsm_status=?

    WHERE application_id=?

    """, (

        status,
        application_id

    ))

    conn.commit()
    conn.close()


# =====================================================
# OTP LOGS
# =====================================================

def save_otp(email, otp):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO otp_logs(

        email,
        otp

    )

    VALUES(

        ?,?

    )

    """, (

        email,
        otp

    ))

    conn.commit()
    conn.close()


def verify_otp(email, otp):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM otp_logs

    WHERE

        email=?

    AND

        otp=?

    ORDER BY id DESC

    LIMIT 1

    """, (

        email,
        otp

    ))

    data = cursor.fetchone()

    conn.close()

    return data


# =====================================================
# ACTIVITY LOG
# =====================================================

def log_activity(email, module, action):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO activity_logs(

        email,
        module,
        action

    )

    VALUES(

        ?,?,?

    )

    """, (

        email,
        module,
        action

    ))

    conn.commit()
    conn.close()


def get_activity_logs():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM activity_logs

    ORDER BY created_at DESC

    """)

    data = cursor.fetchall()

    conn.close()

    return data


# =====================================================
# INITIALIZE DATABASE
# =====================================================

if __name__ == "__main__":

    create_tables()

    print("===================================")
    print(" MyGovTalent AI Database Initialized")
    print("===================================")