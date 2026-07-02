"""
secrets.py — 凭据安全管理模块
敏感配置（API Key、SMTP 密码等）通过 keyring 存储到 Windows 凭据管理器，
不在磁盘上留下明文。.env 只保留非敏感配置。

读取优先级：keyring → 环境变量/.env → 报错

用法：
    from secrets import get_secret
    api_key = get_secret("OPENAI_API_KEY")
"""

import keyring
import os

# keyring 服务名，所有凭据归到同一组
SERVICE_NAME = "github-trend-monitor"

# 需要通过 keyring 管理的敏感字段
SENSITIVE_KEYS = {
    "OPENAI_API_KEY",
    "SMTP_PASS",
}


def get_secret(key: str) -> str:
    """
    安全读取配置值。
    优先级：keyring → 环境变量 → 抛异常

    :param key: 配置键名，如 "OPENAI_API_KEY"
    :return: 配置值
    :raises ValueError: 未找到配置
    """
    # 1. 优先从 keyring 读取
    val = keyring.get_password(SERVICE_NAME, key)
    if val:
        return val

    # 2. 回退到环境变量（兼容不使用 keyring 的场景）
    val = os.environ.get(key, "")
    if val:
        return val

    # 3. 找不到
    raise ValueError(
        f"未找到配置 {key}。"
        f"请运行 setup_secrets.py 录入凭据，"
        f"或在环境变量中设置。"
    )


def set_secret(key: str, value: str) -> None:
    """将敏感值写入 keyring。"""
    keyring.set_password(SERVICE_NAME, key, value)


def delete_secret(key: str) -> None:
    """从 keyring 删除指定凭据。"""
    try:
        keyring.delete_password(SERVICE_NAME, key)
    except keyring.errors.PasswordDeleteError:
        pass  # 不存在则忽略


def list_secrets() -> list[str]:
    """列出 keyring 中已存储的凭据键名（不暴露值）。"""
    stored = []
    for key in SENSITIVE_KEYS:
        val = keyring.get_password(SERVICE_NAME, key)
        if val:
            stored.append(key)
    return stored
