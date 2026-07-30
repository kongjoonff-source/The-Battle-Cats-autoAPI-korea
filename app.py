from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import threading
import secrets
import time
import requests
from datetime import datetime, timedelta
from bcsfe_handler_full import process_all_items
from config import (
    PUSHBULLET_API_KEY, BANK_NAME, BANK_ACCOUNT, ACCOUNT_HOLDER,
    CATFOOD_PRICES, XP_PRICES, TICKET_PRICES,
    DATA_DIR, SERVER_HOST, SERVER_PORT, SERVER_DEBUG,
    ADMIN_PASSWORD, ADMIN_ALLOWED_IPS, SECRET_KEY
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=365)

os.makedirs(DATA_DIR, exist_ok=True)

# bcsfe 초기화 (gunicorn 환경에서도 모듈 로드 시 1회 실행)
def _init_bcsfe():
    try:
        from bcsfe.core import core_data
        core_data.init_data()
        print("[INFO] bcsfe 초기화 완료")
    except Exception as e:
        print(f"[WARN] bcsfe 초기화 실패: {e}")

_init_bcsfe()

# ========== Keep-Alive (Render 무료 플랜 슬립 방지) ==========
def _keep_alive():
    """5분마다 자기 자신에게 핑을 보내서 Render 슬립 방지"""
    # RENDER_EXTERNAL_URL이 없으면 KEEP_ALIVE_URL 환경변수 사용 (다른 Render 계정/서비스 대응)
    url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("KEEP_ALIVE_URL")
    if not url:
        print("[KEEP-ALIVE] 비활성화: RENDER_EXTERNAL_URL/KEEP_ALIVE_URL 없음")
        return
    # URL 끝 슬래시 정리
    url = url.rstrip("/")
    ping_path = os.environ.get("KEEP_ALIVE_PATH", "/health")
    interval = int(os.environ.get("KEEP_ALIVE_INTERVAL", "300"))  # 기본 5분(300초)
    print(f"[KEEP-ALIVE] 활성화: {url}{ping_path} ({interval}초 간격)")
    while True:
        try:
            resp = requests.get(url + ping_path, timeout=10)
            print(f"[KEEP-ALIVE] 핑 전송: {datetime.now().strftime('%H:%M:%S')} -> {resp.status_code}")
        except Exception as e:
            print(f"[KEEP-ALIVE] 핑 실패: {e}")
        time.sleep(interval)

# Render 환경 또는 KEEP_ALIVE_URL 설정 시 keep-alive 스레드 시작
if os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("KEEP_ALIVE_URL"):
    threading.Thread(target=_keep_alive, daemon=True).start()

ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
DEPOSITS_FILE = os.path.join(DATA_DIR, "deposits.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
ACCESS_KEYS_FILE = os.path.join(DATA_DIR, "access_keys.json")

# ========== 데이터 로드/저장 ==========

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def load_deposits():
    if os.path.exists(DEPOSITS_FILE):
        with open(DEPOSITS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_deposits(deposits):
    with open(DEPOSITS_FILE, "w", encoding="utf-8") as f:
        json.dump(deposits, f, ensure_ascii=False, indent=2)

def load_access_keys():
    if os.path.exists(ACCESS_KEYS_FILE):
        with open(ACCESS_KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_access_keys(keys):
    with open(ACCESS_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)

def is_key_valid(key):
    """키가 존재하고 만료되지 않았는지 확인"""
    keys = load_access_keys()
    for k in keys:
        if k["key"] == key:
            expires_at = datetime.fromisoformat(k["expires_at"])
            if datetime.now() < expires_at:
                return True, k
    return False, None

# 모든 상품 가격
def get_all_prices():
    prices = {}
    prices.update(CATFOOD_PRICES)
    prices.update(XP_PRICES)
    prices.update(TICKET_PRICES)
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            prices.update(saved)
    return prices

# 기본 아이템 리스트 (동적 가격)
def get_item_definitions():
    """모든 BCSFE 아이템 정의"""
    return [
        # 통조림
        {"id": "catfood_10000", "type": "catfood", "name": "통조림 10,000개", "amount": 10000, "icon": "🥫", "category": "통조림", "price": 500},
        {"id": "catfood_30000", "type": "catfood", "name": "통조림 30,000개", "amount": 30000, "icon": "🥫", "category": "통조림", "price": 1500},
        {"id": "catfood_45000", "type": "catfood", "name": "통조림 45,000개", "amount": 45000, "icon": "🥫", "category": "통조림", "price": 2000},
        # XP
        {"id": "xp_99999999", "type": "xp", "name": "XP 99,999,999", "amount": 99999999, "icon": "✨", "category": "XP", "price": 1000},
        {"id": "xp_50000000", "type": "xp", "name": "XP 50,000,000", "amount": 50000000, "icon": "✨", "category": "XP", "price": 500},
        {"id": "xp_10000000", "type": "xp", "name": "XP 10,000,000", "amount": 10000000, "icon": "✨", "category": "XP", "price": 200},
        # 티켓
        {"id": "rare_10", "type": "rare_ticket", "name": "레어 티켓 10개", "amount": 10, "icon": "🎟️", "category": "티켓", "price": 1500},
        {"id": "rare_50", "type": "rare_ticket", "name": "레어 티켓 50개", "amount": 50, "icon": "🎟️", "category": "티켓", "price": 5000},
        {"id": "legend_5", "type": "legend_ticket", "name": "레전드 티켓 5개", "amount": 5, "icon": "🌟", "category": "티켓", "price": 2000},
        {"id": "legend_10", "type": "legend_ticket", "name": "레전드 티켓 10개", "amount": 10, "icon": "🌟", "category": "티켓", "price": 3500},
        {"id": "platinum_3", "type": "platinum_ticket", "name": "플래티넘 티켓 3개", "amount": 3, "icon": "💎", "category": "티켓", "price": 2500},
        {"id": "platinum_10", "type": "platinum_ticket", "name": "플래티넘 티켓 10개", "amount": 10, "icon": "💎", "category": "티켓", "price": 7000},
        {"id": "normal_50", "type": "normal_ticket", "name": "노멀 티켓 50개", "amount": 50, "icon": "🎫", "category": "티켓", "price": 1000},
        {"id": "normal_100", "type": "normal_ticket", "name": "노멀 티켓 100개", "amount": 100, "icon": "🎫", "category": "티켓", "price": 1500},
        # 조각
        {"id": "platinum_shard_5", "type": "platinum_shard", "name": "플래티넘 조각 5개", "amount": 5, "icon": "🔷", "category": "기타", "price": 2000},
        {"id": "platinum_shard_10", "type": "platinum_shard", "name": "플래티넘 조각 10개", "amount": 10, "icon": "🔷", "category": "기타", "price": 3500},
        # 리더십 / NP
        {"id": "leadership_10", "type": "leadership", "name": "리더십 10개", "amount": 10, "icon": "⚡", "category": "기타", "price": 500},
        {"id": "leadership_50", "type": "leadership", "name": "리더십 50개", "amount": 50, "icon": "⚡", "category": "기타", "price": 2000},
        {"id": "np_1000", "type": "np", "name": "NP 1,000개", "amount": 1000, "icon": "🧬", "category": "기타", "price": 1000},
        {"id": "np_5000", "type": "np", "name": "NP 5,000개", "amount": 5000, "icon": "🧬", "category": "기타", "price": 4000},
        {"id": "np_10000", "type": "np", "name": "NP 10,000개", "amount": 10000, "icon": "🧬", "category": "기타", "price": 7000},
    ]

# ========== 접근 키 게이트 ==========

@app.before_request
def check_access_key():
    """유효한 키가 없으면 게이트 페이지로 리다이렉트"""
    # 예외 경로 (키 입력, 관리자, 정적 파일, 헬스체크)
    exempt_prefixes = ['/gate', '/api/verify-key', '/static', '/admin', '/api/admin', '/health', '/ping']
    for prefix in exempt_prefixes:
        if request.path.startswith(prefix):
            return

    # 세션에 유효한 키가 있는지 확인
    user_key = session.get('access_key')
    if user_key:
        valid, _ = is_key_valid(user_key)
        if valid:
            return  # 통과

    # 유효한 키 없음 → 게이트로
    return redirect(url_for('gate'))

# ========== 라우트: 게이트 ==========

@app.route("/gate")
def gate():
    """키 입력 페이지"""
    user_key = session.get('access_key')
    if user_key:
        valid, _ = is_key_valid(user_key)
        if valid:
            return redirect(url_for('index'))
    return render_template("gate.html")

@app.route("/api/verify-key", methods=["POST"])
def verify_key():
    """키 검증 및 세션 설정"""
    data = request.json
    key = data.get("key", "").strip()
    valid, key_data = is_key_valid(key)
    if valid:
        session.permanent = True
        session['access_key'] = key
        # 세션 만료를 키 만료시간에 맞춤
        expires_at = datetime.fromisoformat(key_data['expires_at'])
        app.permanent_session_lifetime = expires_at - datetime.now()
        return jsonify({"success": True, "message": "접근이 허용되었습니다"})
    return jsonify({"success": False, "error": "유효하지 않거나 만료된 키입니다"}), 403

# ========== 라우트: 헬스체크 (Keep-Alive / 외부 핑용) ==========

@app.route("/health")
def health():
    """헬스체크 엔드포인트 (접근 키 없이 접근 가능, 가벼운 응답)"""
    return jsonify({
        "status": "ok",
        "service": "nyanko-charge",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/ping")
def ping():
    """핑 엔드포인트 (단순 텍스트 응답, 외부 모니터링용)"""
    return "pong", 200

# ========== 라우트: 메인 ==========

@app.route("/")
def index():
    items = get_item_definitions()
    return render_template("index.html",
        items=items,
        bank_name=BANK_NAME,
        bank_account=BANK_ACCOUNT,
        account_holder=ACCOUNT_HOLDER)

@app.route("/api/items")
def api_items():
    """아이템 목록 API"""
    return jsonify(get_item_definitions())

@app.route("/api/submit", methods=["POST"])
def submit_order():
    """주문 제출"""
    data = request.json
    buyer_name = data.get("buyer_name", "").strip()
    transfer_code = data.get("transfer_code", "").strip()
    confirmation_code = data.get("confirmation_code", "").strip()
    selected_items = data.get("items", [])

    if not all([buyer_name, transfer_code, confirmation_code]):
        return jsonify({"error": "모든 필드를 입력해주세요"}), 400

    if not selected_items:
        return jsonify({"error": "아이템을 선택해주세요"}), 400

    items_def = get_item_definitions()
    total_price = 0
    item_details = []

    for sel in selected_items:
        item_id = sel.get("id", "")
        quantity = int(sel.get("quantity", 1))
        match = next((i for i in items_def if i["id"] == item_id), None)
        if match:
            total_price += match["price"] * quantity
            item_details.append({
                **match,
                "quantity": quantity,
                "line_price": match["price"] * quantity
            })

    if total_price <= 0:
        return jsonify({"error": "유효한 아이템을 선택해주세요"}), 400

    orders = load_orders()
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"

    order = {
        "id": order_id,
        "buyer_name": buyer_name,
        "transfer_code": transfer_code,
        "confirmation_code": confirmation_code,
        "items": item_details,
        "total_price": total_price,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "result": None,
        "deposit_confirmed": False
    }

    orders.append(order)
    save_orders(orders)

    item_summary = ", ".join([f"{i['name']}x{i['quantity']}" for i in item_details])

    return jsonify({
        "order_id": order_id,
        "total_price": total_price,
        "items": item_summary,
        "message": f"주문 완료! {total_price}원을 입금해주세요."
    })

@app.route("/api/order/<order_id>")
def get_order(order_id):
    """주문 상태 확인"""
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "주문 없음"}), 404
    return jsonify(order)

@app.route("/api/process", methods=["POST"])
def process_order_direct():
    """입금 없이 바로 처리"""
    data = request.json
    order_id = data.get("order_id", "").strip()

    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id and o["status"] == "pending"), None)

    if not order:
        return jsonify({"error": "주문 없음"}), 404

    order["status"] = "processing"
    save_orders(orders)

    def process_background():
        try:
            bcsfe_items = []
            for item in order["items"]:
                for _ in range(item["quantity"]):
                    bcsfe_items.append({
                        "type": item["type"],
                        "amount": item["amount"]
                    })

            print(f"[APP] 처리 시작: {order['id']}")
            print(f"[APP] 전송코드: {order['transfer_code']}")
            print(f"[APP] 인증번호: {order['confirmation_code']}")
            print(f"[APP] 아이템: {bcsfe_items}")

            success, new_tc, new_cc, error, results = process_all_items(
                order["transfer_code"],
                order["confirmation_code"],
                bcsfe_items
            )

            print(f"[APP] 처리 결과: success={success}, error={error}")
            print(f"[APP] 새 코드: {new_tc} / {new_cc}")

            order["status"] = "completed" if success else "failed"
            order["result"] = {
                "success": success,
                "new_transfer_code": new_tc,
                "new_confirmation_code": new_cc,
                "error": error,
                "details": results
            }
        except Exception as e:
            print(f"[APP] 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            order["status"] = "failed"
            order["result"] = {"success": False, "error": str(e), "details": []}
        order["completed_at"] = datetime.now().isoformat()
        save_orders(orders)

    thread = threading.Thread(target=process_background)
    thread.start()

    return jsonify({
        "message": "처리 시작!",
        "order_id": order["id"]
    })

# ========== 라우트: 관리자 ==========

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    """관리자 로그인"""
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session.permanent = True
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template("admin_login.html", error="비밀번호가 틀렸습니다")
    return render_template("admin_login.html")

@app.route("/admin/panel")
def admin_panel():
    """관리자 패널"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    orders = load_orders()
    deposits = load_deposits()
    prices = get_all_prices()
    access_keys = load_access_keys()

    # 만료 여부 표시
    now = datetime.now()
    for k in access_keys:
        k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now

    # 통계
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.get('status') == 'completed'])
    pending_orders = len([o for o in orders if o.get('status') == 'pending'])
    failed_orders = len([o for o in orders if o.get('status') == 'failed'])
    total_revenue = sum(o.get('total_price', 0) for o in orders if o.get('status') == 'completed')

    return render_template("admin.html",
        orders=orders,
        deposits=deposits,
        prices=prices,
        access_keys=access_keys,
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        failed_orders=failed_orders,
        total_revenue=total_revenue
    )

@app.route("/admin/logout")
def admin_logout():
    """관리자 로그아웃"""
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route("/admin/update-prices", methods=["POST"])
def admin_update_prices():
    """가격 일괄 업데이트"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    prices = data.get("prices", {})
    # 정수 변환
    prices = {k: int(v) for k, v in prices.items()}
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True, "message": "가격이 저장되었습니다"})

@app.route("/admin/manual-deposit", methods=["POST"])
def admin_manual_deposit():
    """수동 입금 확인"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    buyer_name = data.get("buyer_name", "")
    deposit_amount = data.get("deposit_amount", 0)

    deposits = load_deposits()
    deposit = {
        "id": f"DEP{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "buyer_name": buyer_name,
        "amount": deposit_amount,
        "timestamp": datetime.now().isoformat(),
        "manual": True
    }
    deposits.append(deposit)
    save_deposits(deposits)

    return jsonify({"success": True, "message": "입금 확인 완료"})

@app.route("/admin/data")
def admin_export_data():
    """데이터 내보내기"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = {
        "orders": load_orders(),
        "deposits": load_deposits(),
        "prices": get_all_prices(),
        "access_keys": load_access_keys()
    }
    return jsonify(data)

# ========== 라우트: 키 관리 (관리자 전용) ==========

@app.route("/api/admin/keys")
def admin_list_keys():
    """전체 키 목록"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    keys = load_access_keys()
    now = datetime.now()
    for k in keys:
        k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now
    return jsonify(keys)

@app.route("/api/admin/keys/generate", methods=["POST"])
def admin_generate_key():
    """새 키 생성 (만료기간 설정 가능)"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403

    data = request.json
    days = int(data.get("days", 1))
    hours = int(data.get("hours", 0))
    label = data.get("label", "")

    new_key = secrets.token_urlsafe(16)
    created_at = datetime.now()
    expires_at = created_at + timedelta(days=days, hours=hours)

    keys = load_access_keys()
    key_entry = {
        "key": new_key,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "label": label
    }
    keys.append(key_entry)
    save_access_keys(keys)

    print(f"[ADMIN] 새 키 생성: {new_key} (만료: {expires_at})")
    return jsonify({"success": True, "key": key_entry})

@app.route("/api/admin/keys/<key>/delete", methods=["POST"])
def admin_delete_key(key):
    """키 삭제"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    keys = load_access_keys()
    keys = [k for k in keys if k["key"] != key]
    save_access_keys(keys)
    return jsonify({"success": True, "message": "키가 삭제되었습니다"})

# ========== 실행 ==========

if __name__ == "__main__":
    print("=" * 70)
    print("🐱 냥코통조림충전소 - BCSFE 풀버전")
    print("=" * 70)
    print()
    print(f"서버 시작! http://localhost:{SERVER_PORT}")
    print(f"계좌: {BANK_NAME} {BANK_ACCOUNT} ({ACCOUNT_HOLDER})")
    print()

    app.run(debug=SERVER_DEBUG, host=SERVER_HOST, port=SERVER_PORT, threaded=True)