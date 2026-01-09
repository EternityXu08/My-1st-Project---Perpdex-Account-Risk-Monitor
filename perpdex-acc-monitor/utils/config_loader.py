import os
from dotenv import load_dotenv
import yaml
from typing import Dict, List, Any

# === 调试添加：打印加载路径和部分环境变量 ===
print("当前工作目录:", os.getcwd())
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
print("尝试加载 .env 文件路径:", dotenv_path)
print("该路径是否存在:", os.path.exists(dotenv_path))

load_dotenv(dotenv_path=dotenv_path)  # 显式指定路径，强制加载 config/.env

# 调试：打印所有包含 GRVT 或 PARADEX 的环境变量
print("\n当前环境变量中包含 GRVT 或 PARADEX 的键:")
for key, value in os.environ.items():
    if "GRVT" in key or "PARADEX" in key:
        print(f"  {key} = {value[:20]}...")  # 只显示前20位

print("\n=== load_dotenv 完成 ===\n")
# === 调试结束 ===

load_dotenv()

def get_all_accounts(exchange: str) -> List[Dict[str, str]]:
    """
    改进版：更宽松地检测多账户
    GRVT: 寻找所有包含 GRVT_ 并以数字结尾的变量作为 API_KEY，同数字的 SUB_ACCOUNT_ID
    Paradex: 寻找所有包含 PARADEX_JWT_ 并以数字结尾的变量
    """
    accounts = []
    env_vars = dict(os.environ)
    prefix = exchange.upper() + "_"
    
    # 收集所有可能的账户编号
    possible_numbers = set()
    for key in env_vars:
        if key.startswith(prefix):
            # 提取可能的数字后缀
            parts = key.split("_")
            if len(parts) >= 3 and parts[-1].isdigit():
                possible_numbers.add(parts[-1])
            elif len(parts) >= 2 and parts[-1].isdigit():
                possible_numbers.add(parts[-1])
    
    for num in sorted(possible_numbers):
        account = {}
        if exchange == "grvt":
            api_key = os.getenv(f"GRVT_API_KEY_{num}") or os.getenv(f"{prefix}API_KEY_{num}")
            sub_id = os.getenv(f"GRVT_SUB_ACCOUNT_ID_{num}") or os.getenv(f"{prefix}SUB_ACCOUNT_ID_{num}")
            if api_key:
                account["api_key"] = api_key
                account["sub_account_id"] = sub_id or ""
                accounts.append(account)
        elif exchange == "paradex":
            jwt = os.getenv(f"PARADEX_JWT_{num}") or os.getenv(f"{prefix}JWT_{num}")
            if jwt:
                account["jwt"] = jwt
                accounts.append(account)
    
    return accounts

def get_exchange_config(exchange: str) -> Dict[str, Any]:
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "config", "exchanges.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["exchanges"].get(exchange.lower(), {})

def list_all_exchanges() -> List[str]:
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "config", "exchanges.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return list(config["exchanges"].keys())
