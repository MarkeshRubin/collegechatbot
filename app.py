import os
import time
import uuid
import streamlit as st
from src.storage import load_kb, add_kb_entry, update_kb_entry, delete_kb_entry, load_logs, append_log, load_feedback, append_feedback
from src.nlp_engine import StudioNLPEngine
from src.charts import daily_bar, category_donut

st.set_page_config(page_title="College Chatbot Enquiry", page_icon="🎓", layout="wide")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

def inject_css(dark: bool):
    css_file = os.path.join("assets", "studio.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    if dark:
        st.markdown("<style>.stApp{background:#090D16;color:#F8FAFC;}.kpi-box{background:#111827;border-color:#1F2937;}</style>", unsafe_allow_html=True)

def init_state():
    if "sid" not in st.session_state:
        st.session_state.sid = str(uuid.uuid4())[:8]
    if "kb" not in st.session_state:
        st.session_state.kb = load_kb()
    if "engine" not in st.session_state:
        st.session_state.engine = StudioNLPEngine(st.session_state.kb)
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "last_cat" not in st.session_state:
        st.session_state.last_cat = None
    if "queued_q" not in st.session_state:
        st.session_state.queued_q = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

def reload_engine():
    st.session_state.kb = load_kb()
    st.session_state.engine = StudioNLPEngine(st.session_state.kb)

def process_prompt(prompt: str, lang: str):
    t0 = time.perf_counter()
    st.session_state.chat.append({"role": "user", "content": prompt})
    res = st.session_state.engine.query(prompt, st.session_state.last_cat, lang)
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    if res["matched"]:
        st.session_state.last_cat = res["category"]
    st.session_state.chat.append({
        "role": "assistant",
        "content": res["answer"],
        "category": res["category"],
        "confidence": res["confidence"],
        "latency": latency_ms,
        "follow_ups": res["follow_ups"]
    })
    append_log(st.session_state.sid, lang, prompt, res["category"], res["matched_question"], res["answer"], res["confidence"], res["status"])

def student_workspace(lang: str):
    st.markdown('''
    <div class="studio-header">
        <h1>🎓 Smart College Chatbot Enquiry</h1>
        <p>Instant Automated Admissions, Courses, Fees, Scholarships & Campus Assistant</p>
        <div class="live-pill"><span class="pulse-dot"></span> AI Studio Engine Ready • 100% Local CSV Grounded</div>
    </div>
    ''', unsafe_allow_html=True)

    t_chat, t_kb, t_form, t_fb = st.tabs(["💬 Interactive AI Chat", "📚 Knowledge Directory", "📩 Direct Enquiry", "⭐ Rate Experience"])

    with t_chat:
        st.info("👋 **Welcome to Smart College Enquiry Assistant!** Ask anything about admissions, B.Tech/MBA courses, tuition fees, scholarships, hostel, or placements.")

        st.caption("⚡ **Quick Prompts:**")
        quick_prompts = [
            "What undergraduate courses are offered?",
            "What is the tuition fee structure?",
            "Are merit scholarships available?",
            "How are the placement records?",
            "Are hostel facilities available?",
            "How can I contact the college office?"
        ]
        cols = st.columns(3)
        for i, qp in enumerate(quick_prompts):
            if cols[i % 3].button(qp, key=f"qp_{i}", use_container_width=True):
                st.session_state.queued_q = qp

        if st.session_state.chat:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat = []
                st.session_state.last_cat = None
                st.rerun()

        st.divider()
        for m in st.session_state.chat:
            with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🤖"):
                st.markdown(m["content"])
                if m["role"] == "assistant":
                    st.markdown(
                        f'<span class="tag-badge">📂 {m["category"]}</span>'
                        f'<span class="tag-badge">🎯 Confidence: {int(m["confidence"]*100)}%</span>'
                        f'<span class="tag-badge">⚡ {m["latency"]} ms</span>',
                        unsafe_allow_html=True
                    )

        if st.session_state.chat and st.session_state.chat[-1]["role"] == "assistant":
            fups = st.session_state.chat[-1].get("follow_ups", [])
            if fups:
                st.caption("💡 **Suggested Follow-ups:**")
                fcols = st.columns(len(fups))
                for idx, fq in enumerate(fups):
                    if fcols[idx].button(fq, key=f"fup_{len(st.session_state.chat)}_{idx}", use_container_width=True):
                        st.session_state.queued_q = fq

        user_input = st.chat_input("Type your college question here...")
        active_q = user_input or st.session_state.queued_q
        if active_q:
            st.session_state.queued_q = None
            process_prompt(active_q, lang)
            st.rerun()

    with t_kb:
        st.subheader("📚 Verified College Knowledge Base")
        kb = st.session_state.kb
        q_filter = st.text_input("🔍 Filter topics or keywords")
        view_df = kb[kb["Question"].str.contains(q_filter, case=False, na=False) | kb["Answer"].str.contains(q_filter, case=False, na=False)] if q_filter else kb
        for _, r in view_df.iterrows():
            with st.expander(f"[{r['Category']}] {r['Question']}"):
                st.write(r["Answer"])

    with t_form:
        st.subheader("📩 Submit a Direct Admissions Enquiry")
        with st.form("direct_enq", clear_on_submit=True):
            n = st.text_input("Student Name *")
            e = st.text_input("Email / Phone *")
            msg = st.text_area("Your Enquiry *")
            if st.form_submit_button("Send to Admissions Desk", type="primary"):
                if n and e and msg:
                    append_log(st.session_state.sid, lang, f"[{n} | {e}] {msg}", "Direct Enquiry", "Form Submission", "Queued for counselor callback", 1.0, "Unanswered")
                    st.success("✅ Submitted! Our admissions counselor will contact you shortly.")

    with t_fb:
        st.subheader("⭐ Student Feedback & Rating")
        with st.form("fb_box", clear_on_submit=True):
            stars = st.slider("Rate your experience (1 - 5 Stars)", 1, 5, 5)
            topic = st.selectbox("Enquiry Topic", ["Admissions", "Courses & Fees", "Placements", "Hostel & Campus", "Other"])
            note = st.text_area("Additional Comments")
            if st.form_submit_button("Submit Rating", type="primary"):
                append_feedback(stars, topic, note)
                st.success("🎉 Thank you for your feedback!")

def admin_workspace():
    st.markdown('<div class="studio-header"><h1>🛡️ Admin Studio & Analytics</h1><p>Manage Knowledge Base, Track Student Queries & Export Reports</p></div>', unsafe_allow_html=True)
    if not st.session_state.is_admin:
        with st.form("login"):
            pw = st.text_input("Admin Password (default: admin123)", type="password")
            if st.form_submit_button("Unlock Studio Admin", type="primary"):
                if pw == ADMIN_PASS:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        return

    if st.button("🚪 Lock Admin Session"):
        st.session_state.is_admin = False
        st.rerun()

    logs = load_logs()
    kb = st.session_state.kb
    fb = load_feedback()

    c1, c2, c3, c4 = st.columns(4)
    unans = int((logs["Status"] == "Unanswered").sum()) if not logs.empty else 0
    avg_r = round(float(fb["Rating"].mean()), 1) if not fb.empty else 5.0
    c1.markdown(f'<div class="kpi-box"><div class="kpi-title">Total Enquiries</div><div class="kpi-num">{len(logs)}</div><div class="kpi-foot">All logged queries</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-box accent"><div class="kpi-title">Unanswered</div><div class="kpi-num">{unans}</div><div class="kpi-foot">Needs counselor follow-up</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-box"><div class="kpi-title">KB Articles</div><div class="kpi-num">{len(kb)}</div><div class="kpi-foot">Active NLP vectors</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-box accent"><div class="kpi-title">Student Rating</div><div class="kpi-num">{avg_r} ⭐</div><div class="kpi-foot">From {len(fb)} reviews</div></div>', unsafe_allow_html=True)

    st.write("")
    tab1, tab2, tab3 = st.tabs(["📊 Live Charts & Logs", "🧠 Knowledge Base CRUD", "⭐ Feedback"])

    with tab1:
        ch1, ch2 = st.columns(2)
        with ch1:
            f1 = daily_bar(logs)
            if f1: st.plotly_chart(f1, use_container_width=True)
        with ch2:
            f2 = category_donut(logs)
            if f2: st.plotly_chart(f2, use_container_width=True)
        st.dataframe(logs.iloc[::-1], use_container_width=True, hide_index=True)
        st.download_button("📥 Export Logs CSV", logs.to_csv(index=False).encode("utf-8"), "enquiry_report.csv", "text/csv")

    with tab2:
        st.dataframe(kb, use_container_width=True, hide_index=True)
        col_add, col_edit = st.columns(2)
        with col_add:
            st.markdown("#### ➕ Add New Q&A")
            with st.form("add_kb", clear_on_submit=True):
                cat = st.text_input("Category (e.g., Fees, Admissions)")
                q = st.text_input("Question")
                kw = st.text_input("Keywords (semicolon separated)")
                a = st.text_area("Verified Answer")
                if st.form_submit_button("Add & Rebuild Index", type="primary"):
                    if cat and q and a:
                        add_kb_entry(cat, q, kw, a)
                        reload_engine()
                        st.success("Added & NLP index refreshed!")
                        st.rerun()
        with col_edit:
            st.markdown("#### ✏️ Edit or Delete Q&A")
            if not kb.empty:
                opts = {f"ID {r['ID']}: {r['Question'][:45]}": int(r["ID"]) for _, r in kb.iterrows()}
                sel = st.selectbox("Select Entry", list(opts.keys()))
                eid = opts[sel]
                rec = kb[kb["ID"] == eid].iloc[0]
                with st.form("edit_kb"):
                    ecat = st.text_input("Category", rec["Category"])
                    eq = st.text_input("Question", rec["Question"])
                    ekw = st.text_input("Keywords", rec["Keywords"])
                    ea = st.text_area("Answer", rec["Answer"])
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Save Changes", type="primary"):
                        update_kb_entry(eid, ecat, eq, ekw, ea)
                        reload_engine()
                        st.success("Updated!")
                        st.rerun()
                    if b2.form_submit_button("🗑️ Delete"):
                        delete_kb_entry(eid)
                        reload_engine()
                        st.warning("Deleted!")
                        st.rerun()

    with tab3:
        st.dataframe(fb, use_container_width=True, hide_index=True)

def main():
    init_state()
    with st.sidebar:
        st.markdown(" ")
        mode = st.radio("Workspace", ["🧑‍🎓 Student AI Assistant", "🛡️ Admin Studio"])
        st.divider()
        lang = st.selectbox("🌐 Language", ["English", "Tamil"])
        dark = st.toggle("🌙 Dark Mode", value=True)
        st.divider()
        st.caption(f"Session ID: `{st.session_state.sid}`")
        st.caption(f"Knowledge Records: **{len(st.session_state.kb)}**")

    inject_css(dark)
    if mode == "🧑‍🎓 Student AI Assistant":
        student_workspace(lang)
    else:
        admin_workspace()

if __name__ == "__main__":
    main()
