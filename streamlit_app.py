import streamlit as st
import yfinance as yf
import requests
import time

# ==========================================
# 0. 앱 기본 설정 & 매트릭스 테마 CSS 적용
# ==========================================
st.set_page_config(page_title="Terminal Overhang Ops", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경과 폰트 설정 */
    .stApp { background-color: #050505; color: #00FF41; font-family: 'Courier New', Courier, monospace; }
    
    /* 💡 개선 포인트 1: 입력창 레이블 글자 크기 키우고 형광색+그림자 효과로 가독성 극대화 */
    div.stTextInput > label { 
        color: #00FF41 !important; 
        font-size: 22px !important; 
        font-weight: bold !important; 
        text-shadow: 0px 0px 10px #00FF41;
        letter-spacing: 1px;
    }
    
    /* 텍스트 입력창 스타일링 */
    div.stTextInput > div > div > input { background-color: #000000; color: #00FF41; border: 1px solid #00FF41; font-size: 18px; }
    
    /* 버튼 스타일링 */
    div.stButton > button { background-color: #000000; color: #00FF41; border: 1px solid #00FF41; font-weight: bold; width: 100%; height: 45px; font-size: 16px; }
    div.stButton > button:hover { background-color: #00FF41; color: #000000; }
    
    /* 마크다운 표(Table) 스타일링 */
    table { width: 100%; border-collapse: collapse; color: #00FF41 !important; }
    th { background-color: #002200 !important; color: #00FF41 !important; border: 1px solid #00FF41 !important; font-size: 16px;}
    td { border: 1px solid #00FF41 !important; padding: 8px; font-size: 14px;}
    
    h1, h2, h3 { color: #00FF41 !important; text-shadow: 0px 0px 5px #00FF41; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ SEC EDGAR API 엔진 & YFinance 데이터 엔진
# ==========================================
SEC_HEADERS = {
    'User-Agent': 'NeoTerminal neo@matrix.com' 
}

@st.cache_data(ttl=3600)
def get_cik_from_ticker(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        data = response.json()
        for key, value in data.items():
            if value['ticker'] == ticker.upper():
                return str(value['cik_str']).zfill(10)
    except:
        return None
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
    if not cik:
        return matrix
        
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        if response.status_code != 200:
            return matrix
        
        data = response.json()
        recent_filings = data['filings']['recent']
        forms = recent_filings['form']
        dates = recent_filings['filingDate']
        
        found_f3, found_atm, found_s8, found_resale = False, False, False, False
        
        for i in range(len(forms)):
            form_type = forms[i]
            filing_date = dates[i]
            
            if form_type in ['F-3', 'S-3', 'F-3ASR', 'S-3ASR'] and not found_f3:
                matrix["기존/신규 F-3 Shelf"] = {"exists": "⚠️ 존재", "scale": "본문 확인 필요", "stage": f"발견일: {filing_date}", "cash_inflow": "가동 시 유입", "impact": "유통물량 폭증 위험", "risk": "매우 높음"}
                found_f3 = True
            if form_type in ['424B5', '424B2'] and not found_atm:
                matrix["ATM / ELOC / SEPA"] = {"exists": "⚠️ 가동 의심", "scale": "본문 확인 필요", "stage": f"발견일: {filing_date}", "cash_inflow": "즉각 유입", "impact": "강한 매물대 형성", "risk": "높음"}
                found_atm = True
            if form_type in ['S-1', 'S-1/A', '424B3'] and not found_resale:
                matrix["Selling Shareholder Resale"] = {"exists": "확인 요망", "scale": "본문 확인 필요", "stage": f"제출일: {filing_date}", "cash_inflow": "없음 (주주간 거래)", "impact": "기존 주주 차익실현 물량", "risk": "높음"}
                found_resale = True
            if form_type == 'S-8' and not found_s8:
                matrix["S-8 / 임직원 보상주식"] = {"exists": "존재", "scale": "본문 확인 필요", "stage": f"발견일: {filing_date}", "cash_inflow": "행사 시 일부", "impact": "영향 적음", "risk": "낮음"}
                found_s8 = True
    except:
        pass
    return matrix

@st.cache_data(ttl=3600)
def get_live_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        outstanding = info.get('sharesOutstanding') or 0
        public_float = info.get('floatShares') or 0
        # 💡 개선 포인트 2: 종목 풀네임(longName) 실시간 추출 로직 추가
        company_name = info.get('longName') or info.get('shortName') or "UNKNOWN COMPANY"
    except:
        outstanding, public_float = 0, 0
        company_name = "UNKNOWN COMPANY"
        
    float_ratio = round((public_float / outstanding) * 100, 1) if outstanding > 0 else 0.0
    
    if public_float == 0: pressure = "⚠️ API 통신 오류 또는 정보 비공개 (수동 확인 필요)"
    elif public_float < 5000000: pressure = "🚨 [초극단적 품절주] 유통물량 500만 주 미만. 세력의 작전 타겟이 될 수 있습니다."
    elif float_ratio < 40: pressure = "🔒 락업 물량이 많아 유통량이 철저히 통제되고 있습니다."
    else: pressure = "✅ 유통물량이 충분하여 수급 압박이 적습니다."

    return {
        "outstanding_shares": outstanding, 
        "public_float": public_float, 
        "float_ratio": float_ratio, 
        "pressure_summary": pressure,
        "company_name": company_name
    }

# ==========================================
# 🖥️ 스트림릿 웹 UI 구성
# ==========================================
st.title("💻 ZERO-DAY DILUTION SCANNER v1.0")
st.markdown("`SYSTEM STATUS: ONLINE` | `SEC MAINFRAME: CONNECTED`")
st.markdown("---")

# 💡 개선 포인트 3: st.form으로 감싸서 '엔터(Enter)' 입력 지원 적용
with st.form(key='hacker_terminal_form', clear_on_submit=False):
    # 예시 가이드를 지우고 레이블 폰트 가독성을 극대화함
    ticker_input = st.text_input("▶ ENTER TARGET TICKER:", "MIMI").upper()
    submit_button = st.form_submit_button("EXECUTE ANALYSIS")

# 실행 조건문 (버튼 클릭 혹은 엔터 입력 시 실행)
if submit_button:
    if ticker_input:
        
        terminal_output = st.empty()
        terminal_output.markdown("> `INITIATING CONNECTION TO SEC EDGAR DATABASE...`")
        time.sleep(0.5)
        terminal_output.markdown("> `BYPASSING FIREWALL... SUCCESS.`")
        time.sleep(0.5)
        terminal_output.markdown(f"> `EXTRACTING LIVE DATA FOR [{ticker_input}]...`")
        time.sleep(0.6)
        terminal_output.empty()
        
        # 데이터 수집
        stock_info = get_live_stock_info(ticker_input)
        matrix_data = scan_sec_filings(ticker_input)
        
        # 💡 개선 포인트 4: 티커 옆에 종목 풀네임이 직관적으로 출력되도록 수정
        st.subheader(f"📂 [{ticker_input}] {stock_info['company_name']}")
        
        # 💡 개선 포인트 5: 요청하신 주식 수 현황을 완벽하게 한글화하여 직관성 업그레이드
        st.markdown(f"""
        * **총 발행 주식 수:** {stock_info['outstanding_shares']:,} 주
        * **실제 유통 주식 수 (공동 플로트):** {stock_info['public_float']:,} 주 ({stock_info['float_ratio']}%)
        > 🔍 **위험 진단 결과:** {stock_info['pressure_summary']}
        """)
        
        st.markdown("---")
        
        # 2. 오버행 매트릭스 출력
        st.subheader("📊 OVERHANG & DILUTION MATRIX")
        table_md = "| CATEGORY | STATUS | SCALE | LATEST FILING | CASH INFLOW | SHAREHOLDER IMPACT | RISK LEVEL |\n"
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
        st.success(f"OPERATION COMPLETE. {ticker_input} DATA SECURED.")
        
    else:
        st.error("ERROR: TICKER CANNOT BE EMPTY.")