# app.py - ScholarAI: The AI Career Co-Pilot (Final Version)
import streamlit as st
import requests
import json
import os
from io import BytesIO
from zipfile import ZipFile

# -------------------------
# Config
# -------------------------
LLAMA_URL = "http://localhost:11434/api/generate"
LLAMA_TIMEOUT = 300
USER_DATA_FILE = "user_data.json"
st.set_page_config(page_title="ScholarAI Co-Pilot", layout="wide")


# -------------------------
# Helper: Call local LLaMA (Ollama)
# -------------------------
def call_llama(prompt, max_tokens=2048, timeout=LLAMA_TIMEOUT, model="llama3"):
    payload = {"model": model, "prompt": prompt, "stream": False, "max_tokens": max_tokens}
    try:
        resp = requests.post(LLAMA_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.RequestException as e:
        st.error(f"Error contacting LLaMA: {e}. Is 'ollama serve' running?")
        return None
    except json.JSONDecodeError:
        st.error(f"Failed to decode LLaMA's response. Raw response: {resp.text}")
        return None


# -------------------------
# Data Persistence
# -------------------------
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return None


def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    st.toast("Progress saved!", icon="✅")


# -------------------------
# AI Generation Functions
# -------------------------
def generate_roadmap(major, goal, start_semester):
    # FIX APPLIED: Prompt is now highly specific for all list items to ensure correct data structures.
    prompt = f"""
    Act as an expert academic and career advisor for a university student.
    - Major: {major}
    - Career Goal: {goal}
    - Starting Semester: {start_semester}

    Generate a detailed, semester-by-semester roadmap for 4 semesters. For EACH semester, provide:
    1.  courses: A list of objects, where each object has a 'name' key (e.g., [{{"name": "Intro to AI"}}]).
    2.  certifications: A list of 1-2 relevant online certifications, each with a 'name' and 'url'.
    3.  project: A dictionary with a 'title' and a 'description' for a practical project.
    4.  papers: A list of 2 relevant academic papers, each with a 'title' and a 'url' (e.g., to arXiv or ACM).
    5.  research_skill: A string describing a specific research skill to develop.

    Return the response ONLY as a single, minified, valid JSON object with a root key "roadmap" which is a list of semester objects.
    """
    response_text = call_llama(prompt, model="llama3:8b-instruct-q8_0")
    if not response_text: return None
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0: raise ValueError("No JSON object found")
        return json.loads(response_text[json_start:json_end])
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"AI failed to generate a valid plan. Please try again. Error: {e}")
        st.text_area("LLM Raw Output:", response_text, height=200)
        return None


def generate_project_plan(project_title):
    # FIX APPLIED: Prompt now asks for simple strings in lists to avoid TypeErrors.
    prompt = f"""
    Based on the project idea: '{project_title}', create a detailed project plan for a student. Include:
    1.  key_features: A list of 3-5 simple strings for the core MVP features.
    2.  tech_stack: A list of simple strings for recommended technologies.
    3.  milestones: A list of simple strings for the step-by-step milestones.
    4.  repo_structure: A dictionary representing the file/folder structure (e.g., {{"app.py": "", "templates/": {{"index.html": ""}}}}).

    Return the response ONLY as a single, minified, valid JSON object.
    """
    response_text = call_llama(prompt)
    if not response_text: return None
    try:
        # FIX APPLIED: Robust JSON extraction to handle conversational text from the LLM.
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the response")

        json_str = response_text[json_start:json_end]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Failed to generate project plan. Error: {e}")
        st.text_area("LLM Raw Output:", response_text, height=150)
        return None


def generate_weekly_nudge(user_data):
    prompt = f"""
    Here is a student's progress on their roadmap: {json.dumps(user_data)}.

    Generate a concise, encouraging weekly 'nudge' message in markdown. The message should:
    1.  Briefly celebrate a recently completed item if any.
    2.  Suggest 1-2 concrete, achievable goals for this week from their 'Not Started' items.
    3.  Offer a motivational tip related to their main career goal: {user_data['profile']['goal']}.
    """
    return call_llama(prompt, max_tokens=500)


def generate_structured_notes(raw_notes):
    prompt = f"""
    You are an expert study assistant. Reorganize and enhance the following raw notes into structured markdown.
    - Create a clear structure with headings and subheadings.
    - Bold all key terms.
    - At the end, add a "Key Takeaways" section with a bulleted list.
    Raw Notes: --- {raw_notes} ---
    """
    return call_llama(prompt, max_tokens=1000)


# -------------------------
# UI Rendering Functions
# -------------------------
def render_setup_page():
    st.header("Welcome to your AI Career Co-Pilot 🚀")
    st.markdown(
        "Let's set up your personalized roadmap to success. This will generate a multi-semester plan tailored to your goals.")
    with st.form("setup_form"):
        name = st.text_input("Your Name")
        major = st.text_input("Your Major (e.g., Computer Science)")
        goal = st.text_input("Your Career Goal (e.g., Machine Learning Engineer)")
        start_semester = st.text_input("Your Current or Starting Semester (e.g., Fall 2025)")
        submitted = st.form_submit_button("Generate My Roadmap")

        if submitted and all([name, major, goal, start_semester]):
            with st.spinner("Your AI Co-Pilot is building your multi-year strategy... This may take a moment."):
                roadmap_data = generate_roadmap(major, goal, start_semester)
            if roadmap_data:
                full_data = {
                    "profile": {"name": name, "major": major, "goal": goal},
                    "roadmap": roadmap_data.get("roadmap", [])
                }
                for semester in full_data["roadmap"]:
                    for key, val in semester.items():
                        if isinstance(val, list) and val and isinstance(val[0], dict):
                            for item in val: item['completed'] = False
                        elif isinstance(val, dict):
                            val['completed'] = False
                save_user_data(full_data)
                st.session_state.user_data = full_data
                st.success("Your roadmap is ready!")
                st.rerun()


def render_dashboard():
    data = st.session_state.user_data
    profile = data.get("profile", {})
    st.title(f"👋 Welcome back, {profile.get('name', 'Student')}!")
    st.subheader(f"Your Goal: {profile.get('goal', 'N/A')}")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🗺️ My Roadmap", "📝 Notes Assistant", "⚙️ Settings"])

    with tab1:
        if st.button("✨ Get My Weekly Nudge"):
            with st.spinner("Generating your focus for the week..."):
                nudge = generate_weekly_nudge(data)
                st.info(nudge)

        for i, semester in enumerate(data.get("roadmap", [])):
            with st.expander(f"### {semester.get('semester', 'Unnamed Semester')}", expanded=(i == 0)):
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("#### 🎓 Courses")
                    for j, course in enumerate(semester.get('courses', [])):
                        is_done = st.checkbox(
                            course['name'], value=course.get('completed', False), key=f"sem{i}_course{j}"
                        )
                        if is_done != course.get('completed', False):
                            st.session_state.user_data['roadmap'][i]['courses'][j]['completed'] = is_done
                            save_user_data(st.session_state.user_data)
                with cols[1]:
                    st.markdown("#### 📜 Certifications")
                    for j, cert in enumerate(semester.get('certifications', [])):
                        is_done = st.checkbox(
                            f"[{cert['name']}]({cert['url']})", value=cert.get('completed', False),
                            key=f"sem{i}_cert{j}"
                        )
                        if is_done != cert.get('completed', False):
                            st.session_state.user_data['roadmap'][i]['certifications'][j]['completed'] = is_done
                            save_user_data(st.session_state.user_data)

                st.markdown("#### 🛠️ Project")
                project = semester.get('project', {})
                proj_cols = st.columns([0.8, 0.2])
                with proj_cols[0]:
                    is_done = st.checkbox(
                        f"**{project.get('title', '')}**: {project.get('description', '')}",
                        value=project.get('completed', False), key=f"sem{i}_project"
                    )
                    if is_done != project.get('completed', False):
                        st.session_state.user_data['roadmap'][i]['project']['completed'] = is_done
                        save_user_data(st.session_state.user_data)
                with proj_cols[1]:
                    if st.button("Plan Project", key=f"plan_proj_{i}"):
                        st.session_state.selected_project = project.get('title')

                if st.session_state.get('selected_project') == project.get('title'):
                    with st.container(border=True):
                        st.markdown(f"#### Planning: {project.get('title')}")
                        plan = generate_project_plan(project.get('title'))
                        if plan:
                            st.write("**Key Features:**", ", ".join(plan.get('key_features', [])))
                            st.write("**Tech Stack:**", ", ".join(plan.get('tech_stack', [])))
                            st.write("**Milestones:**")
                            for m in plan.get('milestones', []): st.markdown(f"- {m}")

                            if st.button("Download Repo Structure", key=f"dl_repo_{i}"):
                                in_memory_zip = BytesIO()
                                with ZipFile(in_memory_zip, 'w') as zf:
                                    def add_to_zip(structure, path=""):
                                        for name, content in structure.items():
                                            current_path = os.path.join(path, name)
                                            if isinstance(content, dict):
                                                add_to_zip(content, current_path)
                                            else:
                                                zf.writestr(current_path, str(content))

                                    add_to_zip(plan.get('repo_structure', {}))
                                st.download_button(
                                    "Download .zip", data=in_memory_zip.getvalue(),
                                    file_name=f"{project.get('title').replace(' ', '_')}_scaffold.zip",
                                    mime="application/zip"
                                )
                        if st.button("Close Planner", key=f"close_planner_{i}"):
                            st.session_state.selected_project = None
                            st.rerun()

    with tab2:
        st.header("✍️ Notes Assistant")
        st.markdown(
            "Paste your raw notes from a lecture or paper, and the AI will structure and summarize them for you.")
        raw_notes = st.text_area("Paste Raw Notes Here:", height=250)
        if st.button("Structure My Notes"):
            if raw_notes:
                with st.spinner("AI is organizing your thoughts..."):
                    structured_notes = generate_structured_notes(raw_notes)
                    st.markdown("### Your Structured Notes")
                    st.markdown(structured_notes)
            else:
                st.warning("Please paste some notes first.")

    with tab3:
        st.header("⚙️ Settings")
        st.warning("This will delete your current roadmap and all progress!")
        if st.button("Reset and Start Over"):
            if os.path.exists(USER_DATA_FILE):
                os.remove(USER_DATA_FILE)
            st.session_state.clear()
            st.rerun()


# -------------------------
# Main App Logic
# -------------------------
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()

if st.session_state.user_data:
    render_dashboard()
else:
    render_setup_page()