import os

# ============================================================
#  환경변수 기반 설정 (Render / 로컬 공용)
# ============================================================

# 관리자 비밀번호 (반드시 환경변수로 설정하세요)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "zizer731!!")

# 관리자 패널 접근 IP
_default_ips = os.environ.get("ADMIN_ALLOWED_IPS", "127.0.0.1,::1,localhost")
ADMIN_ALLOWED_IPS = [ip.strip() for ip in _default_ips.split(",") if ip.strip()]

# bcsfe 데이터/세이브 디렉토리 (Render 리눅스 환경 대응)
if os.environ.get("BCSFE_DATA_DIR"):
    BCSFE_DATA_DIR = os.environ["BCSFE_DATA_DIR"]
else:
    BCSFE_DATA_DIR = os.path.join(os.path.expanduser("~"), "bcsfe")

BCSFE_SAVE_DIR = os.environ.get("BCSFE_SAVE_DIR", os.path.join(BCSFE_DATA_DIR, "saves"))

# 데이터 디렉토리 (주문/로그/쿠폰 JSON)
DATA_DIR = os.environ.get("DATA_DIR", "data")

# Flask 세션 암호화 키 (반드시 환경변수로 설정하세요)
SECRET_KEY = os.environ.get("SECRET_KEY", "nyanko-charge-secret-2024-change-me")

# 키 구매 설정 (호환성 유지 - 실제로는 쿠폰 코드 시스템 사용)
KEY_PURCHASE_ENABLED = os.environ.get("KEY_PURCHASE_ENABLED", "true").lower() == "true"
KEY_PRICES = {
    "1day": {"name": "1일 키", "price": 0, "days": 1},
    "3day": {"name": "3일 키", "price": 0, "days": 3},
    "7day": {"name": "7일 키", "price": 0, "days": 7},
    "30day": {"name": "30일 키", "price": 0, "days": 30},
}

# 서버 설정
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("PORT", os.environ.get("SERVER_PORT", "5000")))
SERVER_DEBUG = os.environ.get("SERVER_DEBUG", "false").lower() == "true"