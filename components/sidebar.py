import streamlit as st
import streamlit.components.v1 as components
import os
import sys
from utils import session_manager, kb_manager

# 获取项目根目录（medical_rag_streamlit 目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_svg_avatar(avatar_type):
    """加载 SVG 头像内容"""
    avatar_file = "头像 男孩.svg" if avatar_type == "boy" else "头像 女孩.svg"
    avatar_path = os.path.join(BASE_DIR, avatar_file)
    try:
        with open(avatar_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def render_sidebar_user_info():
    """渲染侧边栏顶部用户信息模块（仅登录后显示）"""
    is_logged_in = st.session_state.get("is_logged_in", False)
    username = st.session_state.get("username", "")

    if not is_logged_in or not username:
        return

    avatar_type = st.session_state.get("user_avatar", "boy")
    user_menu_open = st.session_state.get("sidebar_user_menu_open", False)

    # ---- 用户信息行 ----
    theme = st.session_state.get("theme", "light")
    is_dark = theme == "dark"
    text_color = "#ffffff" if is_dark else "#2c3e50"
    border_color = "#4b5563" if is_dark else "#e5e7eb"

    svg_content = _load_svg_avatar(avatar_type)

    col_avatar, col_name, col_arrow = st.columns([0.8, 3.5, 0.5])
    with col_avatar:
        if svg_content:
            st.markdown(
                f"<div style='width:36px;height:36px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;margin-top:4px;'>{svg_content}</div>",
                unsafe_allow_html=True,
            )
        else:
            avatar_text = username[0].upper()
            st.markdown(
                f"<div style='width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#4A90E2,#357ABD);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:16px;margin-top:4px;'>{avatar_text}</div>",
                unsafe_allow_html=True,
            )
    with col_name:
        st.markdown(
            f"<div style='padding-top:12px;font-size:14px;font-weight:500;color:{text_color};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{username}</div>",
            unsafe_allow_html=True,
        )
    with col_arrow:
        arrow = "▾" if user_menu_open else "▸"
        if st.button(arrow, key="sidebar_user_menu_btn", help="展开用户菜单"):
            st.session_state["sidebar_user_menu_open"] = not user_menu_open
            st.rerun()

    # ---- 下拉菜单 ----
    if user_menu_open:
        st.markdown(
            f"<div style='background:{'#374151' if is_dark else '#ffffff'}; border-radius:8px; padding:4px 0; margin:8px 8px 0 8px; box-shadow:0 2px 8px rgba(0,0,0,0.1);'>",
            unsafe_allow_html=True,
        )

        # 退出登录
        if st.button("退出登录 🚪", key="sidebar_logout_btn", use_container_width=True):
            st.session_state["is_logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["sidebar_user_menu_open"] = False
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # 底部分隔线
    st.markdown(
        f"<hr style='margin:12px 0 4px 0; border:none; border-top:1px solid {border_color};'>",
        unsafe_allow_html=True,
    )


def render_sidebar():
    theme = st.session_state.get("theme", "light")
    is_dark = theme == "dark"
    text_color = "#ffffff" if is_dark else "#2c3e50"
    border_color = "#4b5563" if is_dark else "#e8edf3"
    caption_color = "#9ca3af" if is_dark else "#6b7280"
    card_bg = "#374151" if is_dark else "#f8fafc"
    is_logged_in = st.session_state.get("is_logged_in", False)
    
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <span class="sidebar-title">医疗RAG助手</span>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ 新建对话", key="sidebar_new", use_container_width=True):
                new_session = session_manager.create_new_session()
                st.session_state.current_session_id = new_session["session_id"]
                st.session_state.messages = []
                kb_manager.clear_temp_files()
                st.session_state.temp_kb_files = []
                st.rerun()
        with col2:
            if st.button("🗑️ 清空当前", key="sidebar_clear", use_container_width=True):
                st.session_state.messages = []
                st.session_state.temp_kb_files = []
                if st.session_state.get("current_session_id"):
                    session_manager.clear_temp_kb_files(st.session_state.current_session_id)
                    kb_manager.clear_temp_files()
                st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        search_keyword = st.text_input(
            "搜索",
            placeholder="搜索问诊标题、病症关键词",
            key="sidebar_search",
            label_visibility="collapsed"
        )

        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"<b style='color:{text_color}; font-size:14px;'>📋 历史对话</b>", unsafe_allow_html=True)

        sessions = session_manager.get_all_sessions()
        if search_keyword:
            sessions = session_manager.search_sessions(search_keyword)
            if sessions:
                st.caption(f"🔍 找到 {len(sessions)} 条相关对话")

        categories = {}
        for s in sessions:
            cat = s.get("category", "主对话")
            categories.setdefault(cat, []).append(s)

        for cat, cat_sessions in categories.items():
            with st.expander(f"📂 {cat} ({len(cat_sessions)})", expanded=(cat == "主对话")):
                for s in cat_sessions:
                    sid = s["session_id"]
                    title = s.get("title", "未命名对话")
                    msg_count = len(s.get("messages", []))
                    is_active = st.session_state.get("current_session_id") == sid

                    display_title = title
                    if search_keyword:
                        display_title = title.replace(
                            search_keyword,
                            f"**`{search_keyword}`**"
                        )

                    cols = st.columns([5, 1])
                    with cols[0]:
                        prefix = "▸ " if is_active else ""
                        btn_label = f"{prefix}{display_title} ({msg_count}条)"
                        if st.button(btn_label, key=f"btn_{sid}", use_container_width=True):
                            st.session_state["is_loading"] = True
                            if st.session_state.get("current_session_id") != sid:
                                kb_manager.clear_temp_files()
                                st.session_state.temp_kb_files = []
                            st.session_state.current_session_id = sid
                            loaded = session_manager.load_session(sid)
                            if loaded:
                                st.session_state.messages = loaded.get("messages", [])
                                st.session_state.temp_kb_files = loaded.get("temp_kb_files", [])
                            st.session_state["is_loading"] = False
                            st.rerun()
                    with cols[1]:
                        menu_key = f"show_menu_{sid}"
                        if st.button("⋮", key=f"menu_{sid}", help="更多操作"):
                            st.session_state[menu_key] = not st.session_state.get(menu_key, False)

                    if st.session_state.get(menu_key, False):
                        st.markdown(
                            f"""
                            <div style="background:{card_bg}; padding:8px 12px; border-radius:8px; margin:4px 0;">
                            """,
                            unsafe_allow_html=True,
                        )
                        new_name = st.text_input("重命名", value=title, key=f"rename_{sid}", label_visibility="collapsed")
                        op_cols = st.columns(3)
                        with op_cols[0]:
                            if st.button("💾 保存", key=f"save_{sid}", use_container_width=True):
                                session_manager.rename_session(sid, new_name)
                                st.session_state[menu_key] = False
                                st.rerun()
                        with op_cols[1]:
                            if st.button("🗑️ 删除", key=f"del_{sid}", use_container_width=True):
                                session_manager.delete_session(sid)
                                if st.session_state.get("current_session_id") == sid:
                                    st.session_state.current_session_id = None
                                    st.session_state.messages = []
                                    st.session_state.temp_kb_files = []
                                st.rerun()
                        with op_cols[2]:
                            if is_logged_in:
                                md = session_manager.export_session_to_markdown(sid)
                                st.download_button(
                                    "📥 导出",
                                    md,
                                    file_name=f"{title}.md",
                                    key=f"dl_{sid}",
                                    use_container_width=True,
                                )
                            else:
                                if st.button("🔒 登录后导出", key=f"login_dl_{sid}", use_container_width=True):
                                    st.session_state["show_login_form"] = True
                                    st.session_state["auth_tab"] = "login"
                                    st.session_state["auth_error"] = ""
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"<b style='color:{text_color}; font-size:14px;'>📚 知识库配置</b>", unsafe_allow_html=True)

        with st.expander("📤 上传医学资料", expanded=False):
            if not is_logged_in:
                st.markdown(f"""
                <div style="background:{card_bg}; padding:16px; border-radius:8px; text-align:center;">
                    <div style="font-size:24px; margin-bottom:8px;">🔒</div>
                    <div style="font-size:14px; color:{text_color}; font-weight:500;">登录后可用</div>
                    <div style="font-size:12px; color:{caption_color}; margin-top:4px;">上传医学资料需要登录账号</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔑 去登录", key="kb_login_trigger"):
                    st.session_state["show_login_form"] = True
                    st.session_state["auth_tab"] = "login"
                    st.session_state["auth_error"] = ""
                    st.rerun()
            else:
                kb_type = st.radio(
                    "上传到",
                    ["📁 全局公共库（永久）", "📂 本次对话临时库"],
                    index=0,
                    horizontal=True,
                    key="global_kb_type",
                )
                is_global = "全局" in kb_type

                uploaded = st.file_uploader(
                    "支持 PDF/Word/TXT/图片",
                    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
                    key="global_kb_uploader",
                )

                if uploaded:
                    if is_global:
                        path = kb_manager.add_kb_file(uploaded)
                        st.success(f"✅ 已上传到全局知识库: {uploaded.name}")
                    else:
                        path = kb_manager.add_temp_file(uploaded)
                        st.session_state.setdefault("temp_kb_files", []).append(path)
                        if st.session_state.get("current_session_id"):
                            session_manager.add_temp_kb_file(st.session_state["current_session_id"], path)
                        st.success(f"✅ 已添加到临时知识库: {uploaded.name}")

                    progress_bar = st.progress(0, text="解析中...")
                    for p in range(0, 101, 25):
                        progress_bar.progress(p, text=f"处理中... {p}%")
                    progress_bar.empty()
                    st.success("文件处理完成")

                stats = kb_manager.get_kb_stats()
                st.caption(f"📊 文档数: {stats['doc_count']} | 大小: {stats['total_size_mb']} MB")

                if st.button("🗑️ 清空知识库", key="clear_kb", use_container_width=True):
                    kb_manager.clear_kb()
                    st.success("全局知识库已清空")
                    st.rerun()

        with st.expander("⚙️ 向量库设置", expanded=False):
            vector_store = st.selectbox(
                "向量库类型",
                ["Chroma (本地)", "Milvus (远程)", "FAISS (本地)"],
                index=0,
            )
            st.session_state["vector_store"] = vector_store

            embed_bg = "#1f2937" if is_dark else "#eff6ff"
            embed_text = "#9ca3af" if is_dark else "#2c3e50"
            embed_highlight = "#60a5fa" if is_dark else "#2b6cb0"
            st.markdown(
                f"""
                <div style="background:{embed_bg}; padding:10px; border-radius:8px; margin:8px 0;">
                    <div style="font-size:13px; color:{embed_text};">
                        <b>🤖 嵌入模型</b><br>
                        <span style="color:{embed_highlight};">bge-large-zh-v1.5</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.text_input("API地址", value="http://127.0.0.1:8000", key="api_base")

        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"<b style='color:{text_color}; font-size:14px;'>⚙️ 模型参数</b>", unsafe_allow_html=True)

        with st.expander("🎛️ 参数调节", expanded=False):
            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; margin-bottom:4px;">
                    <b>系统提示词</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.session_state["sys_prompt"] = st.text_area(
                "系统提示词",
                value="你是一个专业的医疗健康助手，请用通俗易懂的语言回答用户的健康问题。",
                key="sys_prompt_input",
                label_visibility="collapsed",
                height=100,
            )

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; margin-bottom:4px;">
                    <b>温度系数</b> <span style="color:#ef4444;">⚠️ 医疗推荐 0.1~0.3</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.session_state["temperature"] = st.slider(
                "温度系数",
                0.01, 2.0, 0.7, 0.01,
                label_visibility="collapsed",
                help="数值越高回答越发散，更容易产生医学幻觉。医疗场景建议偏低值。",
            )

            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; margin-bottom:4px;">
                    <b>top_p</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.session_state["top_p"] = st.slider(
                "top_p",
                0.01, 1.0, 0.8, 0.01,
                label_visibility="collapsed",
                help="采样概率阈值，控制生成文本的多样性。",
            )

            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; margin-bottom:4px;">
                    <b>最大输出长度</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.session_state["max_tokens"] = st.slider(
                "最大输出长度",
                256, 8192, 1024, 8,
                label_visibility="collapsed",
            )

            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; margin-bottom:4px;">
                    <b>保留历史对话数量</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.session_state["history_len"] = st.slider(
                "历史对话数量",
                1, 10, 1, 1,
                label_visibility="collapsed",
                help="控制保留的历史对话轮数。",
            )

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            model_options = ["deepseek-chat", "deepseek-medical", "qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"]
            current_model = st.session_state.get("model", "deepseek-chat")
            try:
                default_index = model_options.index(current_model)
            except ValueError:
                default_index = 0
            
            model = st.selectbox(
                "模型选择",
                model_options,
                index=default_index,
                label_visibility="collapsed",
                help="qwen系列使用通义千问API，deepseek系列使用DeepSeek API",
            )
            st.session_state["model"] = model

            stream = st.checkbox("流式输出", value=True, key="stream_output")
            st.session_state["stream"] = stream

        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"<b style='color:{text_color}; font-size:14px;'>🎭 角色模式</b>", unsafe_allow_html=True)

        role = st.radio(
            "角色模式",
            ["👤 患者问诊模式", "👨‍⚕️ 医生辅助模式"],
            index=0,
            label_visibility="collapsed",
        )
        st.session_state["role_mode"] = "patient" if "患者" in role else "doctor"

        if st.session_state["role_mode"] == "patient":
            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; background:{card_bg}; padding:8px; border-radius:6px;">
                    📖 通俗化解释、禁忌提醒、就医建议
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="font-size:12px; color:{caption_color}; background:{card_bg}; padding:8px; border-radius:6px;">
                    📚 专业术语、文献溯源、鉴别诊断思路
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"<b style='color:{text_color}; font-size:14px;'>🎨 主题模式</b>", unsafe_allow_html=True)
        
        current_theme = st.session_state.get("theme", "light")
        theme_options = ["☀️ 浅色模式", "🌙 深色模式"]
        selected_theme = st.radio(
            "",
            theme_options,
            index=0 if current_theme == "light" else 1,
            label_visibility="collapsed",
            key="theme_radio",
        )
        
        new_theme = "light" if "浅色" in selected_theme else "dark"
        if new_theme != current_theme:
            st.session_state["theme"] = new_theme
            st.rerun()

        st.markdown("""
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        st.markdown(f"<b style='color:{text_color}; font-size:14px;'>📡 系统状态</b>", unsafe_allow_html=True)

        kb_stats = kb_manager.get_kb_stats()
        temp_files = len(st.session_state.get("temp_kb_files", []))

        st.markdown(
            f"""
            <div style="font-size:12px; color:{caption_color};">
                <table style="width:100%;">
                    <tr><td>📄 全局文档</td><td style="text-align:right;">{kb_stats['doc_count']} 篇</td></tr>
                    <tr><td>📁 临时文件</td><td style="text-align:right;">{temp_files} 个</td></tr>
                    <tr><td>🤖 模型</td><td style="text-align:right;">医疗RAG模型</td></tr>
                    <tr><td>🔗 接口</td><td style="text-align:right;">🟢 演示模式</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ──────────── 弹性空白 + 分割线 + 底部固定用户面板 ────────────
        st.markdown('<div class="sidebarBottomSpacer"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<hr style="margin:4px 0; border:none; border-top:1px solid {border_color};">',
            unsafe_allow_html=True,
        )

        # ── 底部用户面板（内联，避免缓存） ──
        bottom_is_logged_in = st.session_state.get("is_logged_in", False)
        bottom_username = st.session_state.get("username", "")

        if bottom_is_logged_in and bottom_username:
            avatar_type = st.session_state.get("user_avatar", "boy")
            svg_content = _load_svg_avatar(avatar_type)

            col_av, col_name, col_btn = st.columns([0.7, 2.5, 1])
            with col_av:
                if svg_content:
                    st.markdown(
                        f'<div style="width:40px;height:40px;border-radius:50%;overflow:hidden;'
                        f'display:flex;align-items:center;justify-content:center;flex-shrink:0;'
                        f'margin-top:2px;">{svg_content}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="width:40px;height:40px;border-radius:50%;'
                        f'background:linear-gradient(135deg,#4A90E2,#357ABD);'
                        f'display:flex;align-items:center;justify-content:center;'
                        f'color:white;font-weight:700;font-size:18px;flex-shrink:0;'
                        f'margin-top:2px;">{bottom_username[0].upper()}</div>',
                        unsafe_allow_html=True,
                    )
            with col_name:
                st.markdown(
                    f'<span style="font-size:16px;font-weight:600;color:{text_color};'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
                    f'display:inline-block;padding-top:8px;">{bottom_username}</span>',
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button("退出登录", key="sbb_logout", use_container_width=True):
                    st.session_state["is_logged_in"] = False
                    st.session_state["username"] = ""
                    st.rerun()
        else:
            if st.button("登录 / 注册", key="sbb_login_btn", use_container_width=True):
                st.session_state["show_login_form"] = True
                st.session_state["auth_tab"] = "login"
                st.session_state["auth_error"] = ""
                st.rerun()

        # CSS：强制侧边栏内容区为 flex 列，弹性空白把底部面板推到底
        st.markdown("""
        <style>
            section[data-testid="stSidebar"] > div:first-child > div:first-child {
                display: flex !important;
                flex-direction: column !important;
            }
            .sidebarBottomSpacer {
                flex: 1 !important;
                min-height: 12px !important;
            }
        </style>
        """, unsafe_allow_html=True)
