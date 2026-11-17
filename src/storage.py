import os
import pandas as pd
from datetime import datetime

KB_PATH = os.path.join("data", "knowledge_base.csv")
LOGS_PATH = os.path.join("data", "chat_history.csv")
FB_PATH = os.path.join("data", "feedback_logs.csv")

KB_COLS = ["ID", "Category", "Question", "Keywords", "Answer"]
LOG_COLS = ["Log_ID", "Timestamp", "Date", "Session_ID", "Language", "Query", "Category", "Matched_Question", "Response", "Confidence", "Status"]
FB_COLS = ["ID", "Timestamp", "Rating", "Topic", "Comment"]

def load_kb() -> pd.DataFrame:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(KB_PATH):
        pd.DataFrame(columns=KB_COLS).to_csv(KB_PATH, index=False)
    df = pd.read_csv(KB_PATH)
    for col in KB_COLS:
        if col not in df.columns:
            df[col] = ""
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
    return df.sort_values("ID").reset_index(drop=True)

def save_kb(df: pd.DataFrame) -> None:
    df = df[KB_COLS].copy()
    df["ID"] = range(1, len(df) + 1)
    df.to_csv(KB_PATH, index=False)

def add_kb_entry(category: str, question: str, keywords: str, answer: str) -> pd.DataFrame:
    df = load_kb()
    new_row = pd.DataFrame([{"ID": len(df) + 1, "Category": category.strip(), "Question": question.strip(), "Keywords": keywords.strip(), "Answer": answer.strip()}])
    updated = pd.concat([df, new_row], ignore_index=True)
    save_kb(updated)
    return load_kb()

def update_kb_entry(entry_id: int, category: str, question: str, keywords: str, answer: str) -> pd.DataFrame:
    df = load_kb()
    mask = df["ID"] == entry_id
    if mask.any():
        df.loc[mask, ["Category", "Question", "Keywords", "Answer"]] = [category.strip(), question.strip(), keywords.strip(), answer.strip()]
        save_kb(df)
    return load_kb()

def delete_kb_entry(entry_id: int) -> pd.DataFrame:
    df = load_kb()
    df = df[df["ID"] != entry_id].reset_index(drop=True)
    save_kb(df)
    return load_kb()

def load_logs() -> pd.DataFrame:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOGS_PATH):
        pd.DataFrame(columns=LOG_COLS).to_csv(LOGS_PATH, index=False)
    return pd.read_csv(LOGS_PATH)

def append_log(session_id: str, lang: str, query: str, category: str, matched_q: str, response: str, conf: float, status: str) -> None:
    df = load_logs()
    now = datetime.now()
    row = pd.DataFrame([{
        "Log_ID": len(df) + 1,
        "Timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Date": now.strftime("%Y-%m-%d"),
        "Session_ID": session_id,
        "Language": lang,
        "Query": query,
        "Category": category,
        "Matched_Question": matched_q,
        "Response": response,
        "Confidence": round(conf, 4),
        "Status": status
    }])
    pd.concat([df, row], ignore_index=True).to_csv(LOGS_PATH, index=False)

def load_feedback() -> pd.DataFrame:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(FB_PATH):
        pd.DataFrame(columns=FB_COLS).to_csv(FB_PATH, index=False)
    return pd.read_csv(FB_PATH)

def append_feedback(rating: int, topic: str, comment: str) -> None:
    df = load_feedback()
    row = pd.DataFrame([{
        "ID": len(df) + 1,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Rating": rating,
        "Topic": topic,
        "Comment": comment.strip() or "No comment"
    }])
    pd.concat([df, row], ignore_index=True).to_csv(FB_PATH, index=False)
