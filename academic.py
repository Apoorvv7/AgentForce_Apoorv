import streamlit as st
import pandas as pd
import json
import plotly.figure_factory as ff
import datetime
import random
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Load Data ---
courses_df = pd.read_csv("data/courses.csv")
projects_data = json.load(open("data/projects.json", "r", encoding="utf-8"))
research_df = pd.read_csv("data/research.csv")
tips_data = json.load(open("data/tips.json", "r", encoding="utf-8"))

# --- Streamlit Setup ---
st.set_page_config(page_title="Academic Planner AI", layout="wide")
st.title("🎓 Academic Planner AI ")

# --- Helper Functions ---
def get_user_name():
    if "name" not in st.session_state:
        st.session_state.name = ""
    st.session_state.name = st.text_input("Your Name", value=st.session_state.name)
    return st.session_state.name

def get_current_courses():
    if "courses_taken" not in st.session_state:
        st.session_state.courses_taken = []
    courses_str = st.text_area(
        "Courses Already Taken (comma separated)",
        value=", ".join(st.session_state.courses_taken)
    )
    st.session_state.courses_taken = [c.strip() for c in courses_str.split(",") if c.strip()]
    return st.session_state.courses_taken

def get_career_goal():
    if "career_goal" not in st.session_state:
        st.session_state.career_goal = "AI Researcher"
    st.session_state.career_goal = st.selectbox(
        "Career Goal",
        ["AI Researcher", "Web Developer", "Cybersecurity Engineer", "Data Scientist"],
        index=["AI Researcher", "Web Developer", "Cybersecurity Engineer", "Data Scientist"].index(st.session_state.career_goal)
    )
    return st.session_state.career_goal

def get_academic_interests():
    if "interests" not in st.session_state:
        st.session_state.interests = []
    st.session_state.interests = st.multiselect(
        "Academic Interests",
        ["Machine Learning", "Computer Vision", "Natural Language Processing", "Web Development", "Cybersecurity"],
        default=st.session_state.interests
    )
    return st.session_state.interests

# --- Inputs ---
name = get_user_name()
degree = st.selectbox("Degree Program", ["B.Tech CSE", "B.Sc Physics", "M.Sc Mathematics", "Other"])
year = st.selectbox("Current Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
courses_taken = get_current_courses()
career_goal = get_career_goal()
interests = get_academic_interests()
time_available = st.slider("Weekly Time Available (in hours)", 5, 40, 15)

# --- Recommended Courses ---
if st.button("Generate Plan"):
    recommended_courses = courses_df[
        (courses_df['year'] == int(year[0])) & (courses_df['career_goal'] == career_goal)
    ]['course_name'].tolist()
    recommended_courses = [c for c in recommended_courses if c.strip() not in courses_taken]

    st.subheader("📚 Recommended Courses")
    if recommended_courses:
        for course in recommended_courses:
            st.write(f"- {course}")
    else:
        st.write("No new courses found for your selection.")

    # --- Project Ideas ---
    st.subheader("🧪 Project Ideas")
    project_list = []
    for interest in interests:
        if interest in projects_data:
            project_list.extend(projects_data[interest])
    if project_list:
        st.write(f"- {random.choice(project_list)}")
    else:
        st.write("No project ideas found for your interests.")

    # --- Research Guidance ---
    st.subheader("🔬 Research Guidance")
    research_list = research_df[research_df['topic'].isin(interests)]
    if not research_list.empty:
        for _, row in research_list.iterrows():
            st.write(f"- [{row['title']}]({row['link']})")
    else:
        st.write("No research papers found for your interests.")

# --- Smart Weekly Schedule ---
st.subheader("🗓 Smart Weekly Schedule (AI-Like)")

if "task_data" not in st.session_state:
    st.session_state.task_data = []

num_tasks = st.number_input("Number of tasks/projects to plan", min_value=1, max_value=10, value=len(st.session_state.task_data) or 3, step=1)

while len(st.session_state.task_data) < num_tasks:
    st.session_state.task_data.append({"name": "", "priority": "Medium", "deadline": datetime.date.today() + datetime.timedelta(days=7)})

st.session_state.task_data = st.session_state.task_data[:num_tasks]

for i in range(num_tasks):
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.session_state.task_data[i]["name"] = st.text_input(f"Task {i + 1} Name", value=st.session_state.task_data[i]["name"], key=f"task_{i}_name")
    with col2:
        st.session_state.task_data[i]["priority"] = st.selectbox(f"Priority {i + 1}", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.task_data[i]["priority"]), key=f"task_{i}_priority")
    with col3:
        st.session_state.task_data[i]["deadline"] = st.date_input(f"Deadline {i + 1}", value=st.session_state.task_data[i]["deadline"], key=f"task_{i}_deadline")

if st.button("Generate Smart Plan"):
    task_data = st.session_state.task_data
    total_hours = time_available
    schedule_data = []
    priority_weights = {"Low": 1, "Medium": 2, "High": 3}

    today = datetime.date.today()
    for task in task_data:
        days_left = max((task["deadline"] - today).days, 1)
        urgency_factor = max(1, (14 - days_left) / 14)
        task["weight"] = priority_weights[task["priority"]] * urgency_factor

    total_weight = sum(t["weight"] for t in task_data)

    for task in task_data:
        allocated_hours = round((task["weight"] / total_weight) * total_hours, 1)
        daily_hours = round(allocated_hours / 7, 2)
        task["allocated_hours"] = allocated_hours
        task["daily_hours"] = daily_hours

    start_hour = 8
    for day_index, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        date = today + datetime.timedelta(days=day_index)
        current_time = start_hour
        for task in task_data:
            if task["daily_hours"] > 0:
                start_dt = datetime.datetime.combine(date, datetime.time(int(current_time), int((current_time % 1) * 60)))
                end_dt = start_dt + datetime.timedelta(hours=task["daily_hours"])
                schedule_data.append(dict(Task=task["name"], Start=start_dt, Finish=end_dt, Resource=task["priority"]))
                current_time += task["daily_hours"] + 0.5

    fig = ff.create_gantt(schedule_data, index_col='Resource', show_colorbar=False, group_tasks=True, showgrid_x=True, showgrid_y=True, height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🤖 AI Reasoning Behind This Plan")
    reasoning = "\n".join([f"- **{t['name']}**: {t['allocated_hours']} hrs/week (Priority: {t['priority']}, Deadline: {t['deadline']}, Daily: {t['daily_hours']} hrs)" for t in task_data])
    st.write(reasoning)

    # --- PDF Export ---
    def export_schedule_to_pdf(schedule_data, reasoning, filename="schedule.pdf"):
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph("Academic Schedule", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Reasoning:", styles["Heading2"]))
        elements.append(Paragraph(reasoning, styles["Normal"]))
        elements.append(Spacer(1, 12))

        table_data = [["Task", "Start", "Finish", "Resource"]]
        for row in schedule_data:
            table_data.append([row.get("Task", ""), str(row.get("Start", "")), str(row.get("Finish", "")), row.get("Resource", "")])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        doc.build(elements)
        return filename

    pdf_path = export_schedule_to_pdf(schedule_data, reasoning)
    with open(pdf_path, "rb") as f:
        st.download_button(label="📄 Download Smart Schedule PDF", data=f, file_name="smart_schedule.pdf", mime="application/pdf")

# --- Tips ---
st.subheader("💡 Tips & Resources")
if career_goal in tips_data:
    for tip in tips_data[career_goal]:
        st.write(f"- {tip}")
else:
    st.write("No tips available for this career goal.")





