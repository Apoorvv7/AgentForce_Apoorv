import streamlit as st
import pandas as pd

st.set_page_config(page_title="Academic Planner AI", layout="wide")

st.title("🎓 Academic Planner AI (Free Version)")

# --- User Inputs ---
name = st.text_input("Your Name")
degree = st.selectbox("Degree Program", ["B.Tech CSE", "B.Sc Physics", "M.Sc Mathematics", "Other"])
year = st.selectbox("Current Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
courses_taken = st.text_area("Courses Already Taken (comma separated)")
career_goal = st.selectbox("Career Goal", ["AI Researcher", "Web Developer", "Cybersecurity Engineer", "Data Scientist"])
interests = st.multiselect("Academic Interests", ["Machine Learning", "Computer Vision", "Natural Language Processing", "Web Development", "Cybersecurity"])
time_available = st.slider("Weekly Time Available (in hours)", 5, 40, 15)

if st.button("Generate Plan"):
    st.subheader("📚 Recommended Courses")
    st.write("This will come from courses.csv based on your inputs.")

    st.subheader("🧪 Project Ideas")
    st.write("This will come from projects.json based on your interests.")

    st.subheader("🔬 Research Guidance")
    st.write("This will come from research.csv or arXiv feed.")

    st.subheader("🗓 Weekly Schedule")
    st.write(f"We will create a schedule using {time_available} hrs/week.")

    st.subheader("💡 Tips & Resources")
    st.write("This will come from tips.json based on your career goal.")
