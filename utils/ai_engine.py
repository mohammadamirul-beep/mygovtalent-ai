"""Central AI scoring engine for MyGovTalent AI.

This module is the single source of truth for AI Match Score and
AI Match Explanation. All pages should use calculate_ai_match().
"""

AI_WEIGHTS = {
    "academic": 20,
    "specialization": 25,
    "experience": 25,
    "certification": 10,
    "course": 15,
    "state": 5,
}


def _value(row, key, default=""):
    try:
        val = row[key]
    except Exception:
        try:
            val = row.get(key, default)
        except Exception:
            val = default
    return default if val is None else val


def _int_value(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def split_multi(value):
    return [x.strip() for x in str(value or "").split(",") if x.strip()]


def match_multi_detail(profile_value, vacancy_value):
    profile_items = [x.lower() for x in split_multi(profile_value)]
    vacancy_items = [x.lower() for x in split_multi(vacancy_value)]

    if not vacancy_items:
        return 0, 0, 0

    matched = sum(1 for item in vacancy_items if item in profile_items)
    ratio = matched / len(vacancy_items)
    return matched, len(vacancy_items), ratio


def calculate_ai_match(profile, vacancy):
    """Return (score, explanation_lines, recommendation)."""
    score = 0
    explanation = []

    profile_academic = str(_value(profile, "academic", ""))
    vacancy_academic = str(_value(vacancy, "academic", ""))
    if profile_academic and profile_academic == vacancy_academic:
        score += AI_WEIGHTS["academic"]
        explanation.append(f"✔ Akademik sepadan (+{AI_WEIGHTS['academic']})")
    else:
        explanation.append("✘ Akademik tidak sepadan (+0)")

    profile_specialization = str(_value(profile, "specialization", ""))
    vacancy_specialization = str(_value(vacancy, "specialization", ""))
    if profile_specialization and profile_specialization == vacancy_specialization:
        score += AI_WEIGHTS["specialization"]
        explanation.append(f"✔ Bidang pengkhususan sepadan (+{AI_WEIGHTS['specialization']})")
    else:
        explanation.append("✘ Bidang pengkhususan tidak sepadan (+0)")

    profile_exp = _int_value(_value(profile, "experience", 0))
    vacancy_exp = _int_value(_value(vacancy, "experience", 0))
    if profile_exp >= vacancy_exp:
        score += AI_WEIGHTS["experience"]
        explanation.append(f"✔ Pengalaman memenuhi syarat ({profile_exp} tahun ≥ {vacancy_exp} tahun) (+{AI_WEIGHTS['experience']})")
    else:
        explanation.append(f"✘ Pengalaman belum memenuhi syarat ({profile_exp} tahun < {vacancy_exp} tahun) (+0)")

    cert_match, cert_total, cert_ratio = match_multi_detail(
        _value(profile, "certification", ""),
        _value(vacancy, "certification", ""),
    )
    cert_score = round(cert_ratio * AI_WEIGHTS["certification"])
    score += cert_score
    if cert_total:
        explanation.append(f"✔ Pensijilan sepadan {cert_match}/{cert_total} (+{cert_score})")
    else:
        explanation.append("ℹ Tiada pensijilan khusus ditetapkan (+0)")

    course_match, course_total, course_ratio = match_multi_detail(
        _value(profile, "course", ""),
        _value(vacancy, "course", ""),
    )
    course_score = round(course_ratio * AI_WEIGHTS["course"])
    score += course_score
    if course_total:
        explanation.append(f"✔ Kursus sepadan {course_match}/{course_total} (+{course_score})")
    else:
        explanation.append("ℹ Tiada kursus khusus ditetapkan (+0)")

    profile_state = str(_value(profile, "state", ""))
    vacancy_state = str(_value(vacancy, "state", ""))
    if profile_state and profile_state == vacancy_state:
        score += AI_WEIGHTS["state"]
        explanation.append(f"✔ Negeri sama dengan lokasi kekosongan (+{AI_WEIGHTS['state']})")
    else:
        explanation.append("✘ Negeri berbeza (+0)")

    score = int(round(score))

    if score >= 85:
        recommendation = "Sangat sesuai untuk jawatan ini."
    elif score >= 70:
        recommendation = "Sesuai dan wajar dipertimbangkan."
    elif score >= 50:
        recommendation = "Boleh dipertimbangkan dengan semakan lanjut."
    else:
        recommendation = "Padanan rendah berbanding keperluan iklan."

    return score, explanation, recommendation
