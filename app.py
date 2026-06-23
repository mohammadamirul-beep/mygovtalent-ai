import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="MyGovTalent AI",
    page_icon="🧠",
    layout="wide"
)

# ==================================
# CUSTOM CSS
# ==================================

st.markdown("""
<style>

[data-testid="metric-container"]{
    background-color:#f8f9fa;
    border:1px solid #dee2e6;
    padding:15px;
    border-radius:12px;
}

</style>
""", unsafe_allow_html=True)

# ==================================
# HEADER
# ==================================

st.title("🧠 MyGovTalent AI")

st.caption(
    "AI-Powered Talent Intelligence Platform for Public Sector Workforce Optimization"
)

# ==================================
# SIDEBAR
# ==================================

st.sidebar.title("🧠 MyGovTalent AI")

menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🤖 AI Profiling",
        "🔍 Talent Discovery",
        "🎯 Vacancy Matching",
        "📢 Vacancy Portal",
        "📊 Analytics"
    ]
)

# ==================================
# FILE UPLOAD
# ==================================

uploaded_file = st.file_uploader(
    "Upload Employee Data",
    type=["xlsx", "csv"]
)

if uploaded_file is None:

    st.info(
        "📂 Sila upload fail Excel terlebih dahulu."
    )

    st.stop()

# ==================================
# READ FILE
# ==================================

if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# ==================================
# VALIDATION
# ==================================

required_columns = [
    "Nama",
    "Jawatan",
    "Bahagian",
    "Kursus",
    "Pensijilan",
    "Pengalaman"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"Kolum tidak dijumpai: {missing_columns}"
    )

    st.stop()

# ==================================
# AI PROFILING ENGINE
# ==================================

def generate_ai_skills(row):

    text = f"""
    {row['Kursus']}
    {row['Pensijilan']}
    {row['Pengalaman']}
    """.lower()

    mapping = {

        "Artificial Intelligence": [
            "ai",
            "artificial intelligence",
            "machine learning",
            "generative ai"
        ],

        "Data Analytics": [
            "power bi",
            "dashboard",
            "analytics",
            "data"
        ],

        "Cybersecurity": [
            "cyber",
            "security",
            "crisc",
            "cisa"
        ],

        "Project Management": [
            "pmp",
            "project",
            "projek"
        ],

        "Leadership": [
            "ketua",
            "head",
            "lead",
            "director"
        ],

        "Cloud Computing": [
            "azure",
            "aws",
            "cloud"
        ]
    }

    skills = []

    for skill_name, keywords in mapping.items():

        if any(
            keyword in text
            for keyword in keywords
        ):
            skills.append(skill_name)

    return ", ".join(skills)

# ==================================
# NORMALIZE SKILL
# ==================================

def normalize_skill(skill):

    mapping = {

        "ai": "artificial intelligence",
        "analytics": "data analytics",
        "cyber": "cybersecurity",
        "project": "project management",
        "cloud": "cloud computing"

    }

    skill = skill.strip().lower()

    return mapping.get(
        skill,
        skill
    )

# ==================================
# GENERATE AI SKILLS
# ==================================

df["AI Skills"] = df.apply(
    generate_ai_skills,
    axis=1
)

df["Skill Count"] = df["AI Skills"].apply(
    lambda x: len([
        s for s in str(x).split(",")
        if s.strip()
    ])
)

# ==================================
# DASHBOARD
# ==================================

if menu == "🏠 Dashboard":

    all_skills = []

    for skills in df["AI Skills"]:

        for skill in str(skills).split(","):

            skill = skill.strip()

            if skill:
                all_skills.append(skill)

    ai_count = df["AI Skills"].str.contains(
        "Artificial Intelligence",
        case=False,
        na=False
    ).sum()

    readiness = round(
        (ai_count / len(df)) * 100
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Pegawai",
        len(df)
    )

    col2.metric(
        "Bahagian",
        df["Bahagian"].nunique()
    )

    col3.metric(
        "AI Skills",
        len(set(all_skills))
    )

    col4.metric(
        "Talent Pool",
        len(df)
    )

    col5.metric(
        "AI Ready",
        ai_count
    )

    st.markdown("---")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=readiness,
        title={
            'text': "AI Readiness Index (%)"
        },
        gauge={
            'axis': {
                'range': [0,100]
            }
        }
    ))

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("---")

    division_df = (
        df.groupby("Bahagian")
        .size()
        .reset_index(
            name="Bilangan Pegawai"
        )
    )

    fig = px.bar(
        division_df,
        x="Bahagian",
        y="Bilangan Pegawai",
        title="Talent Distribution by Division"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("---")

    st.subheader(
        "🏆 Top Talent Ranking"
    )

    top_talent = df.sort_values(
        "Skill Count",
        ascending=False
    )

    st.dataframe(
        top_talent[
            [
                "Nama",
                "Jawatan",
                "Bahagian",
                "AI Skills",
                "Skill Count"
            ]
        ].head(10),
        use_container_width=True
    )

    st.markdown("---")

    st.subheader(
        "👥 Employee Repository"
    )

    st.dataframe(
        df,
        use_container_width=True
    )
    # ==================================
# AI PROFILING
# ==================================

elif menu == "🤖 AI Profiling":

    st.header("🤖 AI Competency Profiling")

    st.success(
        f"{len(df)} competency profiles generated successfully."
    )

    st.dataframe(
        df[
            [
                "Nama",
                "Jawatan",
                "Bahagian",
                "AI Skills"
            ]
        ],
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("🏆 Top AI Talent")

    top_ai = df.sort_values(
        "Skill Count",
        ascending=False
    )

    st.dataframe(
        top_ai[
            [
                "Nama",
                "Jawatan",
                "Bahagian",
                "AI Skills",
                "Skill Count"
            ]
        ].head(10),
        use_container_width=True
    )

# ==================================
# TALENT DISCOVERY
# ==================================

elif menu == "🔍 Talent Discovery":

    st.header("🔍 Talent Discovery")

    search_skill = st.text_input(
        "Cari Kemahiran"
    )

    if search_skill:

        search_skill = normalize_skill(
            search_skill
        )

        result = df[
            df["AI Skills"]
            .str.contains(
                search_skill,
                case=False,
                na=False
            )
        ]

        st.success(
            f"{len(result)} pegawai ditemui"
        )

        st.dataframe(
            result[
                [
                    "Nama",
                    "Jawatan",
                    "Bahagian",
                    "AI Skills"
                ]
            ],
            use_container_width=True
        )

# ==================================
# VACANCY MATCHING
# ==================================

elif menu == "🎯 Vacancy Matching":

    st.header("🎯 Vacancy Matching")

    st.info(
        "Contoh: AI, Analytics, Cyber, Project, Cloud"
    )

    required_skills = st.text_input(
        "Kemahiran Diperlukan (pisahkan dengan koma)"
    )

    if st.button(
        "Match Candidate"
    ):

        skills_needed = [

            normalize_skill(skill)

            for skill in required_skills.split(",")

            if skill.strip()

        ]

        results = []

        for _, row in df.iterrows():

            employee_skills = str(
                row["AI Skills"]
            ).lower()

            matched = 0

            matched_skills = []

            for skill in skills_needed:

                if skill in employee_skills:

                    matched += 1

                    matched_skills.append(
                        skill
                    )

            if len(skills_needed) > 0:

                score = round(
                    (
                        matched /
                        len(skills_needed)
                    ) * 100
                )

            else:

                score = 0

            results.append({

                "Nama":
                    row["Nama"],

                "Jawatan":
                    row["Jawatan"],

                "Bahagian":
                    row["Bahagian"],

                "AI Skills":
                    row["AI Skills"],

                "Matched Skills":
                    ", ".join(
                        matched_skills
                    ),

                "Match Score (%)":
                    score

            })

        result_df = pd.DataFrame(
            results
        )

        result_df = result_df[
            result_df[
                "Match Score (%)"
            ] > 0
        ]

        result_df = result_df.sort_values(
            by="Match Score (%)",
            ascending=False
        )

        st.subheader(
            "🏆 Recommended Candidates"
        )

        if len(result_df) == 0:

            st.warning(
                "Tiada calon sepadan."
            )

        else:

            st.dataframe(
                result_df,
                use_container_width=True
            )

# ==================================
# VACANCY PORTAL
# ==================================

elif menu == "📢 Vacancy Portal":

    st.header(
        "📢 Vacancy Portal"
    )

    vacancy_name = st.text_input(
        "Nama Jawatan"
    )

    vacancy_division = st.text_input(
        "Bahagian"
    )

    vacancy_skills = st.text_input(
        "Kemahiran Diperlukan"
    )

    if st.button(
        "Create Vacancy"
    ):

        st.success(
            "Vacancy berjaya direkodkan"
        )

        st.write(
            "### Ringkasan Kekosongan"
        )

        st.write(
            "Jawatan:",
            vacancy_name
        )

        st.write(
            "Bahagian:",
            vacancy_division
        )

        st.write(
            "Skills:",
            vacancy_skills
        )

        skills_needed = [

            normalize_skill(skill)

            for skill in vacancy_skills.split(",")

            if skill.strip()

        ]

        results = []

        for _, row in df.iterrows():

            employee_skills = str(
                row["AI Skills"]
            ).lower()

            matched = 0

            for skill in skills_needed:

                if skill in employee_skills:

                    matched += 1

            score = 0

            if len(skills_needed) > 0:

                score = round(
                    (
                        matched /
                        len(skills_needed)
                    ) * 100
                )

            results.append({

                "Nama":
                    row["Nama"],

                "Jawatan":
                    row["Jawatan"],

                "Bahagian":
                    row["Bahagian"],

                "AI Skills":
                    row["AI Skills"],

                "Match Score (%)":
                    score

            })

        result_df = pd.DataFrame(
            results
        )

        result_df = result_df[
            result_df[
                "Match Score (%)"
            ] > 0
        ]

        result_df = result_df.sort_values(
            by="Match Score (%)",
            ascending=False
        )

        st.subheader(
            "🏆 Cadangan Calon"
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )
        # ==================================
# ANALYTICS
# ==================================

elif menu == "📊 Analytics":

    st.header("📊 Talent Analytics")

    # ==========================
    # TOP SKILLS
    # ==========================

    skill_count = {}

    for skills in df["AI Skills"]:

        for skill in str(skills).split(","):

            skill = skill.strip()

            if skill:

                skill_count[skill] = (
                    skill_count.get(skill, 0) + 1
                )

    skill_df = pd.DataFrame(
        list(skill_count.items()),
        columns=[
            "Skill",
            "Count"
        ]
    )

    skill_df = skill_df.sort_values(
        by="Count",
        ascending=False
    )

    st.subheader(
        "📈 Top Skills"
    )

    fig = px.bar(
        skill_df,
        x="Skill",
        y="Count",
        title="Top Skills Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ==========================
    # KPI ANALYTICS
    # ==========================

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Skills",
        len(skill_df)
    )

    col2.metric(
        "Most Dominant Skill",
        skill_df.iloc[0]["Skill"]
        if len(skill_df) > 0
        else "-"
    )

    col3.metric(
        "Total Profiles",
        len(df)
    )

    # ==========================
    # HEATMAP
    # ==========================

    st.markdown("---")

    st.subheader(
        "🔥 Competency Heatmap"
    )

    heatmap_data = []

    for _, row in df.iterrows():

        for skill in str(
            row["AI Skills"]
        ).split(","):

            skill = skill.strip()

            if skill:

                heatmap_data.append({

                    "Bahagian":
                        row["Bahagian"],

                    "Skill":
                        skill

                })

    heatmap_df = pd.DataFrame(
        heatmap_data
    )

    if len(heatmap_df) > 0:

        pivot = pd.crosstab(
            heatmap_df["Bahagian"],
            heatmap_df["Skill"]
        )

        fig = px.imshow(
            pivot,
            text_auto=True,
            aspect="auto",
            title="Competency Heatmap"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ==========================
    # TALENT GAP
    # ==========================

    st.markdown("---")

    st.subheader(
        "⚠️ Talent Gap Analysis"
    )

    gap_df = skill_df.sort_values(
        by="Count",
        ascending=True
    )

    st.dataframe(
        gap_df.head(10),
        use_container_width=True
    )

    st.warning(
        "Kemahiran dengan bilangan pegawai rendah perlu diberi fokus pembangunan bakat."
    )

    # ==========================
    # DIVISION SKILL MATRIX
    # ==========================

    st.markdown("---")

    st.subheader(
        "🏢 Division Skill Matrix"
    )

    if len(heatmap_df) > 0:

        matrix = pd.crosstab(
            heatmap_df["Bahagian"],
            heatmap_df["Skill"]
        )

        st.dataframe(
            matrix,
            use_container_width=True
        )

    # ==========================
    # TOP TALENT
    # ==========================

    st.markdown("---")

    st.subheader(
        "🏆 Top Talent Ranking"
    )

    ranking_df = df.sort_values(
        "Skill Count",
        ascending=False
    )

    st.dataframe(
        ranking_df[
            [
                "Nama",
                "Jawatan",
                "Bahagian",
                "AI Skills",
                "Skill Count"
            ]
        ].head(20),
        use_container_width=True
    )

    # ==========================
    # AI READINESS BY DIVISION
    # ==========================

    st.markdown("---")

    st.subheader(
        "🤖 AI Readiness by Division"
    )

    readiness_data = []

    for division in df["Bahagian"].unique():

        total = len(
            df[
                df["Bahagian"] == division
            ]
        )

        ai_ready = len(

            df[
                (df["Bahagian"] == division)
                &
                (
                    df["AI Skills"]
                    .str.contains(
                        "Artificial Intelligence",
                        case=False,
                        na=False
                    )
                )
            ]

        )

        readiness_pct = round(
            (ai_ready / total) * 100
        )

        readiness_data.append({

            "Bahagian":
                division,

            "AI Readiness":
                readiness_pct

        })

    readiness_df = pd.DataFrame(
        readiness_data
    )

    fig = px.bar(
        readiness_df,
        x="Bahagian",
        y="AI Readiness",
        title="AI Readiness by Division"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )