import streamlit as st
import yfinance as yf
import requests
import time
import streamlit_analytics2 as streamlit_analytics

# ==========================================
# 0. 앱 기본 설정 & 초압축 매트릭스 다크 테마 고정
# ==========================================
st.set_page_config(page_title="Terminal Overhang Ops", layout="wide")

st.markdown("""
    <style>
    /* 상하 여백을 컴팩트하게 축소하여 스크롤 생성 방지 */
    .block-container { padding-top: 3.5rem !important; padding-bottom: 1rem !important; max-width: 95% !important; }
    
    /* 시스템 테마(라이트 모드)를 무시하고 칠흑색 배경과 형광 초록 글씨 강제 고정 */
    .stApp { background-color: #050505 !important; color: #00FF41 !important; font-family: 'Courier New', Courier, monospace; }
    
    /* 입력창 레이블 가독성 확보 및 겹침 버그 수정 */
    div.stTextInput > label, label[data-testid="stWidgetLabel"] { 
        color: #00FF41 !important; 
        font-size: 16px !important; 
        font-weight: bold !important; 
        text-shadow: 0px 0px 5px #00FF41;
        margin-bottom: 5px !important;
        display: inline-block !important;
    }
    
    /* 입력창 내부 다크 스타일 강제 지정 */
    div.stTextInput > div > div > input { 
        background-color: #000000 !important; 
        color: #00FF41 !important; 
        border: 1px solid #00FF41 !important; 
        font-size: 16px;
        margin-top: 2px !important;
    }
    
    /* 라이트 모드 환경에서도 버튼이 하얗게 변하지 않도록 다크 스타일 고정 */
    div.stButton > button, div.stFormSubmitButton > button { 
        background-color: #000000 !important; 
        color: #00FF41 !important; 
        border: 1px solid #00FF41 !important; 
        font-weight: bold !important; 
        width: 100% !important; 
        height: 38px !important; 
        font-size: 15px !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover { background-color: #00FF41 !important; color: #000000 !important; }
    
    /* 표(Table) 내부 컴팩트 여백 및 다크 모드 스타일링 */
    table { width: 100%; border-collapse: collapse; color: #00FF41 !important; margin-top: 5px !important; }
    th { background-color: #001100 !important; color: #00FF41 !important; border: 1px solid #00FF41 !important; font-size: 14px; padding: 6px 10px !important; }
    td { border: 1px solid #00FF41 !important; padding: 6px 10px !important; font-size: 13px; background-color: #000000 !important; }
    
    hr { margin: 0.8rem 0 !important; border-color: #004411 !important; }
    h1, h2, h3 { color: #00FF41 !important; text-shadow: 0px 0px 5px #00FF41; margin-top: 5px !important; margin-bottom: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ 보안 관제 1호: 디스코드 실시간 알림 로깅 엔진
# ==========================================
def send_discord_log(ticker, company_name, pressure_summary):
    # 🔒 GitHub 노출 방지: 주소를 소스코드에서 지우고 클라우드 인프라(Secrets)에서 읽어옴
    DISCORD_WEBHOOK_URL = st.secrets.get("DISCORD_WEBHOOK_URL", "")
    
    if not DISCORD_WEBHOOK_URL:
        return 
        
    payload = {
        "username": "DILUTION RADAR WATCHDOG",
        "embeds": [
            {
                "title": f"🚨 [ACCESS LOG] TARGET SCANNED: {ticker}",
                "color": 65281, 
                "fields": [
                    {"name": "종목 풀네임", "value": company_name, "inline": True},
                    {"name": "수급 진단 결과", "value": pressure_summary, "inline": False}
                ],
                "footer": {"text": "TERMINAL-OVERHANG-OPS SECURITY SYSTEM"}
            }
        ]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except:
        pass

# ==========================================
# ⚙️ 데이터 연동 백엔드 코어 (SEC & YFinance)
# ==========================================
SEC_HEADERS = {'User-Agent': 'NeoTerminal neo@matrix.com'}

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
    elif public_float < 5000000: pressure = "🚨 [초극단적 품절주] 유통물량 500만 주 미만. 세력 작전 타겟 확률 농후."
    elif float_ratio < 40: pressure = "🔒 락업 물량이 많아 유통량이 철저히 통제됨."
    else: pressure = "✅ 유통물량 충분. 수급 압박 적음."
    return {"outstanding_shares": outstanding, "public_float": public_float, "float_ratio": float_ratio, "pressure_summary": pressure, "company_name": company_name}

# ==========================================
# 🖥️ 보안 관제 2호: 분석 래퍼 엔진 가동
# ==========================================
# 🔒 GitHub 노출 방지: 관리자 비밀번호도 인프라 환경 변수에서 로드 (로컬 기본값: mimi_local)
admin_password = st.secrets.get("ANALYTICS_PASSWORD", "mimi_local")

with streamlit_analytics.track(unsafe_password=admin_password):

    # 요청하신 타이틀 문구 확정
    st.markdown("### 💻 TERMINAL-OVERHANG-OPS v1 STATUS: ONLINE")

    # st.form 빌드로 엔터(Enter) 입력 자동 지원
    with st.form(key='hacker_terminal_form'):
        ticker_input = st.text_input("▶ ENTER TARGET TICKER:", "MIMI").upper()
        submit_button = st.form_submit_button("EXECUTE SCAN (ENTER)")

    if submit_button and ticker_input:
        terminal_output = st.empty()
        terminal_output.markdown("`[SYSTEM] CONNECTING TO SEC MAINFRAME... OK.`")
        time.sleep(0.2)
        terminal_output.empty()
        
        stock_info = get_live_stock_info(ticker_input)
        matrix_data = scan_sec_filings(ticker_input)
        
        # 디스코드 웹훅 알림 자동 발사
        send_discord_log(ticker_input, stock_info['company_name'], stock_info['pressure_summary'])
        
        # 주식 수 현황 직관적 한글 패치 및 풀네임 출력
        st.markdown(f"**📂 [{ticker_input}] {stock_info['company_name']}**")
        st.markdown(f"• **총 발행 주식 수:** {stock_info['outstanding_shares']:,} 주 | **실제 유통 주식 수:** {stock_info['public_float']:,} 주 ({stock_info['float_ratio']}%)\n> 🔍 **진단:** {stock_info['pressure_summary']}")
        st.markdown("---")
        
        # 오버행 매트릭스 표 생성
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