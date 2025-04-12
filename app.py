import os
import streamlit as st
import PyPDF2
import docx
import google.generativeai as genai
import plotly.graph_objects as go

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Page Setup
st.set_page_config(page_title="Resume Analyzer & Job Matcher", page_icon="🧠", layout="wide")

# Custom CSS
st.markdown("""
<style>
body {
    background-color: #f5f8fa;
}
.main-title {
    font-size: 40px;
    font-weight: bold;
    color: #2c3e50;
    text-align: center;
    margin-top: 10px;
}
.sub-title {
    font-size: 18px;
    color: #7f8c8d;
    text-align: center;
    margin-bottom: 30px;
}
.section-card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-top: 20px;
}
.success-banner {
    background: linear-gradient(to right, #27ae60, #2ecc71);
    color: white;
    font-size: 16px;
    padding: 12px;
    text-align: center;
    border-radius: 8px;
    margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)

# Titles
st.markdown('<h1 class="main-title">🧠 Resume Analyzer & Job Matcher</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI-powered feedback, job suggestions & ATS scoring</p>', unsafe_allow_html=True)

# Upload resume
uploaded_file = st.file_uploader("📄 Upload your Resume (.pdf or .docx)", type=["pdf", "docx"])

# Extract resume text
def extract_resume_text(file_path, file_type):
    text = ""
    if file_type == "pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    elif file_type == "docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text.strip()

# General analysis
def analyze_resume(text):
    prompt = f"""
    You are an AI Resume Consultant. Based on the following resume details:
    {text}

    Provide:
    1. Suitable job roles.
    2. Skills missing for these roles.
    3. Courses/certifications to learn them.
    4. Resume improvement tips.

    Use the format:
    [Job Roles]
    - Role 1
    - Role 2

    [Missing Skills]
    - Skill: Suggestion

    [Resume Tips]
    - Tip 1
    - Tip 2
    """
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    return response.text.strip()

# Targeted ATS analysis
def analyze_resume_with_role(resume_text, desired_role):
    prompt = f"""
    You are an AI resume evaluator for ATS systems.

    Resume:
    {resume_text}

    Target Role: {desired_role}

    1. Based on the resume, give an ATS score out of 100 for this role.
    2. List missing skills required for a strong match.
    3. Recommend relevant certifications or courses for those skills.
    4. Provide 2-3 tips to improve the resume for this specific job.

    Return all results in the following format:

    [ATS Score]
    - Score: XX/100

    [Missing Skills]
    - Skill: Recommendation

    [Courses/Certifications]
    - Skill: Course Name or Provider

    [Improvement Tips]
    - Tip 1
    - Tip 2
    """
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    return response.text.strip()

# Speedometer gauge for ATS
def render_ats_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "ATS Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#27ae60"},
            'steps': [
                {'range': [0, 40], 'color': '#e74c3c'},
                {'range': [40, 70], 'color': '#f1c40f'},
                {'range': [70, 100], 'color': '#2ecc71'},
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    return fig

# Main Logic
if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1]
    file_path = f"temp_resume.{file_type}"

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("✅ Resume uploaded successfully!")

    with st.spinner("🔍 Extracting resume content..."):
        resume_text = extract_resume_text(file_path, file_type)

    os.remove(file_path)

    if not resume_text:
        st.error("❌ Could not extract text. Try another file format.")
    else:
        with st.spinner("🤖 Analyzing resume with AI..."):
            result = analyze_resume(resume_text)

        if result:
            st.markdown("## 📌 General Resume Insights")
            st.markdown('<div class="section-card">', unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs(["💼 Job Matches", "🔍 Missing Skills", "📝 Resume Tips"])
            job_roles, skills, tips = "", "", ""

            if "[Job Roles]" in result:
                sections = result.split("[")
                for section in sections:
                    if section.startswith("Job Roles]"):
                        job_roles = section.replace("Job Roles]", "").strip()
                    elif section.startswith("Missing Skills]"):
                        skills = section.replace("Missing Skills]", "").strip()
                    elif section.startswith("Resume Tips]"):
                        tips = section.replace("Resume Tips]", "").strip()

            with tab1:
                st.markdown("### 💼 Suggested Job Roles")
                st.markdown(job_roles or "No suggestions found.")

            with tab2:
                st.markdown("### 🔍 Missing Skills & Suggestions")
                st.markdown(skills or "No missing skills identified.")

            with tab3:
                st.markdown("### 📝 General Resume Tips")
                st.markdown(tips or "No tips provided.")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<div class="success-banner">✅ General analysis complete!</div>', unsafe_allow_html=True)

        # Desired Role Input
        desired_role = st.text_input("🎯 Want to aim for a specific role? (e.g., Data Analyst, ML Engineer)")

        if desired_role:
            with st.spinner("🧠 Evaluating resume for your target job role..."):
                role_analysis = analyze_resume_with_role(resume_text, desired_role)

            if role_analysis:
                st.markdown("## 🎯 Targeted Job Role Analysis")
                tab4, tab5, tab6, tab7 = st.tabs(["📈 ATS Score", "📉 Missing Skills", "🎓 Courses", "🛠 Resume Tips"])
                score, missing, course_suggest, role_tips = "", "", "", ""

                if "[ATS Score]" in role_analysis:
                    sections = role_analysis.split("[")
                    for section in sections:
                        if section.startswith("ATS Score]"):
                            score = section.replace("ATS Score]", "").strip()
                        elif section.startswith("Missing Skills]"):
                            missing = section.replace("Missing Skills]", "").strip()
                        elif section.startswith("Courses/Certifications]"):
                            course_suggest = section.replace("Courses/Certifications]", "").strip()
                        elif section.startswith("Improvement Tips]"):
                            role_tips = section.replace("Improvement Tips]", "").strip()

                with tab4:
                    st.markdown("### 📈 ATS Score (Visualized)")
                    try:
                        numeric_score = int(score.split(":")[-1].strip().replace("/100", ""))
                        st.plotly_chart(render_ats_gauge(numeric_score), use_container_width=True)
                    except:
                        st.warning("⚠️ Couldn't parse ATS score. Showing raw result:")
                        st.text(score)

                with tab5:
                    st.markdown("### 📉 Role-Specific Missing Skills")
                    st.markdown(missing or "No gaps found.")

                with tab6:
                    st.markdown("### 🎓 Course/Certification Suggestions")
                    st.markdown(course_suggest or "No courses suggested.")

                with tab7:
                    st.markdown("### 🛠 Tips to Improve Resume for Target Role")
                    st.markdown(role_tips or "Looks good already!")

                st.markdown('<div class="success-banner">🎉 Tailored analysis done! Use this to improve & apply with confidence.</div>', unsafe_allow_html=True)
                st.balloons()
