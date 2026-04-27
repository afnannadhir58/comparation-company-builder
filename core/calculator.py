import yfinance as yf

def fetch_financial_metrics(ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            # yfinance 1.3.0+ secara otomatis menggunakan curl_cffi
            stock = yf.Ticker(ticker)
            info = stock.info
            
            mkt_cap = info.get('marketCap', 0) or 0
            total_debt = info.get('totalDebt', 0) or 0
            total_cash = info.get('totalCash', 0) or 0
            ev = mkt_cap + total_debt - total_cash
            
            revenue = info.get('totalRevenue', 0) or 0
            ebitda = info.get('ebitda', 0) or 0
            
            ev_rev = round(ev / revenue, 2) if revenue > 0 else 0
            ev_ebitda = round(ev / ebitda, 2) if ebitda > 0 else 0
            
            results.append({
                "Ticker": ticker,
                "EV (Bn)": round(ev / 1e9, 2),
                "EV/Revenue": ev_rev,
                "EV/EBITDA": ev_ebitda,
                "Rev Growth (%)": round((info.get('revenueGrowth', 0) or 0) * 100, 2),
                "Gross Margin (%)": round((info.get('grossMargins', 0) or 0) * 100, 2)
            })
        except:
            continue
    return results

def calculate_implied_valuation(target_revenue, comps_df):
    if comps_df.empty or target_revenue in [0, None]:
        return {"Median Multiple": 0, "Implied EV (Bn)": 0}
        
    median_multiple = comps_df['EV/Revenue'].median()
    implied_ev = target_revenue * median_multiple
    return {
        "Median Multiple": round(median_multiple, 2),
        "Implied EV (Bn)": round(implied_ev / 1e9, 2)
    }