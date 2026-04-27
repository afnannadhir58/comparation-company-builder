import yfinance as yf
import os   

# Set cache location ke folder lokal agar tidak kena error "unable to open database file"
# di folder sistem yang mungkin terproteksi.
cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "yf_cache")
if not os.path.exists(cache_path):
    os.makedirs(cache_path)

# Mencoba set lokasi cache jika didukung oleh versi yfinance ini
try:
    yf.set_tz_cache_location(cache_path)
except:
    pass

def get_company_profile(ticker):
    """Mengambil profil lengkap dengan User-Agent Chrome."""
    try:
        print(f"[DEBUG] Mencoba menarik data untuk: {ticker}")
        
        # yfinance 1.3.0+ secara otomatis menggunakan curl_cffi untuk menangani session & headers
        company = yf.Ticker(ticker)
        info = company.info
        
        # Validasi jika Yahoo tetap memblokir dan mengembalikan dictionary kosong
        if not info or 'longName' not in info:
            print("[DEBUG] Yahoo memblokir request atau Ticker tidak valid. Info dict kosong.")
            return None
            
        return {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "summary": info.get("longBusinessSummary", "No summary available."),
            "symbol": ticker,
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0))
        }
    except Exception as e:
        print(f"[DEBUG ERROR] Kegagalan sistem yfinance: {str(e)}")
        return None

def get_industry_candidates(target_sector, target_ticker):
    """
    Mencari kandidat perusahaan pembanding secara dinamis.
    Mencoba mengambil dari peers yfinance, jika gagal gunakan mock universe yang lebih luas.
    """
    candidates_tickers = []
    
    try:
        # 1. Mencoba mengambil peers dari yfinance (beberapa ticker punya data ini)
        ticker_obj = yf.Ticker(target_ticker)
        # Peers sering tersedia di info atau melalui metode lain di beberapa versi yf
        # Kita coba ambil dari data internal jika tersedia
        peers = ticker_obj.info.get('recommendations', [])
        if not peers:
            # Fallback ke pencarian manual di universe yang lebih besar
            pass
        else:
            candidates_tickers = [p.get('symbol') for p in peers if p.get('symbol')]
    except:
        pass

    # 2. Universe yang lebih luas mencakup berbagai sektor (Tech, Finance, Retail, Energy, Healthcare)
    broad_universe = [
        # Tech & Software
        "MSFT", "AAPL", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "ORCL", "SAP", "CRM", "ADBE", "INTC", "AMD", 
        # Finance
        "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "PYPL",
        # Retail & Consumer
        "WMT", "COST", "TGT", "HD", "LOW", "NKE", "SBUX", "KO", "PEP", "PG",
        # Healthcare
        "JNJ", "PFE", "UNH", "ABBV", "MRK", "LLY",
        # Energy & Industrials
        "XOM", "CVX", "CAT", "GE", "BA", "HON", "UPS", "FEDX",
        # Communication & Entertainment
        "DIS", "NFLX", "CMCSA", "VZ", "T"
    ]
    
    # Gabungkan dan unikkan
    all_potential = list(set(candidates_tickers + broad_universe))
    
    candidates = []
    for ticker in all_potential:
        if ticker == target_ticker:
            continue
        try:
            # Ambil info dasar saja untuk filtering awal
            info = yf.Ticker(ticker).info
            # Filter berdasarkan sektor agar relevan secara industri
            if info.get('sector') == target_sector:
                candidates.append({
                    "ticker": ticker,
                    "name": info.get("longName"),
                    "summary": info.get("longBusinessSummary")
                })
        except:
            continue
            
    # Jika masih terlalu sedikit, ambil yang satu industri (lebih spesifik)
    return candidates