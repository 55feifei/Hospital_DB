"""通用工具：密码哈希、输入校验。"""

import hashlib
import re


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


PHONE_RE   = re.compile(r"^1[3-9]\d{9}$")
ID_CARD_RE = re.compile(r"^\d{17}[\dXx]$")


def is_valid_phone(phone: str) -> bool:
    return bool(phone) and bool(PHONE_RE.match(phone))


def is_valid_id_card(idc: str) -> bool:
    return bool(idc) and bool(ID_CARD_RE.match(idc))


def is_valid_username(username: str) -> bool:
    return bool(username) and re.match(r"^[A-Za-z0-9_]{3,30}$", username) is not None
