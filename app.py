from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import threading
import secrets
import time
import hashlib
from datetime import datetime, timedelta
import zoneinfo
from bcsfe_handler_full import process_all_items
from config import (
    DATA_DIR, SERVER_HOST, SERVER_PORT, SERVER_DEBUG,
    ADMIN_PASSWORD, ADMIN_ALLOWED_IPS, SECRET_KEY,
    KEY_PURCHASE_ENABLED, KEY_PRICES
)

# 한국 시간대 설정 (Render 서버는 UTC 사용)
KST = zoneinfo.ZoneInfo("Asia/Seoul")
def now_kst():
    return datetime.now(KST)

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

# ========== 기기绑定 (Device Binding) 시스템 ==========

def get_device_fingerprint():
    """요청 헤더에서 기기 지문 생성"""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
    ua = request.headers.get('User-Agent', 'unknown')
    accept = request.headers.get('Accept', '')
    lang = request.headers.get('Accept-Language', '')
    raw = f"{ip}|{ua}|{accept}|{lang}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def get_device_id():
    """쿠키 또는 지문에서 기기 ID 획득"""
    device_id = request.cookies.get('device_id')
    if device_id:
        return device_id
    return get_device_fingerprint()

def get_device_info():
    """사람이 읽을 수 있는 기기 정보"""
    ua = request.headers.get('User-Agent', 'unknown')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
    is_mobile = any(m in ua for m in ['Mobile', 'iPhone', 'Android', 'iPad'])
    device_type = '모바일' if is_mobile else 'PC'
    browser = 'Unknown'
    if 'Chrome' in ua and 'Edg' not in ua:
        browser = 'Chrome'
    elif 'Firefox' in ua:
        browser = 'Firefox'
    elif 'Safari' in ua and 'Chrome' not in ua:
        browser = 'Safari'
    elif 'Edg' in ua:
        browser = 'Edge'
    # OS 감지
    if 'Windows' in ua:
        os_name = 'Windows'
    elif 'Mac' in ua:
        os_name = 'macOS'
    elif 'Android' in ua:
        os_name = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        os_name = 'iOS'
    elif 'Linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'Unknown'
    return f"{device_type} · {browser} · {os_name}"

def is_key_valid(key, device_id=None):
    """키 유효성 검사 (기기绑定 옵션)
    
    키가 아직 활성화되지 않은 경우(activated_at 없음) 시간이 흐르지 않음.
    키를 사용(활성화)하면 그때부터 expires_at이 설정됨.
    """
    keys = load_access_keys()
    for k in keys:
        if k["key"] == key:
            # 아직 활성화되지 않은 키는 시간이 흐르지 않음
            if not k.get("activated_at"):
                if device_id:
                    bound_device = k.get("device_id")
                    if bound_device and bound_device != device_id:
                        return False, None, "device_mismatch"
                return True, k, None
            # 활성화된 키는 만료 시간 확인
            if not k.get("expires_at"):
                return True, k, None
            try:
                expires_at = datetime.fromisoformat(k["expires_at"])
                if datetime.now() >= expires_at:
                    return False, None, "expired"
            except (ValueError, TypeError):
                return True, k, None
            if device_id:
                bound_device = k.get("device_id")
                if bound_device and bound_device != device_id:
                    return False, None, "device_mismatch"
            return True, k, None
    return False, None, "not_found"

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
        # ===== BCSFE 스테이지 클리어 (VIP 전용) =====
        {"id": "clear_chapter_1", "type": "clear_stages", "name": "제1장 클리어", "icon": "🌍", "category": "스테이지", "price": 0, "chapter_id": 1, "vip_only": True},
        {"id": "clear_chapter_2", "type": "clear_stages", "name": "제2장 클리어", "icon": "🌍", "category": "스테이지", "price": 0, "chapter_id": 2, "vip_only": True},
        {"id": "clear_chapter_3", "type": "clear_stages", "name": "제3장 클리어", "icon": "🌍", "category": "스테이지", "price": 0, "chapter_id": 3, "vip_only": True},
        {"id": "clear_chapter_4", "type": "clear_stages", "name": "미래편 제1장 클리어", "icon": "🚀", "category": "스테이지", "price": 0, "chapter_id": 4, "vip_only": True},
        {"id": "clear_chapter_5", "type": "clear_stages", "name": "미래편 제2장 클리어", "icon": "🚀", "category": "스테이지", "price": 0, "chapter_id": 5, "vip_only": True},
        {"id": "clear_chapter_6", "type": "clear_stages", "name": "미래편 제3장 클리어", "icon": "🚀", "category": "스테이지", "price": 0, "chapter_id": 6, "vip_only": True},
        {"id": "clear_chapter_7", "type": "clear_stages", "name": "우주편 제1장 클리어", "icon": "🌌", "category": "스테이지", "price": 0, "chapter_id": 7, "vip_only": True},
        {"id": "clear_chapter_8", "type": "clear_stages", "name": "우주편 제2장 클리어", "icon": "🌌", "category": "스테이지", "price": 0, "chapter_id": 8, "vip_only": True},
        {"id": "clear_chapter_9", "type": "clear_stages", "name": "우주편 제3장 클리어", "icon": "🌌", "category": "스테이지", "price": 0, "chapter_id": 9, "vip_only": True},
        {"id": "clear_all_stages", "type": "clear_all_stages", "name": "전체 스테이지 클리어", "icon": "🏆", "category": "스테이지", "price": 0, "vip_only": True},
    ]

# 기기 ID 쿠키 자동 설정
@app.after_request
def set_device_cookie(response):
    try:
        if not request.cookies.get('device_id'):
            device_id = get_device_id()
            response.set_cookie('device_id', device_id,
                                max_age=365*24*3600, httponly=True, samesite='Lax')
    except Exception:
        pass
    return response

# 접근 키 게이트
@app.before_request
def check_access_key():
    exempt_prefixes = ['/gate', '/api/verify-key', '/api/redeem-coupon', '/static', '/admin', '/api/admin', '/health', '/ping']
    for prefix in exempt_prefixes:
        if request.path.startswith(prefix):
            return
    user_key = session.get('access_key')
    if user_key:
        device_id = get_device_id()
        valid, _, error = is_key_valid(user_key, device_id)
        if valid:
            return
        if error == "device_mismatch":
            session.pop('access_key', None)
            return redirect(url_for('gate', error='device'))
    return redirect(url_for('gate'))

# 게이트
@app.route("/gate")
def gate():
    error = request.args.get('error', '')
    user_key = session.get('access_key')
    if user_key:
        device_id = get_device_id()
        valid, _, _ = is_key_valid(user_key, device_id)
        if valid:
            return redirect(url_for('index'))
    return render_template("gate.html", key_purchase_enabled=is_key_purchase_enabled(), error=error)

@app.route("/api/verify-key", methods=["POST"])
def verify_key():
    """키 검증 및 활성화
    
    - 아직 활성화되지 않은 키: 기기绑定 + 활성화 (그때부터 시간 흐름)
    - 이미 활성화된 키: 유효성만 확인
    """
    data = request.json
    key = data.get("key", "").strip()
    device_id = get_device_id()
    valid, key_data, error = is_key_valid(key, device_id)
    if valid:
        keys = load_access_keys()
        is_new_binding = False
        is_new_activation = False
        
        for k in keys:
            if k["key"] == key:
                # 기기绑定 (첫 사용 시)
                if not k.get("device_id"):
                    k["device_id"] = device_id
                    k["bound_at"] = datetime.now().isoformat()
                    k["device_info"] = get_device_info()
                    is_new_binding = True
                
                # 키 활성화 (사용 전까지 시간 안 흐름 → 사용하면 그때부터)
                if not k.get("activated_at"):
                    k["activated_at"] = datetime.now().isoformat()
                    duration = int(k.get("duration", 1))
                    unit = k.get("unit", "day")
                    if unit == "hour":
                        k["expires_at"] = (datetime.now() + timedelta(hours=duration)).isoformat()
                    else:
                        k["expires_at"] = (datetime.now() + timedelta(days=duration)).isoformat()
                    is_new_activation = True
                    add_log("키 활성화", f"키 활성화 시작", f"키: {key[:8]}... 기간: {duration}{'시간' if unit == 'hour' else '일'} 만료: {k['expires_at']}")
                break
        
        save_access_keys(keys)
        
        session.permanent = True
        session['access_key'] = key
        
        # 세션 만료 시간 설정
        if key_data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(key_data["expires_at"])
                app.permanent_session_lifetime = expires_at - datetime.now()
            except:
                app.permanent_session_lifetime = timedelta(days=365)
        
        add_log("키 사용", f"키 접속 성공", f"키: {key[:8]}... 만료: {key_data.get('expires_at', '활성화 전')}")
        return jsonify({
            "success": True,
            "message": "키가 적용되었습니다!" + (" (키가 활성화되어 시간이 흐르기 시작합니다!)" if is_new_activation else ""),
            "applied": True,
            "in_use": True,
            "is_new_binding": is_new_binding,
            "is_new_activation": is_new_activation,
            "device_info": key_data.get("device_info", get_device_info()),
            "expires_at": key_data.get("expires_at", "")
        })
    
    error_messages = {
        "expired": "키가 만료되었습니다",
        "device_mismatch": "이 키는 다른 기기에서 이미 사용 중입니다 (키 1개 = 1기기 전용)",
        "not_found": "유효하지 않거나 만료된 키입니다"
    }
    return jsonify({"success": False, "error": error_messages.get(error, "유효하지 않거나 만료된 키입니다")}), 403

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
    device_id = get_device_id()
    keys = load_access_keys()
    key_entry = {
        "key": new_key,
        "created_at": activated_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "label": f"쿠폰-{code[:8]}...-{coupon.get('label', '')}",
        "device_id": device_id,
        "bound_at": activated_at.isoformat(),
        "device_info": get_device_info()
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

@app.route("/api/my-key")
def my_key():
    key = session.get('access_key', '')
    device_id = get_device_id()
    if key:
        valid, key_data, _ = is_key_valid(key, device_id)
        if valid:
            return jsonify({
                "key": key,
                "in_use": bool(key_data.get("device_id")),
                "device_info": key_data.get("device_info", ""),
                "bound_at": key_data.get("bound_at", ""),
                "expires_at": key_data.get("expires_at", ""),
                "key_type": key_data.get("key_type", "normal")
            })
    return jsonify({"key": ""})

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
    
    # 키 타입 확인 (권한 체크)
    user_key = session.get('access_key', '')
    key_type = "normal"
    if user_key:
        keys = load_access_keys()
        for k in keys:
            if k["key"] == user_key:
                key_type = k.get("key_type", "normal")
                break
    
    items_def = get_item_definitions()
    item_details = []
    for sel in selected_items:
        item_id = sel.get("id", "")
        quantity = int(sel.get("quantity", 1))
        match = next((i for i in items_def if i["id"] == item_id), None)
        if match:
            # 권한 체크
            if not check_item_permission(match["type"], key_type):
                return jsonify({"error": f"'{match['name']}'은(는) {('VIP' if key_type == 'vip' else '일반')}키에서 사용할 수 없습니다"}), 403
            detail = {**match, "quantity": quantity}
            if match.get("needs_cat_id"):
                detail["cat_id"] = int(sel.get("cat_id", -1))
            if match.get("needs_levels"):
                detail["base_level"] = int(sel.get("base_level", -1))
                detail["plus_level"] = int(sel.get("plus_level", -1))
            if match.get("needs_custom_amount"):
                detail["amount"] = int(sel.get("custom_amount", 0))
            if match.get("chapter_id"):
                detail["chapter_id"] = int(match.get("chapter_id", 0))
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
    """주문 처리 - Render 무료 플랜에서 백그라운드 스레드가 동작하지 않아 동기식으로 처리"""
    data = request.json
    order_id = data.get("order_id", "").strip()
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id and o["status"] == "pending"), None)
    if not order:
        return jsonify({"error": "주문 없음 또는 이미 처리 중"}), 404
    order["status"] = "processing"
    save_orders(orders)
    add_log("충전 시작", f"주문: {order_id} / 이름: {order['buyer_name']}", f"아이템 수: {len(order['items'])}")
    
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
                if item.get("chapter_id"):
                    entry["chapter_id"] = item.get("chapter_id", 0)
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
            add_log("충전 완료", f"주문: {order_id} / 이름: {order['buyer_name']}", f"새 전송코드: {new_tc} / 새 인증번호: {new_cc}")
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
    return jsonify({"message": "처리 완료!", "order_id": order["id"], "status": order["status"]})

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
        try:
            k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now if k.get('expires_at') else False
        except (ValueError, TypeError):
            k['is_expired'] = False
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
        try:
            k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now if k.get('expires_at') else False
        except (ValueError, TypeError):
            k['is_expired'] = False
    return jsonify(keys)

@app.route("/api/admin/keys/generate", methods=["POST"])
def admin_generate_key():
    """키 생성 API - 일/시간 단위, 여러 개 한번에 생성, 일반/VIP 선택
    
    생성된 키는 사용(활성화) 전까지 시간이 흐르지 않음.
    키를 사용하면 그때부터 expires_at이 설정됨.
    """
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    duration = int(data.get("duration", data.get("days", 1)))
    unit = data.get("unit", "day")  # "day" or "hour"
    count = int(data.get("count", 1))
    label = data.get("label", "")
    key_type = data.get("key_type", "normal")  # "normal" or "vip"
    
    if duration <= 0:
        return jsonify({"error": "기간은 1 이상이어야 합니다"}), 400
    if count <= 0 or count > 100:
        return jsonify({"error": "생성 개수는 1~100개 사이여야 합니다"}), 400
    if key_type not in ["normal", "vip"]:
        return jsonify({"error": "키 타입은 normal 또는 vip여야 합니다"}), 400
    
    created_at = datetime.now()
    keys = load_access_keys()
    generated_keys = []
    
    for _ in range(count):
        new_key = secrets.token_urlsafe(16)
        key_entry = {
            "key": new_key,
            "created_at": created_at.isoformat(),
            "expires_at": None,  # 활성화 전까지 None (시간 안 흐름)
            "duration": duration,
            "unit": unit,
            "activated_at": None,  # 아직 활성화 안됨
            "label": label,
            "key_type": key_type,  # "normal" or "vip"
            "device_id": None,
            "bound_at": None,
            "device_info": None
        }
        keys.append(key_entry)
        generated_keys.append(key_entry)
    
    save_access_keys(keys)
    unit_text = "시간" if unit == "hour" else "일"
    type_text = "VIP" if key_type == "vip" else "일반"
    add_log("키 생성", f"{type_text}키 {count}개 생성", f"기간: {duration}{unit_text} 라벨: {label}")
    return jsonify({"success": True, "keys": generated_keys, "count": count})

# ===== 키 권한 설정 =====
KEY_PERMISSIONS_FILE = os.path.join(DATA_DIR, "key_permissions.json")

def load_key_permissions():
    """키 타입별 권한 설정 로드"""
    defaults = {
        "normal": {
            "catfood": True,
            "xp": True,
            "tickets": True,
            "cats": True,
            "stages": False,  # 스테이지 클리어는 기본적으로 VIP 전용
            "custom": True,
            "other": True
        },
        "vip": {
            "catfood": True,
            "xp": True,
            "tickets": True,
            "cats": True,
            "stages": True,
            "custom": True,
            "other": True
        }
    }
    if os.path.exists(KEY_PERMISSIONS_FILE):
        try:
            with open(KEY_PERMISSIONS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for kt in ["normal", "vip"]:
                    if kt in saved:
                        defaults[kt].update(saved[kt])
        except:
            pass
    return defaults

def save_key_permissions(permissions):
    with open(KEY_PERMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(permissions, f, ensure_ascii=False, indent=2)

def get_key_permissions_for_type(key_type):
    """특정 키 타입의 권한 반환"""
    perms = load_key_permissions()
    return perms.get(key_type, perms.get("normal", {}))

def check_item_permission(item_type, key_type):
    """아이템 타입이 키 타입의 권한에 포함되는지 확인"""
    perms = get_key_permissions_for_type(key_type)
    
    # 카테고리 매핑
    category_map = {
        "catfood": ["catfood"],
        "xp": ["xp"],
        "tickets": ["rare_ticket", "legend_ticket", "platinum_ticket", "normal_ticket", "platinum_shard", "leadership", "np"],
        "cats": ["unlock_cat", "unlock_all_cats", "unlock_all_obtainable_cats", "true_form_cat", "true_form_all_cats", "fourth_form_cat", "fourth_form_all_cats", "upgrade_cat", "upgrade_all_cats_max", "upgrade_cat_max", "upgrade_talents_cat", "upgrade_talents_all_cats", "unlock_cat_guide_cat", "unlock_all_cat_guide"],
        "stages": ["clear_stages", "clear_all_stages"],
        "custom": ["catfood", "xp", "rare_ticket", "legend_ticket", "platinum_ticket", "normal_ticket", "platinum_shard", "leadership", "np"],
        "other": ["user_rank", "unlock_equip"]
    }
    
    for category, types in category_map.items():
        if item_type in types:
            return perms.get(category, True)
    
    return True  # 기본적으로 허용

@app.route("/api/admin/key-permissions", methods=["GET"])
def admin_get_key_permissions():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    return jsonify(load_key_permissions())

@app.route("/api/admin/key-permissions", methods=["POST"])
def admin_save_key_permissions():
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    data = request.json
    permissions = load_key_permissions()
    
    # normal 권한 업데이트
    if "normal" in data:
        for key, value in data["normal"].items():
            permissions["normal"][key] = bool(value)
    
    # vip 권한 업데이트
    if "vip" in data:
        for key, value in data["vip"].items():
            permissions["vip"][key] = bool(value)
    
    save_key_permissions(permissions)
    add_log("권한 설정", "키 권한 설정 변경", "")
    return jsonify({"success": True, "message": "권한 설정이 저장되었습니다"})

@app.route("/api/admin/keys/<key>/delete", methods=["POST"])
def admin_delete_key(key):
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    keys = load_access_keys()
    keys = [k for k in keys if k["key"] != key]
    save_access_keys(keys)
    add_log("키 삭제", f"키: {key[:8]}...", "")
    return jsonify({"success": True, "message": "키가 삭제되었습니다"})

@app.route("/api/admin/keys/delete-expired", methods=["POST"])
def admin_delete_expired_keys():
    """만료된 키 일괄 삭제"""
    if not session.get('admin'):
        return jsonify({"error": "관리자 권한 필요"}), 403
    keys = load_access_keys()
    now = datetime.now()
    expired_keys = []
    active_keys = []
    for k in keys:
        try:
            if k.get('expires_at') and datetime.fromisoformat(k['expires_at']) < now:
                expired_keys.append(k)
            else:
                active_keys.append(k)
        except (ValueError, TypeError):
            active_keys.append(k)
    save_access_keys(active_keys)
    add_log("키 일괄 삭제", f"만료된 키 {len(expired_keys)}개 삭제", "")
    return jsonify({"success": True, "deleted_count": len(expired_keys), "message": f"만료된 키 {len(expired_keys)}개가 삭제되었습니다"})

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