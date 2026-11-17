# Smart College Enquiry AI Studio (Local Full-Stack Edition)

An interactive, AI-studio style **College Enquiry Assistant & Administrative Analytics Suite** built with Python, Streamlit, Scikit-learn, Pandas, and Plotly.

## Project Structure
```text
smart_college_ai_studio/
├── app.py                     # Main Studio UI & Admin Analytics Dashboard
├── requirements.txt           # Python dependencies
├── README.md                  # Quickstart guide
├── data/
│   ├── knowledge_base.csv     # Verified College Q&A Knowledge Base
│   ├── chat_history.csv       # Automated Enquiry & Analytics Log
│   └── feedback_logs.csv      # Student Ratings & Feedback
├── src/
│   ├── __init__.py
│   ├── nlp_engine.py          # Hybrid TF-IDF + Fuzzy Token + Intent Engine
│   ├── storage.py             # CSV Storage, Validation & CRUD Manager
│   └── charts.py              # Interactive Plotly Studio Visualizations
└── assets/
    └── studio.css             # Modern AI Studio Glassmorphism & Dark/Light Theme
```

## Quick Start
1. Install packages:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python -m streamlit run app.py
   ```
3. Default Admin Passcode: `admin123`
