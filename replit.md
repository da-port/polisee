# PoliSee Clarity

## Overview
PoliSee Clarity is a consumer-first web application that helps homeowners understand their existing homeowners insurance policy before a disaster happens. Users can upload their policy PDF, select a disaster scenario, and receive AI-powered analysis showing what's covered, what's excluded, estimated out-of-pocket costs, and coverage gap alerts.

**Tagline:** Understand. Prepare. Protect.

## Current State
The MVP is fully functional with:
- User registration and login system
- PDF policy upload to OpenAI Files API
- AI-powered policy analysis for 9 disaster scenarios
- Coverage breakdown with estimated costs
- Gap alerts and recommendations
- Analysis history tracking per user

## Project Architecture

### File Structure
- `app.py` - Main Streamlit application with UI, authentication, and OpenAI integration
- `models.py` - SQLAlchemy database models (User, PolicyAnalysisResult)
- `.streamlit/config.toml` - Streamlit server configuration

### Database Schema
**users table:**
- id (primary key)
- email (unique)
- password_hash (bcrypt hashed)
- created_at

**policy_analysis_results table:**
- id (primary key)
- user_id (foreign key to users)
- upload_timestamp
- scenario
- file_id (OpenAI file reference)
- openai_response_json
- out_of_pocket_estimate
- gap_alerts

### Key Technologies
- **Frontend:** Streamlit with custom CSS (navy-blue theme, mobile-first)
- **Backend:** Python 3.11
- **Database:** PostgreSQL with SQLAlchemy ORM
- **AI:** OpenAI Responses API with gpt-4o for PDF analysis
- **Authentication:** bcrypt for password hashing

## Disaster Scenarios Supported
1. Burst Pipe / Interior Water Leak
2. Roof Hail Damage
3. Basement Flood (Groundwater Seepage)
4. Fence Wind Damage
5. Tree Damage to Dwelling
6. Appliance Power Surge
7. Hurricane
8. Fire
9. Theft

## Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string (auto-configured)
- `OPENAI_API_KEY` - OpenAI API key for policy analysis

## Running the Application
```
streamlit run app.py --server.port 5000
```

## Recent Changes
- January 2026: Initial MVP release with user authentication, PDF upload, OpenAI policy analysis, and analysis history tracking
