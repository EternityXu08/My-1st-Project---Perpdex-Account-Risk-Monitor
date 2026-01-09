from exchanges.grvt import get_all_grvt_data
from exchanges.paradex import get_all_paradex_data
from typing import Dict, List, Any
import datetime

def safe_float(value, default=0.0):
    if value is None or value == '' or value == 'N/A':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def aggregate_all_data() -> Dict[str, Any]:
    grvt_data = get_all_grvt_data()
    paradex_data = get_all_paradex_data()
    
    update_time_beijing = "N/A"
    
    total_equity = 0.0
    total_exposure = 0.0
    
    exchanges = []
    
    # GRVT
    grvt_group = {
        "exchange_name": "GRVT",
        "Exchange Equity": 0.0,
        "Exchange Exposure": 0.0,
        "Exchange Gross Exposure": 0.0,
        "accounts": []
    }
    
    for acc in grvt_data:
        summary = acc["summary"]
        positions = acc["positions"]
        
        equity = 0.0
        available_balance = 0.0
        if summary:
            equity = safe_float(summary.get('total_equity') or summary.get('totalEquity'))
            available_balance = safe_float(summary.get('available_balance') or summary.get('availableBalance'))
            total_equity += equity
            grvt_group["Exchange Equity"] += equity
            
            event_time_str = summary.get('event_time')
            if event_time_str and update_time_beijing == "N/A":
                try:
                    event_time_float = float(event_time_str)
                    event_time_s = event_time_float / 1e9
                    beijing_time = datetime.datetime.fromtimestamp(event_time_s, tz=datetime.timezone(datetime.timedelta(hours=8)))
                    update_time_beijing = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
        
        account_data = {
            "Equity": equity,
            "Available Balance": available_balance,
            "positions": []
        }
        
        net_exposure = 0.0
        gross_exposure = 0.0
        for pos in positions:
            size = safe_float(pos.get("size"))
            exposure = safe_float(pos.get("notional_value"))
            liq_price = safe_float(pos.get("est_liquidation_price"))
            
            net_exposure += exposure
            gross_exposure += abs(exposure)
            
            instrument = pos.get("instrument", "")
            if "_" in instrument:
                instrument = instrument.split("_")[0] + "-PERP"
            else:
                instrument = "N/A"
            
            account_data["positions"].append({
                "Instrument": instrument,
                "Size": size,
                "Exposure": exposure,
                "Liq.price": round(liq_price, 2) if liq_price != 0 else 0.0
            })
        
        account_equity = equity if equity > 0 else 1  # 避免除0
        net_leverage = round(abs(net_exposure) / account_equity, 2)
        gross_leverage = round(gross_exposure / account_equity, 2)
        
        account_data["Net Exposure"] = net_exposure
        account_data["Net Leverage"] = net_leverage
        account_data["Gross Exposure"] = gross_exposure
        account_data["Gross Leverage"] = gross_leverage
        
        grvt_group["accounts"].append(account_data)
        grvt_group["Exchange Exposure"] += net_exposure
        grvt_group["Exchange Gross Exposure"] += gross_exposure
        total_exposure += net_exposure
    
    exchanges.append(grvt_group)
    
    # Paradex
    paradex_group = {
        "exchange_name": "Paradex",
        "Exchange Equity": 0.0,
        "Exchange Exposure": 0.0,
        "Exchange Gross Exposure": 0.0,
        "accounts": []
    }
    
    for acc in paradex_data:
        summary = acc["summary"]
        positions = acc["positions"]
        
        equity = 0.0
        available_balance = 0.0
        if summary:
            equity = safe_float(summary.get('account_value'))
            available_balance = safe_float(summary.get('free_collateral'))
            total_equity += equity
            paradex_group["Exchange Equity"] += equity
        
        account_data = {
            "Equity": equity,
            "Available Balance": available_balance,
            "positions": []
        }
        
        net_exposure = 0.0
        gross_exposure = 0.0
        for pos in positions:
            size = safe_float(pos.get("size"))
            mark_price = safe_float(pos.get("mark_price"))
            exposure = size * mark_price
            liq_price = safe_float(pos.get("liquidation_price"))
            
            net_exposure += exposure
            gross_exposure += abs(exposure)
            
            market = pos.get("market", "")
            instrument = market.split("-")[0] + "-PERP" if "-" in market else "N/A"
            
            account_data["positions"].append({
                "Instrument": instrument,
                "Size": size,
                "Exposure": exposure,
                "Liq.price": round(liq_price, 2) if liq_price != 0 else 0.0
            })
        
        account_equity = equity if equity > 0 else 1
        net_leverage = round(abs(net_exposure) / account_equity, 2)
        gross_leverage = round(gross_exposure / account_equity, 2)
        
        account_data["Net Exposure"] = net_exposure
        account_data["Net Leverage"] = net_leverage
        account_data["Gross Exposure"] = gross_exposure
        account_data["Gross Leverage"] = gross_leverage
        
        paradex_group["accounts"].append(account_data)
        paradex_group["Exchange Exposure"] += net_exposure
        paradex_group["Exchange Gross Exposure"] += gross_exposure
        total_exposure += net_exposure
    
    exchanges.append(paradex_group)
    
    result = {
        "update_time": update_time_beijing,
        "Total Equity": total_equity,
        "Total Exposure": total_exposure,
        "exchanges": exchanges
    }
    
    return result
