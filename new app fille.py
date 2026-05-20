import streamlit as st
import PyPDF2
from PyPDF2.errors import PdfReadError
import docx2txt
import pandas as pd
import re
import plotly.express as px
from urllib.parse import quote

# --- 1. SET PAGE CONFIG (Wide layout jaisa screen mein hai) ---
st.set_page_config(layout="wide", page_title="AI Candidate Screener")

if 'users_db' not in st.session_state:
    st.session_state['users_db'] = {'admin': '12345'}
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'show_signup' not in st.session_state:
    st.session_state['show_signup'] = False

# --- 2. ADVANCED CSS FOR MATCHING IMAGE UI ---
def local_css():
    st.markdown("""
    <style>
    /* Background Soft Pink Tint */
    .stApp { 
        background-color: #f6e6f1;
        color: #2b2b2b;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* LEFT SIDEBAR: Same as Image (Deep Pink / Reddish Gold Accents) */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #9b1c4b 0%, #d63384 100%) !important;
        border-right: 5px solid gold;
        box-shadow: 5px 0 20px rgba(0,0,0,0.2);
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* 3D Sidebar Title Shield */
    .sidebar-shield {
        background: linear-gradient(135deg, #1f3c6d 0%, #0d1b2a 100%);
        border: 3px solid gold;
        border-radius: 20px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* 3D Glass Cards (Main Panel Body) */
    .glass-card {
        background: white;
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255,255,255,0.8);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
        margin-bottom: 20px;
    }
    
    /* KPI Counter (42 Resumes Screened Look) */
    .kpi-badge {
        background: radial-gradient(circle, #ffffff 0%, #f9f0f6 100%);
        border: 2px solid #e83e8c;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(232,62,140,0.15);
    }
    
    /* Buttons 3D Pop-out Effect */
    div.stButton > button { 
        background: linear-gradient(135deg, #ff4bb4 0%, #d63384 100%) !important; 
        color: white !important; 
        border-radius: 12px !important; 
        border: none !important;
        box-shadow: 0 5px 15px rgba(214, 51, 132, 0.4);
        font-weight: bold;
        width: 100%;
        padding: 10px 20px !important;
    }
    div.stButton > button:hover { 
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(214, 51, 132, 0.6);
    }
    </style>
    """, unsafe_allow_html=True)

def extract_info(text):
    email_list = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone_list = re.findall(r'(\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})', text)
    email = email_list[0] if email_list else "Not Found"
    phone = phone_list[0] if phone_list else ""
    return email, re.sub(r'\D', '', phone)

# --- 3. AUTH PAGE ---
if not st.session_state['is_logged_in']:
    local_css()
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div class='glass-card' style='text-align:center;'>
                <h1 style='color:#d63384; margin-bottom:5px;'>AI CANDIDATE SCREENER</h1>
                <p style='color:#777; font-weight:bold;'>VIP HR PORTAL ACCESS</p>
            </div>
        """, unsafe_allow_html=True)
        
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("SECURE LOGIN 🚀"):
            if u in st.session_state['users_db'] and st.session_state['users_db'][u] == p:
                st.session_state['is_logged_in'] = True
                st.rerun()
            else: st.error("Access Denied!")
    st.stop()

# --- 4. MAIN VIP DASHBOARD ---
local_css()

# SIDEBAR (Same Content Placement as Image Left Column)
with st.sidebar:
    st.markdown("""
        <div class='sidebar-shield'>
            <h2 style='color:gold !important; margin:0; font-size:28px;'>AI</h2>
            <p style='color:white !important; margin:0; font-size:14px; font-weight:bold;'>Candidate Screener</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("LOGOUT 🚪"):
        st.session_state['is_logged_in'] = False
        st.rerun()
        
    st.markdown("<hr style='border-color:rgba(255,255,255,0.3);'>", unsafe_allow_html=True)
    st.markdown("### 🎯 Selection Rules")
    pass_score = st.slider("Min Selection Score (%)", 0, 100, 50)
    skills_in = st.text_area("Keywords (Skills)", "Python, SQL, React")
    REQUIRED = [s.strip().lower() for s in skills_in.split(",") if s.strip()]

# MAIN PANEL (Right Side Grid Layout)
st.markdown("<h2 style='color: #9b1c4b; letter-spacing: 1px;'>HR ADMIN PANEL</h2>", unsafe_allow_html=True)

files = st.file_uploader("Upload Resumes (PDF or Word Documents)", type=["pdf", "docx"], accept_multiple_files=True)

if files:
    results = []
    for f in files:
        text = ""
        try:
            if f.name.endswith('.pdf'):
                pdf = PyPDF2.PdfReader(f)
                text = "".join([p.extract_text() or "" for p in pdf.pages])
            elif f.name.endswith('.docx'):
                text = docx2txt.process(f)
            
            if text:
                email, phone = extract_info(text)
                found = [s for s in REQUIRED if s in text.lower()]
                score = (len(found) / len(REQUIRED)) * 100 if REQUIRED else 0
                
                results.append({
                    "Name": f.name, "Score": round(score, 1),
                    "Status": "✅ Selected" if score >= pass_score else "❌ Rejected",
                    "Email": email, "Phone": phone, "Skills Found": ", ".join(found)
                })
        except Exception:
            continue

    if results:
        df = pd.DataFrame(results)
        
        # Grid Structure like the Screenshot (Card on Left, Graph on Right)
        c1, c2 = st.columns([1.2, 2])
        
        with c1:
            st.markdown(f"""
                <div class='kpi-badge'>
                    <h5 style='color:#777; margin:0;'>CANDIDATE DASHBOARD</h5>
                    <h1 style='font-size:75px; color:#9b1c4b; margin:0; font-weight:900;'>{len(df)}</h1>
                    <p style='font-weight:bold; color:#d63384; margin:0;'>RESUMES SCREENED</p>
                </div>
            """, unsafe_allow_html=True)
            
        with c2:
            fig = px.bar(df, x="Name", y="Score", color="Status", 
                         title="SCORE OVERVIEW",
                         color_discrete_map={"✅ Selected": "#d63384", "❌ Rejected": "#ff9a9e"})
            fig.update_layout(
                plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#333', margin=dict(t=30, b=0, l=0, r=0), height=210
            )
            st.plotly_chart(fig, use_container_width=True)

        # Bottom Data Table Section
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Outreach System
        st.divider()
        st.subheader("✉️ Fast Outreach Center")
        sel_name = st.selectbox("Choose Candidate", df["Name"].unique())
        user_row = df[df["Name"] == sel_name].iloc[0]

        col_a, col_b = st.columns(2)
        with col_a:
            target_mail = st.text_input("Candidate Email", user_row["Email"])
            target_wa = st.text_input("WhatsApp (Numbers Only)", user_row["Phone"])
        with col_b:
            email_subject = f"Application Update for {sel_name}"
            msg_body = f"Dear {sel_name},\n\nWe reviewed your profile and you are {user_row['Status']}.\n\nRegards,\nHR Team"
            final_msg = st.text_area("Custom Message", msg_body, height=100)
            
            b1, b2 = st.columns(2)
            with b1: st.link_button("📱 WhatsApp", f"https://wa.me/{target_wa}?text={quote(final_msg)}")
            with b2: st.link_button("📧 Send Email", f"mailto:{target_mail}?subject={quote(email_subject)}&body={quote(final_msg)}")
