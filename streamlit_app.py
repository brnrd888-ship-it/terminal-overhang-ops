import streamlit as st
import yfinance as yf
import requests
import time
import streamlit_analytics2 as streamlit_analytics
import streamlit.components.v1 as components

# ==========================================
# 0. 반응형 블룸버그 터미널 vs 라이트 어드민 테마 동적 제어
# ==========================================
st.set_page_config(page_title="Terminal Overhang Ops", layout="wide")

is_analytics_mode = "analytics" in st.query_params

if is_analytics_mode:
    st.markdown("""
        <style>
        .block-container { padding-top: 2.5rem !important; max-width: 90% !important; }
        .stApp { background-color: #f8f9fa !important; color: #212529 !important; font-family: -apple-system, sans-serif; }
        div.stTextInput > label { color: #495057 !important; font-weight: 600; }
        div.stTextInput > div > div > input { background-color: #ffffff !important; color: #212529 !important; border: 1px solid #ced4da !important; }
        div.stFormSubmitButton > button { background-color: #0d6efd !important; color: #ffffff !important; border: none !important; }
        h1, h2, h3 { color: #212529 !important; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .block-container { padding-top: 2.5rem !important; padding-bottom: 1rem !important; max-width: 95% !important; }
        .stApp { background-color: #11141a !important; color: #ffffff !important; font-family: 'Consolas', 'Courier New', monospace; }
        
        div.stTextInput > label, label[data-testid="stWidgetLabel"] { 
            color: #ff9900 !important; font-size: 15px !important; font-weight: bold !important; 
            margin-bottom: 5px !important; display: inline-block !important;
        }
        
        div.stTextInput > div > div > input { 
            background-color: #1c222d !important; color: #ffffff !important; border: 1px solid #3b4656 !important; font-size: 15px;
        }
        
        div.stFormSubmitButton > button { 
            background-color: #2b3543 !important; color: #ff9900 !important; border: 1px solid #ff9900 !important; 
            font-weight: bold !important; width: 100% !important; height: 38px !important; font-size: 14px !important;
        }
        div.stFormSubmitButton > button:hover { background-color: #ff9900 !important; color: #11141a !important; }
        
        h1, h2, h3 { color: #ff9900 !important; margin-top: 5px !important; margin-bottom: 5px !important; font-weight: bold !important; }
        
        div[data-testid="stExpander"] { background-color: #1c222d !important; border: 1px solid #3b4656 !important; border-radius: 4px; }
        div[data-testid="stExpander"] summary p { color: #ff9900 !important; font-weight: bold !important; font-size: 14px !important; }
        div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] { color: #ffffff !important; font-size: 13px !important; line-height: 1.6; }
        
        hr, div[data-testid="stMarkdownContainer"] hr { 
            margin: 4px 0 !important; 
            padding: 0 !important;
            border-color: #3b4656 !important; 
        }
        
        /* 반응형 하이브리드 CSS */
        .pc-table-view { display: block !important; }
        .mobile-card-view { display: none !important; }
        
        table { width: 100%; border-collapse: collapse; color: #ffffff !important; margin-top: 5px !important; }
        th { background-color: #1c222d !important; color: #ff9900 !important; border: 1px solid #3b4656 !important; font-size: 13px; padding: 8px 12px !important; }
        td { border: 1px solid #3b4656 !important; padding: 8px 12px !important; font-size: 12px; background-color: #11141a !important; }
        
        table a, .overhang-card a { color: #ff9900 !important; text-decoration: none !important; font-weight: bold !important; }
        table a:hover, .overhang-card a:hover { text-decoration: underline !important; color: #00FF41 !important; }
        
        @media (max-width: 768px) {
            .block-container { max-width: 100% !important; padding: 1rem !important; padding-top: 2rem !important; }
            h3 { font-size: 16px !important; line-height: 1.3 !important; }
            div.stTextInput > label { font-size: 14px !important; }
            
            .pc-table-view { display: none !important; }
            .mobile-card-view { display: block !important; }
            
            .overhang-card {
                background-color: #1c222d !important;
                border: 1px solid #3b4656 !important;
                border-radius: 6px !important;
                padding: 12px !important;
                margin-bottom: 12px !important;
                line-height: 1.5 !important;
            }
            .card-header {
                font-size: 14px !important;
                font-weight: bold !important;
                color: #ff9900 !important;
                border-bottom: 1px solid #3b4656 !important;
                padding-bottom: 6px !important;
                margin-bottom: 8px !important;
                display: flex !important;
                justify-content: space-between !important;
            }
            .card-row { font-size: 12px !important; margin-bottom: 5px !important; color: #e0e0e0 !important; }
            .card-label { color: #8a96a8 !important; font-weight: bold !important; display: inline-block !important; width: 85px !important; }
        }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# ⚙️ 💡 우회 최적화: 무료 차트 레이아웃 딥링크 임베드 엔진
# ==========================================
def render_ops_chart(ticker):
    chart_layout_id = "cqlbNcAm"
    
    # 사용자가 입력한 티커를 미국의 NASDAQ 시장 데이터 소스로 결합하여 주가 불일치 방지
    embed_url = f"https://www.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol=NASDAQ:{ticker}&interval=5&theme=dark&style=1&timezone=America%2FNew_York&studies=%5B%5D&layout={chart_layout_id}"
    
    tv_html = f"""
    <iframe src="{embed_url}" 
            style="width: 100%; height: 500px; border: 1px solid #3b4656; background-color: #11141a;" 
            allowfullscreen>
    </iframe>
    """
    components.html(tv_html, height=520)

# ==========================================
# ⚙️ 데이터 연동 백엔드 코어 (SEC & YFinance)
# ==========================================
SEC_HEADERS = {'User-Agent': 'BloombergTerminal master@bloomberg.com'}

@st.cache_data(ttl=3600)
def get_cik_from_ticker(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        data = response.json()
        for key, value in data.items():
            if value['ticker'] == ticker.upper(): return str(value['cik_str']).zfill(10)
    except: return None
    return None

@st.cache_data(ttl=3600)
def scan_sec_filings(ticker):
    matrix = {
        "기존/신규 F-3 Shelf": {"exists": "없음", "scale": "-", "stage": "최근 1년간 공시 없음", "cash_inflow": "가동 시 유입", "impact": "지분 희석 위험", "risk": "낮음", "url": None},
        "ATM / ELOC / SEPA": {"exists": "없음", "scale": "-", "stage": "최근 1년간 공시 없음", "cash_inflow": "-", "impact": "-", "risk": "낮음", "url": None},
        "전환사채 (CB) / 전환우선주": {"exists": "SEC 공시 확인 필요", "scale": "-", "stage": "10-Q/10-K 주석 확인", "cash_inflow": "-", "impact": "-", "risk": "확인 필요", "url": None},
        "워런트 (Warrants)": {"exists": "SEC 공시 확인 필요", "scale": "-", "stage": "계약서 별도 확인", "cash_inflow": "-", "impact": "-", "risk": "확인 필요", "url": None},
        "Selling Shareholder Resale": {"exists": "확인되지 않음", "scale": "-", "stage": "대기 물량 없음", "cash_inflow": "없음", "impact": "해당 없음", "risk": "낮음", "url": None},
        "S-8 / 임직원 보상주식": {"exists": "없음", "scale": "-", "stage": "최근 1년간 공시 없음", "cash_inflow": "옵션 행사 시 일부", "impact": "단기 영향 미미", "risk": "낮음", "url": None}
    }
    cik = get_cik_from_ticker(ticker)
    if not cik: return matrix
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        if response.status_code != 200: return matrix
        data = response.json()
        recent_filings = data['filings']['recent']
        forms, dates, acc_nos = recent_filings['form'], recent_filings['filingDate'], recent_filings['accessionNumber']
        
        found_f3, found_atm, found_s8, found_resale = False, False, False, False
        latest_report_url = None
        
        for i in range(len(forms)):
            form_type, filing_date, acc_no = forms[i], dates[i], acc_nos[i]
            raw_acc = acc_no.replace("-", "")
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{raw_acc}/{acc_no}-index.htm"
            
            if form_type in ['10-Q', '10-K', '20-F'] and not latest_report_url:
                latest_report_url = doc_url
            
            if form_type in ['F-3', 'S-3', 'F-3ASR', 'S-3ASR'] and not found_f3:
                matrix["기존/신규 F-3 Shelf"] = {"exists": "⚠️ 존재", "scale": "↗ 본문 확인", "stage": f"발견: {filing_date}", "cash_inflow": "가동 시 유입", "impact": "물량 폭증 위험", "risk": "매우 높음", "url": doc_url}; found_f3 = True
            if form_type in ['424B5', '424B2'] and not found_atm:
                matrix["ATM / ELOC / SEPA"] = {"exists": "⚠️ 가동 의심", "scale": "↗ 본문 확인", "stage": f"발견: {filing_date}", "cash_inflow": "즉각 유입", "impact": "강한 매물대", "risk": "높음", "url": doc_url}; found_atm = True
            if form_type in ['S-1', 'S-1/A', '424B3'] and not found_resale:
                matrix["Selling Shareholder Resale"] = {"exists": "확인 요망", "scale": "↗ 본문 확인", "stage": f"제출: {filing_date}", "cash_inflow": "없음", "impact": "기존 주주 덤핑", "risk": "높음", "url": doc_url}; found_resale = True
            if form_type == 'S-8' and not found_s8:
                matrix["S-8 / 임직원 보상주식"] = {"exists": "존재", "scale": "↗ 본문 확인", "stage": f"발견: {filing_date}", "cash_inflow": "행사 시 일부", "impact": "영향 미미", "risk": "낮음", "url": doc_url}; found_s8 = True
                
        if latest_report_url:
            matrix["전환사채 (CB) / 전환우선주"]["url"] = latest_report_url
            matrix["전환사채 (CB) / 전환우선주"]["scale"] = "↗ 최신 보고서 확인"
            matrix["워런트 (Warrants)"]["url"] = latest_report_url
            matrix["워런트 (Warrants)"]["scale"] = "↗ 최신 보고서 확인"
            
    except: pass
    return matrix

@st.cache_data(ttl=3600)
def get_live_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        outstanding = info.get('sharesOutstanding') or 0
        public_float = info.get('floatShares') or 0
        company_name = info.get('longName') or info.get('shortName') or "UNKNOWN COMPANY"
        current_price = info.get('regularMarketPrice') or info.get('currentPrice') or 0.0
        price_change = info.get('regularMarketChange') or 0.0
        price_change_percent = info.get('regularMarketChangePercent') or 0.0
    except: 
        outstanding, public_float, company_name = 0, 0, "UNKNOWN COMPANY"
        current_price, price_change, price_change_percent = 0.0, 0.0, 0.0
    float_ratio = round((public_float / outstanding) * 100, 1) if outstanding > 0 else 0.0
    
    if public_float == 0: 
        pressure = "⚠️ API 오류 또는 정보 비공개 (수동 확인 필요)"
        border_color = "#ff9900"
    elif public_float < 5000000: 
        pressure = "🚨 [초극단적 품절주] 유통물량 500만 주 미만. 세력 작전 타겟 확률 농후."
        border_color = "#ff3333"
    elif float_ratio < 40: 
        pressure = "🔒 락업 물량이 많아 유통량이 철저히 통제됨."
        border_color = "#ff9900"
    else: 
        pressure = "✅ 유통물량 충분. 수급 압박 적음."
        border_color = "#00FF41"
        
    return {
        "outstanding_shares": outstanding, 
        "public_float": public_float, 
        "float_ratio": float_ratio, 
        "pressure_summary": pressure, 
        "company_name": company_name, 
        "border_color": border_color,
        "current_price": current_price,
        "price_change": price_change,
        "price_change_percent": price_change_percent
    }

def send_discord_log(ticker, company_name, pressure_summary, border_color):
    DISCORD_WEBHOOK_URL = st.secrets.get("DISCORD_WEBHOOK_URL", "")
    if not DISCORD_WEBHOOK_URL: return 
    clean_summary = pressure_summary.replace("<span style='color:#ff9900;'>", "").replace("<span style='color:#ff3333; font-weight:bold;'>", "").replace("<span style='color:#00FF41;'>", "").replace("</span>", "")
    color_map = {"#ff3333": 16724787, "#ff9900": 16750848, "#00FF41": 65345}
    embed_color = color_map.get(border_color, 16750848)
    payload = {
        "username": "BLOOMBERG DILUTION RADAR",
        "embeds": [{
            "title": f"📊 [ACCESS LOG] TARGET SCANNED: {ticker}",
            "color": embed_color, 
            "fields": [
                {"name": "종목 풀네임", "value": company_name, "inline": True},
                {"name": "수급 진단 결과", "value": clean_summary, "inline": False}
            ],
            "footer": {"text": "TERMINAL-OVERHANG-OPS AUDIT TRACE"}
        }]
    }
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except: pass

# ==========================================
# 🖥️ 보안 관제 2호: 분석 래퍼 엔진 가동
# ==========================================
admin_password = st.secrets.get("ANALYTICS_PASSWORD", "mimi_local")

with streamlit_analytics.track(unsafe_password=admin_password):

    if not is_analytics_mode:
        st.markdown("### 💻 TERMINAL-OVERHANG-OPS v1.0")

    with st.form(key='hacker_terminal_form'):
        ticker_input = st.text_input("▶ ENTER TARGET TICKER:", value="").upper().strip()
        submit_button = st.form_submit_button("EXECUTE SCAN (ENTER)")

    if submit_button:
        if not ticker_input:
            st.error("ERROR: PLEASE ENTER A VALID TICKER.")
        else:
            stock_info = get_live_stock_info(ticker_input)
            matrix_data = scan_sec_filings(ticker_input)
            send_discord_log(ticker_input, stock_info['company_name'], stock_info['pressure_summary'], stock_info['border_color'])
            
            current_price = stock_info['current_price']
            price_change = stock_info['price_change']
            change_percent = stock_info['price_change_percent']
            
            price_fmt = f"{current_price:,.2f}" if isinstance(current_price, float) and not current_price.is_integer() else f"{current_price:,}"
            change_fmt = f"{abs(price_change):,.2f}" if isinstance(price_change, float) and not price_change.is_integer() else f"{abs(price_change):,}"
            
            is_positive = price_change >= 0
            ui_status = {
                True:  {"color": "#ff3333", "sign": "+", "emoji": "🔺"},
                False: {"color": "#3388ff", "sign": "-", "emoji": "🔻"}
            }[is_positive]
            
            st.markdown(f"<h3 style='margin-top: 5px; margin-bottom: 0px; color: #ff9900;'>📂 {stock_info['company_name']} ({ticker_input})</h3>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin-top: 2px; margin-bottom: 6px; display: inline-block; font-weight: bold;'>${price_fmt} <span style='color: {ui_status['color']}; font-size: 18px; font-weight: bold; margin-left: 6px;'>{ui_status['emoji']} {ui_status['sign']}{change_fmt} ({ui_status['sign']}{abs(change_percent):.2f}%)</span></h2>", unsafe_allow_html=True)
            st.markdown(f"• **총 발행 주식 수:** {stock_info['outstanding_shares']:,} 주 | **실제 유통 주식 수:** {stock_info['public_float']:,} 주 ({stock_info['float_ratio']}%)\n")
            st.markdown(f"<div style='border-left: 4px solid {stock_info['border_color']}; background-color: #1c222d; padding: 10px 15px; margin: 8px 0; border-radius: 2px;'><b style='color: {stock_info['border_color']}; font-size: 14px;'>🔍 시스템 종합 진단:</b> {stock_info['pressure_summary']}</div>", unsafe_allow_html=True)
            
            # 📊 오더블록 전술 차트 호출 (입력된 티커 연동)
            st.markdown("#### 📊 TACTICAL RADAR CHART (5M + EXTENDED SESSION)")
            render_ops_chart(ticker_input)
            
            st.markdown("---")
            
            master_categories = ["기존/신규 F-3 Shelf", "ATM / ELOC / SEPA", "전환사채 (CB) / 전환우선주", "워런트 (Warrants)", "Selling Shareholder Resale", "S-8 / 임직원 보상주식"]
            
            # 1. 🖥️ PC 전용 가로 표 뷰 생성
            pc_html = "<div class='pc-table-view'><table>"
            pc_html += "<tr><th>CATEGORY</th><th>STATUS</th><th>SCALE</th><th>LATEST FILING</th><th>CASH INFLOW</th><th>SHAREHOLDER IMPACT</th><th>RISK</th></tr>"
            for cat in master_categories:
                d = matrix_data.get(cat)
                c_status = f"<a href='{d['url']}' target='_blank'>{d['exists']}</a>" if d['url'] else d['exists']
                if "⚠️" in d['exists'] and d['url']:
                    c_status = f"<a href='{d['url']}' target='_blank' style='color:#ff3333;'>{d['exists']}</a>"
                
                c_risk = f"<span style='color:#ff3333;font-weight:bold;'>{d['risk']}</span>" if d['risk'] in ['매우 높음', '높음'] else (f"<span style='color:#ff9900;font-weight:bold;'>{d['risk']}</span>" if d['risk'] == '확인 필요' else d['risk'])
                scale_view = f"<a href='{d['url']}' target='_blank'>{d['scale']}</a>" if d['url'] else d['scale']
                cat_view = f"<a href='{d['url']}' target='_blank'>{cat}</a>" if d['url'] else f"<b>{cat}</b>"
                pc_html += f"<tr><td>{cat_view}</td><td>{c_status}</td><td>{scale_view}</td><td>{d['stage']}</td><td>{d['cash_inflow']}</td><td>{d['impact']}</td><td>{c_risk}</td></tr>"
            pc_html += "</table></div>"
            st.markdown(pc_html, unsafe_allow_html=True)
            
            # 2. 📱 모바일 전용 카드 뷰 생성
            mobile_html = "<div class='mobile-card-view'>"
            for cat in master_categories:
                d = matrix_data.get(cat)
                c_status = f"<a href='{d['url']}' target='_blank'>{d['exists']}</a>" if d['url'] else d['exists']
                if "⚠️" in d['exists'] and d['url']:
                    c_status = f"<a href='{d['url']}' target='_blank' style='color:#ff3333;'>{d['exists']}</a>"
                    
                c_risk = f"<span style='color:#ff3333;font-weight:bold;'>{d['risk']}</span>" if d['risk'] in ['매우 높음', '높음'] else (f"<span style='color:#ff9900;font-weight:bold;'>{d['risk']}</span>" if d['risk'] == '확인 필요' else d['risk'])
                scale_view = f"<a href='{d['url']}' target='_blank'>{d['scale']}</a>" if d['url'] else d['scale']
                cat_view = f"<a href='{d['url']}' target='_blank'>📌 {cat}</a>" if d['url'] else f"📌 {cat}"
                
                card_chunk = (
                    "<div class='overhang-card'>"
                    f"<div class='card-header'><span>{cat_view}</span><span>{c_risk}</span></div>"
                    f"<div class='card-row'><span class='card-label'>• 상태:</span> {c_status}</div>"
                    f"<div class='card-row'><span class='card-label'>• 규모:</span> {scale_view}</div>"
                    f"<div class='card-row'><span class='card-label'>• 최근공시:</span> {d['stage']}</div>"
                    f"<div class='card-row'><span class='card-label'>• 자금유입:</span> {d['cash_inflow']}</div>"
                    f"<div class='card-row'><span class='card-label'>• 주주영향:</span> {d['impact']}</div>"
                    "</div>"
                )
                mobile_html += card_chunk
            mobile_html += "</div>"
            st.markdown(mobile_html, unsafe_allow_html=True)

    # 하단 요원 가이드
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💡 [요원 가이드] TERMINAL OPERATION QUICK GUIDE (사용 팁 보기)"):
        st.markdown("### 📊 3초 퀀트 오버행 분석 공식")
        st.markdown("#### **1. 상단 실제 유통 주식 수 (Public Float) 확인**")
        st.markdown("• **500만 주 미만** (:red[**🚨 초극단적 품절주**]): 적은 거래량으로도 상한가 제한 없이 수백% 폭등할 수 있지만, 반대로 세력이 던지면 하한가 없이 폭락하는 양날의 검입니다. 철저히 당일 단타로만 접근하십시오.")
        st.markdown("---") 
        st.markdown("#### **2. 하단 오버행 매트릭스 리스크 체크**")
        st.markdown("• :red[**⚠️ 존재 (F-3 Shelf)**]: 회사가 대규모 유상증자 폭탄을 장착해 둔 상태입니다. 주가가 호재를 타고 폭등할 때 회사가 스위치를 켜고 주식을 기습 투하하므로 오버나이트(다음날로 물량 넘기기)는 절대 자제하십시오.")
        st.markdown("• :red[**⚠️ 가동 의심 (ATM / ELOC)**]: 증권사를 통해 장중에 기계적으로 매물을 찔끔찔끔 던지는 악성 매도 계약이 체결된 상태입니다. 주가가 올라가려고 할 때마다 머리를 누르는 '두더지 망치' 역할을 하므로 장기 상승이 어렵습니다.")
        st.markdown("---")
        st.markdown("#### **3. 🚀 최고의 단타 황금 조합**")
        st.markdown("• 실제 유통 주식 수는 500만 주 미만으로 가벼운데, 아래 매트릭스에 유상증자 무기(F-3, ATM) 리스크가 전부 :green[**'없음/낮음'**]인 종목 ➡️ 위에서 누르는 매물이 전혀 없기 때문에 세력이 마음 놓고 펌핑을 주도할 수 있는 최고의 작전주 후보군입니다.")