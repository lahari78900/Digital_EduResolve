import streamlit as st
import sqlite3
import uuid
import pandas as pd
from datetime import datetime

# --- 1. CHEERFUL STYLING ---
def apply_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #FDFCF0; }
        .stButton>button { background-color: #FF4B4B; color: white; border-radius: 25px; height: 3em; width: 100%; border: none; font-weight: bold; }
        .stButton>button:hover { background-color: #FF8383; }
        .stTextInput>div>div>input { border: 2px solid #4CAF50; border-radius: 12px; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 15px; border-left: 5px solid #FF4B4B; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
        .dispatch-console { background-color: #1e1e1e; color: #00FF00; padding: 15px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; border: 1px solid #333; }
        .notification-box { background-color: #E8F5E9; border-left: 5px solid #4CAF50; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('cms_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS complaints
                 (id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT,
                  subject TEXT, description TEXT, location TEXT, 
                  root_dept TEXT, days_suffering INTEGER, 
                  status TEXT, created_at TEXT, 
                  assigned_worker TEXT, student_rating INTEGER, student_emoji TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id TEXT, message TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

# --- 3. NOTIFICATION LOGIC ---
def trigger_notification(tid, email, name, message):
    conn = sqlite3.connect('cms_system.db')
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute("INSERT INTO notifications (ticket_id, message, timestamp) VALUES (?,?,?)", (tid, message, now))
    conn.commit()
    conn.close()
    st.session_state.last_dispatch = {"to": email, "name": name, "msg": message}

# --- 4. NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "welcome"
def navigate(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- 5. PAGE: WELCOME ---
def welcome_page():
    st.title("🌟 Welcome to Digital EduResolve")
    st.subheader("Your Campus, Your Voice, Our Responsibility.")
    st.markdown("""
    ### Hello there! 👋 
    We believe that a great learning environment starts with listening to its students. 
    Whether it's a technical glitch or a facility issue, we are here to bridge the gap.
    
    **How it works:**
    1. Verify your credentials.
    2. Describe your grievance with details.
    3. Track live updates until resolution by our **Help Desk**.
    """)
    st.write("---")
    if st.button("Get Started ➡️"): navigate("credentials")

# --- 6. PAGE: CREDENTIALS ---
def credentials_page():
    st.title("Let's get to know you!")
    with st.form("user_identity_form"):
        name = st.text_input("Your Name", placeholder="e.g. John Doe")
        email = st.text_input("Your Email", placeholder="e.g. student@college.edu")
        phone = st.text_input("Phone Number", placeholder="e.g. 9876543210")
        st.write("---")
        col_back, col_next = st.columns([1, 1])
        if col_back.form_submit_button("⬅️ Back"): navigate("welcome")
        if col_next.form_submit_button("Next ➡️"):
            if "@" not in email or "." not in email: st.error("Please enter a valid email address! 📧")
            elif not phone.isdigit() and phone != "": st.error("Phone number must contain only numbers! 🔢")
            else:
                st.session_state.user_data = {"name": name if name else "Anonymous", "email": email, "phone": phone}
                navigate("complaint_form")

# --- 7. PAGE: COMPLAINT FORM ---
def complaint_form():
    st.title("📝 What's on your mind?")
    with st.form("grievance_form"):
        sub = st.text_input("Subject", placeholder="e.g. Leaking tap, WiFi issue")
        loc = st.text_input("Location", placeholder="e.g. Library, 1st Floor")
        dept = st.selectbox("Category", ["General Help Desk", "Plumbing", "Electrical", "IT Support", "Academic", "Others"])
        days = st.number_input("Days suffering?", min_value=1)
        desc = st.text_area("Detailed Description", placeholder="Please describe the issue...")
        st.write("---")
        col_back, col_submit = st.columns([1, 1])
        if col_back.form_submit_button("⬅️ Back"): navigate("credentials")
        if col_submit.form_submit_button("Submit Ticket🚀"):
            if sub and desc:
                cid = str(uuid.uuid4())[:8].upper()
                conn = sqlite3.connect('cms_system.db')
                conn.execute("INSERT INTO complaints (id, name, email, phone, subject, description, location, root_dept, days_suffering, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                             (cid, st.session_state.user_data['name'], st.session_state.user_data['email'], st.session_state.user_data['phone'], sub, desc, loc, dept, days, "Pending", datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                trigger_notification(cid, st.session_state.user_data['email'], st.session_state.user_data['name'], "Ticket Received by Help Desk.")
                st.session_state.last_id = cid
                st.balloons(); st.success(f"Ticket Submitted! ID: {cid}")
            else: st.error("Please fill in the Subject and Description!")
    if st.button("Track Progress"): navigate("tracking")

# --- 8. PAGE: TRACKING ---
def tracking_page():
    st.title("Track Your Request")
    tid = st.text_input("Enter Ticket ID", value=st.session_state.get('last_id', ""), placeholder="e.g. 4A2B9C")
    if tid:
        conn = sqlite3.connect('cms_system.db')
        df = pd.read_sql(f"SELECT * FROM complaints WHERE id='{tid}'", conn)
        if not df.empty:
            row = df.iloc[0]
            st.subheader(f"Current Status: {row['status']}")
            st.write("### 🔔 Update History")
            logs = pd.read_sql(f"SELECT message, timestamp FROM notifications WHERE ticket_id='{tid}' ORDER BY id DESC", conn)
            for _, log in logs.iterrows():
                st.markdown(f'<div class="notification-box"><b>[{log["timestamp"]}]</b>: {log["message"]}</div>', unsafe_allow_html=True)
            if row['assigned_worker']: st.info(f"🛠️ **Handled by:** {row['assigned_worker']}")
            if row['status'] == "Resolved" and not row['student_rating']:
                with st.form("feedback"):
                    st.markdown("### 🎈 Rate the Help Desk Resolution")
                    r = st.slider("Rating", 1, 5, 5); e = st.selectbox("Emoji", ["😊 Happy", "🤩 Awesome", "👍 Helpful"])
                    if st.form_submit_button("Submit Feedback ⭐"):
                        conn.execute("UPDATE complaints SET student_rating=?, student_emoji=? WHERE id=?", (r, e, tid))
                        conn.commit(); st.rerun()
        else: st.error("Ticket ID not found.")
    st.write("---")
    if st.button("Home"): navigate("welcome")

# --- 9. HELP DESK PORTAL ---
def help_desk_dashboard():
    st.title("🛠️ Help Desk Terminal")
    st.write("Managing on-site tickets and student support.")
    conn = sqlite3.connect('cms_system.db')
    df = pd.read_sql("SELECT * FROM complaints WHERE root_dept='General Help Desk' AND status!='Resolved'", conn)
    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"TICKET: {row['subject']} ({row['location']})"):
                st.write(f"**Description:** {row['description']}")
                agent = st.text_input("Agent Name", key=f"hd_{row['id']}")
                if st.button("Mark as Resolved ✅", key=f"hdb_{row['id']}"):
                    if agent:
                        conn.execute("UPDATE complaints SET status='Resolved', assigned_worker=? WHERE id=?", (agent, row['id']))
                        conn.commit()
                        trigger_notification(row['id'], row['email'], row['name'], f"Resolved by Help Desk Agent: {agent}")
                        st.rerun()
                    else: st.error("Enter Agent Name")
    else: st.info("Help Desk queue is clear!")
    render_dispatch_console()

# --- 10. ADMIN DASHBOARD ---
def admin_dashboard():
    st.title("🛡️ Admin Oversight")
    conn = sqlite3.connect('cms_system.db')
    df = pd.read_sql("SELECT * FROM complaints", conn)
    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tickets", len(df)); m2.metric("Pending", len(df[df['status'] == 'Pending'])); m3.metric("Resolved", len(df[df['status'] == 'Resolved']))
        for _, row in df.iterrows():
            with st.expander(f"[{row['status']}] {row['subject']}"):
                c1, c2 = st.columns(2)
                worker = c1.text_input("Staff", value=row['assigned_worker'] if row['assigned_worker'] else "", key=f"aw_{row['id']}")
                status = c2.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], index=["Pending", "In Progress", "Resolved"].index(row['status']), key=f"as_{row['id']}")
                if st.button("Save & Notify 🔔", key=f"ab_{row['id']}"):
                    conn.execute("UPDATE complaints SET status=?, assigned_worker=? WHERE id=?", (status, worker, row['id']))
                    conn.commit()
                    trigger_notification(row['id'], row['email'], row['name'], f"Your ticket is now {status}. Worker: {worker}")
                    st.rerun()
    render_dispatch_console()

def render_dispatch_console():
    if "last_dispatch" in st.session_state:
        st.write("---")
        st.write("📡 **Live Transmission Console**")
        d = st.session_state.last_dispatch
        st.markdown(f"""<div class="dispatch-console">
        >>> PUSHING UPDATE TO: {d['to']}<br>
        >>> MESSAGE: {d['msg']}<br>
        >>> STATUS: SENT ✅
        </div>""", unsafe_allow_html=True)

# --- MAIN ---
def main():
    st.set_page_config(page_title="EduResolve", layout="wide")
    init_db(); apply_styles()
    st.sidebar.markdown("### 🏢 EduResolve Nav")
    role = st.sidebar.selectbox("🔑 Access Role", ["🎓 Student View", "🛠️ Help Desk", "🛡️ Administrator"])
    if "Administrator" in role:
        if st.sidebar.text_input("PIN", type="password") == "admin123": admin_dashboard()
    elif "Help Desk" in role: help_desk_dashboard()
    else:
        pages = {"welcome": welcome_page, "credentials": credentials_page, "complaint_form": complaint_form, "tracking": tracking_page}
        pages[st.session_state.page]()

if __name__ == "__main__": main()