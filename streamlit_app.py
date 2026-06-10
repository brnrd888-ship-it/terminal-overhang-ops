import streamlit as st
import yfinance as yf
import requests
import time
import streamlit_analytics2 as streamlit_analytics

# ==========================================
# 0. 반응형 블룸버그 터미널 vs 라이트 어드민 테마 동적 제어
# ==========================================
st.set_page_config(page_title="Terminal Overhang Ops", layout="wide")

# 💡 개선 1: URL에 ?analytics=on이 붙으면 대시보드를 화사한 라이트 모드로 자동 스위칭
is_analytics_mode = "analytics" in st.query_params

if is_analytics_mode:
    # 📊 보통의 깔끔한 라이트 버전 대시보드 CSS
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
    # 🍊 가독성을 극대화한 블룸버그 터미널(Bloomberg Terminal) 전용 다크/앰버 CSS
    st.markdown("""
        <style>
        /* 기본 여백 설정 및 반응형 미디어 쿼리 주입 */
        .block-container { padding-top: 2.5rem !important; padding-bottom: 1rem !important; max-width: 95% !important; }
        
        /* 블룸버그 특유의 다크 차콜 배경과 기본 화이트 폰트 조합 */
        .stApp { background-color: #11141a !important; color: #ffffff !important; font-family: 'Consolas', 'Courier New', monospace; }
        
        /* 입력창 레이블: 블룸버그 시그니처 앰버(Amber/오렌지) 색상 고정 */
        div.stTextInput > label, label[data-testid="stWidgetLabel"] { 
            color: #ff9900 !important; font-size: 15px !important; font-weight: bold !important; 
            text-shadow: none !important; margin-bottom: 5px !important; display: inline-block !important;
        }
        
        /* 입력창 스타일 */
        div.stTextInput > div > div > input { 
            background-color: #1c222d !important; color: #ffffff !important; border: 1px solid #3b4656 !important; font-size: 15px;
        }
        
        /* 버튼 스타일 */
        div.stFormSubmitButton > button { 
            background-color: #2b3543 !important; color: #ff9900 !important; border: 1px solid #ff9900 !important; 
            font-weight: bold !important; width: 100% !important; height: 38px !important; font-size: 14px !important;
        }
        div.stFormSubmitButton > button:hover { background-color: #ff9900 !important; color: #11141a !important; }
        
        /* 💡 개선 2: 모바일/태블릿 반응형 표 스타일링 및 블룸버그 그리드 라인 구현 */
        table { width: 100%; border-collapse: collapse; color: #ffffff !important; margin-top: 5px !important; }
        th { background-color: #1c222d !important; color: #ff9900 !important; border: 1px solid #3b4656 !important; font-size: 13px; padding: 6px 8px !important; }
        td { border: 1px solid #3b4656 !important; padding: 6px 8px !important; font-size: 12px; background-color: #11141a !important; }
        
        hr { margin: 0.8rem 0 !important; border-color: #3b4656 !important; }
        h1, h2, h3 { color: #ff9900 !important; margin-top: 5px !important; margin-bottom: 5px !important; }
        
        /* 📱 모바일 디스플레이 초압축 최적화 대응 */
        @media (max-width: 768px) {
            .block-container { max-width: 100% !important; padding: 1rem !important; }
            th, td { padding: 4px 5px !important; font-size: 11px !important; }
            div.stTextInput > label { font-size: 13px !important; }
        }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# ⚙️ 보안 관제 1호: 디스코드 실시간 알림 로깅 엔진
# ==========================================
def send_discord_log(ticker, company_name, pressure_summary):
    DISCORD_WEBHOOK_URL = st.secrets.get("DISCORD_WEBHOOK_URL", "")
    if not DISCORD_WEBHOOK_URL:
        return 
        
    payload = {
        "username": "BLOOMBERG DILUTION RADAR",
        "embeds": [
            {
                "title": f"📊 [ACCESS LOG] TARGET SCANNED: {ticker}",
                "color": 16750848, # 블룸버그 오렌지색 색상 코드
                "fields": [
                    {"name": "종목 풀네임", "value": company_name, "inline": True},
                    {"name": "수급 진단 결과", "value": pressure_summary, "inline": False}
                ],
                "footer": {"text": "TERMINAL-OVERHANG-OPS AUDIT TRACE"}
            }
        ]
    }
    try:
        # 💡 에러 추적을 위해 타임아웃 발생 시 무시하도록 처리
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except:
        pass

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
            if value['ticker'] == ticker.upper():
                return str(value['cik_str']).zfill(10)
    except: return None
    return None

@st.cache_data(ttl=3600)
def scan_sec_filings(ticker):
    matrix = {
        "기존/신규 F-3 Shelf": {"exists": "없음", "scale": "-", "stage": "최근 1년간 공시 없음", "cash_inflow": "가동 시 유입", "impact": "지분 희석 위험", "risk": "낮음"},
        "ATM / ELOC / SEPA": {"exists": "없음", "scale": "-", "stage": "최근 1년간 공시 없음", "cash_inflow": "-", "impact": "-", "risk": "낮음"},
        "전환사채 (CB) / 전환우선주": {"exists": "SEC 공시 확인 필요", "scale": "-", "stage": "10-Q/10-K 주석 확인", "cash_inflow": "-", "impact": "-", "risk": "확인 필요"},
        "워런트 (Warrants)": {"exists": "SEC 공시 확인 필요", "scale": "-", "stage": "계약서 별도 확인", "cash_inflow": "-", "impact": "-", "risk": "확인 필요"},
        "Selling Shareholder Resale": {"exists": "확인되지 않음", "scale": "-", "stage": "대기 물량 없음", "cash_inflow": "없음", "impact": "해당 없음", "risk": "낮음"},
        "S-8 / 임직원 보상주식": {"exists": "없음", "scale": "-", "stage": "최근 1년간 공시 없음", "cash_inflow": "옵션 행사 시 일부", "impact": "단기 영향 미미", "risk": "낮음"}
    }
    cik = get_cik_from_ticker(ticker)
    if not cik: return matrix
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        if response.status_code != 200: return matrix
        data = response.json()
        recent_filings = data['filings']['recent']
        forms, dates = recent_filings['form'], recent_filings['filingDate']
        found_f3, found_atm, found_s8, found_resale = False, False, False, False
        for i in range(len(forms)):
            form_type, filing_date = forms[i], dates[i]
            if form_type in ['F-3', 'S-3', 'F-3ASR', 'S-3ASR'] and not found_f3:
                matrix["기존/신규 F-3 Shelf"] = {"exists": "⚠️ 존재", "scale": "본문 확인", "stage": f"발견: {filing_date}", "cash_inflow": "가동 시 유입", "impact": "물량 폭증 위험", "risk": "매우 높음"}; found_f3 = True
            if form_type in ['424B5', '424B2'] and not found_atm:
                matrix["ATM / ELOC / SEPA"] = {"exists": "⚠️ 가동 의심", "scale": "본문 확인", "stage": f"발견: {filing_date}", "cash_inflow": "즉각 유입", "impact": "강한 매물대", "risk": "높음"}; found_atm = True
            if form_type in ['S-1', 'S-1/A', '424B3'] and not found_resale:
                matrix["Selling Shareholder Resale"] = {"exists": "확인 요망", "scale": "본문 확인", "stage": f"제출: {filing_date}", "cash_inflow": "없음", "impact": "기존 주주 덤핑", "risk": "높음"}; found_resale = True
            if form_type == 'S-8' and not found_s8:
                matrix["S-8 / 임직원 보상주식"] = {"exists": "존재", "scale": "본문 확인", "stage": f"발견: {filing_date}", "cash_inflow": "행사 시 일부", "impact": "영향 미미", "risk": "낮음"}; found_s8 = True
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
    except: outstanding, public_float, company_name = 0, 0, "UNKNOWN COMPANY"
    float_ratio = round((public_float / outstanding) * 100, 1) if outstanding > 0 else 0.0
    if public_float == 0: pressure = "⚠️ API 오류 또는 비공개 (수동 확인 필요)"
    elif public_float < 5000000: pressure = "🔴 [초극단적 품절주] 유통물량 500만 주 미만. 세력 작전 타겟 확률 농후."
    elif float_ratio < 40: pressure = "🟡 락업 물량이 많아 유통량이 철저히 통제됨."
    else: pressure = "🟢 유통물량 충분. 수급 압박 적음."
    return {"outstanding_shares": outstanding, "public_float": public_float, "float_ratio": float_ratio, "pressure_summary": pressure, "company_name": company_name}

# ==========================================
# 🖥️ 보안 관제 2호: 분석 래퍼 엔진 가동
# ==========================================
admin_password = st.secrets.get("ANALYTICS_PASSWORD", "mimi_local")

with streamlit_analytics.track(unsafe_password=admin_password):

    if not is_analytics_mode:
        st.markdown("### 💻 TERMINAL-OVERHANG-OPS v1.0 STATUS: ONLINE")

    with st.form(key='hacker_terminal_form'):
        # 💡 개선 3: 종목 디폴트 값("MIMI")을 완전히 지워 비워둠
        ticker_input = st.text_input("▶ ENTER TARGET TICKER:", value="").upper().strip()
        submit_button = st.form_submit_button("EXECUTE SCAN (ENTER)")

    if submit_button:
        # 💡 개선 4: 빈 값 입력 시 예외 처리 적용
        if not ticker_input:
            st.error("ERROR: PLEASE ENTER A VALID TICKER.")
        else:
            terminal_output = st.empty()
            if not is_analytics_mode:
                terminal_output.markdown("`[SYSTEM] CONNECTING TO SEC MAINFRAME... OK.`")
                time.sleep(0.2)
                terminal_output.empty()
            
            stock_info = get_live_stock_info(ticker_input)
            matrix_data = scan_sec_filings(ticker_input)
            
            # 디스코드 로그 전송
            send_discord_log(ticker_input, stock_info['company_name'], stock_info['pressure_summary'])
            
            # 레이아웃 출력
            st.markdown(f"**📂 [{ticker_input}] {stock_info['company_name']}**")
            st.markdown(f"• **총 발행 주식 수:** {stock_info['outstanding_shares']:,} 주 | **실제 유통 주식 수:** {stock_info['public_float']:,} 주 ({stock_info['float_ratio']}%)\n> 🔍 **진단:** {stock_info['pressure_summary']}")
            st.markdown("---")
            
            # 표 생성
            table_md = "| CATEGORY | STATUS | SCALE | LATEST FILING | CASH INFLOW | SHAREHOLDER IMPACT | RISK |\n"
            table_md += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            
            master_categories = [
                "기존/신규 F-3 Shelf", "ATM / ELOC / SEPA", 
                "전환사채 (CB) / 전환우선주", "워런트 (Warrants)", 
                "Selling Shareholder Resale", "S-8 / 임직원 보상주식"
            ]
            
            for cat in master_categories:
                data = matrix_data.get(cat)
                risk_style = f"**{data['risk']}**" if data['risk'] in ['높음', '매우 높음', '확인 필요'] else data['risk']
                table_md += f"| **{cat}** | {data['exists']} | {data['scale']} | {data['stage']} | {data['cash_inflow']} | {data['impact']} | {risk_style} |\n"
                
            st.markdown(table_md)