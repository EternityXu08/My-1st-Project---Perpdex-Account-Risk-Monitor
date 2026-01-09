import requests
import json
from typing import List, Dict, Any
from utils.config_loader import get_all_accounts, get_exchange_config

class ParadexAccount:
    def __init__(self, jwt: str, account_index: int):
        self.jwt = jwt
        self.account_index = account_index
        self.config = get_exchange_config("paradex")
        self.base_url = self.config["base_url"]
        self.headers = {
            "Authorization": f"Bearer {self.jwt}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取账户资产总结"""
        url = f"{self.base_url}/{self.config['endpoints']['summary']}"
        response = requests.get(url, headers=self.headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                return data[0]
        print(f"Paradex 账户{self.account_index} summary 查询失败: {response.status_code} {response.text}")
        return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓，并从 unrealized_pnl 精确反推 mark_price 和 notional_value，只返回真实持仓 (size != 0)"""
        url = f"{self.base_url}/{self.config['endpoints']['positions']}"
        response = requests.get(url, headers=self.headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            positions = data.get("results", []) if isinstance(data, dict) else data
            
            filtered_positions = []
            for pos in positions:
                size = float(pos.get("size", 0))
                if size == 0:
                    continue  # 跳过已平仓的历史记录
                
                entry_price = float(pos.get("average_entry_price", 0))
                unrealized_pnl = float(pos.get("unrealized_pnl", 0))
                
                if size > 0:  # LONG
                    mark_price = entry_price + unrealized_pnl / size
                else:  # SHORT
                    mark_price = entry_price - unrealized_pnl / abs(size)
                
                pos["mark_price"] = round(mark_price, 6)
                pos["notional_value"] = round(abs(size) * mark_price, 2)
                
                filtered_positions.append(pos)
            
            return filtered_positions
        
        print(f"Paradex 账户{self.account_index} positions 查询失败: {response.status_code} {response.text}")
        return []

    def get_open_orders(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{self.config['endpoints']['open_orders']}"
        response = requests.get(url, headers=self.headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else []
        elif response.status_code == 404:
            return []  # 无挂单正常
        print(f"Paradex 账户{self.account_index} open_orders 查询失败: {response.status_code}")
        return []

    def get_fills(self, limit: int = 500) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{self.config['endpoints']['fills']}"
        params = {"limit": limit}
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else []
        print(f"Paradex 账户{self.account_index} fills 查询失败: {response.status_code}")
        return []

def get_all_paradex_data() -> List[Dict[str, Any]]:
    """返回所有 Paradex 账户的完整数据"""
    accounts = get_all_accounts("paradex")
    all_data = []
    for i, acc in enumerate(accounts, 1):
        jwt = acc["jwt"]
        account = ParadexAccount(jwt, i)
        data = {
            "account_index": i,
            "summary": account.get_summary(),
            "positions": account.get_positions(),
            "open_orders": account.get_open_orders(),
            "fills": account.get_fills()
        }
        all_data.append(data)
    return all_data
