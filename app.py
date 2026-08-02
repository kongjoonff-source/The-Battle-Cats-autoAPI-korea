from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import threading
import secrets
import time
from datetime import datetime, timedelta
from bcsfe_handler_full import process_all_items
from config import (
    DATA_DIR, SERVER_HOST, SERVER_PORT, SERVER_DEBUG,
    ADMIN_PASSWORD, ADMIN_ALLOWED_IPS, SECRET_KEY,
    KEY_PURCHASE_ENABLED, KEY_PRICES
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=365)

@app.template_filter("number_format")
def number_format(value):
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

os.makedirs(DATA_DIR, exist_ok=True)

def _init_bcsfe():
    try:
        from bcsfe.core import core_data
        core_data.init_data()
        print("[INFO] bcsfe 초기화 완료")
    except Exception as e:
        print(f"[WARN] bcsfe 초기화 실패: {e}")

_init_bcsfe()

# Keep-Alive
def _keep_alive():
    url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("KEEP_ALIVE_URL")
    if not url:
        print("[KEEP-ALIVE] 비활성화")
        return
    url = url.rstrip("/")
    ping_path = os.environ.get("KEEP_ALIVE_PATH", "/health")
    interval = int(os.environ.get("KEEP_ALIVE_INTERVAL", "300"))
    print(f"[KEEP-ALIVE] 활성화: {url}{ping_path} ({interval}초)")
    while True:
        try:
            import requests as req
            resp = req.get(url + ping_path, timeout=10)
            print(f"[KEEP-ALIVE] 핑: {resp.status_code}")
        except Exception as e:
            print(f"[KEEP-ALIVE] 핑 실패: {e}")
        time.sleep(interval)

if os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("KEEP_ALIVE_URL"):
    threading.Thread(target=_keep_alive, daemon=True).start()

# 파일 경로
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
ACCESS_KEYS_FILE = os.path.join(DATA_DIR, "access_keys.json")
COUPON_CODES_FILE = os.path.join(DATA_DIR, "coupon_codes.json")
ACTIVITY_LOG_FILE = os.path.join(DATA_DIR, "activity_log.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# 데이터 로드/저장
def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def load_access_keys():
    if os.path.exists(ACCESS_KEYS_FILE):
        with open(ACCESS_KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_access_keys(keys):
    with open(ACCESS_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)

def load_coupon_codes():
    if os.path.exists(COUPON_CODES_FILE):
        with open(COUPON_CODES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_coupon_codes(coupons):
    with open(COUPON_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(coupons, f, ensure_ascii=False, indent=2)

def load_activity_log():
    if os.path.exists(ACTIVITY_LOG_FILE):
        with open(ACTIVITY_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_activity_log(logs):
    with open(ACTIVITY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def add_log(category, message, detail=""):
    logs = load_activity_log()
    entry = {
        "id": f"LOG{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3)}",
        "category": category,
        "message": message,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    }
    logs.append(entry)
    if len(logs) > 1000:
        logs = logs[-1000:]
    save_activity_log(logs)
    print(f"[LOG] [{category}] {message} {detail}")

def load_settings():
    defaults = {"key_purchase_enabled": KEY_PURCHASE_ENABLED}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            defaults.update(saved)
    return defaults

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def is_key_purchase_enabled():
    return load_settings().get("key_purchase_enabled", KEY_PURCHASE_ENABLED)

def is_key_valid(key):
    keys = load_access_keys()
    for k in keys:
        if k["key"] == key:
            expires_at = datetime.fromisoformat(k["expires_at"])
            if datetime.now() < expires_at:
                return True, k
    return False, None

# 아이템 정의
def get_item_definitions():
    return [
        {"id": "catfood_10000", "type": "catfood", "name": "통조림 10,000개", "amount": 10000, "icon": "🥫", "category": "통조림", "price": 0},
        {"id": "catfood_30000", "type": "catfood", "name": "통조림 30,000개", "amount": 30000, "icon": "🥫", "category": "통조림", "price": 0},
        {"id": "catfood_45000", "type": "catfood", "name": "통조림 45,000개", "amount": 45000, "icon": "🥫", "category": "통조림", "price": 0},
        {"id": "xp_99999999", "type": "xp", "name": "XP 99,999,999", "amount": 99999999, "icon": "✨", "category": "XP", "price": 0},
        {"id": "xp_50000000", "type": "xp", "name": "XP 50,000,000", "amount": 50000000, "icon": "✨", "category": "XP", "price": 0},
        {"id": "xp_10000000", "type": "xp", "name": "XP 10,000,000", "amount": 10000000, "icon": "✨", "category": "XP", "price": 0},
        {"id": "rare_10", "type": "rare_ticket", "name": "레어 티켓 10개", "amount": 10, "icon": "🎟️", "category": "티켓", "price": 0},
        {"id": "rare_50", "type": "rare_ticket", "name": "레어 티켓 50개", "amount": 50, "icon": "🎟️", "category": "티켓", "price": 0},
        {"id": "legend_5", "type": "legend_ticket", "name": "레전드 티켓 5개", "amount": 5, "icon": "🌟", "category": "티켓", "price": 0},
        {"id": "legend_10", "type": "legend_ticket", "name": "레전드 티켓 10개", "amount": 10, "icon": "🌟", "category": "티켓", "price": 0},
        {"id": "platinum_3", "type": "platinum_ticket", "name": "플래티넘 티켓 3개", "amount": 3, "icon": "💎", "category": "티켓", "price": 0},
        {"id": "platinum_10", "type": "platinum_ticket", "name": "플래티넘 티켓 10개", "amount": 10, "icon": "💎", "category": "티켓", "price": 0},
        {"id": "normal_50", "type": "normal_ticket", "name": "노멀 티켓 50개", "amount": 50, "icon": "🎫", "category": "티켓", "price": 0},
        {"id": "normal_100", "type": "normal_ticket", "name": "노멀 티켓 100개", "amount": 100, "icon": "🎫", "category": "티켓", "price": 0},
        {"id": "platinum_shard_5", "type": "platinum_shard", "name": "플래티넘 조각 5개", "amount": 5, "icon": "🔷", "category": "기타", "price": 0},
        {"id": "platinum_shard_10", "type": "platinum_shard", "name": "플래티넘 조각 10개", "amount": 10, "icon": "🔷", "category": "기타", "price": 0},
        {"id": "leadership_10", "type": "leadership", "name": "리더십 10개", "amount": 10, "icon": "⚡", "category": "기타", "price": 0},
        {"id": "leadership_50", "type": "leadership", "name": "리더십 50개", "amount": 50, "icon": "⚡", "category": "기타", "price": 0},
        {"id": "np_1000", "type": "np", "name": "NP 1,000개", "amount": 1000, "icon": "🧬", "category": "기타", "price": 0},
        {"id": "np_5000", "type": "np", "name": "NP 5,000개", "amount": 5000, "icon": "🧬", "category": "기타", "price": 0},
        {"id": "np_10000", "type": "np", "name": "NP 10,000개", "amount": 10000, "icon": "🧬", "category": "기타", "price": 0},
        {"id": "unlock_all_cats", "type": "unlock_all_cats", "name": "모든 고양이 언락", "icon": "🐱", "category": "고양이추가", "price": 0},
        {"id": "unlock_all_obtainable", "type": "unlock_all_obtainable_cats", "name": "획득 가능한 고양이 언락", "icon": "🐾", "category": "고양이추가", "price": 0},
        {"id": "unlock_cat_id", "type": "unlock_cat", "name": "특정 고양이 ID 언락", "icon": "🔍", "category": "고양이추가", "price": 0, "needs_cat_id": True},
        {"id": "true_form_all", "type": "true_form_all_cats", "name": "모든 고양이 3진화", "icon": "⭐", "category": "고양이진화", "price": 0},
        {"id": "true_form_cat_id", "type": "true_form_cat", "name": "특정 고양이 3진화", "icon": "🌟", "category": "고양이진화", "price": 0, "needs_cat_id": True},
        {"id": "fourth_form_all", "type": "fourth_form_all_cats", "name": "모든 고양이 4진화", "icon": "💫", "category": "고양이진화", "price": 0},
        {"id": "fourth_form_cat_id", "type": "fourth_form_cat", "name": "특정 고양이 4진화", "icon": "✨", "category": "고양이진화", "price": 0, "needs_cat_id": True},
        {"id": "upgrade_all_max", "type": "upgrade_all_cats_max", "name": "모든 고양이 만렙 강화", "icon": "🔝", "category": "고양이강화", "price": 0},
        {"id": "upgrade_cat_max_id", "type": "upgrade_cat_max", "name": "특정 고양이 만렙 강화", "icon": "📈", "category": "고양이강화", "price": 0, "needs_cat_id": True},
        {"id": "upgrade_cat_custom", "type": "upgrade_cat", "name": "특정 고양이 레벨 지정 강화", "icon": "⚙️", "category": "고양이강화", "price": 0, "needs_cat_id": True, "needs_levels": True},
        {"id": "talents_all_max", "type": "upgrade_talents_all_cats", "name": "모든 고양이 특훈 만렙", "icon": "🎯", "category": "고양이특훈", "price": 0},
        {"id": "talents_cat_max_id", "type": "upgrade_talents_cat", "name": "특정 고양이 특훈 만렙", "icon": "🏹", "category": "고양이특훈", "price": 0, "needs_cat_id": True},
        {"id": "cat_guide_all", "type": "unlock_all_cat_guide", "name": "모든 고양이 도감 등록", "icon": "📖", "category": "고양이도감", "price": 0},
        {"id": "cat_guide_cat_id", "type": "unlock_cat_guide_cat", "name": "특정 고양이 도감 등록", "icon": "📚", "category": "고양이도감", "price": 0, "needs_cat_id": True},
        {"id": "catfood_custom", "type": "catfood", "name": "통조림 커스텀", "icon": "🥫", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "xp_custom", "type": "xp", "name": "XP 커스텀", "icon": "✨", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "rare_ticket_custom", "type": "rare_ticket", "name": "레어티켓 커스텀", "icon": "🎟️", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "legend_ticket_custom", "type": "legend_ticket", "name": "레전드티켓 커스텀", "icon": "🌟", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "platinum_ticket_custom", "type": "platinum_ticket", "name": "플래티넘티켓 커스텀", "icon": "💎", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "normal_ticket_custom", "type": "normal_ticket", "name": "노멀티켓 커스텀", "icon": "🎫", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "platinum_shard_custom", "type": "platinum_shard", "name": "플래티넘조각 커스텀", "icon": "🔷", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "leadership_custom", "type": "leadership", "name": "리더십 커스텀", "icon": "⚡", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "np_custom", "type": "np", "name": "NP 커스텀", "icon": "🧬", "category": "커스텀", "price": 0, "needs_custom_amount": True},
        {"id": "user_rank_calc", "type": "user_rank", "name": "유저랭크 재계산", "icon": "📊", "category": "기타기능", "price": 0},
        {"id": "unlock_equip", "type": "unlock_equip", "name": "장비 메뉴 해제", "icon": "🔓", "category": "기타기능", "price": 0},
    ]

# 접근 키 게이트
@app.before_request
def check_access_key():
    exempt_prefixes = ['/gate', '/api/verify-key', '/api/redeem-coupon', '/static', '/admin', '/api/admin', '/health', '/ping']
    for prefix in exempt_prefixes:
        if request.path.startswith(prefix):
            return
    user_key = session.get('access_key')
    if user_key:
        valid, _ = is_key_valid(user_key)
        if valid:
            return
    return redirect(url_for('gate'))

# 게이트
@app.route("/gate")
def gate():
    user_key = session.get('access_key')
    if user_key:
        valid, _ = is_key_valid(user_key)
        if valid:
            return redirect(url_for('index'))
    return render_template("gate.html", key_purchase_enabled=is_key_purchase_enabled())

@app.route("/api/verify-key", methods=["POST"])
def verify_key():
    data = request.json
    key = data.get("key", "").strip()
    valid, key_data = is_key_valid(key)
    if valid:
        session.permanent = True
        session['access_key'] = key
        expires_at = datetime.fromisoformat(key_data['expires_at'])
        app.permanent_session_lifetime = expires_at - datetime.now()
        add_log("키 사용", f"키 접속 성공", f"키: {key[:8]}... 만료: {key_data['expires_at']}")
        return jsonify({"success": True, "message": "접근이 허용되었습니다"})
    return jsonify({"success": False, "error": "유효하지 않거나 만료된 키입니다"}), 403

# 쿠폰 코드 시스템
@app.route("/api/redeem-coupon", methods=["POST"])
def redeem_coupon():
    data = request.json
    code = data.get("code", "").strip()
    if not code:
        return jsonify({"success": False, "error": "코드를 입력해주세요"}), 400
    coupons = load_coupon_codes()
    coupon = next((c for c in coupons if c["code"] == code), None)
    if not coupon:
        return jsonify({"success": False, "error": "존재하지 않는 코드입니다"}), 404
    if coupon.get("used"):
        return jsonify({"success": False, "error": "이미 사용된 코드입니다"}), 400
    new_key = secrets.token_urlsafe(16)
    activated_at = datetime.now()
    expires_at = activated_at + timedelta(days=coupon["days"])
    keys = load_access_keys()
    key_entry = {
        "key": new_key,
        "created_at": activated_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "label": f"쿠폰-{code[:8]}...-{coupon.get('label', '')}"
    }
    keys.append(key_entry)
    save_access_keys(keys)
    coupon["used"] = True
    coupon["used_at"] = activated_at.isoformat()
    coupon["issued_key"] = new_key
    save_coupon_codes(coupons)
    session.permanent = True
    session['access_key'] = new_key
    app.permanent_session_lifetime = expires_at - datetime.now()
    add_log("쿠폰 사용", f"쿠폰 코드 사용: {code}", f"키 발급: {new_key[:8]}... 기간: {coupon['days']}일 만료: {expires_at.isoformat()}")
    return jsonify({
        "success": True,
        "key": new_key,
        "expires_at": expires_at.isoformat(),
        "days": coupon["days"],
        "message": f"키가 발급되었습니다! ({coupon['days']}일간 사용 가능)"
    })

# 헬스체크
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "nyanko-charge", "timestamp": datetime.now().isoformat()}), 200

@app.route("/ping")
def ping():
    return "pong", 200

# 메인
@app.route("/")
def index():
    items = get_item_definitions()
    return render_template("index.html", items=items)

@app.route("/api/items")
def api_items():
    return jsonify(get_item_definitions())

@app.route("/api/submit", methods=["POST"])
def submit_order():
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
    item_details = []
    for sel in selected_items:
        item_id = sel.get("id", "")
        quantity = int(sel.get("quantity", 1))
        match = next((i for i in items_def if i["id"] == item_id), None)
        if match:
            detail = {**match, "quantity": quantity}
            if match.get("needs_cat_id"):
                detail["cat_id"] = int(sel.get("cat_id", -1))
            if match.get("needs_levels"):
                detail["base_level"] = int(sel.get("base_level", -1))
                detail["plus_level"] = int(sel.get("plus_level", -1))
            if match.get("needs_custom_amount"):
                detail["amount"] = int(sel.get("custom_amount", 0))
            item_details.append(detail)
    if not item_details:
        return jsonify({"error": "유효한 아이템을 선택해주세요"}), 400
    orders = load_orders()
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    order = {
        "id": order_id,
        "buyer_name": buyer_name,
        "transfer_code": transfer_code,
        "confirmation_code": confirmation_code,
        "items": item_details,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "result": None
    }
    orders.append(order)
    save_orders(orders)
    item_summary = ", ".join([f"{i['name']}x{i['quantity']}" for i in item_details])
    add_log("주문 생성", f"주문: {order_id} / 이름: {buyer_name}", f"아이템: {item_summary}")
    return jsonify({"order_id": order_id, "message": "주문 완료!"})

@app.route("/api/order/<order_id>")
def get_order(order_id):
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "주문 없음"}), 404
    return jsonify(order)

@app.route("/api/process", methods=["POST"])
def process_order_direct():
    data = request.json
    order_id = data.get("order_id", "").strip()
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id and o["status"] == "pending"), None)
    if not order:
        return jsonify({"error": "주문 없음 또는 이미 처리 중"}), 404
    order["status"] = "processing"
    save_orders(orders)
    add_log("충전 시작", f"주문: {order_id} / 이름: {order['buyer_name']}", f"아이템 수: {len(order['items'])}")
    def process_background():
        try:
            bcsfe_items = []
            for item in order["items"]:
                for _ in range(item["quantity"]):
                    entry = {"type": item["type"], "amount": item.get("amount", 0)}
                    if item.get("needs_cat_id"):
                        entry["cat_id"] = item.get("cat_id", -1)
                    if item.get("needs_levels"):
                        entry["base_level"] = item.get("base_level", -1)
                        entry["plus_level"] = item.get("plus_level", -1)
                    if item.get("needs_custom_amount"):
                        entry["amount"] = item.get("amount", 0)
                    bcsfe_items.append(entry)
            print(f"[APP] 처리 시작: {order['id']} / 이름: {order['buyer_name']}")
            success, new_tc, new_cc, error, results = process_all_items(
                order["transfer_code"], order["confirmation_code"], bcsfe_items
            )
            order["status"] = "completed" if success else "failed"
            order["result"] = {
                "success": success,
                "new_transfer_code": new_tc,
                "new_confirmation_code": new_cc,
                "error": error,
                "details": results
            }
            if success:
                add_log("충전 완료", f"주문: {order_id} / 이름: {order['buyer_name']}", f"새 코드: {new_tc[:12]}...")
            else:
                add_log("충전 실패", f"주문: {order_id} / 이름: {order['buyer_name']}", f"오류: {error}")
        except Exception as e:
            print(f"[APP] 예외: {e}")
            import traceback
            traceback.print_exc()
            order["status"] = "failed"
            order["result"] = {"success": False, "error": str(e), "details": []}
            add_log("충전 오류", f"주문: {order_id} / 이름: {order['buyer_name']}", f"예외: {str(e)}")
        order["completed_at"] = datetime.now().isoformat()
        save_orders(orders)
    thread = threading.Thread(target=process_background)
    thread.start()
    return jsonify({"message": "처리 시작!", "order_id": order["id"]})

# 관리자
@app.route("/admin/panel", methods=["GET", "POST"])
def admin_panel():
    return admin_handler()

@app.route("/admin", methods=["GET", "POST"])
def admin_root():
    return admin_handler()

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login_alt():
    return admin_handler()

def admin_handler():
    if request.method == "GET" and session.get('admin'):
        return show_admin_dashboard()
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session.permanent = True
            session['admin'] = True
            add_log("관리자", "관리자 로그인", "")
            return redirect(url_for('admin_panel'))
        return render_template("admin_login.html", error="비밀번호가 틀렸습니다")
    return render_template("admin_login.html")

def show_admin_dashboard():
    orders = load_orders()
    access_keys = load_access_keys()
    coupons = load_coupon_codes()
    logs = load_activity_log()
    now = datetime.now()
    for k in access_keys:
        k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.get('status') == 'completed'])
    pending_orders = len([o for o in orders if o.get('status') == 'pending'])
    failed_orders = len([o for o in orders if o.get('status') == 'failed'])
    return render_template("admin.html",
        orders=orders, access_keys=access_keys, coupons=coupons, logs=logs,
        total_orders=total_orders, completed_orders=completed_orders,
        pending_orders=pending_orders, failed_orders=failed_orders,
        key_purchase_enabled=is_key_purchase_enabled(),
        key_prices=KEY_PRICES)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_panel'))

# 쿠폰 코드 관리
@app.route("/api/admin/coupons/list")
def admin_list_coupons():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    return jsonify(load_coupon_codes())

@app.route("/api/admin/coupons/create", methods=["POST"])
def admin_create_coupon():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    code = data.get("code", "").strip()
    days = int(data.get("days", 1))
    label = data.get("label", "").strip()
    if not code:
        return jsonify({"error": "코드를 입력해주세요"}), 400
    if days <= 0:
        return jsonify({"error": "기간은 1일 이상이어야 합니다"}), 400
    coupons = load_coupon_codes()
    if any(c["code"] == code for c in coupons):
        return jsonify({"error": "이미 존재하는 코드입니다"}), 400
    coupon = {
        "code": code,
        "days": days,
        "label": label,
        "used": False,
        "created_at": datetime.now().isoformat(),
        "used_at": None,
        "issued_key": None
    }
    coupons.append(coupon)
    save_coupon_codes(coupons)
    add_log("쿠폰 생성", f"코드: {code}", f"기간: {days}일 라벨: {label}")
    return jsonify({"success": True, "message": "쿠폰 코드가 생성되었습니다"})

@app.route("/api/admin/coupons/delete", methods=["POST"])
def admin_delete_coupon():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    code = data.get("code", "").strip()
    coupons = load_coupon_codes()
    coupons = [c for c in coupons if c["code"] != code]
    save_coupon_codes(coupons)
    add_log("쿠폰 삭제", f"코드: {code}", "")
    return jsonify({"success": True, "message": "쿠폰이 삭제되었습니다"})

# 키 관리
@app.route("/api/admin/keys")
def admin_list_keys():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    keys = load_access_keys()
    now = datetime.now()
    for k in keys:
        k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now
    return jsonify(keys)

@app.route("/api/admin/keys/generate", methods=["POST"])
def admin_generate_key():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    days = int(data.get("days", 1))
    label = data.get("label", "")
    new_key = secrets.token_urlsafe(16)
    created_at = datetime.now()
    expires_at = created_at + timedelta(days=days)
    keys = load_access_keys()
    key_entry = {"key": new_key, "created_at": created_at.isoformat(), "expires_at": expires_at.isoformat(), "label": label}
    keys.append(key_entry)
    save_access_keys(keys)
    add_log("키 생성", f"키: {new_key[:8]}...", f"만료: {expires_at} 라벨: {label}")
    return jsonify({"success": True, "key": key_entry})

@app.route("/api/admin/keys/<key>/delete", methods=["POST"])
def admin_delete_key(key):
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    keys = load_access_keys()
    keys = [k for k in keys if k["key"] != key]
    save_access_keys(keys)
    add_log("키 삭제", f"키: {key[:8]}...", "")
    return jsonify({"success": True, "message": "키가 삭제되었습니다"})

# 활동 로그
@app.route("/api/admin/logs")
def admin_list_logs():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    return jsonify(load_activity_log())

@app.route("/api/admin/logs/clear", methods=["POST"])
def admin_clear_logs():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    save_activity_log([])
    add_log("로그", "활동 로그 전체 삭제", "")
    return jsonify({"success": True, "message": "로그가 삭제되었습니다"})

@app.route("/api/admin/logs/<log_id>/delete", methods=["POST"])
def admin_delete_log(log_id):
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    logs = load_activity_log()
    logs = [l for l in logs if l["id"] != log_id]
    save_activity_log(logs)
    return jsonify({"success": True, "message": "로그가 삭제되었습니다"})

# 키 발급 토글
@app.route("/api/admin/key-purchase/toggle", methods=["POST"])
def admin_toggle_key_purchase():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    enabled = data.get("enabled", True)
    settings = load_settings()
    settings["key_purchase_enabled"] = enabled
    save_settings(settings)
    status = "활성화" if enabled else "비활성화"
    add_log("설정", f"키 발급 {status}", "")
    return jsonify({"success": True, "enabled": enabled, "message": f"키 발급이 {status}되었습니다"})

if __name__ == "__main__":
    print("=" * 70)
    print("🐱 냥코 자동충전 - 쿠폰 코드 시스템 v12.0")
    print("=" * 70)
    print()
    print(f"서버 시작! http://localhost:{SERVER_PORT}")
    print()
    app.run(debug=SERVER_DEBUG, host=SERVER_HOST, port=SERVER_PORT, threaded=True)