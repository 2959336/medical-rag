# -*- coding: utf-8 -*-
"""
火山引擎豆包语音合成大模型 2.0 客户端
音色：zh_female_tianmeitaozi_uranus_bigtts（甜美桃子 2.0）
接口：V3 HTTP 单向流式（新版控制台认证，只需 X-Api-Key）
凭据仅存后端，前端不暴露任何密钥。
"""
import re
import uuid
import base64
import json
import requests

# ====== 凭据（仅后端，禁止暴露到前端） ======
# 新版控制台 API Key（控制台 > API Key管理 获取）
VOLC_API_KEY = "3a143257-4799-495a-9f30-30c680b8edf8"
# 2.0 音色专用资源 ID
VOLC_RESOURCE_ID = "seed-tts-2.0"
# 甜美桃子 2.0（注意是 uranus 后缀，mars 后缀是 1.0 版本）
DEFAULT_SPEAKER = "zh_female_tianmeitaozi_uranus_bigtts"

V3_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"

# 单次合成文本上限（超过则分段）
MAX_SEGMENT_LEN = 300


def _split_text(text: str, max_len: int = MAX_SEGMENT_LEN):
    """按句子边界切分长文本，单段不超过 max_len 字。"""
    if not text:
        return []
    sentences = re.split(r'(?<=[。！？!?\n])', text)
    segments, cur = [], ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        while len(s) > max_len:
            if cur:
                segments.append(cur)
                cur = ""
            segments.append(s[:max_len])
            s = s[max_len:]
        if len(cur) + len(s) <= max_len:
            cur += s
        else:
            if cur:
                segments.append(cur)
            cur = s
    if cur:
        segments.append(cur)
    return segments


def _synthesis_once(text: str, speaker: str = DEFAULT_SPEAKER,
                     speed: int = 0, volume: int = 0) -> bytes:
    """单段文本合成，返回 mp3 字节。失败抛异常。"""
    headers = {
        "X-Api-Key": VOLC_API_KEY,
        "X-Api-Resource-Id": VOLC_RESOURCE_ID,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    payload = {
        "req_params": {
            "text": text,
            "speaker": speaker,
            "audio_params": {
                "format": "mp3",
                "sample_rate": 24000,
                "speech_rate": speed,    # [-50, 100]
                "loudness_rate": volume,  # [-50, 100]
            },
        },
    }

    session = requests.Session()
    resp = session.post(V3_URL, headers=headers, json=payload, stream=True, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    audio_chunks = []
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            chunk = json.loads(line.decode("utf-8"))
        except Exception:
            continue
        code = chunk.get("code")
        msg = chunk.get("message", "")
        data = chunk.get("data")
        if code == 20000000:
            break
        if code not in (0, None):
            raise RuntimeError(f"Volc TTS error code={code}, message={msg}")
        if data:
            audio_chunks.append(base64.b64decode(data))

    if not audio_chunks:
        raise RuntimeError("未收到音频数据")
    return b"".join(audio_chunks)


def synthesize(text: str, speaker: str = DEFAULT_SPEAKER,
               speed: int = 0, volume: int = 0) -> bytes:
    """
    文本转语音（甜美桃子 2.0 音色）。
    长文本自动分段（≤300字/段）合成后拼接为单个 mp3。
    返回 mp3 字节流。
    """
    if not text or not text.strip():
        raise ValueError("文本不能为空")

    segments = _split_text(text.strip())
    if not segments:
        raise ValueError("文本切分后为空")

    if len(segments) == 1:
        return _synthesis_once(segments[0], speaker, speed, volume)

    parts = []
    for seg in segments:
        parts.append(_synthesis_once(seg, speaker, speed, volume))
    return b"".join(parts)


def synthesize_or_error(text: str) -> dict:
    """
    供 Streamlit 调用的安全包装。
    成功返回 {"ok": True, "audio": mp3_bytes}
    失败返回 {"ok": False, "msg": "错误描述"}
    """
    try:
        audio = synthesize(text)
        return {"ok": True, "audio": audio}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
