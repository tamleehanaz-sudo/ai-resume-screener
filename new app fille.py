import streamlit as st
import PyPDF2
from PyPDF2.errors import PdfReadError
import docx2txt
import pandas as pd
import re
import plotly.express as px
from urllib.parse import quote

# --- 1. SESSION STATE (Login handle karne ke liye) ---
if 'users_db' not in st.session_state:
    st.session_state['users_db'] = {'admin': '12345'}
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'show_signup' not in st.session_state:
    st.session_state['show_signup'] = False

# --- 2. ADVANCED 3D & GLASSMORPHISM THEME (Same as Image) ---
def local_css():
    st.markdown("""
    <style>
    /* Full App Background */
    .stApp { 
        background: radial-gradient(circle at 50% 50%, #ff9a9e 0%, #64b5f6 100%);
        color: #2b2b2b;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* VIP 3D Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(12px);
        border-right: 2px solid rgba(255, 255, 255, 0.5);
        box-shadow: 5px 0 25px rgba(0,0,0,0.1);
    }
    
    /* Glassmorphism Cards/Containers */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 8px 32px 0 rgba(214, 51, 132, 0.15);
    }
    
    /* 3D Shiny Buttons */
    div.stButton > button { 
        background: linear-gradient(135deg, #ff4bb4 0%, #d63384 100%); 
        color: white !important; 
        border-radius: 25px !important; 
        border: 1px solid rgba(255,255,255,0.4) !important;
        box-shadow: 0 6px 15px rgba(214, 51, 132, 0.4), inset 0 2px 4px rgba(255,255,255,0.4);
        font-weight: bold;
        font-size: 16px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { 
        transform: translateY(-3px); 
        box-shadow: 0 10px 20px rgba(214, 51, 132, 0.6);
        background: linear-gradient(135deg, #d63384 0%, #b8266d 100%);
    }
    
    /* Dataframe/Table styling */
    .stDataFrame { 
        background: rgba(255, 255, 255, 0.7) !important; 
        border-radius: 15px; 
        padding: 10px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
    }
    
    /* Main Dashboard Header Grid */
    .vip-header {
        background: rgba(255, 255, 255, 0.5);
        border-radius: 25px;
        padding: 20px;
        border: 2px solid gold;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CV SCANNER LOGIC ---
def extract_info(text):
    email_list = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone_list = re.findall(r'(\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})', text)
    
    email = email_list[0] if email_list else "Not Found"
    phone = phone_list[0] if phone_list else ""
    clean_phone = re.sub(r'\D', '', phone) 
    
    return email, clean_phone

# --- 4. AUTHENTICATION PAGE ---
def auth_page():
    local_css()
    st.markdown("""
        <div style='background: rgba(255,255,255,0.3); padding: 30px; border-radius: 30px; box-shadow: 0 20px 50px rgba(0,0,0,0.15); border: 2px solid rgba(255,255,255,0.5);'>
            <h1 style='text-align: center; color: #d63384; font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);'>👑 AI Candidate Screener</h1>
            <p style='text-align: center; font-weight: bold; color: #555;'>VIP Recruitment Edition</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("") # Gap dene ke liye
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state['show_signup']:
            st.markdown("<h3 style='color: #d63384;'>📝 Create VIP Account</h3>", unsafe_allow_html=True)
            u = st.text_input("Choose Username")
            p = st.text_input("Choose Password", type="password")
            if st.button("Sign Up ✨"):
                st.session_state['users_db'][u] = p
                st.success("Account Created! Login Now.")
                st.session_state['show_signup'] = False
                st.rerun()
            if st.button("Back"):
                st.session_state['show_signup'] = False
                st.rerun()
        else:
            st.markdown("<h3 style='color: #d63384;'>🔑 Secure Access</h3>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Enter Portal 🚀"):
                if u in st.session_state['users_db'] and st.session_state['users_db'][u] == p:
                    st.session_state['is_logged_in'] = True
                    st.rerun()
                else: st.error("Access Denied: Invalid Credentials!")
            if st.button("Request Account (Sign Up)"):
                st.session_state['show_signup'] = True
                st.rerun()

# --- 5. MAIN HR DASHBOARD ---
def dashboard():
    local_css()
    
    # Sidebar setup
    st.sidebar.markdown("<h2 style='color: #d63384; text-align:center;'>⚙️ SETTINGS</h2>", unsafe_allow_html=True)
    if st.sidebar.button("Logout Portal 🚪"):
        st.session_state['is_logged_in'] = False
        st.rerun()

    pass_score = st.sidebar.slider("Min Selection Score (%)", 0, 100, 50)
    skills_in = st.sidebar.text_area("Keywords (Skills to Search)", "Python, SQL, React")
    REQUIRED = [s.strip().lower() for s in skills_in.split(",") if s.strip()]
 
    #-----6 Main Top Banner (File Processing)
    st.markdown("""
        <div style='background: linear-gradient(135deg, #4b1248 0%, #f0c27b 100%); border-radius: 20px; padding: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.2); border: 2px solid #fff; margin-bottom: 25px;'>
            <h1 style='color: white; margin: 0; font-size: 2.5rem; text-shadow: 3px 3px 6px rgba(0,0,0,0.4); float: left;'>👑 AI CANDIDATE SCREENER</h1>
            <h3 style='color: #fff; margin: 5px 0 0 0; text-align: right; font-weight: 300;'>HR ADMIN PANEL</h3>
            <div style='clear: both;'></div>
        </div>
    """, unsafe_allow_html=True)
    
    files = st.file_uploader("Drag and Drop Resumes (PDF or Word)", type=["pdf", "docx"], accept_multiple_files=True)

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
            except Exception as e:
                st.warning(f"⚠️ {f.name} read nahi ho saki (File corrupt hai).")
                continue

        if results:
            df = pd.DataFrame(results)
            
#-------7 KPI Counter Badge (Skills matching & Scoring)
            st.markdown(f"""
                <div style='background: rgba(255,255,255,0.7); border-radius: 15px; padding: 15px; text-align: center; border-left: 5px solid #d63384; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);'>
                    <span style='font-size: 1.2rem; color: #555; font-weight: bold;'>TOTAL RESUMES PROCESSED: </span>
                    <span style='font-size: 2rem; color: #d63384; font-weight: 900; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>{len(df)}</span>
                </div>
            """, unsafe_allow_html=True)

#-------8 Visual 3D Styled Chart(Data Display)
            fig = px.bar(df, x="Name", y="Score", color="Status", 
                         title="CANDIDATE SCORE OVERVIEW",
                         color_discrete_map={"✅ Selected": "#d63384", "❌ Rejected": "#ff9a9e"})
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#333'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Interactive Table
            st.dataframe(df, use_container_width=True)

# ----9 OUTREACH SECTION --- (unique part of system)
            st.divider()
            st.markdown("<h3 style='color: #d63384;'>✉️ Fast Outreach Center</h3>", unsafe_allow_html=True)
            sel_name = st.selectbox("Choose Candidate", df["Name"].unique())
            user_row = df[df["Name"] == sel_name].iloc[0]

            col_a, col_b = st.columns(2)
            with col_a:
                target_mail = st.text_input("Candidate Email", user_row["Email"])
                target_wa = st.text_input("WhatsApp (With Country Code)", user_row["Phone"])
            
            with col_b:
                email_subject = f"Application Update for {sel_name}"
                if "✅" in user_row["Status"]:
                    msg_body = f"Dear {sel_name},\n\nI hope you are well. We have reviewed your application and we are pleased to shortlist you for the next round. Our team will contact you soon for an interview schedule.\n\nRegards,\nHR Team"
                else:
                    msg_body = f"Dear {sel_name},\n\nThank you for applying. After reviewing your profile, we regret to inform you that we are moving forward with other candidates. We wish you the best for your future.\n\nRegards,\nHR Team"

                final_msg = st.text_area("Custom Message", msg_body, height=130)
                
                b1, b2 = st.columns(2)
                with b1:
                    st.link_button("📱 WhatsApp", f"https://wa.me/{target_wa}?text={quote(final_msg)}")
                with b2:
                    st.link_button("📧 Send Email", f"mailto:{target_mail}?subject={quote(email_subject)}&body={quote(final_msg)}")
        else:
            st.error("❌ Koi bhi file process nahi ho saki.")

# --- APP START ---
if st.session_state['is_logged_in']:
    dashboard()
else:
    auth_page()
