"""라우트 테스트 스크립트 - 500 에러 원인 찾기"""
import sys
from datetime import datetime, timedelta
from app import app, load_access_keys, save_access_keys

def test_without_key():
    print("=== / (키 없음) 테스트 ===")
    client = app.test_client()
    r = client.get("/")
    print(f"Status: {r.status_code} -> Location: {r.headers.get('Location')}")

def test_with_key():
    print("=== 키 검증 API 테스트 ===")
    now = datetime.now()
    expires = now + timedelta(days=7)
    keys = load_access_keys()
    test_key = "test_key_123"
    keys.append({
        "key": test_key,
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "label": "test"
    })
    save_access_keys(keys)

    client = app.test_client()
    try:
        r = client.post("/api/verify-key", json={"key": test_key})
        print(f"Status: {r.status_code}")
        print(f"Response: {r.data[:200]}")

        print()
        print("=== / (키 있음) 테스트 ===")
        r = client.get("/")
        print(f"Status: {r.status_code}")
        if r.status_code >= 500:
            print(f"Response: {r.data[:1000]}")
        else:
            print("OK")
    finally:
        # 정리
        keys = load_access_keys()
        keys = [k for k in keys if k["key"] != test_key]
        save_access_keys(keys)

def test_admin_panel():
    print()
    print("=== /admin (로그인 안됨) 테스트 ===")
    client = app.test_client()
    r = client.get("/admin")
    print(f"Status: {r.status_code}")
    if r.status_code >= 500:
        print(f"Response: {r.data[:1000]}")

    print()
    print("=== /admin/panel (로그인 안됨) 테스트 ===")
    r = client.get("/admin/panel")
    print(f"Status: {r.status_code} -> Location: {r.headers.get('Location')}")

def test_admin_with_login():
    print()
    print("=== /admin/panel 로그인 테스트 ===")
    from config import ADMIN_PASSWORD
    client = app.test_client()
    r = client.post("/admin/panel", data={"password": ADMIN_PASSWORD})
    print(f"Status: {r.status_code} -> Location: {r.headers.get('Location')}")

    print()
    print("=== /admin/panel (로그인됨) 테스트 ===")
    r = client.get("/admin/panel")
    print(f"Status: {r.status_code}")
    if r.status_code >= 500:
        print(f"Response: {r.data[:1000]}")
    else:
        print("OK")

    print()
    print("=== /api/admin/keys (로그인됨) 테스트 ===")
    r = client.get("/api/admin/keys")
    print(f"Status: {r.status_code}")
    if r.status_code >= 500:
        print(f"Response: {r.data[:1000]}")
    else:
        print("OK")

def test_submit_order():
    print()
    print("=== /api/submit 주문 테스트 (키 없음 - 게이트로 리다이렉트 예상) ===")
    client = app.test_client()
    r = client.post("/api/submit", json={
        "buyer_name": "테스트",
        "transfer_code": "ABC123",
        "confirmation_code": "123456",
        "items": [{"id": "catfood_10000", "quantity": 1}]
    })
    print(f"Status: {r.status_code} -> Location: {r.headers.get('Location')}")

if __name__ == "__main__":
    test_without_key()
    test_with_key()
    test_admin_panel()
    test_admin_with_login()
    test_submit_order()
    print()
    print("✅ 모든 테스트 완료")