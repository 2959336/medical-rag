import re
from typing import List


def desensitize_text(text: str) -> str:
    """对敏感个人信息脱敏，但保留医疗术语"""
    # 身份证号（18位）
    text = re.sub(r"\b\d{17}[\dXx]\b", lambda m: m.group()[:4] + "**********" + m.group()[-3:], text)
    # 手机号（11位）
    text = re.sub(r"\b1[3-9]\d{9}\b", lambda m: m.group()[:3] + "****" + m.group()[-4:], text)
    # 姓名脱敏仅对明显是姓名的模式（如"姓名：张三"），不处理自由文本中的短中文片段
    text = re.sub(r"(姓名[：:])\s*[\u4e00-\u9fa5]{2,4}", r"\1***", text)
    return text


def check_risk_keywords(text: str) -> str:
    """检测紧急风险，仅返回警告文字（不阻断对话）"""
    risk_patterns = [
        (r"自杀|自残|结束生命|不想活了", "⚠️ 检测到涉及自我伤害的内容，请拨打心理援助热线 400-161-9995 或前往医院。"),
        (r"在家手术|自己手术|自行手术", "⚠️ 手术需在正规医疗机构进行，请勿自行操作。"),
    ]
    for pattern, warning in risk_patterns:
        if re.search(pattern, text):
            return warning
    return ""


def truncate_history(messages: List[dict], max_pairs: int = 10) -> List[dict]:
    # 保留最近 max_pairs 轮对话（每轮包含 user + assistant）
    if len(messages) <= max_pairs * 2:
        return messages
    return messages[-max_pairs * 2:]


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
