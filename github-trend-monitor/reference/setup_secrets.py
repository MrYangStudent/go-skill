"""
setup_secrets.py — 一次性凭据录入脚本
将敏感配置写入 Windows 凭据管理器（via keyring），无需明文存储。

用法：
    python setup_secrets.py          # 交互式录入所有凭据
    python setup_secrets.py --check  # 检查已有凭据状态
    python setup_secrets.py --reset  # 清除所有已存凭据
"""

import getpass
import sys
from pathlib import Path

# 确保能导入项目模块
sys.path.insert(0, str(Path(__file__).parent))

from secrets import SERVICE_NAME, SENSITIVE_KEYS, set_secret, delete_secret, list_secrets
import keyring


# 每个敏感字段的提示信息
SECRET_PROMPTS = {
    "OPENAI_API_KEY": {
        "label": "OpenAI / DeepSeek API Key",
        "hint": "如 sk-db4b1bba8be340ce...",
        "example": "sk-xxxxxxxxxxxxxxxx",
    },
    "SMTP_PASS": {
        "label": "SMTP 授权密码",
        "hint": "QQ邮箱 → 设置 → 账户 → 生成授权码",
        "example": "16位授权码",
    },
}


def check_status():
    """检查凭据存储状态。"""
    print(f"服务名：{SERVICE_NAME}")
    print("-" * 40)
    for key in SENSITIVE_KEYS:
        val = keyring.get_password(SERVICE_NAME, key)
        status = "✅ 已存储" if val else "❌ 未设置"
        print(f"  {key}: {status}")
    print()
    stored = list_secrets()
    print(f"已存储 {len(stored)}/{len(SENSITIVE_KEYS)} 项")


def setup_all():
    """交互式录入所有凭据。"""
    print("=" * 52)
    print(" GitHub 趋势监控 — 凭据录入")
    print("=" * 52)
    print(f"\n凭据将存储到系统密钥环（服务名: {SERVICE_NAME}）")
    print("输入时不会显示明文，按 Enter 跳过已有项\n")

    for key in SENSITIVE_KEYS:
        # 检查是否已存在
        existing = keyring.get_password(SERVICE_NAME, key)
        if existing:
            masked = existing[:4] + "****" + existing[-4:]
            overwrite = input(f"\n{key} 已存在（{masked}），是否覆盖？[y/N] ").strip().lower()
            if overwrite != "y":
                print(f"  → 跳过 {key}")
                continue

        prompt_info = SECRET_PROMPTS.get(key, {"label": key, "hint": "", "example": ""})
        print(f"\n📌 {prompt_info['label']}")
        if prompt_info["hint"]:
            print(f"   提示：{prompt_info['hint']}")
        if prompt_info["example"]:
            print(f"   示例：{prompt_info['example']}")

        value = getpass.getpass(f"   请输入 {key}: ").strip()
        if not value:
            print(f"  → 未输入，跳过")
            continue

        set_secret(key, value)
        # 验证写入
        verify = keyring.get_password(SERVICE_NAME, key)
        if verify == value:
            print(f"  ✅ {key} 已安全存储")
        else:
            print(f"  ❌ {key} 存储失败，请重试")

    print("\n" + "=" * 52)
    check_status()


def reset_all():
    """清除所有已存凭据。"""
    print("⚠️ 即将清除所有已存储凭据！")
    confirm = input("确认删除？输入 YES 继续: ").strip()
    if confirm != "YES":
        print("已取消")
        return

    for key in SENSITIVE_KEYS:
        delete_secret(key)
        print(f"  🗑️ 已删除 {key}")
    print("\n清除完成")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--check":
            check_status()
        elif arg == "--reset":
            reset_all()
        else:
            print(f"未知参数: {arg}")
            print("用法: setup_secrets.py [--check|--reset]")
    else:
        setup_all()


if __name__ == "__main__":
    main()
