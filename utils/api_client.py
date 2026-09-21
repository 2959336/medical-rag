import requests
import json
import base64
from typing import List, Dict, Any, Optional, Iterator

DEFAULT_API_BASE = "http://127.0.0.1:6066"
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"
DASHSCOPE_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def get_api_base() -> str:
    try:
        import streamlit as st
        return st.session_state.get("api_base", DEFAULT_API_BASE)
    except Exception:
        return DEFAULT_API_BASE


def get_deepseek_api_key() -> str:
    try:
        import streamlit as st
        return st.session_state.get("deepseek_api_key", "")
    except Exception:
        return ""


def is_deepseek_model(model: str) -> bool:
    """判断是否为DeepSeek系列模型"""
    return model.startswith("deepseek-")


def get_vision_api_key() -> str:
    try:
        import streamlit as st
        return st.session_state.get("vision_api_key", "")
    except Exception:
        return ""


def describe_images(images: List[str], prompt: str = "请详细描述这张图片的内容，包括所有可见的文字、物体、人物、颜色、场景等。如果是医疗相关图片（如皮肤症状、检查报告、药品等），请特别关注医学细节。") -> str:
    """
    使用阿里云DashScope的qwen-vl-plus视觉模型识别图片并返回文字描述。
    images: base64 data_url 列表
    """
    api_key = get_vision_api_key()
    if not api_key:
        print("[DEBUG] describe_images: vision_api_key 未配置")
        return "[图片识别密钥未配置]"

    # 打印图片大小信息用于调试
    for i, img_url in enumerate(images):
        header_len = img_url.index(",") + 1 if "," in img_url else 0
        b64_len = len(img_url) - header_len
        approx_kb = b64_len * 3 / 4 / 1024
        print(f"[DEBUG] describe_images: 图片{i} 大小约 {approx_kb:.0f}KB, 格式={img_url[:30]}...")

    # 阿里云DashScope OpenAI兼容模式，用 qwen-vl-plus 视觉模型
    content_parts = []
    for img_url in images:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": img_url}
        })
    content_parts.append({"type": "text", "text": prompt})

    messages = [{"role": "user", "content": content_parts}]
    payload = {
        "model": "qwen-vl-plus",
        "messages": messages,
        "max_tokens": 1024,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        print(f"[DEBUG] describe_images: 发送请求到阿里云DashScope, 模型=qwen-vl-plus, 图片数={len(images)}")
        resp = requests.post(
            f"{DASHSCOPE_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=120,
        )
        print(f"[DEBUG] describe_images: 响应状态码={resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                print(f"[DEBUG] describe_images: 识别成功, 内容长度={len(content)}, 预览={content[:100]}...")
                return content
            else:
                print(f"[DEBUG] describe_images: 返回空内容, 完整响应={json.dumps(data, ensure_ascii=False)[:500]}")
                return "[图片识别返回空]"
        elif resp.status_code == 401:
            print(f"[DEBUG] describe_images: 401错误, 响应={resp.text[:300]}")
            return f"[图片识别失败：API Key 无效，HTTP {resp.status_code}]"
        else:
            try:
                err = resp.json()
                err_msg = err.get("error", {}).get("message", "未知错误")
                print(f"[DEBUG] describe_images: HTTP {resp.status_code}, 错误={err_msg}")
                return f"[图片识别失败：{err_msg}]"
            except Exception:
                print(f"[DEBUG] describe_images: HTTP {resp.status_code}, 响应文本={resp.text[:300]}")
                return f"[图片识别失败，HTTP {resp.status_code}]"
    except requests.exceptions.Timeout:
        print("[DEBUG] describe_images: 请求超时（120秒）")
        return "[图片识别超时，请尝试上传更小的图片]"
    except Exception as e:
        print(f"[DEBUG] describe_images: 异常={str(e)}")
        return f"[图片识别异常：{str(e)}]"

def chat_with_stream(
    query: str,
    sys_prompt: str = "你是一个有用的助手。",
    history: List[Dict[str, str]] = None,
    history_len: int = 1,
    temperature: float = 0.7,
    top_p: float = 0.8,
    max_tokens: int = 2048,
    stream: bool = True,
    model: str = "qwen-plus",
    images: List[str] = None,
) -> Iterator[str]:
    """
    通义千问和DeepSeek统一的流式聊天接口
    qwen系列使用通义千问API，deepseek系列使用DeepSeek API
    
    images: base64 data_url 列表，支持 OpenAI Vision 格式直传 DeepSeek
    """
    
    if is_deepseek_model(model):
        api_key = get_deepseek_api_key()
        if not api_key:
            yield "⚠️ 请先填写 DeepSeek API 密钥。"
            return

        # 构建消息
        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        if history and history_len > 0:
            keep_count = history_len * 2
            for h in history[-keep_count:]:
                role = h.get("role", "")
                content = h.get("content", "")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": content})

        # 图片识别：先调硅基流动 VL 模型取文字描述，再拼入 prompt
        actual_query = query
        if images:
            import streamlit as st
            with st.spinner("正在识别图片内容..."):
                desc = describe_images(images)
            if desc.startswith("[图片识别"):
                # 识别失败 → 直接把错误信息返回给用户，不发给 DeepSeek
                yield f"⚠️ {desc}\n\n图片识别未成功，请尝试以下操作：\n1. 上传更小尺寸的图片（建议 1MB 以内）\n2. 确保图片清晰、内容明确\n3. 或用文字描述您的症状，我来帮您分析"
                return
            else:
                actual_query = f"[图片描述]\n{desc}\n\n[用户问题]\n{query}"
                print(f"[DEBUG] chat_with_stream: 图片识别成功，拼接后的query长度={len(actual_query)}")

        messages.append({"role": "user", "content": actual_query})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        url = f"{DEEPSEEK_API_BASE}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=180)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "未知错误")
                    yield f"⚠️ DeepSeek API 调用失败：{error_msg}"
                except Exception:
                    yield f"⚠️ DeepSeek API 调用失败（HTTP {response.status_code}）"
                return

            if stream:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data)
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            else:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                yield content

        except requests.exceptions.ConnectionError:
            yield "⚠️ 网络连接失败，请检查网络设置。"
        except requests.exceptions.Timeout:
            yield "⚠️ 请求超时，请稍后重试。"
        except Exception as e:
            yield f"⚠️ DeepSeek API 调用异常：{str(e)}"
    
    else:
        # 通义千问系列模型（原有逻辑）
        payload = {
            "query": query,
            "sys_prompt": sys_prompt,
            "history_len": history_len,
            "history": history or [],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": stream,
            "model": model,
        }
        api_base = get_api_base()
        url = f"{api_base}/chat"

        try:
            response = requests.post(url, json=payload, stream=True, timeout=180)
            response.raise_for_status()

            if stream:
                for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                    if chunk:
                        yield chunk
            else:
                chunks = ""
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        chunks += chunk
                yield chunks
        except requests.exceptions.ConnectionError:
            yield "⚠️ 后端服务未连接。请确保后端服务已启动，或检查接口地址配置。"
        except Exception as e:
            yield f"⚠️ 后端请求失败：{str(e)}"


def chat_with_rag(
    session_id: str,
    user_query: str,
    history: List[Dict[str, str]],
    top_k: int = 5,
    temperature: float = 0.2,
    role_mode: str = "patient",
    temp_kb_files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    payload = {
        "session_id": session_id,
        "user_query": user_query,
        "top_k": top_k,
        "temperature": temperature,
        "role_mode": role_mode,
        "history": history,
        "temp_kb_files": temp_kb_files or [],
    }
    api_base = get_api_base()
    url = f"{api_base}/api/chat"
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {
            "answer": "⚠️ 后端服务未连接。当前为演示模式，以下为模拟回复。\n\n请确保RAG后端服务已启动，或检查接口地址配置。",
            "ref_docs": [],
            "risk_warn": "",
            "disclaimer": "本内容仅供参考，不能替代执业医师面诊，急症请立即前往医院。",
        }
    except Exception as e:
        return {
            "answer": f"请求异常: {str(e)}",
            "ref_docs": [],
            "risk_warn": "",
            "disclaimer": "本内容仅供参考，不能替代执业医师面诊，急症请立即前往医院。",
        }


def mock_chat_response(user_query: str, role_mode: str = "patient") -> Dict[str, Any]:
    if role_mode == "doctor":
        answer = (
            f"**【专业辅助模式】**\n\n"
            f"针对「{user_query}」的临床分析如下：\n\n"
            f"1. **鉴别诊断思路**：需结合患者主诉、体格检查及辅助检查综合判断。\n"
            f"2. **诊疗要点**：建议参考最新临床指南，关注循证医学证据等级。\n"
            f"3. **用药参考**：具体剂量需根据患者肝肾功能及药物相互作用调整。\n\n"
            f"> 提示：本回复为演示内容，接入真实后端后可获取RAG检索结果。"
        )
    else:
        answer = (
            f"**【患者通俗模式】**\n\n"
            f"您好，关于「{user_query}」的建议如下：\n\n"
            f"1. **日常注意**：保持规律作息，遵医嘱用药，定期复查相关指标。\n"
            f"2. **危险预警**：如出现胸痛、呼吸困难、意识模糊等，请立即前往急诊。\n"
            f"3. **就诊提示**：建议携带既往病历和检查报告，便于医生全面评估。\n\n"
            f"> 提示：本回复为演示内容，接入真实后端后可获取RAG检索结果。"
        )
    return {
        "answer": answer,
        "ref_docs": [
            {"source": "《内科学》第9版", "content": "相关章节要点摘要...", "page": "128"},
            {"source": "《中国高血压防治指南》", "content": "指南推荐意见摘要...", "page": "45"},
        ],
        "risk_warn": "",
        "disclaimer": "本内容仅供参考，不能替代执业医师面诊，急症请立即前往医院。",
    }
