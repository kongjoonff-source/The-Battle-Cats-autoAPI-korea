import os

# ============================================================
#  환경변수 기반 설정 (Render / 로컬 공용)
#  - Render 대시보드의 Environment 탭에서 아래 키들을 등록하세요.
#  - 로컬에서는 .env 파일 또는 시스템 환경변수로 설정 가능.
# ============================================================

# Pushbullet API 설정
PUSHBULLET_API_KEY = os.environ.get("PUSHBULLET_API_KEY", "")

# 은행 계좌 정보 (무통장입금용)
BANK_NAME = os.environ.get("BANK_NAME", "토스뱅크")
BANK_ACCOUNT = os.environ.get("BANK_ACCOUNT", "1908-9467-3821")
ACCOUNT_HOLDER = os.environ.get("ACCOUNT_HOLDER", "공예준")

# 상품 가격 설정 (관리자 패널에서 수정 가능)
CATFOOD_PRICES = {
    "10000": 500,      # 10,000개 - 500원
    "30000": 1000,     # 30,000개 - 1,000원
    "45000": 2000,     # 45,000개 - 2,000원 (최대)
}

# XP 상품
XP_PRICES = {
    "99999999": 1000,  # 99,999,999 XP - 1,000원
}

# 티켓 상품
TICKET_PRICES = {
    "rare_10": 1500,       # 레어 티켓 10개 - 1,500원
    "legend_5": 2000,      # 레전드 티켓 5개 - 2,000원
    "platinum_3": 2500,    # 플래티넘 티켓 3개 - 2,500원
}

# 관리자 비밀번호 (반드시 환경변수로 설정하세요)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "zizer731!!")

# 관리자 패널 접근 IP
# Render 프록시 뒤에서는 127.0.0.1만으로는 접근 안 될 수 있음.
# 외부 접속을 허용하려면 ADMIN_ALLOWED_IPS 환경변수에 쉼표로 구분.
_default_ips = os.environ.get("ADMIN_ALLOWED_IPS", "127.0.0.1,::1,localhost")
ADMIN_ALLOWED_IPS = [ip.strip() for ip in _default_ips.split(",") if ip.strip()]

# bcsfe 데이터/세이브 디렉토리 (Render 리눅스 환경 대응)
# - 환경변수가 없으면 플랫폼별 기본 경로 사용
if os.environ.get("BCSFE_DATA_DIR"):
    BCSFE_DATA_DIR = os.environ["BCSFE_DATA_DIR"]
else:
    BCSFE_DATA_DIR = os.path.join(os.path.expanduser("~"), "bcsfe")

BCSFE_SAVE_DIR = os.environ.get("BCSFE_SAVE_DIR", os.path.join(BCSFE_DATA_DIR, "saves"))

# 데이터 디렉토리 (주문/입금/가격 JSON)
# Render의 영구 디스크를 마운트한 경우 해당 경로로 변경 가능.
DATA_DIR = os.environ.get("DATA_DIR", "data")

# Flask 세션 암호화 키 (반드시 환경변수로 설정하세요)
SECRET_KEY = os.environ.get("SECRET_KEY", "nyanko-charge-secret-2024-change-me")

# 키 구매 설정
KEY_PURCHASE_ENABLED = os.environ.get("KEY_PURCHASE_ENABLED", "true").lower() == "true"
KEY_PRICES = {
    "1day": {"name": "1일 키", "price": 5000, "days": 1},
    "3day": {"name": "3일 키", "price": 10000, "days": 3},
}

# 서버 설정
# Render는 PORT 환경변수를 자동으로 넘겨줌.
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("PORT", os.environ.get("SERVER_PORT", "5000")))
SERVER_DEBUG = os.environ.get("SERVER_DEBUG", "false").lower() == "true"