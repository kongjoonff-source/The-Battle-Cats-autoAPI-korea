from flask import Flask, render_template, request, jsonify
import json
import os
import threading
from datetime import datetime
from bcsfe_handler_full import process_all_items
from config import (
    PUSHBULLET_API_KEY, BANK_NAME, BANK_ACCOUNT, ACCOUNT_HOLDER,
    CATFOOD_PRICES, XP_PRICES, TICKET_PRICES,
    DATA_DIR, SERVER_HOST, SERVER_PORT, SERVER_DEBUG
)

app = Flask(__name__)

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
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
DEPOSITS_FILE = os.path.join(DATA_DIR, "deposits.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")

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

# ========== 라우트 ==========

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
            # 아이템 리스트를 bcsfe 형식으로 변환
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

if __name__ == "__main__":
    print("=" * 70)
    print("🐱 냥코통조림충전소 - BCSFE 풀버전")
    print("=" * 70)
    print()
    print(f"서버 시작! http://localhost:{SERVER_PORT}")
    print(f"계좌: {BANK_NAME} {BANK_ACCOUNT} ({ACCOUNT_HOLDER})")
    print()

    app.run(debug=SERVER_DEBUG, host=SERVER_HOST, port=SERVER_PORT, threaded=True)