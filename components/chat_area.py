import streamlit as st
import streamlit.components.v1 as components
import time
import os
from utils import helpers
from utils import session_manager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _inject_wechat_css():
    """仿微信聊天界面 CSS —— 每次调用都注入，确保 rerun 后样式不丢失"""
    is_dark = st.session_state.get("theme", "light") == "dark"
    st.markdown("""
    <style>
    /* ====== 全局聊天页底色 ====== */
    .stApp { background-color: #f5f5f5 !important; }
    .stMainBlockContainer, .block-container {
        background-color: #f5f5f5 !important;
        padding-top: 0 !important;
        padding-bottom: 160px !important;
    }

    /* ====== 覆盖 Streamlit 默认按钮/输入框在聊天区的样式 ====== */
    .stMainBlockContainer .stButton > button,
    .block-container .stButton > button {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        color: #333 !important;
        border-radius: 6px !important;
        font-size: 12px !important;
        padding: 4px 12px !important;
        min-height: auto !important;
        box-shadow: none !important;
        margin-bottom: 0 !important;
    }

    /* ====== 消息行 ====== */
    .wechat-msg-row {
        display: flex !important;
        align-items: flex-start !important;
        margin-bottom: 16px !important;
        padding: 0 12px !important;
    }
    .wechat-msg-row.user { flex-direction: row-reverse !important; }

    /* ====== 圆形头像 40x40 ====== */
    .wechat-avatar {
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        min-height: 40px !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        flex-shrink: 0 !important;
        margin: 0 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .wechat-avatar img, .wechat-avatar svg {
        width: 40px !important;
        height: 40px !important;
        display: block !important;
    }
    .wechat-avatar img {
        object-fit: cover !important;
    }
    .wechat-avatar.placeholder {
        background: #4A90E2;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }

    /* ====== 气泡 ====== */
    .wechat-bubble {
        max-width: 70% !important;
        padding: 12px 14px !important;
        font-size: 15px !important;
        line-height: 1.65 !important;
        word-wrap: break-word !important;
        word-break: break-word !important;
        position: relative !important;
    }
    .wechat-bubble.ai {
        background: #ffffff !important;
        color: #1a1a1a !important;
        border-radius: 4px 16px 16px 16px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
    }
    .wechat-bubble.user {
        background: #07C160 !important;
        color: #ffffff !important;
        border-radius: 16px 4px 16px 16px !important;
    }
    .wechat-bubble.user a { color: #ffffff !important; text-decoration: underline !important; }

    /* ====== 时间戳 ====== */
    .wechat-time {
        font-size: 11px !important;
        color: #999 !important;
        text-align: center !important;
        margin-top: 4px !important;
    }

    /* ====== 免责声明 ====== */
    .wechat-bubble .disclaimer {
        font-size: 12px !important;
        color: #999 !important;
        margin-top: 10px !important;
        padding-top: 10px !important;
        border-top: 1px solid #eee !important;
    }

    /* ====== 聊天头部栏 ====== */
    .wechat-header {
        display: flex !important;
        align-items: center !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        border-bottom: 1px solid #e5e7eb !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 100 !important;
        gap: 10px !important;
    }
    .wechat-header-title {
        font-size: 17px !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
        flex: 1 !important;
    }

    /* ====== 参考来源卡片 ====== */
    .wechat-refs {
        background: #f8f9fa !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin-top: 8px !important;
        font-size: 12px !important;
        border-left: 3px solid #07C160 !important;
    }

    /* ====== 正在输入动画 ====== */
    .wechat-typing {
        display: flex !important;
        align-items: center !important;
        gap: 4px !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        border-radius: 4px 16px 16px 16px !important;
        max-width: 80px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
    }
    .wechat-typing-dot {
        width: 8px !important; height: 8px !important;
        border-radius: 50% !important;
        background: #c0c0c0 !important;
        animation: typing-bounce 1.4s ease-in-out infinite !important;
    }
    .wechat-typing-dot:nth-child(2) { animation-delay: 0.2s !important; }
    .wechat-typing-dot:nth-child(3) { animation-delay: 0.4s !important; }
    @keyframes typing-bounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }

    /* ====== 底部输入栏（固定） ====== */
    .bottom-bar-fixed {
        position: fixed !important;
        bottom: 0 !important;
        z-index: 9999 !important;
        background: #ffffff !important;
        border-top: 1px solid #e5e7eb !important;
        padding: 10px 16px 14px 16px !important;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.04) !important;
        box-sizing: border-box !important;
    }
    [class*="st-key-chat_input_"] textarea {
        border-radius: 24px !important;
        border: 1px solid #e5e7eb !important;
        font-size: 15px !important;
        min-height: 44px !important;
        max-height: 120px !important;
        resize: none !important;
        background: #f7f7f7 !important;
        padding: 10px 16px !important;
        color: #1a1a1a !important;
    }
    [class*="st-key-chat_input_"] textarea:focus {
        border-color: #07C160 !important;
        box-shadow: 0 0 0 2px rgba(7,193,96,0.12) !important;
        outline: none !important;
        background: #ffffff !important;
    }
    /* 隐藏 Streamlit 自动生成的 Ctrl+Enter 提示，改用自定义字符计数 */
    [class*="st-key-chat_input_"] small,
    [class*="st-key-chat_input_"] .st-cb {
        display: none !important;
    }
    .chat-char-count {
        text-align: right; font-size: 12px; color: #999;
        margin-top: 2px; padding-right: 4px;
    }

    /* ====== 隐藏 send 桥接按钮 ====== */
    .st-key-send_hidden_btn,
    .st-key-send_hidden_btn * {
        display: none !important; visibility: hidden !important;
        height: 0 !important; width: 0 !important;
        margin: 0 !important; padding: 0 !important;
        position: absolute !important; left: -9999px !important;
    }
    /* ====== 隐藏工具栏桥接按钮 ====== */
    [class*="st-key-ht_"], [class*="st-key-ht_"] * {
        display: none !important; visibility: hidden !important;
        height: 0 !important; width: 0 !important;
        margin: 0 !important; padding: 0 !important;
        position: absolute !important; left: -9999px !important;
    }
    /* ====== 消息工具栏按钮（气泡内部，自动等宽） ====== */
    .msg-toolbar {
        display: flex !important;
        gap: 6px !important;
        margin: 8px -14px -12px -14px !important;
        padding: 8px 14px !important;
        border-top: 1px solid #eee !important;
        width: auto !important;
        box-sizing: border-box !important;
    }
    .msg-toolbar .tool-btn {
        flex: 1 !important;
        height: 38px !important;
        border-radius: 16px !important;
        background: #f7f8fa !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        font-size: 14px !important;
        color: #333 !important;
        cursor: pointer !important;
        transition: background 0.2s ease !important;
        font-family: inherit !important;
        padding: 0 6px !important;
        user-select: none !important;
        -webkit-tap-highlight-color: transparent !important;
    }
    .msg-toolbar .tool-btn.btn-copy:hover { background: #e8f4ff !important; }
    .msg-toolbar .tool-btn.btn-retry:hover { background: #fff7e8 !important; }
    .msg-toolbar .tool-btn.btn-star:hover { background: #f7f8fa !important; }
    .msg-toolbar .tool-btn.btn-export:hover { background: #e8f9ef !important; }
    .msg-toolbar .tool-btn:disabled {
        opacity: 0.5 !important;
        pointer-events: none !important;
    }
    /* ====== 语音按钮 ====== */
    #voice_btn {
        width: 100% !important;
        height: 68px !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        background: #f3f4f6 !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    #voice_btn:hover { background: #e5e7eb !important; }
    #voice_btn svg {
        width: 24px !important;
        height: 24px !important;
    }
    #voice_btn.recording {
        background: #fee2e2 !important;
        border-color: #fca5a5 !important;
        animation: voice-breathe 1.5s ease-in-out infinite !important;
    }
    @keyframes voice-breathe {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.08); }
    }
    .voice-recording-hint {
        text-align: center !important;
        color: #ef4444 !important;
        font-size: 13px !important;
        margin-bottom: 8px !important;
        display: none !important;
    }
    .voice-recording-hint.show { display: block !important; }
    /* ====== Toast 容器 ====== */
    .toast-container {
        position: fixed !important;
        top: 80px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        z-index: 99999 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 8px !important;
        pointer-events: none !important;
    }
    .toast-msg {
        background: rgba(0,0,0,0.8) !important;
        color: #fff !important;
        padding: 8px 20px !important;
        border-radius: 20px !important;
        font-size: 13px !important;
        animation: toast-in 0.3s ease, toast-out 0.3s ease 2.5s forwards !important;
    }
    @keyframes toast-in {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes toast-out {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

    # ====== 深色模式覆盖 ======
    if is_dark:
        st.markdown("""
        <style>
        .stApp { background-color: #1f2937 !important; }
        .stMainBlockContainer, .block-container {
            background-color: #1f2937 !important;
        }
        .stMainBlockContainer .stButton > button,
        .block-container .stButton > button {
            background: #374151 !important;
            border: 1px solid #4b5563 !important;
            color: #e5e7eb !important;
        }
        .wechat-bubble.ai {
            background: #374151 !important;
            color: #e5e7eb !important;
        }
        .wechat-bubble .disclaimer {
            color: #9ca3af !important;
            border-top: 1px solid #4b5563 !important;
        }
        .wechat-header {
            background: #1f2937 !important;
            border-bottom: 1px solid #4b5563 !important;
        }
        .wechat-header-title { color: #e5e7eb !important; }
        .wechat-refs {
            background: #374151 !important;
        }
        .wechat-typing {
            background: #374151 !important;
        }
        .wechat-time { color: #9ca3af !important; }
        .bottom-bar-fixed {
            background: #1f2937 !important;
            border-top: 1px solid #4b5563 !important;
        }
        [class*="st-key-chat_input_"] textarea {
            background: #374151 !important;
            color: #e5e7eb !important;
            border: 1px solid #4b5563 !important;
        }
        [class*="st-key-chat_input_"] textarea::placeholder { color: #9ca3af !important; }
        [class*="st-key-chat_input_"] textarea:focus {
            border-color: #07C160 !important;
            background: #374151 !important;
        }
        .chat-char-count { color: #9ca3af !important; }
        .msg-toolbar {
            border-top: 1px solid #4b5563 !important;
        }
        .msg-toolbar .tool-btn {
            background: #374151 !important;
            color: #e5e7eb !important;
        }
        #voice_btn {
            background: #374151 !important;
            border: 1px solid #4b5563 !important;
        }
        #voice_btn:hover { background: #4b5563 !important; }
        .st-key-btn_upload_bottom button,
        .st-key-btn_template_bottom button,
        .st-key-btn_tools_bottom button {
            background: #374151 !important;
            border: 1px solid #4b5563 !important;
            color: #e5e7eb !important;
        }
        </style>
        """, unsafe_allow_html=True)


# ==================== Avatar Helpers ====================

def _get_user_avatar():
    avatar_type = st.session_state.get("user_avatar", "boy")
    avatar_file = "头像 男孩.svg" if avatar_type == "boy" else "头像 女孩.svg"
    avatar_path = os.path.join(BASE_DIR, avatar_file)
    return avatar_path if os.path.exists(avatar_path) else None


def _get_bot_avatar():
    avatar_path = os.path.join(BASE_DIR, "聊天机器人图标.svg")
    return avatar_path if os.path.exists(avatar_path) else None


def _render_avatar_html(avatar_path, fallback_text="?"):
    if avatar_path and os.path.exists(avatar_path):
        import base64, re
        ext = os.path.splitext(avatar_path)[1].lower()
        if ext == ".svg":
            with open(avatar_path, "r", encoding="utf-8") as f:
                svg = re.sub(
                    r'\s(width|height)\s*=\s*["\'][^"\']*["\']',
                    '', f.read(), flags=re.IGNORECASE
                )
            b64 = base64.b64encode(svg.encode("utf-8")).decode()
            return (
                f'<div class="wechat-avatar"'
                f' style="background-image:url(data:image/svg+xml;base64,{b64});'
                f'background-size:cover;background-position:center;"></div>'
            )
        else:
            with open(avatar_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return (
                f'<div class="wechat-avatar"'
                f' style="background-image:url(data:image/png;base64,{b64});'
                f'background-size:cover;background-position:center;"></div>'
            )
    letter = fallback_text[0].upper() if fallback_text else "?"
    return f'<div class="wechat-avatar placeholder">{letter}</div>'


# ==================== Recommendations ====================

RECOMMENDATIONS = [
    "高血压怎么平稳控制血压？",
    "慢阻肺日常怎么养护？",
    "术后伤口怎么避免发炎？",
    "糖尿病人一日三餐怎么吃？",
    "感冒多种药能不能混吃？",
    "胸口闷痛需要挂哪个科室？",
    "甲亢复查要看哪些指标？",
    "高血脂平时做什么运动？",
    "冠心病日常需要注意什么？",
]


# ==================== Header ====================

def render_header():
    """欢迎头部"""
    import base64
    logo_path = os.path.join(BASE_DIR, "护士AI图标.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_src = f"data:image/png;base64,{logo_b64}"
    else:
        logo_src = ""

    st.markdown(f"""
    <style>
    .header-wrap {{ text-align: center; padding: 32px 0 16px 0; }}
    .header-logo {{ width: 56px; height: 56px; object-fit: contain; margin-bottom: 12px; }}
    .header-title {{ color: #193350; font-weight: 700; font-size: 24px; margin: 0 0 8px 0; }}
    .header-sub {{ color: #333; font-weight: 600; font-size: 18px; margin: 0 0 6px 0; }}
    .header-desc {{ color: #999; font-size: 13px; margin: 0; }}
    </style>
    <div class="header-wrap">
        <img class="header-logo" src="{logo_src}">
        <h1 class="header-title">医疗 RAG 智能问诊机器人</h1>
        <p class="header-sub">有什么我能帮你的吗？</p>
        <p class="header-desc">本机器人仅提供健康科普参考，不能替代执业医师面诊，出现急症请立刻前往医院就诊。</p>
    </div>
    """, unsafe_allow_html=True)


# ==================== Quick Cards ====================

def render_quick_cards():
    """快捷问诊卡片"""
    st.markdown("""
    <style>
    .quick-card-btn button {
        border: 1px solid #e5e7eb !important;
        background: #ffffff !important;
        font-size: 14px !important;
        border-radius: 10px !important;
        transition: all 0.2s !important;
    }
    .quick-card-btn button:hover {
        border-color: #07C160 !important;
        background: #f0fff4 !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    for row in range(3):
        cols = st.columns(3, gap="small")
        for col in range(3):
            idx = row * 3 + col
            text = RECOMMENDATIONS[idx]
            with cols[col]:
                with st.container():
                    st.markdown('<div class="quick-card-btn">', unsafe_allow_html=True)
                    if st.button(text, key=f"rec_{idx}", use_container_width=True):
                        st.session_state[f"chat_input_{st.session_state.get('_input_ver', 0)}"] = text
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)


# ==================== Active Panel ====================

def render_active_panel():
    """展开的功能面板"""
    import base64
    active_panel = st.session_state.get("active_tool_panel", None)

    if active_panel == "upload":
        uploaded = st.file_uploader(
            "上传图片", type=["png", "jpg", "jpeg", "gif", "webp", "bmp"],
            key="chat_uploader", label_visibility="collapsed",
        )
        if uploaded:
            # 直接转 base64 存入 session_state，不用临时文件
            last_name = st.session_state.get("_last_uploaded_name", "")
            if uploaded.name != last_name:
                try:
                    img_b64 = base64.b64encode(uploaded.getvalue()).decode("utf-8")
                    ext = uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else "jpeg"
                    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
                    data_url = f"data:image/{mime};base64,{img_b64}"
                    pending = st.session_state.setdefault("pending_images", [])
                    # 按名称去重
                    if not any(p["name"] == uploaded.name for p in pending):
                        if len(pending) >= 8:
                            st.warning("最多8张图片")
                        else:
                            pending.append({"name": uploaded.name, "data_url": data_url})
                    st.session_state["_last_uploaded_name"] = uploaded.name
                except Exception:
                    st.error("图片处理失败")
            else:
                st.session_state["_last_uploaded_name"] = ""  # 重置，允许再次选择同名文件

        # 缩略图预览 + 单张删除
        pending = st.session_state.get("pending_images", [])
        if pending:
            st.caption(f"📷 待发送图片 ({len(pending)}张)：")
            cols = st.columns(min(len(pending), 4))
            for i, img in enumerate(pending):
                with cols[i % 4]:
                    st.markdown(
                        f'<img src="{img["data_url"]}" style="width:60px;height:60px;'
                        f'object-fit:cover;border-radius:6px;border:1px solid #e5e7eb;">',
                        unsafe_allow_html=True,
                    )
                    if st.button("✕", key=f"del_img_{i}"):
                        st.session_state["pending_images"].pop(i)
                        st.session_state["_last_uploaded_name"] = ""
                        st.rerun()

    if active_panel == "template":
        templates = [
            ("术前咨询", "我想咨询一下XXX手术前的注意事项"),
            ("慢病复查", "我患有多年的XX病，最近复查想了解指标解读"),
            ("用药答疑", "请问XX药物和XX能不能一起吃"),
            ("检验解读", "帮我看看这个检验报告有什么异常"),
            ("影像报告", "这个CT报告单的结果严重吗"),
        ]
        tcols = st.columns(len(templates))
        for idx, (label, hint) in enumerate(templates):
            with tcols[idx]:
                if st.button(label, key=f"tpl_{idx}", use_container_width=True):
                    st.session_state[f"chat_input_{st.session_state.get('_input_ver', 0)}"] = hint
                    st.session_state["active_tool_panel"] = None
                    st.rerun()

    if active_panel == "tool":
        tools = [
            ("病历生成", "根据症状生成规范门诊病历草稿"),
            ("指标换算", "医学指标单位换算与参考范围查询"),
            ("记录导出", "导出当前问诊记录为文档"),
        ]
        tcols = st.columns(len(tools))
        for idx, (label, hint) in enumerate(tools):
            with tcols[idx]:
                if st.button(label, key=f"tool_{idx}", use_container_width=True):
                    st.session_state[f"chat_input_{st.session_state.get('_input_ver', 0)}"] = f"【{label}】"
                    st.session_state["active_tool_panel"] = None
                    st.rerun()


# ==================== Chat Messages ====================

def render_chat_messages():
    """微信风格聊天消息列表"""
    messages = st.session_state.get("messages", [])
    user_avatar = _get_user_avatar()
    bot_avatar = _get_bot_avatar()
    username = st.session_state.get("username", "用户")

    # ---- 聊天头部栏 ----
    title = "健康咨询助手"
    if st.session_state.get("current_session_id"):
        session_data = session_manager.load_session(st.session_state.current_session_id)
        if session_data:
            title = session_data.get("title", title)

    st.markdown(f"""
    <div class="wechat-header">
        <span class="wechat-header-title" style="padding-left:12px;">{title}</span>
    </div>
    """, unsafe_allow_html=True)

    # ---- 消息列表 ----
    for i, msg in enumerate(messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        refs = msg.get("refs", [])

        if role == "user":
            # 用户消息：右侧绿色气泡
            attachments = msg.get("attachments", [])
            img_tags = ""
            for att in attachments:
                if att.get("type") == "image" and att.get("data_url"):
                    img_tags += f'<img src="{att["data_url"]}" style="max-width:200px;max-height:200px;border-radius:8px;margin-bottom:6px;display:block;">'
            st.markdown(f"""
            <div class="wechat-msg-row user">
                <div class="wechat-bubble user">{img_tags}{content}</div>
            </div>
            """, unsafe_allow_html=True)

        else:
            # AI 消息：气泡内嵌工具栏（自动等宽）
            import base64
            content_b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
            st.markdown(f"""
            <div class="wechat-msg-row">
                <div class="wechat-bubble ai">
                    {content}
                    <div class="msg-toolbar" data-content="{content_b64}">
                        <button class="tool-btn btn-copy" type="button" onclick="window._copyAi(this)">📋<span style="margin-left:4px;">复制</span></button>
                        <button class="tool-btn btn-retry" type="button" onclick="var b=window.parent.document.querySelector('.st-key-ht_retry_{i} button');if(b)b.click()">🔄<span style="margin-left:4px;">重试</span></button>
                        <button class="tool-btn btn-star" type="button" style="cursor:default">☆<span style="margin-left:4px;">收藏</span></button>
                        <button class="tool-btn btn-export" type="button" onclick="window._exportAi(this)">💾<span style="margin-left:4px;">导出</span></button>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 参考资料
            if refs:
                with st.expander("📖 参考医学资料", expanded=False):
                    for ref in refs:
                        source = ref.get("source", "未知来源")
                        page = ref.get("page", "-")
                        snippet = ref.get("content", "")
                        st.markdown(f"""
                        <div class="wechat-refs">
                            <div style="font-weight:600;color:#2c3e50;font-size:13px;">📄 {source} <span style="color:#7f8c8d;">(第{page}页)</span></div>
                            <div style="color:#555;font-size:13px;margin-top:4px;line-height:1.5;">{snippet}</div>
                        </div>
                        """, unsafe_allow_html=True)


            # 隐藏桥接按钮（仅重试需要触发 Python 回调）
            st.button("重试-R", key=f"ht_retry_{i}")

    # 检测重试按钮点击
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            if st.session_state.get(f"ht_retry_{i}"):
                st.session_state[f"ht_retry_{i}"] = False
                _handle_regenerate(i)
                break


def _handle_regenerate(msg_index: int):
    messages = st.session_state.get("messages", [])
    if msg_index > 0 and messages[msg_index - 1]["role"] == "user":
        user_msg = messages[msg_index - 1]["content"]
        st.session_state.messages = messages[:msg_index]
        _handle_send(user_msg, regenerate=True)


# ==================== Bottom Input Bar ====================

def render_bottom_bar():
    """微信风格底部输入栏"""
    active_panel = st.session_state.get("active_tool_panel", None)
    collapsed = st.session_state.get("sidebar_collapsed", False)

    st.markdown(f"""
    <div class="bottom-bar-fixed" style="left:{'0' if collapsed else '280px'};right:0;transition:left 0.2s ease;">
    """, unsafe_allow_html=True)

    # 工具栏行
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📎 上传", key="btn_upload_bottom", use_container_width=True):
            st.session_state["active_tool_panel"] = "upload" if active_panel != "upload" else None
            st.rerun()
    with c2:
        if st.button("📋 模板", key="btn_template_bottom", use_container_width=True):
            st.session_state["active_tool_panel"] = "template" if active_panel != "template" else None
            st.rerun()
    with c3:
        if st.button("🔧 工具", key="btn_tools_bottom", use_container_width=True):
            st.session_state["active_tool_panel"] = "tool" if active_panel != "tool" else None
            st.rerun()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # 输入行
    ic, sc, mc = st.columns([10, 1.2, 1.2])
    with ic:
        input_ver = st.session_state.get("_input_ver", 0)
        st.text_area(
            "输入消息",
            placeholder="描述你的症状或健康疑问...",
            key=f"chat_input_{input_ver}",
            label_visibility="collapsed",
            max_chars=2000,
            height=68,
        )
        st.markdown('<div class="chat-char-count" id="char_count">0/2000</div>', unsafe_allow_html=True)
    with sc:
        st.markdown(
            '<button id="send_btn" '
            'style="width:100%;height:68px;border:none;border-radius:50%;background:#07C160;color:#fff;'
            'cursor:pointer;display:flex;align-items:center;justify-content:center;'
            'transition:all 0.15s;padding:0;font-size:15px;font-weight:600;" '
            'onmouseover="this.style.background=\'#06AD56\'" '
            'onmouseout="this.style.background=\'#07C160\'">'
            '发送</button>',
            unsafe_allow_html=True,
        )
    with mc:
        st.markdown(
            '<button id="voice_btn" title="语音输入" '
            'style="width:100%;height:68px;border:1px solid #e5e7eb;border-radius:8px;background:#f3f4f6;cursor:pointer;'
            'display:flex;align-items:center;justify-content:center;font-size:24px;padding:0;">'
            '🎤</button>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


# ==================== Input Area (Full Assembly) ====================

def render_input_area():
    """底部输入区域合集"""

    # 底部按钮样式
    st.markdown("""
    <style>
    .st-key-btn_upload_bottom button,
    .st-key-btn_template_bottom button,
    .st-key-btn_tools_bottom button {
        background: #f7f7f7 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        color: #555 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        height: 36px !important;
        min-height: 36px !important;
        padding: 6px 10px !important;
        transition: all 0.15s !important;
    }
    .st-key-btn_upload_bottom button:hover,
    .st-key-btn_template_bottom button:hover,
    .st-key-btn_tools_bottom button:hover {
        background: #e8f5e9 !important;
        border-color: #07C160 !important;
        color: #07C160 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    render_active_panel()

    # Voice hint + toast container
    st.markdown("""
    <div id="voice_hint" class="voice-recording-hint">🎙️ 正在录音，语音实时转文字...</div>
    <div id="toast_container" class="toast-container"></div>
    """, unsafe_allow_html=True)

    render_bottom_bar()

    # 隐藏按钮（JS 桥接）
    user_input_val = st.session_state.get(f"chat_input_{st.session_state.get('_input_ver', 0)}", "")
    send_clicked = st.button("发送", key="send_hidden_btn")
    has_pending = bool(st.session_state.get("pending_images", []))
    if send_clicked and (user_input_val.strip() or has_pending):
        _handle_send(user_input_val.strip() if user_input_val.strip() else "")

    # JS：发送按钮 + Enter 键 + 语音识别 → 触发隐藏按钮
    components.html("""
    <script>
    (function() {
        var doc = window.parent.document;
        var top = window.parent;

        // ---- Send message ----
        if (!top._sendMsg) {
            top._sendMsg = function() {
                var btn = doc.querySelector('.st-key-send_hidden_btn button');
                if (btn) btn.click();
            };
        }

        // ---- Toast ----
        if (!top._showToast) {
            top._showToast = function(msg, type) {
                var container = doc.getElementById('toast_container');
                if (!container) return;
                var toast = doc.createElement('div');
                toast.className = 'toast-msg ' + (type || '');
                toast.textContent = msg;
                container.appendChild(toast);
                setTimeout(function() {
                    if (toast.parentNode) toast.parentNode.removeChild(toast);
                }, 3000);
            };
        }

        // ---- 复制 AI 回复 ----
        if (!top._copyAi) {
            top._copyAi = function(btn) {
                var toolbar = btn.closest('.msg-toolbar');
                var b64 = toolbar ? toolbar.getAttribute('data-content') : '';
                var text = b64 ? atob(b64) : '';
                if (text) {
                    navigator.clipboard.writeText(text).then(function() {
                        top._showToast('📋 复制成功');
                    }).catch(function() {
                        top._showToast('复制失败，请重试');
                    });
                }
            };
        }

        // ---- 导出 TXT ----
        if (!top._exportAi) {
            top._exportAi = function(btn) {
                var toolbar = btn.closest('.msg-toolbar');
                var b64 = toolbar ? toolbar.getAttribute('data-content') : '';
                var text = b64 ? atob(b64) : '';
                if (!text) { top._showToast('无内容可导出'); return; }
                var blob = new Blob([text], {type: 'text/plain;charset=utf-8'});
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = '健康咨询记录.txt';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                top._showToast('💾 文件已下载');
            };
        }

        function getTextarea() {
            return doc.querySelector('[class*="st-key-chat_input_"] textarea');
        }

        function setTextarea(text) {
            var ta = getTextarea();
            if (ta) {
                var setter = Object.getOwnPropertyDescriptor(top.HTMLTextAreaElement.prototype, 'value').set;
                setter.call(ta, text);
                ta.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }

        function focusTextarea() {
            var ta = getTextarea();
            if (ta) ta.focus();
        }

        function showToast(msg, type) {
            if (top._showToast) top._showToast(msg, type);
        }

        // ---- Voice Recognition ----
        if (!top._voiceRecognition) {
            top._voiceRecognition = {
                recognition: null,
                isRecording: false,
                finalTranscript: ''
            };

            function initSpeechRecognition() {
                if (!('webkitSpeechRecognition' in top) && !('SpeechRecognition' in top)) {
                    showToast('您的浏览器不支持语音识别', 'error');
                    return false;
                }
                var SR = top.SpeechRecognition || top.webkitSpeechRecognition;
                var rec = new SR();
                rec.continuous = true;
                rec.interimResults = true;
                rec.lang = 'zh-CN';

                rec.onresult = function(event) {
                    var interim = '';
                    for (var i = event.resultIndex; i < event.results.length; i++) {
                        if (event.results[i].isFinal) {
                            top._voiceRecognition.finalTranscript += event.results[i][0].transcript;
                        } else {
                            interim += event.results[i][0].transcript;
                        }
                    }
                    setTextarea(top._voiceRecognition.finalTranscript + interim);
                };

                rec.onerror = function(event) {
                    stopRec();
                    if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                        showToast('无法访问麦克风，请检查权限', 'error');
                    } else if (event.error !== 'no-speech') {
                        showToast('语音识别失败，请重试', 'error');
                    }
                };

                rec.onend = function() {
                    if (top._voiceRecognition.isRecording) {
                        try { rec.start(); } catch(e) {}
                    }
                };

                top._voiceRecognition.recognition = rec;
                return true;
            }

            top._toggleVoice = function() {
                if (!top._voiceRecognition.recognition) {
                    if (!initSpeechRecognition()) return;
                }
                if (top._voiceRecognition.isRecording) {
                    stopRec();
                } else {
                    startRec();
                }
            };

            function startRec() {
                if (!top._voiceRecognition.recognition) return;
                try {
                    top._voiceRecognition.finalTranscript = '';
                    setTextarea('');
                    top._voiceRecognition.recognition.start();
                    top._voiceRecognition.isRecording = true;
                    var vb = doc.getElementById('voice_btn');
                    var vh = doc.getElementById('voice_hint');
                    if (vb) vb.classList.add('recording');
                    if (vh) vh.classList.add('show');
                    showToast('开始录音...', 'success');
                } catch (e) {}
            }

            function stopRec() {
                top._voiceRecognition.isRecording = false;
                if (top._voiceRecognition.recognition) {
                    try { top._voiceRecognition.recognition.stop(); } catch(e) {}
                }
                var vb = doc.getElementById('voice_btn');
                var vh = doc.getElementById('voice_hint');
                if (vb) vb.classList.remove('recording');
                if (vh) vh.classList.remove('show');
                focusTextarea();
                showToast('录音结束', 'success');
            }
        }

        // ---- Bind events ----
        function bindEvents() {
            var sendBtn = doc.getElementById('send_btn');
            var voiceBtn = doc.getElementById('voice_btn');
            var ta = getTextarea();
            var ok = true;

            if (sendBtn && !sendBtn._b) {
                sendBtn.addEventListener('click', function(e) {
                    e.preventDefault(); top._sendMsg();
                });
                sendBtn._b = true;
            }
            if (!sendBtn || !sendBtn._b) ok = false;

            if (voiceBtn && !voiceBtn._vb) {
                voiceBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.blur();
                    top._toggleVoice();
                });
                voiceBtn._vb = true;
            }
            if (!voiceBtn || !voiceBtn._vb) ok = false;

            // 字符计数
            var cc = doc.getElementById('char_count');
            if (ta && cc) { cc.textContent = ta.value.length + '/2000'; }

            return ok;
        }

        var n = 0;
        (function poll() {
            n++;
            if (n > 80) return;
            if (!bindEvents()) setTimeout(poll, 100);
        })();
        setTimeout(poll, 500);
        setTimeout(poll, 1000);
        setTimeout(poll, 2000);
    })();
    </script>
    """, height=1, width=1)


# ==================== Send Handler ====================

def _handle_send(user_input: str, regenerate: bool = False):
    from utils import session_manager, api_client, helpers

    risk = helpers.check_risk_keywords(user_input)
    risk_prefix = f"⚠️ **{risk}**\n\n" if risk else ""

    model = st.session_state.get("model", "deepseek-chat")
    if model.startswith("deepseek-"):
        api_key = st.session_state.get("deepseek_api_key", "")
        if not api_key:
            st.toast("请先填写 DeepSeek API 密钥")
            return

    # 收集已上传的图片（base64 直接存在 session_state）
    pending_images = st.session_state.get("pending_images", [])
    image_b64_list = [img["data_url"] for img in pending_images]

    safe_input = helpers.desensitize_text(user_input)
    # 附件信息存到消息里，供渲染时显示图片
    st.session_state.messages.append({
        "role": "user",
        "content": safe_input,
        "refs": [],
        "attachments": [{"type": "image", "data_url": url} for url in image_b64_list],
    })
    if st.session_state.get("current_session_id"):
        session_manager.append_message(st.session_state["current_session_id"], "user", safe_input)

    # 清空待发送图片
    st.session_state["pending_images"] = []

    history = helpers.truncate_history(
        [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]],
        max_pairs=st.session_state.get("history_len", 1),
    )

    sys_prompt = st.session_state.get("sys_prompt", "你是一个专业的医疗健康助手，请用通俗易懂的语言回答用户的健康问题。")
    temperature = st.session_state.get("temperature", 0.7)
    top_p = st.session_state.get("top_p", 0.8)
    max_tokens = st.session_state.get("max_tokens", 2048)
    stream = st.session_state.get("stream", True)

    try:
        # 正在输入动画
        placeholder = st.empty()
        placeholder.markdown("""
        <div class="wechat-msg-row">
            <div class="wechat-typing">
                <div class="wechat-typing-dot"></div>
                <div class="wechat-typing-dot"></div>
                <div class="wechat-typing-dot"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        chunks = ""
        for chunk in api_client.chat_with_stream(
            query=safe_input,
            sys_prompt=sys_prompt,
            history=history,
            history_len=st.session_state.get("history_len", 1),
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=stream,
            model=model,
            images=image_b64_list if image_b64_list else None,
        ):
            chunks += chunk
            placeholder.markdown(f"""
            <div class="wechat-msg-row">
                <div class="wechat-bubble ai">{chunks}</div>
            </div>
            """, unsafe_allow_html=True)

        disclaimer = "\n\n---\n\n🩺 本内容仅供参考，不能替代执业医师面诊，急症请立即前往医院。"
        full_answer = risk_prefix + chunks + disclaimer
    except Exception as e:
        full_answer = risk_prefix + f"请求异常: {str(e)}"
    finally:
        # 清除流式占位符，避免与 rerun 后的渲染冲突导致内容消失
        placeholder.empty()

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_answer,
        "refs": [],
        "attachments": [],
    })

    if st.session_state.get("current_session_id"):
        session_manager.append_message(st.session_state["current_session_id"], "assistant", full_answer)

    try:
        st.session_state["_input_ver"] = st.session_state.get("_input_ver", 0) + 1
    except Exception:
        pass
    st.rerun()
