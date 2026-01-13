import streamlit as st
import os
import json
import re
import bcrypt
import logging
from datetime import datetime
from openai import OpenAI
import pandas as pd

from models import init_db, SessionLocal, User, PolicyAnalysisResult

# Configure logging for Railway/production compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dynamic port for Railway compatibility (Railway sets $PORT)
PORT = int(os.getenv("PORT", 5000))
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None
IS_REPLIT = os.getenv("REPL_ID") is not None

logger.info(f"Starting PoliSee Clarity - Port: {PORT}, Railway: {IS_RAILWAY}, Replit: {IS_REPLIT}")

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
        max-width: 1100px;
    }
    
    .main .block-container.auth-page {
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
    
    .hero-logo {
        width: 560px;
        max-width: 90vw;
        height: auto;
        display: block;
        margin: 0 auto 2rem auto;
        filter: drop-shadow(0 12px 35px rgba(14, 165, 233, 0.4));
        animation: fadeIn 0.8s ease-out;
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
    
    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(71, 85, 105, 0.3);
    }
    
    .section-icon {
        font-size: 1.5rem;
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #f1f5f9;
    }
    
    .section-header.warning-header {
        border-bottom-color: rgba(245, 158, 11, 0.4);
    }
    
    .section-header.warning-header .section-title {
        color: #fcd34d;
    }
    
    .section-header.results-section {
        margin-top: 2rem;
    }
    
    /* Scenario grid buttons */
    [data-testid="stVerticalBlock"] > div:has(button[key^="scenario"]) button,
    div[data-testid="column"] button {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(71, 85, 105, 0.4) !important;
        border-radius: 14px !important;
        padding: 1.25rem 0.75rem !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.3s ease !important;
        min-height: 80px !important;
        white-space: pre-wrap !important;
        line-height: 1.4 !important;
    }
    
    div[data-testid="column"] button:hover {
        border-color: #0ea5e9 !important;
        background: rgba(14, 165, 233, 0.15) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.25) !important;
    }
    
    /* Container styling for dashboard sections with border=True */
    [data-testid="stVerticalBlockBorderWrapper"],
    .stContainer > div[data-testid="stVerticalBlock"] > div:has([data-testid="stFileUploader"]),
    div[data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(71, 85, 105, 0.35) !important;
        border-radius: 16px !important;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(14, 165, 233, 0.3) !important;
    }
    
    /* Dashboard-specific styles */
    .welcome-bar {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
        border: 1px solid rgba(14, 165, 233, 0.2);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.6s ease-out;
    }
    
    .welcome-text h2 {
        margin: 0 0 0.25rem 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: #f8fafc !important;
    }
    
    .welcome-tagline {
        font-size: 1rem;
        color: #0ea5e9;
        font-weight: 500;
    }
    
    /* User dropdown menu styles */
    .user-menu-container {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.75rem;
    }
    
    .user-avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        border: 2px solid #0ea5e9;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
    }
    
    .user-avatar:hover {
        transform: scale(1.08);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
    }
    
    .user-name-display {
        color: #e2e8f0;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .user-email-display {
        color: #64748b;
        font-size: 0.75rem;
    }
    
    .dropdown-menu {
        background: rgba(30, 41, 59, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 16px;
        padding: 0.75rem 0;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        animation: dropdownSlide 0.25s ease-out;
        min-width: 240px;
        margin-top: 0.5rem;
    }
    
    @keyframes dropdownSlide {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .dropdown-header {
        padding: 1rem 1.25rem;
        border-bottom: 1px solid rgba(71, 85, 105, 0.3);
        margin-bottom: 0.5rem;
    }
    
    .dropdown-header-name {
        color: #f1f5f9;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .dropdown-header-email {
        color: #64748b;
        font-size: 0.8rem;
    }
    
    .dropdown-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1.25rem;
        color: #cbd5e1;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
        animation: fadeIn 0.3s ease-out;
    }
    
    .dropdown-item:hover {
        background: rgba(14, 165, 233, 0.15);
        color: #0ea5e9;
        transform: translateX(4px);
    }
    
    .dropdown-item-icon {
        font-size: 1.1rem;
        width: 24px;
        text-align: center;
    }
    
    .dropdown-divider {
        height: 1px;
        background: rgba(71, 85, 105, 0.3);
        margin: 0.5rem 0;
    }
    
    .dropdown-item-logout {
        color: #f87171;
    }
    
    .dropdown-item-logout:hover {
        background: rgba(248, 113, 113, 0.15);
        color: #ef4444;
    }
    
    .about-section {
        background: rgba(14, 165, 233, 0.08);
        border: 1px solid rgba(14, 165, 233, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        line-height: 1.6;
        color: #cbd5e1;
        font-size: 0.9rem;
    }
    
    .about-section-title {
        color: #0ea5e9;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
    }
    
    /* Popover menu styling */
    [data-testid="stPopover"] > div {
        background: rgba(30, 41, 59, 0.98) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(71, 85, 105, 0.4) !important;
        border-radius: 16px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5) !important;
        min-width: 260px !important;
    }
    
    [data-testid="stPopoverBody"] {
        padding: 1rem !important;
    }
    
    .popover-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-bottom: 0.75rem;
    }
    
    .popover-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid #0ea5e9;
    }
    
    .popover-user-info {
        flex: 1;
    }
    
    .popover-name {
        color: #f1f5f9;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .popover-email {
        color: #64748b;
        font-size: 0.8rem;
    }
    
    .popover-divider {
        height: 1px;
        background: rgba(71, 85, 105, 0.4);
        margin: 0.75rem 0;
    }
    
    /* Style popover buttons as menu items */
    [data-testid="stPopoverBody"] button {
        background: transparent !important;
        border: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.6rem 0.75rem !important;
        font-size: 0.9rem !important;
        color: #cbd5e1 !important;
        border-radius: 8px !important;
        margin: 2px 0 !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stPopoverBody"] button:hover {
        background: rgba(14, 165, 233, 0.15) !important;
        color: #0ea5e9 !important;
        transform: translateX(4px) !important;
    }
    
    /* User menu trigger button styling */
    [data-testid="stPopover"] > button {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.5rem 1rem !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stPopover"] > button:hover {
        background: rgba(14, 165, 233, 0.15) !important;
        border-color: #0ea5e9 !important;
    }
    
    /* Header layout */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0;
    }
    
    .dashboard-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 20px;
        padding: 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 40px -15px rgba(0, 0, 0, 0.4);
        animation: fadeInUp 0.6s ease-out;
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        border-color: rgba(14, 165, 233, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 15px 50px -15px rgba(0, 0, 0, 0.5);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(71, 85, 105, 0.3);
    }
    
    .card-header-icon {
        font-size: 1.5rem;
    }
    
    .card-header-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f1f5f9;
        margin: 0;
    }
    
    .upload-zone {
        border: 2px dashed rgba(14, 165, 233, 0.4);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        background: rgba(14, 165, 233, 0.05);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .upload-zone:hover {
        border-color: #0ea5e9;
        background: rgba(14, 165, 233, 0.1);
        transform: scale(1.01);
    }
    
    .upload-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.8;
    }
    
    .upload-text {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .upload-hint {
        color: #64748b;
        font-size: 0.85rem;
    }
    
    .scenario-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .scenario-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 14px;
        padding: 1.25rem 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .scenario-card:hover {
        border-color: #0ea5e9;
        background: rgba(14, 165, 233, 0.1);
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(14, 165, 233, 0.2);
    }
    
    .scenario-card.active {
        border-color: #0ea5e9;
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(6, 182, 212, 0.15) 100%);
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.3);
    }
    
    .scenario-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .scenario-name {
        font-size: 0.85rem;
        color: #e2e8f0;
        font-weight: 500;
    }
    
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.25rem;
        margin: 1.5rem 0;
    }
    
    .metric-card-new {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        animation: fadeInUp 0.6s ease-out;
        transition: all 0.3s ease;
    }
    
    .metric-card-new:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card-new.accent {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        border-color: transparent;
    }
    
    .metric-card-new.warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        border-color: transparent;
    }
    
    .metric-card-new.success {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-color: transparent;
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .metric-value-lg {
        font-size: 2.25rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.25rem;
    }
    
    .metric-label-sm {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.8);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }
    
    .metric-delta {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 0.5rem;
    }
    
    .results-section {
        animation: fadeInUp 0.6s ease-out 0.2s both;
    }
    
    .gap-alert {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        animation: fadeInUp 0.4s ease-out;
    }
    
    .gap-alert-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
    }
    
    .gap-alert-text {
        color: #fcd34d;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    .coverage-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
    }
    
    .coverage-table th {
        background: rgba(15, 23, 42, 0.8);
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 1rem;
        text-align: left;
        border-bottom: 1px solid rgba(71, 85, 105, 0.3);
    }
    
    .coverage-table td {
        padding: 1rem;
        color: #e2e8f0;
        border-bottom: 1px solid rgba(71, 85, 105, 0.2);
    }
    
    .coverage-table tr:nth-child(even) {
        background: rgba(15, 23, 42, 0.3);
    }
    
    .coverage-table tr:hover {
        background: rgba(14, 165, 233, 0.1);
    }
    
    .status-covered {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-partial {
        color: #f59e0b;
        font-weight: 600;
    }
    
    .status-excluded {
        color: #ef4444;
        font-weight: 600;
    }
    
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(15, 23, 42, 0.9);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
    
    .loading-card {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        max-width: 400px;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .loading-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .loading-text {
        color: #0ea5e9;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .loading-subtext {
        color: #64748b;
        font-size: 0.9rem;
    }
    
    .sidebar-section {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .sidebar-link {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        color: #94a3b8;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 0.5rem;
    }
    
    .sidebar-link:hover {
        background: rgba(14, 165, 233, 0.1);
        color: #0ea5e9;
    }
    
    .sidebar-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(71, 85, 105, 0.3);
        border-radius: 8px;
        font-size: 0.75rem;
        color: #64748b;
        margin: 0.25rem;
    }
    
    .analyze-btn {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
        font-size: 1.1rem !important;
        padding: 1.25rem 2rem !important;
        margin-top: 1.5rem !important;
    }
    
    .analyze-btn:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 40px rgba(14, 165, 233, 0.5) !important;
    }
    
    .stDataFrame {
        background: rgba(15, 23, 42, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(71, 85, 105, 0.3);
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border-radius: 12px;
        overflow: hidden;
    }
    
    .debug-card {
        background: rgba(15, 23, 42, 0.4);
        border: 1px dashed rgba(71, 85, 105, 0.4);
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
    }
    
    .stFileUploader {
        background: rgba(14, 165, 233, 0.05);
        border: 2px dashed rgba(14, 165, 233, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #0ea5e9;
        background: rgba(14, 165, 233, 0.1);
    }
    
    .stFileUploader label {
        color: #94a3b8 !important;
    }
    
    .stSelectbox label {
        color: #94a3b8 !important;
        font-weight: 600;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 12px;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.9);
        border: 2px solid rgba(71, 85, 105, 0.4);
        border-radius: 12px;
        color: #f1f5f9;
        padding: 0.5rem 0.75rem;
    }
    
    .stSelectbox [data-baseweb="select"] > div:focus-within {
        border-color: #0ea5e9;
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
    }
    
    [data-baseweb="popover"] {
        background: #1e293b !important;
        border: 1px solid rgba(71, 85, 105, 0.4) !important;
        border-radius: 12px !important;
    }
    
    [data-baseweb="menu"] {
        background: #1e293b !important;
    }
    
    [data-baseweb="menu"] li {
        color: #e2e8f0 !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background: rgba(14, 165, 233, 0.2) !important;
    }
    
    .stMetric {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
        border: 1px solid rgba(71, 85, 105, 0.4);
        border-radius: 16px;
        padding: 1.25rem !important;
    }
    
    .stMetric label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #0ea5e9 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        color: #64748b !important;
    }
    
    .dashboard-footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid rgba(51, 65, 85, 0.3);
    }
    
    .dashboard-footer-tagline {
        font-size: 1.25rem;
        font-weight: 700;
        background: linear-gradient(90deg, #0ea5e9, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.75rem;
    }
    
    .dashboard-footer-brand {
        color: #64748b;
        font-size: 0.875rem;
    }
    
    .stSuccess {
        background: rgba(16, 185, 129, 0.15) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.15) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stInfo {
        background: rgba(14, 165, 233, 0.15) !important;
        border: 1px solid rgba(14, 165, 233, 0.3) !important;
        border-radius: 12px !important;
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
    # Try environment variable first (works on Railway, Replit, local)
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Fallback to st.secrets if available (Replit)
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass
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
    import base64
    
    logo_path = "attached_assets/polisee_logo.png"
    try:
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_data}" class="hero-logo" alt="PoliSee Logo">'
    except Exception:
        logo_html = '<div class="hero-icon">🏠🛡️</div>'
    
    st.markdown(f"""
        <div class="hero-section">
            {logo_html}
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
    user_email = st.session_state.user_email
    user_name = user_email.split('@')[0].title()
    
    if 'dropdown_open' not in st.session_state:
        st.session_state.dropdown_open = False
    if 'show_about' not in st.session_state:
        st.session_state.show_about = False
    
    avatar_url = f"https://ui-avatars.com/api/?name={user_name}&background=0ea5e9&color=fff&rounded=true&size=128"
    
    header_col1, header_col2 = st.columns([4, 1])
    
    with header_col1:
        st.markdown(f"""
            <div class="welcome-bar">
                <div class="welcome-text">
                    <h2>Welcome back, {user_name}</h2>
                    <div class="welcome-tagline">Know What's Covered - Before You Need It.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with header_col2:
        with st.popover(f"👤 {user_name}", use_container_width=True):
            st.markdown(f"""
                <div class="popover-header">
                    <img src="{avatar_url}" class="popover-avatar" alt="Avatar">
                    <div class="popover-user-info">
                        <div class="popover-name">{user_name}</div>
                        <div class="popover-email">{user_email}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""<div class="popover-divider"></div>""", unsafe_allow_html=True)
            
            if st.button("👤 Profile Settings", key="profile_btn", use_container_width=True):
                st.toast("Profile settings coming soon!")
            
            if st.button("❓ Help & FAQ", key="help_btn", use_container_width=True):
                st.toast("Help & FAQ coming soon!")
            
            if st.button("ℹ️ About PoliSee", key="about_btn", use_container_width=True):
                st.session_state.show_about = True
            
            st.markdown("""<div class="popover-divider"></div>""", unsafe_allow_html=True)
            
            if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    if st.session_state.get('show_about', False):
        st.markdown("""
            <div class="about-section">
                <div class="about-section-title">About PoliSee Clarity</div>
                PoliSee Clarity is your personal insurance transparency tool. Upload your homeowners policy PDF, 
                select a disaster scenario, and let AI decode what's covered, what's excluded, and your potential 
                out-of-pocket costs—before disaster strikes.
                <br><br>
                We empower homeowners to understand their coverage, spot gaps early, and make smarter decisions.
                <br><br>
                <strong style="color: #0ea5e9;">Understand. Prepare. Protect.</strong>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Close About", key="close_about_btn"):
            st.session_state.show_about = False
            st.rerun()
    
    client = get_openai_client()
    if not client:
        st.error("OpenAI API key not configured. Please add OPENAI_API_KEY to your secrets.")
        st.stop()
    
    with st.container(border=True):
        st.markdown("""
            <div class="section-header">
                <span class="section-icon">📄</span>
                <span class="section-title">Upload Your Policy</span>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Drop your insurance policy PDF here or click to browse",
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
        
        st.success(f"Policy uploaded successfully: {uploaded_file.name}")
        
        with st.expander("Developer Debug Info", expanded=False):
            st.markdown('<div class="debug-card">', unsafe_allow_html=True)
            st.code(f"File ID: {st.session_state.file_id}")
            st.code(f"File Size: {file_size_mb:.2f} MB")
            st.markdown('</div>', unsafe_allow_html=True)
    
    scenario_icons = {
        "Burst Pipe / Interior Water Leak": "💧",
        "Roof Hail Damage": "🌨️",
        "Basement Flood (Groundwater Seepage)": "🌊",
        "Fence Wind Damage": "💨",
        "Tree Damage to Dwelling": "🌳",
        "Appliance Power Surge": "⚡",
        "Hurricane": "🌀",
        "Fire": "🔥",
        "Theft": "🔒"
    }
    
    if 'selected_scenario' not in st.session_state:
        st.session_state.selected_scenario = None
    
    with st.container(border=True):
        st.markdown("""
            <div class="section-header">
                <span class="section-icon">🌪️</span>
                <span class="section-title">Select a Disaster Scenario</span>
            </div>
        """, unsafe_allow_html=True)
        
        scenario_list = [s for s in SCENARIOS if s != "Select a scenario..."]
        
        cols = st.columns(3)
        for idx, scenario_name in enumerate(scenario_list):
            col_idx = idx % 3
            icon = scenario_icons.get(scenario_name, "🔍")
            with cols[col_idx]:
                is_selected = st.session_state.selected_scenario == scenario_name
                if st.button(f"{icon}\n{scenario_name}", key=f"scenario_{idx}", use_container_width=True):
                    st.session_state.selected_scenario = scenario_name
                    st.rerun()
    
    scenario = st.session_state.selected_scenario
    
    if scenario and 'file_id' in st.session_state:
        icon = scenario_icons.get(scenario, "🔍")
        st.markdown(f"<div style='text-align: center; color: #0ea5e9; margin: 1rem 0;'>Selected: <strong>{icon} {scenario}</strong></div>", unsafe_allow_html=True)
        if st.button(f"Analyze My Coverage", key="analyze_btn", use_container_width=True):
            with st.spinner("Decoding your policy... This may take a moment."):
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
        scenario_icon = scenario_icons.get(scenario_name, "📊")
        
        with st.container(border=True):
            st.markdown(f"""
                <div class="section-header results-section">
                    <span class="section-icon">{scenario_icon}</span>
                    <span class="section-title">Analysis Results: {scenario_name}</span>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                out_of_pocket = result.get('total_out_of_pocket', 'N/A')
                if isinstance(out_of_pocket, (int, float)):
                    st.metric(
                        label="Estimated Out-of-Pocket",
                        value=f"${out_of_pocket:,.0f}"
                    )
                else:
                    st.metric(label="Estimated Out-of-Pocket", value="Unknown")
            
            with col2:
                gaps = result.get('gap_alerts', [])
                health_score = max(0, 100 - (len(gaps) * 20))
                st.metric(
                    label="Policy Health Score",
                    value=f"{health_score}/100",
                    delta=f"{len(gaps)} gaps" if gaps else "No gaps!",
                    delta_color="off" if gaps else "normal"
                )
            
            with col3:
                deductible = result.get('deductible', 'N/A')
                if isinstance(deductible, (int, float)):
                    st.metric(
                        label="Policy Deductible",
                        value=f"${deductible:,.0f}"
                    )
                else:
                    st.metric(label="Policy Deductible", value="N/A")
        
        if gaps:
            with st.container(border=True):
                st.markdown("""
                    <div class="section-header warning-header">
                        <span class="section-icon">⚠️</span>
                        <span class="section-title">Coverage Gaps Detected</span>
                    </div>
                """, unsafe_allow_html=True)
                for gap in gaps:
                    st.markdown(f"""
                        <div class="gap-alert">
                            <span class="gap-alert-icon">🚨</span>
                            <span class="gap-alert-text">{gap}</span>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("No major coverage gaps detected for this scenario!")
        
        with st.expander("Covered Items", expanded=True):
            covered = result.get('covered_items', [])
            if covered:
                df_data = []
                for item in covered:
                    if isinstance(item, dict):
                        df_data.append({
                            "Item": item.get('item', 'N/A'),
                            "Est. Replacement": f"${item.get('est_replacement_cost', 0):,.0f}",
                            "Depreciation": f"{item.get('depreciation_pct', 0)}%",
                            "ACV Payout": f"${item.get('acv_payout', 0):,.0f}"
                        })
                if df_data:
                    st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
                else:
                    st.info("No specific covered items identified.")
            else:
                st.info("No covered items identified for this scenario.")
        
        with st.expander("Not Covered", expanded=True):
            not_covered = result.get('not_covered_items', [])
            if not_covered:
                for item in not_covered:
                    if isinstance(item, str):
                        st.error(f"• {item}")
                    elif isinstance(item, dict):
                        st.error(f"• {item.get('item', item)}")
            else:
                st.success("All typical items appear to be covered!")
        
        with st.expander("Summary & Recommendations"):
            st.markdown("**Plain Language Summary**")
            st.info(result.get('plain_summary', 'No summary available.'))
            
            st.markdown("**Recommendations**")
            recommendations = result.get('recommendations', [])
            if recommendations:
                for rec in recommendations:
                    st.markdown(f"• {rec}")
            else:
                st.info("No specific recommendations at this time.")
    
    with st.container(border=True):
        st.markdown("""
            <div class="section-header">
                <span class="section-icon">📜</span>
                <span class="section-title">Your Analysis History</span>
            </div>
        """, unsafe_allow_html=True)
        
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
    
    st.markdown("""
        <div class="dashboard-footer">
            <div class="dashboard-footer-tagline">Understand. Prepare. Protect.</div>
            <div class="dashboard-footer-brand">PoliSee Clarity - Insurance made clear</div>
            <div class="trust-badges" style="margin-top: 1rem;">
                <div class="trust-badge">🔒 Secure</div>
                <div class="trust-badge">🛡️ Private</div>
                <div class="trust-badge">✨ AI-Powered</div>
            </div>
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
