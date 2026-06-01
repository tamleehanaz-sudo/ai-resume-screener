import streamlit as st
import PyPDF2
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

# --- 2. THEME & COLORS (Pink Theme Styling) ---
def local_css():
    st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(135deg, #ff9a9e 0%, #ff9a9e 100%); 
        color: #333333; 
    }
    div.stButton > button { 
        background-color: #d63384; color: white; border-radius: 15px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: none; font-weight: bold;
    }
    div.stButton > button:hover { transform: scale(1.02); background-color: #b8266d; }
    .stDataFrame { background: white; border-radius: 10px; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CV SCANNER (Email aur Phone nikalne ke liye) ---
def extract_info(text):
    # Email patterns ko scan karna
    email_list = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    # Phone numbers scan karna
    phone_list = re.findall(r'(\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})', text)
    
    email = email_list[0] if email_list else "Not Found"
    phone = phone_list[0] if phone_list else ""
    # WhatsApp ke liye sirf digits rakhna
    clean_phone = re.sub(r'\D', '', phone) 
    
    return email, clean_phone

# --- 4. LOGIN & SIGNUP ---
def auth_page():
    local_css()
    st.markdown("<h1 style='text-align: center; color: #d63384;'>🌸 AI Candidate Screener</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state['show_signup']:
            st.subheader("📝 Create New Account")
            u = st.text_input("New Username")
            p = st.text_input("New Password", type="password")
            if st.button("Sign Up ✨"):
                st.session_state['users_db'][u] = p
                st.success("Account Created! Please Login.")
                st.session_state['show_signup'] = False
                st.rerun()
            if st.button("Back to Login"):
                st.session_state['show_signup'] = False
                st.rerun()
        else:
            st.subheader("🔑 Secure Login")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Enter Dashboard 🚀"):
                if u in st.session_state['users_db'] and st.session_state['users_db'][u] == p:
                    st.session_state['is_logged_in'] = True
                    st.rerun()
                else: st.error("Ghalat details hain!")
            if st.button("No account? Sign Up"):
                st.session_state['show_signup'] = True
                st.rerun()

# --- 5. MAIN HR DASHBOARD ---
def dashboard():
    local_css()
    st.sidebar.title("HR Admin Panel ⚙️")
    if st.sidebar.button("Logout 🚪"):
        st.session_state['is_logged_in'] = False
        st.rerun()

    # User yahan se criteria set karega
    pass_score = st.sidebar.slider("Min Selection Score (%)", 0, 100, 50)
    skills_in = st.sidebar.text_area("Keywords (Skills)", "Python, SQL, React")
    REQUIRED = [s.strip().lower() for s in skills_in.split(",") if s.strip()]

    st.markdown("<h1 style='color: #d63384;'>🎀 Recruitment Portal</h1>", unsafe_allow_html=True)
    
    files = st.file_uploader("Upload Resumes (PDFs)", type="pdf", accept_multiple_files=True)

    if files:
        results = []
        for f in files:
            # TRY-EXCEPT BLOCK: Corrupt PDF se app ko crash hone se bacha raha hai
            try:
                pdf = PyPDF2.PdfReader(f)
                text = "".join([p.extract_text() or "" for p in pdf.pages])
                email, phone = extract_info(text)
                
                # Score check karne ki logic
                found = [s for s in REQUIRED if s in text.lower()]
                score = (len(found) / len(REQUIRED)) * 100 if REQUIRED else 0
                
                results.append({
                    "Name": f.name, "Score": round(score, 1),
                    "Status": "✅ Selected" if score >= pass_score else "❌ Rejected",
                    "Email": email, "Phone": phone, "Skills Found": ", ".join(found)
                })
            except Exception as e:
                # Agar kisi ek file mein "EOF marker not found" jaisa error aaye toh app crash nahi hogi
                st.warning(f"⚠️ {f.name} ko read nahi kiya ja saka. (Corrupt or Invalid PDF)")

        # Agar kam se kam ek file sahi se process hui ho toh dashboard dikhao
        if results:
            df = pd.DataFrame(results)
            # Visual Graph
            st.plotly_chart(px.bar(df, x="Name", y="Score", color="Status", 
                                   color_discrete_map={"✅ Selected": "#d63384", "❌ Rejected": "#ff9a9e"}))
            st.dataframe(df, use_container_width=True)

            # --- OUTREACH SECTION (Anti-Spam Messages) ---
            st.divider()
            st.subheader("✉️ Fast-Track Contact")
            sel_name = st.selectbox("Choose Candidate", df["Name"].unique())
            user_row = df[df["Name"] == sel_name].iloc[0]

            col_a, col_b = st.columns(2)
            with col_a:
                target_mail = st.text_input("Candidate Email", user_row["Email"])
                target_wa = st.text_input("WhatsApp (Numbers Only)", user_row["Phone"])
            
            with col_b:
                # Har email ka subject alag hoga taaki spam filters na pakrein
                email_subject = f"Application Update for {sel_name}"
                
                # Personalized Message Logic
                if "✅" in user_row["Status"]:
                    msg_body = f"Dear {sel_name},\n\nI hope you are well. We have reviewed your application and we are pleased to shortlist you for the next round. Our team will contact you soon for an interview schedule.\n\nRegards,\nHR Team"
                else:
                    msg_body = f"Dear {sel_name},\n\nThank you for applying. After reviewing your profile, we regret to inform you that we are moving forward with other candidates. We wish you the best for your future.\n\nRegards,\nHR Team"

                final_msg = st.text_area("Custom Message", msg_body, height=150)
                
                b1, b2 = st.columns(2)
                with b1:
                    st.link_button("📱 WhatsApp", f"https://wa.me/{target_wa}?text={quote(final_msg)}")
                with b2:
                    st.link_button("📧 Send Email", f"mailto:{target_mail}?subject={quote(email_subject)}&body={quote(final_msg)}")
        else:
            st.error("Upload ki gayi files mein se koi bhi sahi PDF nahi thi.")

# --- APP START ---
if st.session_state['is_logged_in']:
    dashboard()
else:
    auth_page()
