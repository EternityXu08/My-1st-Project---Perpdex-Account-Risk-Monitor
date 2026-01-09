import requests
from typing import List, Dict, Any
from utils.config_loader import get_all_accounts, get_exchange_config

def safe_float(value, default=0.0):
    """安全转 float，处理空字符串、None 等"""
    if value is None or value == '' or value == 'N/A':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

class GRVTAccount:
    def __init__(self, api_key: str, sub_account_id: str, account_index: int):
        self.api_key = api_key
        self.sub_account_id = sub_account_id
        self.account_index = account_index
        self.config = get_exchange_config("grvt")
        self.auth_url = self.config["auth_url"]
        self.base_url = self.config["base_url"]
        self.headers = self._login()

    def _login(self) -> Dict[str, str]:
        payload = {"api_key": self.api_key}
        try:
            response = requests.post(self.auth_url, json=payload, timeout=30)
            if response.status_code == 200:
                session_cookie = response.cookies.get("gravity")
                account_id = response.headers.get("X-Grvt-Account-Id")
                if session_cookie and account_id:
                    return {
                        "Cookie": f"gravity={session_cookie}",
                        "X-Grvt-Account-Id": account_id,
                        "Content-Type": "application/json"
                    }
            print(f"GRVT 账户{self.account_index} 登录失败: {response.status_code} {response.text}")
        except Exception as e:
            print(f"GRVT 账户{self.account_index} 登录异常: {e}")
        return {}

    def get_summary(self) -> Dict[str, Any]:
        if not self.headers:
            return {}
        url = f"{self.base_url}/{self.config['endpoints']['summary']}"
        payload = {"sub_account_id": self.sub_account_id}
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # GRVT account_summary 返回 {"result": { ... }}
            if "result" in data:
                return data["result"]
            return data  # 兼容直接 dict
        print(f"GRVT 账户{self.account_index} summary 查询失败: {response.status_code} {response.text}")
        return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.headers:
            return []
        url = f"{self.base_url}/{self.config['endpoints']['positions']}"
        payload = {"sub_account_id": self.sub_account_id}
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            positions = data.get("result", []) if "result" in data else data
            # GRVT 原生有 notional 字段，直接使用
            for pos in positions:
                notional = safe_float(pos.get("notional", 0))
                pos["notional_value"] = round(notional, 2)
            return positions
        print(f"GRVT 账户{self.account_index} positions 查询失败: {response.status_code}")
        return []

    def get_open_orders(self) -> List[Dict[str, Any]]:
        if not self.headers:
            return []
        url = f"{self.base_url}/{self.config['endpoints']['open_orders']}"
        payload = {"sub_account_id": self.sub_account_id}
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("result", []) if "result" in data else data
        elif response.status_code == 404:
            return []
        print(f"GRVT 账户{self.account_index} open_orders 查询失败: {response.status_code}")
        return []

    def get_fills(self, limit: int = 500) -> List[Dict[str, Any]]:
        if not self.headers:
            return []
        url = f"{self.base_url}/{self.config['endpoints']['fills']}"
        payload = {"sub_account_id": self.sub_account_id, "limit": limit}
        response = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("result", []) if "result" in data else data
        print(f"GRVT 账户{self.account_index} fills 查询失败: {response.status_code}")
        return []

def get_all_grvt_data() -> List[Dict[str, Any]]:
    accounts = get_all_accounts("grvt")
    all_data = []
    for i, acc in enumerate(accounts, 1):
        api_key = acc["api_key"]
        sub_account_id = acc["sub_account_id"]
        account = GRVTAccount(api_key, sub_account_id, i)
        data = {
            "account_index": i,
            "sub_account_id": sub_account_id,
            "summary": account.get_summary(),
            "positions": account.get_positions(),
            "open_orders": account.get_open_orders(),
            "fills": account.get_fills()
        }
        all_data.append(data)
    return all_data
