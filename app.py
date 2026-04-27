import streamlit as st
import pandas as pd
import yfinance as yf
import re
from datetime import datetime

# Import logika internal
from core.data_fetcher import get_company_profile, get_industry_candidates
from core.ai_engine import analyze_business_dna, get_similarity_score
from core.calculator import fetch_financial_metrics, calculate_implied_valuation
from utils.exporter import export_to_excel, generate_pdf_report

def parse_dna(dna_text):
    """Memecah teks DNA bisnis menjadi bagian-bagian terpisah untuk tampilan grid."""
    sections = {
        "REVENUE MODEL": "Data not extracted",
        "CUSTOMER TYPE": "Data not extracted",
        "ECONOMIC MOAT": "Data not extracted",
        "VALUE PROPOSITION": "Data not extracted",
        "GROWTH DRIVERS": "Data not extracted",
        "KEY RISKS": "Data not extracted"
    }
    
    # Bersihkan markdown agar parsing lebih stabil
    clean_dna = dna_text.replace("**", "").replace("__", "")
    
    # List pola pencarian yang lebih fleksibel
    keys = list(sections.keys())
    for i, key in enumerate(keys):
        # Cari judul bagian (misal "1. REVENUE MODEL" atau "REVENUE MODEL:")
        # Menggunakan regex yang mencari angka opsional, diikuti nama key, diikuti titik atau titik dua opsional
        pattern = rf"(?:\d+\.\s*)?{key}[:\s]*"
        
        # Cari batas akhir (key berikutnya atau akhir teks)
        if i + 1 < len(keys):
            next_key = keys[i+1]
            next_pattern = rf"(?:\d+\.\s*)?{next_key}[:\s]*"
            regex = rf"{pattern}(.*?)(?={next_pattern})"
        else:
            regex = rf"{pattern}(.*)"
            
        match = re.search(regex, clean_dna, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            # Hapus simbol bullet di awal baris jika ada
            content = re.sub(r"^\s*[-*+]\s+", "", content, flags=re.MULTILINE)
            sections[key] = content

    return sections

# 1. Konfigurasi Halaman (Harus Paling Atas)
st.set_page_config(page_title="Terminal AI Comps", layout="wide", initial_sidebar_state="expanded")

# 2. Injeksi CSS (Terminal Aesthetic)
st.markdown("""
    <style>
        /* Mengubah background utama Streamlit */
        .stApp {
            background-color: #000000;
            color: #ff9900;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        /* Menyembunyikan elemen bawaan Streamlit yang mengganggu */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Styling Sidebar bawaan Streamlit agar gelap */
        [data-testid="stSidebar"] {
            background-color: #0a0a0a;
            border-right: 1px solid #ff9900;
        }

        /* Kelas Custom untuk HTML Injection */
        .term-header {
            border-bottom: 2px solid #ff9900;
            padding-bottom: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        .term-title { font-size: 24px; font-weight: bold; color: #ffffff; text-transform: uppercase;}
        .term-sub { color: #aaa; margin-top: 5px; font-size: 12px; }
        .term-user { color: #00ff00; text-align: right; line-height: 1.4; font-size: 13px; }
        
        .term-panel {
            background-color: #0a0a0a;
            border: 1px solid #333333;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: inset 0 0 10px #000;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        .term-panel-title {
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
            margin-bottom: 15px;
            color: #00ffff;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        /* Metric Box Custom */
        .metric-grid { display: flex; gap: 15px; margin-bottom: 15px; }
        .metric-box {
            background-color: #111; border: 1px solid #333;
            padding: 15px; flex: 1; text-align: center;
        }
        .metric-label { color: #aaa; font-size: 11px; margin-bottom: 5px;}
        .metric-value { color: #00ff00; font-size: 24px; font-weight: bold; }
        
        /* Tabel Custom HTML */
        .term-table { width: 100%; border-collapse: collapse; font-size: 13px; color: #fff;}
        .term-table th { background-color: #1a1a1a; color: #00ffff; border: 1px solid #333; padding: 8px; text-align: left;}
        .term-table td { border: 1px solid #333; padding: 8px; }
        .pos-val { color: #00ff00; font-weight: bold;}

        /* DNA Grid Styling */
        .dna-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 10px;
        }
        .dna-card {
            background-color: #111;
            border: 1px solid #333;
            padding: 12px;
            border-left: 3px solid #ff9900;
        }
        .dna-card-title {
            color: #ff9900;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .dna-card-body {
            color: #cccccc;
            font-size: 12px;
            line-height: 1.4;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Custom Header Terminal
current_date = datetime.now().strftime("%Y-%m-%d")
st.markdown(f"""
<div class="term-header">
    <div>
        <div class="term-title">AI COMPARATION BUILDER</div>
        <div class="term-sub">SYS_STATUS: ONLINE | LATENCY: 24ms | DATA: YFINANCE_API</div>
    </div>
    <div class="term-user">
        DATE: {current_date}
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Sidebar Input
with st.sidebar:
    st.markdown("<h3 style='color: #00ffff;'>>> INPUT</h3>", unsafe_allow_html=True)
    target_ticker = st.text_input("TARGET ISSUER:", placeholder="NVDA, TSLA, JPM, etc.").upper()
    
    # Live Preview Section
    if target_ticker:
        with st.spinner("Looking up ticker..."):
            profile = get_company_profile(target_ticker)
            if profile:
                # Menggunakan Google Favicon service sebagai source logo yang lebih stabil
                try:
                    website = yf.Ticker(target_ticker).info.get('website', '')
                    domain = website.replace('http://', '').replace('https://', '').split('/')[0]
                    logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
                except:
                    logo_url = ""

                st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 5px; border-left: 4px solid #00ff00; margin-bottom: 20px;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            {f'<img src="{logo_url}" width="40" style="border-radius: 4px;">' if logo_url else ''}
                            <div>
                                <div style="font-weight: bold; font-size: 16px; color: #00ff00;">{profile['name']}</div>
                                <div style="font-size: 12px; color: #888;">{profile['sector']} | {profile['industry']}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Ticker not found in database.")

    selected_model = st.selectbox("CHOOSE ENGINE:", [
    "mixtral-8x7b-32768",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "llama-3.3-70b-versatile"
    ])
    num_comps = st.slider("COMPARATION :", 3, 10, 5)
    generate_btn = st.button("RUN", type="primary", use_container_width=True)

# 5. Eksekusi Logika Utama
if target_ticker and generate_btn:
    try:
        with st.status(">> ESTABLISHING CONNECTION...", expanded=True) as status:
            st.write("[SYS] Fetching market data...")
            target_profile = get_company_profile(target_ticker)
            if not target_profile:
                st.error("ERR_404: TICKER NOT FOUND")
                st.stop()

            st.write("[AI] Extracting DNA...")
            dna = analyze_business_dna(target_profile['summary'], model_name=selected_model)
            
            st.write("[SYS] Pulling universe...")
            candidates = get_industry_candidates(target_profile['sector'], target_ticker)

            st.write(f"[AI] Running semantic pairwise scoring against {len(candidates)} candidates...")
            scored_list = []
            for cand in candidates:
                # Memanggil Groq untuk scoring pairwise
                res = get_similarity_score(dna, cand['name'], cand['summary'], model_name=selected_model)
                
                # Ambil logo untuk setiap kandidat
                try:
                    c_info = yf.Ticker(cand['ticker']).info
                    c_web = c_info.get('website', '')
                    c_domain = c_web.replace('http://', '').replace('https://', '').split('/')[0]
                    c_logo = f"https://www.google.com/s2/favicons?domain={c_domain}&sz=64"
                except:
                    c_logo = ""

                # Sekarang get_similarity_score mengembalikan dict: {"score": int, "rationale": str}
                try:
                    if isinstance(res, dict):
                        score = res.get("score", 0)
                        rationale = res.get("rationale", "N/A")
                    elif "|" in str(res):
                        # Fallback jika model mengembalikan format lama (string)
                        score_part, rationale_part = str(res).split("|", 1)
                        import re
                        score_digits = re.findall(r'\d+', score_part)
                        score = int(score_digits[0]) if score_digits else 0
                        rationale = rationale_part.strip()
                    else:
                        continue
                    
                    scored_list.append({
                        "Ticker": cand['ticker'],
                        "Name": cand['name'],
                        "Score": score,
                        "Rationale": rationale,
                        "Logo": c_logo
                    })
                except Exception as parse_err:
                    continue
            
            if not scored_list:
                st.error("ERR_AI_SCORING: No candidates passed the similarity filter.")
                st.stop()
            
            top_comps_base = pd.DataFrame(scored_list).sort_values("Score", ascending=False).head(num_comps)

            st.write("[SYS] Calculating financial multiples...")
            fin_metrics = fetch_financial_metrics(top_comps_base['Ticker'].tolist())
            fin_df = pd.DataFrame(fin_metrics)
            
            final_table = pd.merge(top_comps_base, fin_df, on="Ticker")
            target_rev = yf.Ticker(target_ticker).info.get('totalRevenue', 0)
            valuation_res = calculate_implied_valuation(target_rev, final_table)
            
            status.update(label=">> EXECUTION COMPLETE", state="complete")

        # 6. Menampilkan Metrik Utama
        st.markdown(f"""
<div class="term-panel">
<div class="term-panel-title">>> VALUATION OUTPUT</div>
<div class="metric-grid">
    <div class="metric-box">
        <div class="metric-label">IMPLIED EV (MEDIAN)</div>
        <div class="metric-value">${valuation_res['Implied EV (Bn)']} B</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">MEDIAN EV/REV MULTIPLE</div>
        <div class="metric-value">{valuation_res['Median Multiple']}x</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">CURRENT MARKET PRICE</div>
        <div class="metric-value">${target_profile['current_price']}</div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

        # 7. Menampilkan Profil Bisnis dalam Grid
        dna_sections = parse_dna(dna)
        
        dna_html = ""
        for title, content in dna_sections.items():
            # Escape content to avoid breaking HTML but keep newlines
            safe_content = content.replace("\n", "<br>")
            dna_html += f"""<div class="dna-card">
<div class="dna-card-title">{title}</div>
<div class="dna-card-body">{safe_content}</div>
</div>"""

        st.markdown(f"""
<div class="term-panel">
<div class="term-panel-title">>> TARGET STRATEGIC DNA: {target_profile['name']}</div>
<div class="dna-grid">
{dna_html}
</div>
</div>
""", unsafe_allow_html=True)

        # 8. Menampilkan Tabel menggunakan murni HTML agar warnanya sesuai Terminal
        # Kita merender Pandas DataFrame ke HTML manual untuk injeksi kelas CSS
        display_df = final_table.copy()
        
        # Tambahkan kolom Logo ke HTML
        display_df['COMPANY'] = display_df.apply(
            lambda x: f'<div style="display: flex; align-items: center; gap: 10px;">'
                      f'<img src="{x["Logo"]}" width="20" style="border-radius: 2px;">'
                      f'<span>{x["Name"]}</span></div>' if x["Logo"] else x["Name"],
            axis=1
        )

        display_df = display_df.rename(columns={
            "Ticker": "TICKER",
            "Score": "SIM_SCORE",
            "EV/Revenue": "EV/REV",
            "EV/EBITDA": "EV/EBITDA",
            "Rev Growth (%)": "REV_GROWTH(%)",
            "Rationale": "AI_RATIONALE"
        })
        
        html_table = display_df[['TICKER', 'COMPANY', 'SIM_SCORE', 'EV/REV', 'EV/EBITDA', 'REV_GROWTH(%)', 'AI_RATIONALE']].to_html(
            index=False, 
            classes="term-table", 
            escape=False,
            justify="left"
        )
        
        st.markdown(f"""
            <div class="term-panel">
                <div class="term-panel-title">>> AI-SELECTED COMPARABLE COMPANIES</div>
                {html_table}
            </div>
        """, unsafe_allow_html=True)

        # 9. Download Section
        st.markdown("<h3 style='color: #00ffff; font-family: Consolas;'>>> EXPORT DATA</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            excel_data = export_to_excel(final_table.drop(columns=['Logo']))
            st.download_button(
                label=">> DOWNLOAD EXCEL (.XLSX)",
                data=excel_data,
                file_name=f"Comps_{target_ticker}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            pdf_data = generate_pdf_report(target_profile['name'], dna, final_table, valuation_res)
            st.download_button(
                label=">> DOWNLOAD PDF REPORT (.PDF)",
                data=pdf_data,
                file_name=f"Valuation_Report_{target_ticker}.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"SYS_ERR: {str(e)}")

else:
    st.markdown(f"""
        <div class="term-panel" style="text-align: center; color: #555;">
            [ WELCOME {current_date}]
        </div>
    """, unsafe_allow_html=True)