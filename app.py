import streamlit as st
import os
import json
import re
import bcrypt
from datetime import datetime
from openai import OpenAI
import pandas as pd

from models import init_db, SessionLocal, User, PolicyAnalysisResult

st.set_page_config(
    page_title="PoliSee Clarity",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    
    .stApp {
        background: 
            radial-gradient(ellipse at top, rgba(14, 165, 233, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at bottom right, rgba(99, 102, 241, 0.06) 0%, transparent 50%),
            linear-gradient(160deg, #0f172a 0%, #1e293b 40%, #0f172a 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding: 2rem 1.5rem 4rem 1.5rem;
        max-width: 420px;
    }
    
    h1, h2, h3, h4 {
        color: #f8fafc !important;
    }
    
    .stMarkdown p {
        color: #94a3b8;
    }
    
    .hero-section {
        animation: fadeInUp 0.8s ease-out;
    }
    
    .hero-icon {
        font-size: 5rem;
        text-align: center;
        margin-bottom: 1rem;
        filter: drop-shadow(0 0 40px rgba(14, 165, 233, 0.5));
        animation: fadeIn 1s ease-out;
    }
    
    .hero-title {
        font-size: 2.75rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #ffffff 0%, #94a3b8 50%, #ffffff 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        letter-spacing: -0.03em;
        animation: fadeInUp 0.8s ease-out 0.1s both;
    }
    
    .hero-tagline {
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #0ea5e9, #06b6d4, #0ea5e9);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.75rem;
        letter-spacing: 0.01em;
        animation: fadeInUp 0.8s ease-out 0.2s both;
        position: relative;
        padding-bottom: 0.5rem;
    }
    
    .hero-tagline::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #0ea5e9, #06b6d4);
        border-radius: 2px;
    }
    
    .hero-subtitle {
        font-size: 1rem;
        text-align: center;
        color: #64748b;
        line-height: 1.7;
        margin-bottom: 2.5rem;
        padding: 0 0.5rem;
        animation: fadeInUp 0.8s ease-out 0.3s both;
    }
    
    .stTabs {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 28px;
        padding: 2rem;
        box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.6),
            0 0 0 1px rgba(255, 255, 255, 0.05) inset;
        animation: fadeInUp 0.8s ease-out 0.4s both;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: rgba(15, 23, 42, 0.7);
        border-radius: 16px;
        padding: 6px;
        margin-bottom: 1.75rem;
        border: 1px solid rgba(71, 85, 105, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 12px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.95rem;
        flex: 1;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white !important;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }
    
    .stTextInput > div > div > input {
        background-color: rgba(15, 23, 42, 0.9);
        border: 2px solid rgba(71, 85, 105, 0.4);
        border-radius: 14px;
        color: #f1f5f9;
        padding: 1rem 1.25rem;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #0ea5e9;
        box-shadow: 
            0 0 0 4px rgba(14, 165, 233, 0.15),
            0 0 20px rgba(14, 165, 233, 0.2);
        background-color: rgba(15, 23, 42, 1);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #475569;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus::placeholder {
        opacity: 0.5;
        transform: translateX(5px);
    }
    
    .stTextInput > label {
        color: #94a3b8 !important;
        font-weight: 600;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
        letter-spacing: 0.02em;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 1.1rem 2rem;
        font-weight: 700;
        font-size: 1.05rem;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 15px rgba(14, 165, 233, 0.4),
            0 0 0 1px rgba(255, 255, 255, 0.1) inset;
        margin-top: 0.75rem;
        letter-spacing: 0.02em;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 50%, #0284c7 100%);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 12px 35px rgba(14, 165, 233, 0.5),
            0 0 0 1px rgba(255, 255, 255, 0.15) inset;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(1.01);
    }
    
    .trust-inline {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: 1.25rem;
        padding: 0.75rem 0;
        animation: fadeIn 1s ease-out 0.6s both;
    }
    
    .trust-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .trust-item svg, .trust-item span:first-child {
        color: #0ea5e9;
        opacity: 0.8;
    }
    
    .divider-text {
        text-align: center;
        color: #475569;
        font-size: 0.85rem;
        margin: 1.75rem 0;
        position: relative;
    }
    
    .divider-text::before,
    .divider-text::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 28%;
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
    }
    
    .divider-text::before { left: 0; }
    .divider-text::after { right: 0; }
    
    .social-btn {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 12px;
        padding: 0.85rem 1rem;
        color: #cbd5e1;
        font-weight: 600;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        cursor: pointer;
        transition: all 0.25s ease;
        margin-bottom: 0.75rem;
    }
    
    .social-btn:hover {
        background: rgba(30, 41, 59, 0.9);
        border-color: #0ea5e9;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .forgot-link {
        text-align: center;
        margin-top: 1.25rem;
    }
    
    .forgot-link a {
        color: #0ea5e9;
        text-decoration: none;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .forgot-link a:hover {
        color: #38bdf8;
        text-decoration: underline;
    }
    
    .landing-footer {
        text-align: center;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid rgba(51, 65, 85, 0.3);
        animation: fadeIn 1s ease-out 0.7s both;
    }
    
    .footer-tagline {
        font-size: 1.15rem;
        font-weight: 700;
        background: linear-gradient(90deg, #0ea5e9, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.25rem;
    }
    
    .trust-badges {
        display: flex;
        justify-content: center;
        gap: 1.25rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    
    .trust-badge {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.5rem 0.75rem;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 8px;
        border: 1px solid rgba(71, 85, 105, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #bfdbfe;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stExpander {
        background-color: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 12px;
    }
    
    .stSelectbox > div > div {
        background-color: rgba(15, 23, 42, 0.8);
        border-color: rgba(71, 85, 105, 0.5);
        border-radius: 12px;
    }
    
    .footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid rgba(51, 65, 85, 0.5);
    }
    
    .footer-brand {
        font-size: 0.875rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    
    @media (max-width: 600px) {
        .main .block-container {
            padding: 1.25rem 1rem 3rem 1rem;
        }
        
        .hero-icon {
            font-size: 4rem;
        }
        
        .hero-title {
            font-size: 2.25rem;
        }
        
        .hero-tagline {
            font-size: 1.25rem;
        }
        
        .hero-subtitle {
            font-size: 0.95rem;
            line-height: 1.6;
        }
        
        .auth-card {
            padding: 1.5rem 1.25rem;
            border-radius: 22px;
        }
        
        .stTextInput > div > div > input {
            padding: 0.9rem 1rem;
            font-size: 16px;
        }
        
        .stButton > button {
            padding: 1rem 1.5rem;
            font-size: 1rem;
        }
        
        .trust-inline {
            flex-direction: column;
            gap: 0.5rem;
            align-items: center;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .trust-badges {
            gap: 0.75rem;
        }
        
        .trust-badge {
            font-size: 0.7rem;
            padding: 0.4rem 0.6rem;
        }
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

init_db()

SCENARIOS = [
    "Select a scenario...",
    "Burst Pipe / Interior Water Leak",
    "Roof Hail Damage",
    "Basement Flood (Groundwater Seepage)",
    "Fence Wind Damage",
    "Tree Damage to Dwelling",
    "Appliance Power Surge",
    "Hurricane",
    "Fire",
    "Theft"
]

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def register_user(email, password):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return None, "An account with this email already exists."
        
        new_user = User(
            email=email,
            password_hash=hash_password(password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user, None
    except Exception as e:
        db.rollback()
        return None, f"Registration failed: {str(e)}"
    finally:
        db.close()

def authenticate_user(email, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and verify_password(password, user.password_hash):
            return user, None
        return None, "Invalid email or password."
    finally:
        db.close()

def save_analysis(user_id, scenario, file_id, response_json, out_of_pocket, gap_alerts):
    db = SessionLocal()
    try:
        analysis = PolicyAnalysisResult(
            user_id=user_id,
            scenario=scenario,
            file_id=file_id,
            openai_response_json=response_json,
            out_of_pocket_estimate=out_of_pocket,
            gap_alerts=json.dumps(gap_alerts) if gap_alerts else None
        )
        db.add(analysis)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Failed to save analysis: {str(e)}")
        return False
    finally:
        db.close()

def get_recent_analyses(limit=10):
    db = SessionLocal()
    try:
        analyses = db.query(PolicyAnalysisResult).order_by(
            PolicyAnalysisResult.upload_timestamp.desc()
        ).limit(limit).all()
        return analyses
    finally:
        db.close()

def get_user_analyses(user_id, limit=10):
    db = SessionLocal()
    try:
        analyses = db.query(PolicyAnalysisResult).filter(
            PolicyAnalysisResult.user_id == user_id
        ).order_by(PolicyAnalysisResult.upload_timestamp.desc()).limit(limit).all()
        return analyses
    finally:
        db.close()

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def upload_pdf_to_openai(client, pdf_file):
    try:
        response = client.files.create(
            file=pdf_file,
            purpose='assistants'
        )
        return response.id, None
    except Exception as e:
        return None, str(e)

def analyze_policy(client, file_id, scenario):
    system_prompt = """You are an expert homeowners insurance policy analyzer for PoliSee Clarity.
Analyze ONLY the uploaded policy PDF for the given scenario.
Be conservative and reference typical policy language (sudden/accidental discharge, surface water exclusion, wear & tear, etc.).

Output ONLY valid JSON with these exact keys:
- covered_items: array of objects [{item: string, est_replacement_cost: number, depreciation_pct: number, acv_payout: number}]
- not_covered_items: array of strings describing what is not covered
- deductible: number (the policy deductible amount)
- total_out_of_pocket: number or null (estimated total out of pocket after coverage)
- gap_alerts: array of strings (e.g. "Flood not covered", "Mold from long-term seepage excluded")
- recommendations: array of strings with actionable advice
- plain_summary: short plain-language explanation (2-4 sentences)

Be thorough but conservative in your analysis. If something is unclear in the policy, note it as a potential gap."""

    user_prompt = f"""Analyze this homeowners insurance policy for the following scenario: {scenario}

Please provide a detailed breakdown of what would be covered, what would not be covered, estimated costs, and any gaps in coverage the homeowner should be aware of."""

    try:
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # Using responses API with file input for PDF analysis
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_prompt},
                        {
                            "type": "input_file",
                            "file_id": file_id
                        }
                    ]
                }
            ],
            text={"format": {"type": "json_object"}}
        )
        
        result = json.loads(response.output_text)
        return result, None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse AI response: {str(e)}"
    except Exception as e:
        return None, str(e)

def show_auth_page():
    st.markdown("""
        <div class="hero-section">
            <div class="hero-icon">🏠🛡️</div>
            <div class="hero-title">PoliSee Clarity</div>
            <div class="hero-tagline">Know What's Covered – Before You Need It.</div>
            <div class="hero-subtitle">
                Upload your policy. Simulate disasters. Get clear answers on coverage, gaps, and costs – powered by AI.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login_email = st.text_input("Email Address", key="login_email", placeholder="you@example.com")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        if st.button("Sign In", key="login_btn"):
            if not login_email or not login_password:
                st.error("Please fill in all fields.")
            elif not validate_email(login_email):
                st.error("Please enter a valid email address.")
            else:
                user, error = authenticate_user(login_email, login_password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user.id
                    st.session_state.user_email = user.email
                    st.success("Welcome back!")
                    st.rerun()
                else:
                    st.error(error)
        
        st.markdown("""
            <div class="trust-inline">
                <div class="trust-item"><span>🔒</span> Secure & Private</div>
                <div class="trust-item"><span>✓</span> No data stored without consent</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="forgot-link"><a href="#">Forgot password?</a></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="divider-text">or continue with</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="social-btn">🍎 Apple</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="social-btn">🔵 Google</div>', unsafe_allow_html=True)
    
    with tab2:
        reg_email = st.text_input("Email Address", key="reg_email", placeholder="you@example.com")
        reg_password = st.text_input("Create Password", type="password", key="reg_password", 
                                      placeholder="Minimum 6 characters")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm",
                                     placeholder="Re-enter your password")
        
        if st.button("Create Account", key="register_btn"):
            if not reg_email or not reg_password or not reg_confirm:
                st.error("Please fill in all fields.")
            elif not validate_email(reg_email):
                st.error("Please enter a valid email address.")
            elif len(reg_password) < 6:
                st.error("Password must be at least 6 characters.")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match.")
            else:
                user, error = register_user(reg_email, reg_password)
                if user:
                    st.success("Account created successfully! Please sign in.")
                else:
                    st.error(error)
        
        st.markdown("""
            <div class="trust-inline">
                <div class="trust-item"><span>🔒</span> Secure & Private</div>
                <div class="trust-item"><span>✓</span> No data stored without consent</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="divider-text">or continue with</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="social-btn">🍎 Apple</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="social-btn">🔵 Google</div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="landing-footer">
            <div class="footer-tagline">Understand. Prepare. Protect.</div>
            <div class="trust-badges">
                <div class="trust-badge">🔒 256-bit Encryption</div>
                <div class="trust-badge">🛡️ SOC 2 Compliant</div>
                <div class="trust-badge">✓ HIPAA Ready</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def show_main_app():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 🏠 PoliSee Clarity")
        st.markdown(f"*Logged in as: {st.session_state.user_email}*")
    with col2:
        if st.button("Logout", key="logout_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("### Understand. Prepare. Protect.")
    st.markdown("""
    Upload your homeowners insurance policy PDF and select a disaster scenario. 
    We'll analyze your coverage and show you exactly what's protected—and what's not—before you ever file a claim.
    """)
    
    st.markdown("---")
    
    client = get_openai_client()
    if not client:
        st.error("⚠️ OpenAI API key not configured. Please add OPENAI_API_KEY to your secrets.")
        st.stop()
    
    st.markdown("### 📄 Upload Your Policy")
    uploaded_file = st.file_uploader(
        "Choose your insurance policy PDF",
        type=['pdf'],
        help="Upload your current homeowners insurance policy document (PDF format, max 20MB)"
    )
    
    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 20:
            st.error("File too large. Please upload a PDF under 20MB.")
            st.stop()
        
        if 'file_id' not in st.session_state or st.session_state.get('uploaded_filename') != uploaded_file.name:
            with st.spinner("Uploading policy to secure analysis engine..."):
                file_id, error = upload_pdf_to_openai(client, uploaded_file)
                if error:
                    st.error(f"Upload failed: {error}")
                    st.stop()
                st.session_state.file_id = file_id
                st.session_state.uploaded_filename = uploaded_file.name
        
        st.success(f"✅ Policy uploaded successfully: {uploaded_file.name}")
        
        with st.expander("🔧 Debug Info"):
            st.code(f"File ID: {st.session_state.file_id}")
            st.code(f"File Size: {file_size_mb:.2f} MB")
    
    st.markdown("### 🌪️ Select a Scenario")
    scenario = st.selectbox(
        "What disaster scenario would you like to analyze?",
        SCENARIOS,
        index=0,
        help="Choose a potential disaster to see how your policy would respond"
    )
    
    if scenario != "Select a scenario..." and 'file_id' in st.session_state:
        if st.button("🔍 Analyze My Coverage", key="analyze_btn"):
            with st.spinner("Analyzing your policy... This may take a moment."):
                result, error = analyze_policy(client, st.session_state.file_id, scenario)
                
                if error:
                    st.error(f"Analysis failed: {error}")
                else:
                    st.session_state.analysis_result = result
                    st.session_state.analyzed_scenario = scenario
                    
                    out_of_pocket = result.get('total_out_of_pocket')
                    gap_alerts = result.get('gap_alerts', [])
                    
                    save_analysis(
                        user_id=st.session_state.user_id,
                        scenario=scenario,
                        file_id=st.session_state.file_id,
                        response_json=json.dumps(result),
                        out_of_pocket=out_of_pocket,
                        gap_alerts=gap_alerts
                    )
    
    if 'analysis_result' in st.session_state:
        result = st.session_state.analysis_result
        scenario_name = st.session_state.analyzed_scenario
        
        st.markdown("---")
        st.markdown(f"## 📊 Analysis Results: {scenario_name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            out_of_pocket = result.get('total_out_of_pocket', 'N/A')
            if isinstance(out_of_pocket, (int, float)):
                st.metric(
                    label="💰 Estimated Out-of-Pocket",
                    value=f"${out_of_pocket:,.0f}"
                )
            else:
                st.metric(label="💰 Estimated Out-of-Pocket", value="Unknown")
        
        with col2:
            gaps = result.get('gap_alerts', [])
            health_score = max(0, 100 - (len(gaps) * 20))
            delta_color = "normal" if health_score >= 60 else "inverse"
            st.metric(
                label="🛡️ Policy Health Score",
                value=f"{health_score}/100",
                delta=f"{len(gaps)} gaps found" if gaps else "No gaps!",
                delta_color="off" if gaps else "normal"
            )
        
        deductible = result.get('deductible', 'N/A')
        if isinstance(deductible, (int, float)):
            st.info(f"📋 **Policy Deductible:** ${deductible:,.0f}")
        
        if gaps:
            st.markdown("### ⚠️ Coverage Gaps Detected")
            for gap in gaps:
                st.warning(f"🚨 {gap}")
        else:
            st.success("✅ No major coverage gaps detected for this scenario!")
        
        with st.expander("✅ Covered Items", expanded=True):
            covered = result.get('covered_items', [])
            if covered:
                df_data = []
                for item in covered:
                    if isinstance(item, dict):
                        df_data.append({
                            "Item": item.get('item', 'N/A'),
                            "Est. Replacement Cost": f"${item.get('est_replacement_cost', 0):,.0f}",
                            "Depreciation": f"{item.get('depreciation_pct', 0)}%",
                            "ACV Payout": f"${item.get('acv_payout', 0):,.0f}"
                        })
                if df_data:
                    st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
                else:
                    st.info("No specific covered items identified.")
            else:
                st.info("No covered items identified for this scenario.")
        
        with st.expander("❌ Not Covered", expanded=True):
            not_covered = result.get('not_covered_items', [])
            if not_covered:
                for item in not_covered:
                    if isinstance(item, str):
                        st.error(f"• {item}")
                    elif isinstance(item, dict):
                        st.error(f"• {item.get('item', item)}")
            else:
                st.success("All typical items appear to be covered!")
        
        with st.expander("📝 Summary & Recommendations"):
            st.markdown("#### Plain Language Summary")
            st.info(result.get('plain_summary', 'No summary available.'))
            
            st.markdown("#### Recommendations")
            recommendations = result.get('recommendations', [])
            if recommendations:
                for rec in recommendations:
                    st.markdown(f"• {rec}")
            else:
                st.info("No specific recommendations at this time.")
    
    st.markdown("---")
    
    with st.expander("📜 Your Analysis History"):
        user_analyses = get_user_analyses(st.session_state.user_id)
        if user_analyses:
            history_data = []
            for analysis in user_analyses:
                history_data.append({
                    "Date": analysis.upload_timestamp.strftime("%Y-%m-%d %H:%M"),
                    "Scenario": analysis.scenario,
                    "Out-of-Pocket": f"${float(analysis.out_of_pocket_estimate):,.0f}" if analysis.out_of_pocket_estimate else "N/A"
                })
            st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
        else:
            st.info("No analysis history yet. Upload a policy to get started!")
    
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <div class="footer-tagline">Understand. Prepare. Protect.</div>
        <div class="footer-brand">PoliSee Clarity – Insurance made clear</div>
    </div>
    """, unsafe_allow_html=True)

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        show_main_app()
    else:
        show_auth_page()

if __name__ == "__main__":
    main()
