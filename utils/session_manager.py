import json
import os
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

CHAT_HISTORY_DIR = "./chat_history"


def ensure_dir():
    if not os.path.exists(CHAT_HISTORY_DIR):
        os.makedirs(CHAT_HISTORY_DIR)


def generate_session_id() -> str:
    return f"session_{uuid.uuid4().hex[:12]}"


def generate_default_title() -> str:
    return f"问诊 {datetime.now().strftime('%m-%d %H:%M')}"


def get_session_file_path(session_id: str) -> str:
    return os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")


def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    ensure_dir()
    path = get_session_file_path(session_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_session(session_id: str, data: Dict[str, Any]):
    ensure_dir()
    path = get_session_file_path(session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_new_session(title: Optional[str] = None, category: str = "主对话") -> Dict[str, Any]:
    session_id = generate_session_id()
    session = {
        "session_id": session_id,
        "title": title or generate_default_title(),
        "category": category,
        "created_at": time.time(),
        "updated_at": time.time(),
        "messages": [],
        "temp_kb_files": [],
    }
    save_session(session_id, session)
    return session


def delete_session(session_id: str):
    path = get_session_file_path(session_id)
    if os.path.exists(path):
        os.remove(path)


def rename_session(session_id: str, new_title: str):
    session = load_session(session_id)
    if session:
        session["title"] = new_title
        session["updated_at"] = time.time()
        save_session(session_id, session)


def append_message(session_id: str, role: str, content: str, attachments: Optional[List[str]] = None, refs: Optional[List[Dict]] = None):
    session = load_session(session_id)
    if not session:
        session = create_new_session()
        session_id = session["session_id"]
    message = {
        "role": role,
        "content": content,
        "timestamp": time.time(),
        "attachments": attachments or [],
        "refs": refs or [],
    }
    session["messages"].append(message)
    session["updated_at"] = time.time()
    save_session(session_id, session)
    return session


def get_all_sessions() -> List[Dict[str, Any]]:
    ensure_dir()
    sessions = []
    for fname in os.listdir(CHAT_HISTORY_DIR):
        if fname.endswith(".json"):
            path = os.path.join(CHAT_HISTORY_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(data)
            except Exception:
                continue
    sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
    return sessions


def search_sessions(keyword: str) -> List[Dict[str, Any]]:
    sessions = get_all_sessions()
    keyword_lower = keyword.lower()
    results = []
    for s in sessions:
        if keyword_lower in s.get("title", "").lower():
            results.append(s)
            continue
        for msg in s.get("messages", []):
            if keyword_lower in msg.get("content", "").lower():
                results.append(s)
                break
    return results


def export_session_to_markdown(session_id: str) -> str:
    session = load_session(session_id)
    if not session:
        return ""
    lines = [f"# {session.get('title', '对话记录')}\n", f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n", "---\n"]
    for msg in session.get("messages", []):
        role_label = "用户" if msg["role"] == "user" else "机器人"
        lines.append(f"## {role_label}\n\n{msg['content']}\n")
        if msg.get("refs"):
            lines.append("\n**参考医学资料**\n")
            for ref in msg["refs"]:
                lines.append(f"- *{ref.get('source', '')}* (第{ref.get('page', '')}页): {ref.get('content', '')}\n")
        lines.append("\n---\n")
    return "".join(lines)


def add_temp_kb_file(session_id: str, file_path: str):
    session = load_session(session_id)
    if session:
        if file_path not in session.get("temp_kb_files", []):
            session.setdefault("temp_kb_files", []).append(file_path)
            session["updated_at"] = time.time()
            save_session(session_id, session)


def clear_temp_kb_files(session_id: str):
    session = load_session(session_id)
    if session:
        session["temp_kb_files"] = []
        session["updated_at"] = time.time()
        save_session(session_id, session)
