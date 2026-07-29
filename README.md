# 🐱 냥코통조림충전소

자동화된 Battle Cats 통조림 충전 웹사이트입니다.

## ✨ 주요 기능

- **45,000개 통조림 자동 충전** (가격은 관리자가 설정 가능)
- **무통장입금 + Pushbullet 실시간 입금 감지** (또는 수동 확인)
- **자동 기기이전번호/인증번호 생성 및 반환**
- **다중 구매 동시 처리 지원**
- **관리자 패널** - 가격 설정, 구매내역, 입금내역, 지급 실패 내역 확인
- **3분 이내 빠른 처리** - 입금 즉시 자동 충전
- **컴퓨터 꺼져도 24시간 운영** - 백그라운드 실행 지원

## 🚀 설치 및 실행

### 1. 의존성 설치
```powershell
cd C:\Users\USER\Desktop\battle-cats-shop
pip install -r requirements.txt
```

### 2. 설정 확인 (config.py)
```python
PUSHBULLET_API_KEY = "o.P9LtMvpDoNgYXOLogbiPsuIvZc95P2nY"  # Pushbullet API 키
BANK_NAME = "토스뱅크"
BANK_ACCOUNT = "1908-9467-3821"
ACCOUNT_HOLDER = "공예준"
ADMIN_PASSWORD = "admin1234"  # 관리자 비밀번호
```

### 3. 서버 실행
```powershell
# 방법 1: 배치 파일 실행 (권장)
start_server.bat

# 방법 2: 개별 실행
python app.py          # Flask 서버
python pushbullet_listener.py  # Pushbullet 리스너
```

## 📱 사용 방법

### 고객용
1. **게임 준비**: Battle Cats → 설정 → 계정/기기 변경 → 기기 변경 → '서버에 세이브 저장'
2. **주문 생성**: 입금자명, 전송코드, 확인코드 입력 → 주문 생성
3. **입금**: 표시된 계좌로 주문 금액 입금
4. **자동 처리**: 3분 이내 자동으로 충전 완료
5. **결과 확인**: 새 전송코드/인증번호 표시

### 관리자용
- **로그인**: `http://localhost:5000/admin/login` (비밀번호: `admin1234`)
- **가격 설정**: 통조림 수량별 가격 수정
- **구매내역**: 모든 주문 내역 확인
- **입금내역**: 자동/수동 입금 기록
- **지급 실패**: 실패한 주문 재시도

## 📋 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 고객 쇼핑몰 페이지 |
| POST | `/create-order` | 주문 생성 |
| GET | `/order-status/{id}` | 주문 상태 조회 |
| POST | `/check-deposit` | 입금 확인 (수동) |
| POST | `/check-deposit-internal` | Pushbullet 리스너용 |
| GET | `/admin/login` | 관리자 로그인 |
| GET | `/admin` | 관리자 패널 |
| POST | `/admin/update-prices` | 가격 설정 |
| POST | `/admin/manual-deposit` | 수동 입금 확인 |
| GET | `/admin/data` | 데이터 내보내기 |

## 📁 파일 구조
```
battle-cats-shop/
├── app.py                    # Flask 메인 애플리케이션
├── bcsfe_handler.py          # bcsfe 자동화 핸들러
├── config.py                 # 설정 파일
├── pushbullet_listener.py    # 입금 알림 감지
├── requirements.txt          # 의존성 패키지
├── start_server.bat          # 서버 시작 스크립트
├── data/                     # 데이터 저장 (orders.json, deposits.json, prices.json)
├── templates/
│   ├── index.html            # 고객 쇼핑몰
│   ├── admin.html            # 관리자 패널
│   └── admin_login.html      # 관리자 로그인
└── static/
    └── style.css             # 스타일시트
```

## ⚙️ GitHub Pages 배포

GitHub Pages로 배포하려면 정적 HTML 파일만 필요합니다. Flask 앱은 로컬 서버로 유지하고, 고객용 페이지는 GitHub Pages에 호스팅할 수 있습니다.

1. `templates/index.html`을 GitHub Pages에 업로드
2. API URL을 GitHub Pages 도메인으로 변경
3. 로컬 Flask 서버는 24시간 실행 (컴퓨터 꺼져도 유지)

## ⚠️ 주의사항
- bcsfe API 구현은 실제 테스트 후 완성 필요
- Pushbullet API 키가 없으면 수동 확인만 가능
- 실제 결제 전 반드시 테스트로 검증
- 입금자명은 주문 시 입력한 이름과 정확히 일치해야 합니다
- 컴퓨터를 끄더라도 서버를 유지하려면 백그라운드에서 실행하세요

## 🛡️ 보안
- 관리자 비밀번호는 config.py에서 변경 가능
- 세션 기반 인증 사용
- 데이터는 JSON 파일로 안전하게 저장
