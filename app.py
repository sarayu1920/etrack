
import os
import streamlit as st
from google import genai
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import json


# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="ETrack - Education Tracker", page_icon="📚", layout="wide")

# ── API Key ───────────────────────────────────────────────────

api_key= os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)

# ── Data Storage ──────────────────────────────────────────────
DATA_FILE = "study_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ── Sidebar Navigation ────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/graduation-cap.png", width=80)
st.sidebar.title("📚 ETrack")
st.sidebar.markdown("*AI-Powered Education Tracker*")
page = st.sidebar.radio("Navigate", ["🏠 Home", "➕ Log Study", "📊 Progress", "🤖 AI Assistant", "🎯 Goals"])

# ── HOME PAGE ─────────────────────────────────────────────────
if page == "🏠 Home":
    st.title("Welcome to ETrack! 👋")
    st.markdown("### Your AI-Powered Personal Education Tracker")

    col1, col2, col3 = st.columns(3)
    data = load_data()
    total_sessions = len(data)
    total_hours = sum(d["duration"] for d in data) / 60 if data else 0
    subjects = len(set(d["subject"] for d in data)) if data else 0

    col1.metric("📖 Total Sessions", total_sessions)
    col2.metric("⏱️ Total Hours Studied", f"{total_hours:.1f}")
    col3.metric("📚 Subjects Tracked", subjects)

    st.markdown("---")
    st.markdown("""
    ### What can ETrack do for you?
    - ➕ **Log your study sessions** with subject, topic and duration
    - 📊 **Visualize your progress** with beautiful charts
    - 🤖 **Get AI-powered study tips** from Gemini
    - 🎯 **Set and track your study goals**
    """)

# ── LOG STUDY PAGE ────────────────────────────────────────────
elif page == "➕ Log Study":
    st.title("➕ Log a Study Session")
    st.markdown("Track what you studied today!")

    with st.form("study_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("📚 Subject", ["Mathematics", "Science", "English", "History", "Geography", "Computer Science", "Physics", "Chemistry", "Biology", "Other"])
            topic = st.text_input("📝 Topic Studied", placeholder="e.g. Quadratic Equations")
        with col2:
            duration = st.slider("⏱️ Duration (minutes)", 10, 300, 60)
            study_date = st.date_input("📅 Date", value=date.today())
        
        mood = st.select_slider("😊 How was your session?", options=["😴 Tired", "😐 Okay", "🙂 Good", "😊 Great", "🔥 Excellent"])
        notes = st.text_area("📓 Notes (optional)", placeholder="What did you learn today?")
        submitted = st.form_submit_button("✅ Save Session", use_container_width=True)

        if submitted:
            if topic == "":
                st.error("Please enter a topic!")
            else:
                data = load_data()
                data.append({
                    "subject": subject,
                    "topic": topic,
                    "duration": duration,
                    "date": str(study_date),
                    "mood": mood,
                    "notes": notes
                })
                save_data(data)
                st.success(f"✅ Session logged! You studied {subject} for {duration} minutes!")
                st.balloons()

# ── PROGRESS PAGE ─────────────────────────────────────────────
elif page == "📊 Progress":
    st.title("📊 Your Study Progress")
    data = load_data()

    if not data:
        st.info("No study sessions logged yet! Go to 'Log Study' to add your first session.")
    else:
        df = pd.DataFrame(data)

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df, names="subject", values="duration", title="⏱️ Time Spent per Subject")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            subject_time = df.groupby("subject")["duration"].sum().reset_index()
            fig2 = px.bar(subject_time, x="subject", y="duration", title="📚 Study Time by Subject (mins)", color="subject")
            st.plotly_chart(fig2, use_container_width=True)

        df["date"] = pd.to_datetime(df["date"])
        daily = df.groupby("date")["duration"].sum().reset_index()
        fig3 = px.line(daily, x="date", y="duration", title="📈 Daily Study Time Trend", markers=True)
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("### 📋 All Sessions")
        st.dataframe(df[["date", "subject", "topic", "duration", "mood"]].sort_values("date", ascending=False), use_container_width=True)

# ── AI ASSISTANT PAGE ─────────────────────────────────────────
elif page == "🤖 AI Assistant":
    st.title("🤖 AI Study Assistant")
    st.markdown("Powered by **Google Gemini** ✨")

    data = load_data()
    if data:
        df = pd.DataFrame(data)
        summary = df.groupby("subject")["duration"].sum().to_dict()
        context = f"Student's study data: {summary}"
    else:
        context = "Student has no study sessions logged yet."

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask me anything about your studies! 💬")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        prompt = f"""You are ETrack's AI Study Assistant. Help students improve their learning.
        {context}
        Student asks: {user_input}
        Give helpful, encouraging, and specific study advice. Keep it concise and friendly."""

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.models.generate_content(model="models/gemini-2.5-flash", contents=prompt)
                reply = response.text
                st.write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ── GOALS PAGE ────────────────────────────────────────────────
elif page == "🎯 Goals":
    st.title("🎯 Study Goals")
    st.markdown("Set your weekly study targets!")

    GOALS_FILE = "goals_data.json"

    def load_goals():
        if os.path.exists(GOALS_FILE):
            with open(GOALS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_goals(goals):
        with open(GOALS_FILE, "w") as f:
            json.dump(goals, f)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Set Weekly Goal")
        goal_subject = st.selectbox("Subject", ["Mathematics", "Science", "English", "History", "Computer Science", "Physics", "Chemistry", "Biology"])
        goal_hours = st.number_input("Target Hours per Week", min_value=1, max_value=40, value=5)
        if st.button("💾 Save Goal", use_container_width=True):
            goals = load_goals()
            goals[goal_subject] = goal_hours
            save_goals(goals)
            st.success(f"Goal set! Study {goal_hours} hours of {goal_subject} this week! 💪")

    with col2:
        st.markdown("### Your Saved Goals")
        goals = load_goals()
        if goals:
            for subject, hours in goals.items():
                st.info(f"📚 {subject}: {hours} hours/week")
        else:
            st.info("No goals set yet!")

    st.markdown("---")
    st.markdown("### 📊 This Week's Progress vs Goals")
    data = load_data()
    if data:
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        this_week = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
        if not this_week.empty:
            weekly = (this_week.groupby("subject")["duration"].sum() / 60).to_dict()
            goals = load_goals()
            if goals:
                comparison = []
                for subject, target in goals.items():
                    actual = weekly.get(subject, 0)
                    comparison.append({"Subject": subject, "Target Hours": target, "Actual Hours": round(actual, 1)})
                comp_df = pd.DataFrame(comparison)
                fig = px.bar(comp_df, x="Subject", y=["Target Hours", "Actual Hours"], barmode="group", title="Target vs Actual Study Hours")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Set some goals to see comparison!")
        else:
            st.info("No sessions this week yet!")
    else:
        st.info("No data yet! Start logging your sessions.")