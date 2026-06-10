# ⚙️ TERMINAL-OVERHANG-OPS : DILUTION RADAR v1.0

> **OPERATIONAL STATUS:** `ACTIVE`  
> **SEC MAINFRAME LINK:** `BYPASSED / SECURED`  
> **SECURITY LEVEL:** `CLEARANCE REQUIRED (ROOT)`

---

## 👁️ 개요 (MISSION OVERVIEW)

**`terminal-overhang-ops`**는 미국 주식 시장에 숨겨진 기관들의 **오버행(지분 희석) 폭탄**과 **실시간 수급 압박**을 추적하기 위해 설계된 전용 작전 터미널입니다. 

비개발자 요원들도 터미널 환경의 웅장함을 느낄 수 있도록 **The Matrix(매트릭스) 스타일의 Black & Neon-Green 테마**로 빌드되었습니다. 티커(종목 코드)만 입력하면 미국 증권거래위원회(SEC)의 메인프레임을 스캔하여 일급 기밀 데이터를 탈취(?)합니다.

---

## ⚡ 핵심 기능 (TACTICAL FEATURES)

* 📡 **실시간 유통물량 스캔 (Live Float Extraction):** `Yahoo Finance API` 네트워크를 통해 대상 종목의 발행 주식 수와 실제 유통 물량(Public Float)을 1초 만에 가로챕니다.
* 🚨 **초극단적 품절주 감지 (Algorithmic Diagnostics):** 유통물량이 500만 주 미만인 작전 후보 종목을 자동으로 판별하여 폭등/폭락 경보를 발령합니다.
* 🕵️‍♂️ **SEC 백도어 스캔 (SEC Submissions Intercept):** 회사가 은밀하게 제출한 `F-3(선반 유상증자)`, `424B5(ATM 기습 매도 계약)`, `S-8(임직원 물량)` 공시 서류의 날짜를 추적하여 지분 희석 위험도를 실시간 매트릭스로 시각화합니다.

---

## 🛠️ 가동 방법 (OPERATIONAL GUIDE)

### 1. 필수 모듈 주입 (Dependencies)
본 가동 터미널은 텅 빈 컨테이너 환경에서 작동하지 않습니다. 시스템을 구동하기 전, 쉘(CMD / PowerShell)에 아래 명령어를 입력하여 핵심 패키지를 주입하십시오.

```bash
pip install streamlit yfinance requests rich