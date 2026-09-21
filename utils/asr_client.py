# -*- coding: utf-8 -*-
"""
火山引擎豆包语音识别大模型（ASR）客户端
接口：流式输入模式 WebSocket（bigmodel_nostream）
认证：新版控制台 X-Api-Key
凭据仅存后端。
"""
import struct
import json
import uuid
import asyncio

try:
    import websockets
except ImportError:
    websockets = None

# ====== 凭据（仅后端） ======
VOLC_API_KEY = "3a143257-4799-495a-9f30-30c680b8edf8"
# 豆包流式语音识别模型 2.0（小时版）
VOLC_ASR_RESOURCE_ID = "volc.seedasr.sauc.duration"

ASR_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"

# 协议常量
PROTOCOL_VERSION = 1
HEADER_SIZE = 1  # 1 * 4 = 4 bytes

MSG_FULL_CLIENT_REQUEST = 0b0001
MSG_AUDIO_ONLY = 0b0010
MSG_SERVER_RESPONSE = 0b1001
MSG_SERVER_ERROR = 0b1111

FLAG_NO_SEQ = 0b0000
FLAG_POS_SEQ = 0b0001
FLAG_LAST_PACKET = 0b0010

SERIAL_JSON = 0b0001
SERIAL_NONE = 0b0000
COMPRESS_NONE = 0b0000


def _build_header(msg_type, flags, serial=SERIAL_NONE, compress=COMPRESS_NONE):
    """构建4字节协议头。"""
    b0 = (PROTOCOL_VERSION << 4) | HEADER_SIZE
    b1 = (msg_type << 4) | flags
    b2 = (serial << 4) | compress
    b3 = 0
    return bytes([b0, b1, b2, b3])


async def _recognize_async(pcm_bytes: bytes) -> str:
    """异步WebSocket识别PCM音频，返回文本。"""
    if websockets is None:
        raise RuntimeError("缺少 websockets 库，请运行: pip install websockets")

    headers = {
        "X-Api-Key": VOLC_API_KEY,
        "X-Api-Resource-Id": VOLC_ASR_RESOURCE_ID,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }

    async with websockets.connect(ASR_URL, additional_headers=headers) as ws:
        # 1. 发送 full client request（JSON 配置）
        config = {
            "user": {"uid": "med_rag_user"},
            "audio": {
                "format": "pcm",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
                "language": "zh-CN",
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
            },
        }
        payload = json.dumps(config).encode("utf-8")
        header = _build_header(MSG_FULL_CLIENT_REQUEST, FLAG_NO_SEQ, SERIAL_JSON)
        msg = header + struct.pack(">I", len(payload)) + payload
        await ws.send(msg)

        # 2. 快速发送所有音频（大chunk，无sleep）
        chunk_size = 32000  # 1秒音频/片，快速发送
        seq = 1
        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i:i + chunk_size]
            header = _build_header(MSG_AUDIO_ONLY, FLAG_POS_SEQ)
            msg = header + struct.pack(">i", seq) + struct.pack(">I", len(chunk)) + chunk
            await ws.send(msg)
            seq += 1

        # 3. 发送最后一包（负包）
        header = _build_header(MSG_AUDIO_ONLY, FLAG_LAST_PACKET)
        msg = header + struct.pack(">I", 0)
        await ws.send(msg)

        # 4. 接收响应（nostream模式返回一个响应，超时15秒）
        result_text = ""
        try:
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=15)
                if isinstance(response, str) or len(response) < 8:
                    continue

                msg_type = (response[1] >> 4) & 0x0F

                if msg_type == MSG_SERVER_ERROR:
                    psize = struct.unpack(">I", response[4:8])[0]
                    err_payload = response[8:8 + psize]
                    raise RuntimeError(f"ASR错误: {err_payload.decode('utf-8', errors='replace')[:300]}")

                if msg_type == MSG_SERVER_RESPONSE:
                    psize = struct.unpack(">I", response[8:12])[0]
                    resp_payload = response[12:12 + psize]
                    try:
                        data = json.loads(resp_payload.decode("utf-8"))
                    except json.JSONDecodeError:
                        break

                    # result 是 dict，含 text 字段
                    result = data.get("result", {})
                    if isinstance(result, dict):
                        result_text = result.get("text", "")
                    elif isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict):
                                result_text += item.get("text", "")
                    # nostream 模式收到响应即结束
                    break
        except asyncio.TimeoutError:
            if not result_text:
                raise RuntimeError("ASR响应超时（15秒）")

        return result_text


def recognize(pcm_bytes: bytes) -> str:
    """同步包装：识别PCM音频返回文本。"""
    try:
        loop = asyncio.new_event_loop()
        text = loop.run_until_complete(_recognize_async(pcm_bytes))
        loop.close()
        return text
    except Exception as e:
        raise RuntimeError(f"语音识别失败: {e}")


def recognize_or_error(pcm_bytes: bytes) -> dict:
    """安全包装，供 Streamlit 调用。"""
    try:
        text = recognize(pcm_bytes)
        if text:
            return {"ok": True, "text": text}
        return {"ok": False, "msg": "未识别到语音内容"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
