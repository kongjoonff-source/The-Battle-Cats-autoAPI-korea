"""
서버 API 테스트 스크립트
"""
import urllib.request
import json

BASE = "http://localhost:5000"

def test_items():
    data = json.loads(urllib.request.urlopen(f"{BASE}/api/items").read())
    print(f"Items: {len(data)}")
    for i in data[:5]:
        print(f"  {i['id']}: {i['name']} - {i['price']}원")
    return True

def test_submit():
    body = json.dumps({
        "buyer_name": "test_user",
        "transfer_code": "test_code_123",
        "confirmation_code": "12345678",
        "items": [{"id": "catfood_10000", "quantity": 1}]
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/api/submit",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    print(f"Submit: {resp}")
    return resp.get("order_id")

def test_process(order_id):
    body = json.dumps({"order_id": order_id}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/process",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    print(f"Process: {resp}")
    return resp

def test_order_status(order_id):
    data = json.loads(urllib.request.urlopen(f"{BASE}/api/order/{order_id}").read())
    print(f"Status: {data['status']}")
    if data.get("result"):
        print(f"  Result: {data['result']}")
    return data

if __name__ == "__main__":
    print("=" * 60)
    print("서버 API 테스트")
    print("=" * 60)
    
    # 1. 아이템 목록
    print("\n1. 아이템 목록 조회")
    test_items()
    
    # 2. 주문 생성
    print("\n2. 주문 생성")
    order_id = test_submit()
    if order_id:
        print(f"   주문 ID: {order_id}")
        
        # 3. 처리 시작
        print("\n3. 처리 시작")
        test_process(order_id)
        
        # 4. 상태 확인
        print("\n4. 상태 확인")
        import time
        for i in range(5):
            time.sleep(2)
            status = test_order_status(order_id)
            if status["status"] in ("completed", "failed"):
                break
    
    print("\n" + "=" * 60)
    print("테스트 완료")
