import streamlit as st
import pypdf  # PyPDF2 ki jagah naya 'pypdf' use karein
import pandas as pd
import plotly.express as px
import io

# --- FUNCTION: Extract Text From PDF ---
def extract_text_from_pdf(file):
    text = ""
    try:
        # File stream ko dubara shuru se read karne ke liye reset karna
        file.seek(0) 
        pdf_reader = pypdf.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    except Exception as e:
        # Agar file kharab (corrupt) ho toh error alert return karein
        return None
    return text

# --- FUNCTION: AI Screening Logic ---
def screen_resume(text, required_skills):
    if not text:
        return [], 0.0
        
    text = text.lower()
    found_skills = []
    
    for skill in required_skills:
        clean_skill = skill.strip().lower()
        if clean_skill and clean_skill in text:
            found_skills.append(clean_skill.capitalize())
    
    # Score calculation
    score = (len(found_skills) / len(required_skills)) * 100 if required_skills else 0
    return found_skills, round(score, 2)

# --- UI CONFIGURATION ---
st.set_page_config(page_title="AI Resume Screener PRO", layout="wide", page_icon="🚀")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🤖 AI Resume Screening & Analytics System")
st.markdown("Automate your recruitment process with AI-powered skill matching.")
st.divider()

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    skills_input = st.text_area("Target Skills", "Python, SQL, Machine Learning, Data Analysis, Communication", help="Comma separated list of skills")
    REQUIRED_SKILLS = [s.strip() for s in skills_input.split(",") if s.strip()]
    
    threshold = st.slider("Pass Marks (Threshold %)", 0, 100, 50)
    
    st.divider()
    st.info("💡 **Pro Tip:** Ensure PDF files are text-searchable (not scanned images) for best results.")

# --- MAIN CONTENT: UPLOADER ---
uploaded_files = st.file_uploader("Upload Candidates' Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    results_list = []
    corrupt_files = []
    
    with st.status("Analyzing Resumes...", expanded=True) as status:
        for uploaded_file in uploaded_files:
            # 1. Extraction
            raw_text = extract_text_from_pdf(uploaded_file)
            
            # Agar file reading fail ho jaye (EOF marker error ya corruption)
            if raw_text is None:
                corrupt_files.append(uploaded_file.name)
                continue
                
            # 2. Screening
            matched, score = screen_resume(raw_text, REQUIRED_SKILLS)
            
            # 3. Status logic
            status_label = "Shortlisted" if score >= threshold else "Rejected"
            
            results_list.append({
                "Candidate Name": uploaded_file.name,
                "Match Score %": score,
                "Skills Found": ", ".join(matched) if matched else "None",
                "Status": status_label
            })
        status.update(label="Analysis Complete!", state="complete", expanded=False)

    # Agar koi kharab file upload hui ho toh warning dikhayein bina app crash kiye
    if corrupt_files:
        st.error(f"⚠️ Darj zail files kharab (corrupt) hain ya unka format theek nahi hai: {', '.join(corrupt_files)}")

    # Check karein agar kam se kam ek file sahi tarah process hui ho
    if results_list:
        # Convert to DataFrame
        df = pd.DataFrame(results_list)

        # --- DASHBOARD LAYOUT ---
        tab1, tab2 = st.tabs(["📊 Analytics Overview", "📄 Detailed Report"])

        with tab1:
            # Metrics Row
            m_col1, m_col2, m_col3 = st.columns(3)
            total_apps = len(df)
            shortlisted = len(df[df['Status'] == 'Shortlisted'])
            
            m_col1.metric("Total Resumes", total_apps)
            m_col2.metric("Shortlisted", shortlisted, delta=f"{shortlisted/total_apps*100:.1f}%" if total_apps > 0 else "0%")
            m_col3.metric("Avg Match Score", f"{df['Match Score %'].mean():.1f}%")

            st.divider()

            # Visualizations
            v_col1, v_col2 = st.columns([2, 1])
            
            with v_col1:
                st.subheader("Leaderboard")
                fig_bar = px.bar(df.sort_values("Match Score %", ascending=True), 
                                 x="Match Score %", y="Candidate Name", 
                                 color="Status", orientation='h',
                                 color_discrete_map={'Shortlisted': '#2ecc71', 'Rejected': '#e74c3c'},
                                 text="Match Score %")
                st.plotly_chart(fig_bar, use_container_width=True)

            with v_col2:
                st.subheader("Selection Ratio")
                fig_pie = px.pie(df, names='Status', color='Status',
                                 color_discrete_map={'Shortlisted': '#2ecc71', 'Rejected': '#e74c3c'},
                                 hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

        with tab2:
            st.subheader("Final Screening Table")
            st.dataframe(df, use_container_width=True)
            
            # CSV Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Report (CSV)",
                data=csv,
                file_name='screening_results.csv',
                mime='text/csv',
            )
    else:
        st.warning("Koi bhi sahi PDF file process nahi ho saki. Baraye meharbani files check kar ke dubara upload karein.")

else:
    # Placeholder when no files are uploaded
    st.warning("Awaiting file uploads... Please upload PDF resumes from the uploader above.")
    st.image("https://cdn-icons-png.flaticon.com/512/3342/3342137.png", width=100)
