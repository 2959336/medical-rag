import streamlit as st
import streamlit.components.v1 as components
import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from components.sidebar import render_sidebar
from components.chat_area import (
    render_header, render_quick_cards, render_chat_messages, render_input_area,
    _inject_wechat_css,
)
from utils import session_manager, kb_manager

st.set_page_config(
    page_title="医疗RAG智能问诊助手",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────── 持久化用户数据文件 ────────────────────────────
USERS_DB_PATH = os.path.join(script_dir, "_users_db.json")


def _load_users_from_file():
    """从 JSON 文件加载用户数据库，启动 / 重启不丢失"""
    try:
        if os.path.exists(USERS_DB_PATH):
            with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
                db = json.load(f)
            return db.get("valid_users", {}), db.get("user_avatars", {})
    except Exception:
        pass
    # 首次启动 → 写入预设演示账户
    default_users = {"admin": "123456", "user": "123456"}
    default_avatars = {"admin": "boy", "user": "girl"}
    _save_users_to_file(default_users, default_avatars)
    return default_users, default_avatars


def _save_users_to_file(valid_users, user_avatars):
    """持久化写入 JSON，原子性写入防损坏"""
    db = {"valid_users": valid_users, "user_avatars": user_avatars}
    tmp = USERS_DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, USERS_DB_PATH)


# 模块级全局变量，从文件加载
VALID_USERS, USER_AVATARS = _load_users_from_file()


def do_login(username, password):
    """登录校验 —— 账号+密码完全匹配才通过"""
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        st.session_state["auth_error"] = "请输入用户名和密码"
        return
    # 重新从文件加载，确保拿到最新注册数据
    current_users, current_avatars = _load_users_from_file()
    if username not in current_users:
        st.session_state["auth_error"] = "用户名或密码错误"
        return
    if current_users[username] != password:
        st.session_state["auth_error"] = "用户名或密码错误"
        return
    st.session_state["is_logged_in"] = True
    st.session_state["username"] = username
    st.session_state["user_avatar"] = current_avatars.get(username, "boy")
    st.session_state["auth_error"] = ""
    st.session_state["show_login_form"] = False
    st.rerun(scope="app")


def do_register(username, password, password2, gender):
    """注册校验 —— 强制性别选择 + 完整非空校验"""
    username = (username or "").strip()
    password = (password or "").strip()
    password2 = (password2 or "").strip()
    # ① 非空校验
    if not username:
        st.session_state["auth_error"] = "请输入用户名"
        return
    if not password:
        st.session_state["auth_error"] = "请输入密码"
        return
    # ② 性别校验
    if gender not in ("boy", "girl"):
        st.session_state["auth_error"] = "请选择性别"
        return
    # ③ 密码长度
    if len(password) < 6:
        st.session_state["auth_error"] = "密码长度至少6位"
        return
    # ④ 两次密码一致
    if password != password2:
        st.session_state["auth_error"] = "两次密码不一致"
        return
    # ⑤ 用户名不重复（重新从文件加载最新数据）
    current_users, current_avatars = _load_users_from_file()
    if username in current_users:
        st.session_state["auth_error"] = "用户名已存在"
        return
    # ⑥ 写入文件持久化
    current_users[username] = password
    current_avatars[username] = gender
    _save_users_to_file(current_users, current_avatars)
    # 同步模块级变量
    global VALID_USERS, USER_AVATARS
    VALID_USERS, USER_AVATARS = current_users, current_avatars
    st.session_state["auth_error"] = ""
    st.session_state["auth_tab"] = "login"
    st.rerun(scope="app")


def _clear_auth_field_keys():
    """打开登录/注册弹窗时，清除所有输入框的旧缓存值"""
    auth_keys = [
        "login_user_field", "login_pass_field",
        "reg_user_field", "reg_pass_field", "reg_pass2_field",
    ]
    for k in auth_keys:
        if k in st.session_state:
            del st.session_state[k]


def render_top_bar():
    """右上角：未登录显示登录按钮；登录后顶部清爽无控件（用户信息已移至侧边栏底部）"""
    is_logged_in = st.session_state.get("is_logged_in", False)

    if is_logged_in:
        # 登录后：顶部不显示任何用户控件，用户面板在侧边栏底部
        return

    # ── 未登录 → 登录按钮固定在右上角，圆角浅底色 ──
    st.markdown("""
    <style>
        .st-key-open_login_btn {
            position: fixed !important;
            top: 12px !important;
            right: 16px !important;
            z-index: 10000 !important;
        }
        .st-key-open_login_btn button {
            background-color: #f0f4f8 !important;
            color: #4A90E2 !important;
            border: 1px solid #d0dfee !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 6px 16px !important;
            min-height: auto !important;
        }
        .st-key-open_login_btn button:hover {
            background-color: #e3edf7 !important;
            color: #357ABD !important;
            border-color: #4A90E2 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    if st.button("登录 / 注册", key="open_login_btn"):
        st.session_state["show_login_form"] = True
        st.session_state["auth_tab"] = "login"
        st.session_state["auth_error"] = ""
        st.rerun()


def render_login_form():
    """居中悬浮模态弹窗 —— 使用 st.dialog 原生弹窗"""
    if not st.session_state.get("show_login_form", False):
        return

    auth_tab = st.session_state.get("auth_tab", "login")

    # ────── 打开弹窗时清空所有输入框缓存 ──────
    _clear_auth_field_keys()

    if auth_tab == "login":
        _login_dialog()
    else:
        _register_dialog()


@st.dialog("欢迎登录", width="small")
def _login_dialog():
    st.markdown("""
    <style>
    .st-key-login_submit_btn button {
        background-color: #d0e8ff !important;
        color: #000000 !important;
        border: 1px solid #91c4f2 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .st-key-login_submit_btn button:hover {
        background-color: #b8d9f7 !important;
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 从 session_state 实时读取，校验失败后对话框重渲染能拿到最新错误
    auth_error = st.session_state.get("auth_error", "")
    if auth_error:
        st.error(auth_error)

    st.text_input("用户名", key="login_user_field", placeholder="请输入用户名",
                   label_visibility="collapsed")

    # -------- 密码（浏览器原生显隐） --------
    st.text_input("密码", key="login_pass_field", placeholder="请输入密码",
                   type="password", label_visibility="collapsed")

    # -------- 登录 / 取消 --------
    col1, col2 = st.columns([3, 1])
    with col1:
        # 直接从 session_state 取值，避免 dialog 片段中变量捕获延迟问题
        if st.button("登 录", key="login_submit_btn", use_container_width=True):
            do_login(
                st.session_state.get("login_user_field", ""),
                st.session_state.get("login_pass_field", "")
            )
    with col2:
        if st.button("取消", key="login_cancel_btn", use_container_width=True):
            st.session_state["show_login_form"] = False
            st.session_state["auth_error"] = ""
            st.rerun(scope="app")  # 必须 scope="app" 从 dialog 片段回到主脚本

    # -------- 底部注册链接（CSS 去边框 → 纯文字蓝色链接） --------
    st.markdown("---")
    if st.button("没有账号？点击注册", key="go_register_btn", type="tertiary"):
        st.session_state["auth_tab"] = "register"
        st.session_state["auth_error"] = ""
        st.rerun(scope="app")  # 必须 scope="app" 才能打开注册 dialog


@st.dialog("注册账号", width="small")
def _register_dialog():
    st.markdown("""
    <style>
    .st-key-register_submit_btn button {
        background-color: #d0e8ff !important;
        color: #000000 !important;
        border: 1px solid #91c4f2 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .st-key-register_submit_btn button:hover {
        background-color: #b8d9f7 !important;
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 从 session_state 实时读取
    auth_error = st.session_state.get("auth_error", "")
    if auth_error:
        st.error(auth_error)

    st.text_input("用户名", key="reg_user_field", placeholder="请输入用户名",
                   label_visibility="collapsed")

    # -------- 性别选择（图片+文字嵌在一起） --------
    # 读取 SVG 头像
    boy_svg = ""
    girl_svg = ""
    try:
        with open(os.path.join(script_dir, "头像 男孩.svg"), "r", encoding="utf-8") as f:
            boy_svg = f.read()
    except Exception:
        pass
    try:
        with open(os.path.join(script_dir, "头像 女孩.svg"), "r", encoding="utf-8") as f:
            girl_svg = f.read()
    except Exception:
        pass

    reg_gender_val = st.session_state.get("reg_gender_val", "boy")

    selected_border = "3px solid #4A90E2"
    default_border = "2px solid #e5e7eb"
    boy_border = selected_border if reg_gender_val == "boy" else default_border
    girl_border = selected_border if reg_gender_val == "girl" else default_border
    boy_bg = "#eff6ff" if reg_gender_val == "boy" else "#fff"
    girl_bg = "#eff6ff" if reg_gender_val == "girl" else "#fff"

    col_boy, col_girl = st.columns(2)
    with col_boy:
        st.markdown(f"""
        <div style='border:{boy_border}; border-radius:12px; padding:14px 8px 4px 8px; text-align:center; background:{boy_bg};'>
            <div style='width:48px;height:48px;border-radius:50%;overflow:hidden;margin:0 auto 4px auto;display:flex;align-items:center;justify-content:center;'>
                {boy_svg}
            </div>
            <div style='font-size:14px;font-weight:500;color:#333;'>男生</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择", key="reg_boy_btn", use_container_width=True):
            st.session_state["reg_gender_val"] = "boy"
            st.rerun(scope="app")

    with col_girl:
        st.markdown(f"""
        <div style='border:{girl_border}; border-radius:12px; padding:14px 8px 4px 8px; text-align:center; background:{girl_bg};'>
            <div style='width:48px;height:48px;border-radius:50%;overflow:hidden;margin:0 auto 4px auto;display:flex;align-items:center;justify-content:center;'>
                {girl_svg}
            </div>
            <div style='font-size:14px;font-weight:500;color:#333;'>女生</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("选择", key="reg_girl_btn", use_container_width=True):
            st.session_state["reg_gender_val"] = "girl"
            st.rerun(scope="app")

    avatar_gender = reg_gender_val

    # -------- 密码1 + 密码2（浏览器原生显隐） --------
    st.text_input("密码", key="reg_pass_field", placeholder="至少6位",
                   type="password", label_visibility="collapsed")
    st.text_input("确认密码", key="reg_pass2_field", placeholder="再次输入",
                   type="password", label_visibility="collapsed")

    # -------- 注册 / 返回 --------
    col1, col2 = st.columns([3, 1])
    with col1:
        # 直接从 session_state 取值
        if st.button("注 册", key="register_submit_btn", use_container_width=True):
            do_register(
                st.session_state.get("reg_user_field", ""),
                st.session_state.get("reg_pass_field", ""),
                st.session_state.get("reg_pass2_field", ""),
                avatar_gender
            )
    with col2:
        if st.button("返回", key="back_login_btn", use_container_width=True):
            st.session_state["auth_tab"] = "login"
            st.session_state["auth_error"] = ""
            st.rerun(scope="app")  # 必须 scope="app" 才能切回登录 dialog


def init_session_state():
    defaults = {
        "current_session_id": None,
        "messages": [],
        "temp_kb_files": [],
        "role_mode": "patient",
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 5,
        "max_tokens": 2048,
        "max_history_pairs": 10,
        "history_len": 1,
        "api_base": "http://127.0.0.1:6066",
        "vector_store": "Chroma (本地)",
        "show_uploader": False,
        "show_templates": False,
        "show_tools": False,
        "show_kb_search": False,
        "prompt_input": "",
        "sidebar_search": "",
        "sys_prompt": "你是一个专业的医疗健康助手，请用通俗易懂的语言回答用户的健康问题。",
        "model": "deepseek-chat",
        "deepseek_api_key": "",
        "vision_api_key": "",
        "stream": True,
        "is_logged_in": False,
        "username": "",
        "user_avatar": "boy",
        "show_login_form": False,
        "sidebar_user_menu_open": False,
        "sidebar_collapsed": False,
        "topbar_user_menu_open": False,
        "reg_gender_val": "boy",
        "auth_tab": "login",
        "auth_error": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if st.session_state["current_session_id"] is None:
        sessions = session_manager.get_all_sessions()
        if sessions:
            latest = sessions[0]
            st.session_state["current_session_id"] = latest["session_id"]
            st.session_state["messages"] = latest.get("messages", [])
            st.session_state["temp_kb_files"] = latest.get("temp_kb_files", [])
        else:
            new_session = session_manager.create_new_session()
            st.session_state["current_session_id"] = new_session["session_id"]


theme = st.session_state.get("theme", "light")
is_dark = theme == "dark"

bg_color = "#1f2937" if is_dark else "#ffffff"
sidebar_bg = "#111827" if is_dark else "#ffffff"
text_color = "#ffffff" if is_dark else "#222222"
card_bg = "#374151" if is_dark else "#f8fafc"
card_border = "#4b5563" if is_dark else "#e5e7eb"
input_bg = "#374151" if is_dark else "#fafafa"
input_border = "#4b5563" if is_dark else "#e5e7eb"
primary_color = "#4b5563" if is_dark else "#4b5563"
button_text = "#ffffff" if is_dark else "#ffffff"
placeholder_color = "#6b7280" if is_dark else "#6b7280"
slider_color = "#4b5563" if is_dark else "#4b5563"
caption_color = "#9ca3af" if is_dark else "#6b7280"

css = r"""
<style>
    .stApp {
        background-color: BG_COLOR;
    }
    [data-testid="stSidebar"] {
        background-color: SIDEBAR_BG;
        border-right: 1px solid CARD_BORDER;
        padding-top: 8px;
        overflow-y: auto;
        min-width: 280px !important;
        width: 280px !important;
        transform: none !important;
        position: relative !important;
        left: 0 !important;
        right: auto !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
    }
    [data-testid="stSidebar"] .block-container {
        flex: 1 !important;
        overflow-y: auto !important;
        padding-bottom: 20px !important;
        padding-top: 12px !important;
    }
    [data-testid="stSidebar"] .sidebar-header {
        padding: 16px 24px 8px 24px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-sizing: border-box !important;
    }
    [data-testid="stSidebar"] .sidebar-header .sidebar-title {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
        white-space: nowrap !important;
        line-height: 1.2 !important;
        flex-shrink: 0 !important;
        overflow: visible !important;
        text-overflow: clip !important;
        display: inline !important;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar { width: 4px; }
    [data-testid="stSidebar"]::-webkit-scrollbar-track { background: CARD_BG; }
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb { background: CARD_BORDER; border-radius: 2px; }
    [data-testid="stSidebar"] * { color: TEXT_COLOR !important; font-size: 14px !important; }
    [data-testid="stSidebar"] .stTextInput input::placeholder { color: PLACEHOLDER_COLOR !important; }
    [data-testid="stSidebar"] .stButton > button {
        color: TEXT_COLOR !important;
        background-color: CARD_BG !important;
        border: 1px solid CARD_BORDER !important;
    }
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stSidebar"] { padding-left: 0 !important; padding-right: 0 !important; }
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 160px !important;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 1px solid INPUT_BORDER !important;
        background-color: INPUT_BG !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        min-height: 80px !important;
        resize: none !important;
        color: TEXT_COLOR !important;
    }
    .stTextArea textarea::placeholder { color: PLACEHOLDER_COLOR !important; }
    .stTextArea textarea:focus {
        border-color: PRIMARY_COLOR !important;
        box-shadow: 0 0 0 2px rgba(75, 85, 99, 0.1) !important;
        outline: none !important;
    }
    .stButton > button[key="send_btn"] {
        background-color: PRIMARY_COLOR !important;
        color: BUTTON_TEXT !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        height: 80px !important;
        font-size: 15px !important;
        transition: background-color 0.2s ease !important;
    }
    .stButton > button[key="send_btn"]:hover { background-color: #374151 !important; }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 6px 10px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%) !important;
        border-color: #4A90E2 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.12) !important;
    }
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
        background-color: CARD_BG !important;
        color: TEXT_COLOR !important;
        border: 1px solid CARD_BORDER !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button:hover {
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f4ff 100%) !important;
        border-color: #4A90E2 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.12) !important;
    }
    .stButton > button {
        white-space: pre-wrap !important;
        height: auto !important;
        min-height: 50px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        border-radius: 16px !important;
        border: 1px solid CARD_BORDER !important;
        background-color: CARD_BG !important;
        color: TEXT_COLOR !important;
        text-align: center !important;
        transition: box-shadow 0.2s ease !important;
        box-shadow: none !important;
        margin-bottom: 6px !important;
    }
    .stButton > button:hover {
        border-color: PRIMARY_COLOR !important;
        background-color: CARD_BG !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        transform: none !important;
    }
    .stButton > button:active { transform: none !important; }
    .stButton > button[key="btn_voice_fallback"],
    .stButton > button[key="btn_voice_error"] {
        height: 80px !important;
        min-height: 80px !important;
        border-radius: 50% !important;
        background-color: CARD_BG !important;
        border: 1px solid CARD_BORDER !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        padding: 0 !important;
    }
    .stButton > button[key="btn_voice_fallback"] svg,
    .stButton > button[key="btn_voice_error"] svg { width: 28px !important; height: 28px !important; }
    .stButton > button[key="btn_voice_fallback"]:hover,
    .stButton > button[key="btn_voice_error"]:hover {
        background-color: #dbeafe !important;
        border-color: #bfdbfe !important;
        box-shadow: none !important;
    }
    .stHorizontalBlock .stButton > button {
        background-color: CARD_BG !important;
        border: 1px solid CARD_BORDER !important;
        color: TEXT_COLOR !important;
        font-size: 13px !important;
        padding: 6px 12px !important;
        min-height: auto !important;
        border-radius: 6px !important;
    }
    .stHorizontalBlock .stButton > button:hover {
        background-color: CARD_BG !important;
        color: TEXT_COLOR !important;
        border-color: PRIMARY_COLOR !important;
    }
    [data-testid="stChatMessageContent"] { max-width: 85% !important; }
    [data-testid="stChatMessage"][data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]) {
        align-items: flex-end !important;
    }
    .stSpinner > div { color: PRIMARY_COLOR !important; }
    .global-loader-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        z-index: 9999;
        display: flex; align-items: center; justify-content: center;
        backdrop-filter: blur(2px);
    }
    .global-loader-dots { display: flex; gap: 12px; }
    .global-loader-dot {
        width: 16px; height: 16px;
        background-color: #4A90E2;
        border-radius: 50%;
        animation: breathe 1.4s ease-in-out infinite;
    }
    .global-loader-dot:nth-child(1) { animation-delay: 0s; }
    .global-loader-dot:nth-child(2) { animation-delay: 0.2s; }
    .global-loader-dot:nth-child(3) { animation-delay: 0.4s; }
    .global-loader-dot:nth-child(4) { animation-delay: 0.6s; }
    .global-loader-dot:nth-child(5) { animation-delay: 0.8s; }
    @keyframes breathe {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }
    .sidebar-divider { border: none; border-top: 1px solid #e5e7eb; margin: 12px 0; }
    .dark .sidebar-divider { border-top-color: #374151; }
    .streamlit-expanderHeader {
        background-color: CARD_BG !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }
    .stRadio > label { font-size: 13px !important; color: TEXT_COLOR !important; }
    .stSlider > div > div > div { background-color: SLIDER_COLOR !important; }
    .stProgress > div > div > div { background-color: SLIDER_COLOR !important; }
    .stTextInput input {
        border-radius: 6px !important;
        border: 1px solid INPUT_BORDER !important;
        padding: 6px 10px !important;
        font-size: 13px !important;
        background-color: INPUT_BG !important;
        color: TEXT_COLOR !important;
    }
    .stTextInput input::placeholder { color: PLACEHOLDER_COLOR !important; }
    .stTextInput input:focus {
        border-color: PRIMARY_COLOR !important;
        box-shadow: 0 0 0 2px rgba(75, 85, 99, 0.1) !important;
        outline: none !important;
    }
    .stToast { background-color: PRIMARY_COLOR !important; color: white !important; }
    .streamlit-expanderHeader svg { width: 14px !important; height: 14px !important; }

    /* ========== 登录按钮样式（render_top_bar 内联覆盖） ========== */

    /* ========== 登录弹窗内「登录」按钮 - 浅蓝色背景黑色字体 ========== */
    .st-key-login_submit_btn button {
        background-color: #d0e8ff !important;
        color: #000000 !important;
        border: 1px solid #91c4f2 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .st-key-login_submit_btn button:hover {
        background-color: #b8d9f7 !important;
        color: #000000 !important;
    }

    /* ========== 注册弹窗内「注册」按钮 - 浅蓝色背景黑色字体 ========== */
    .st-key-register_submit_btn button {
        background-color: #d0e8ff !important;
        color: #000000 !important;
        border: 1px solid #91c4f2 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .st-key-register_submit_btn button:hover {
        background-color: #b8d9f7 !important;
        color: #000000 !important;
    }

    /* ========== 注册文字链接（蓝色） ========== */
    .st-key-go_register_btn button {
        background: none !important;
        background-color: transparent !important;
        border: none !important;
        color: #4A90E2 !important;
        font-size: 14px !important;
        padding: 4px 0 !important;
        min-height: auto !important;
        box-shadow: none !important;
        font-weight: 400 !important;
        border-radius: 0 !important;
        margin-bottom: 0 !important;
    }
    .st-key-go_register_btn button:hover {
        color: #357ABD !important;
        text-decoration: underline !important;
        background: none !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

</style>
"""

css = css.replace("BG_COLOR", bg_color)
css = css.replace("SIDEBAR_BG", sidebar_bg)
css = css.replace("TEXT_COLOR", text_color)
css = css.replace("CARD_BG", card_bg)
css = css.replace("CARD_BORDER", card_border)
css = css.replace("INPUT_BG", input_bg)
css = css.replace("INPUT_BORDER", input_border)
css = css.replace("PRIMARY_COLOR", primary_color)
css = css.replace("BUTTON_TEXT", button_text)
css = css.replace("PLACEHOLDER_COLOR", placeholder_color)
css = css.replace("SLIDER_COLOR", slider_color)
css = css.replace("CAPTION_COLOR", caption_color)

st.markdown(css, unsafe_allow_html=True)

# 侧边栏收缩展开过渡动画
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        transition: width 0.2s ease, min-width 0.2s ease, flex 0.2s ease !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        transition: opacity 0.2s ease !important;
    }
</style>
""", unsafe_allow_html=True)




def main():
    init_session_state()
    kb_manager.ensure_dirs()

    if st.session_state.get("is_loading", False):
        st.markdown("""
        <div class="global-loader-overlay">
            <div class="global-loader-dots">
                <div class="global-loader-dot"></div>
                <div class="global-loader-dot"></div>
                <div class="global-loader-dot"></div>
                <div class="global-loader-dot"></div>
                <div class="global-loader-dot"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ========== 侧边栏收缩/展开切换按钮 ==========
    collapsed = st.session_state.get("sidebar_collapsed", False)

    # 切换按钮样式：固定悬浮左上角
    st.markdown(f"""
    <style>
        .st-key-sb_toggle {{
            position: fixed !important;
            top: 12px !important;
            left: {"12px" if collapsed else "292px"} !important;
            z-index: 999999 !important;
            transition: left 0.2s ease !important;
        }}
        .st-key-sb_toggle button {{
            width: 40px !important;
            height: 40px !important;
            min-height: 40px !important;
            min-width: 40px !important;
            border-radius: 50% !important;
            padding: 0 !important;
            background: #fff !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
            border: 1px solid #e5e7eb !important;
            font-size: 16px !important;
            color: #333 !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        .st-key-sb_toggle button:hover {{
            background: #f0f0f0 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    arrow = "◀" if not collapsed else "▶"
    if st.button(arrow, key="sb_toggle", help="收起/展开侧边栏"):
        st.session_state["sidebar_collapsed"] = not collapsed
        st.rerun()

    # 收缩 CSS：直接隐藏侧边栏
    if collapsed:
        st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

    render_sidebar()

    render_top_bar()
    render_login_form()

    # 注入 WeChat 风格 CSS（必须在 render_* 之前，确保后续 st.markdown 中的 HTML 有样式）
    _inject_wechat_css()

    messages = st.session_state.get("messages", [])
    if len(messages) == 0:
        render_header()
        render_quick_cards()
    else:
        # 有消息时，用聊天头部 + 气泡列表；不再显示欢迎头部
        render_chat_messages()

    render_input_area()


if __name__ == "__main__":
    main()
