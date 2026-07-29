"""
Pushbullet 실시간 리스너
은행 입금 알림을 감지하여 자동으로 주문 처리를 시작합니다.
입금자명과 금액이 일치하면 자동으로 충전을 처리합니다.
"""
from pushbullet import Pushbullet
import time
import requests
import re
import os
from config import PUSHBULLET_API_KEY

API_URL = "http://localhost:5000"

def extract_buyer_name(message: str) -> str:
    """
    은행 알림 메시지에서 입금자 이름을 추출합니다.
    은행별로 다른 형식에 대응할 수 있도록 여러 패턴을 시도합니다.
    """
    patterns = [
        r'(\w+)님이',                    # "홍길동님이 입금"
        r'입금\s*[:：]?\s*(\w+)',      # "입금: 홍길동"
        r'입금자\s*[:：]?\s*(\w+)',     # "입금자: 홍길동"
        r'\[(\w+)\]',                  # "[홍길동]"
        r'(\w+)\s*님',                  # "홍길동 님"
    ]

    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)

    return None

def extract_amount(message: str) -> int:
    """
    은행 알림 메시지에서 입금 금액을 추출합니다.
    """
    # 숫자 + 원 또는 숫자 + , 패턴
    patterns = [
        r'(\d{1,3}(?:,\d{3})*)\s*원',  # "5,000원"
        r'(\d+)\s*원',                 # "5000원"
        r'(\d{1,3}(?:,\d{3})*)',       # "5,000"
    ]

    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return int(amount_str)
            except ValueError:
                continue

    return 0

def main():
    if PUSHBULLET_API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️ PUSHBULLET_API_KEY를 config.py에 설정해주세요!")
        return

    pb = Pushbullet(PUSHBULLET_API_KEY)

    print("=" * 60)
    print("🐱 냥코통조림충전소 - Pushbullet 리스너")
    print("=" * 60)
    print()
    print("입금 알림을 감지하여 자동 처리합니다...")
    print(f"API URL: {API_URL}")
    print()

    # 마지막으로 처리한 푸시 ID 저장
    last_push_id = None

    # 초기화 시 최근 푸시 가져오기
    try:
        pushes = pb.get_pushes(limit=5)
        if pushes:
            last_push_id = pushes[0].get('iden')
            print(f"마지막 처리된 푸시 ID: {last_push_id}")
    except Exception as e:
        print(f"초기화 중 오류: {e}")

    while True:
        try:
            # 최신 푸시 가져오기
            pushes = pb.get_pushes(limit=10)

            for push in pushes:
                if last_push_id and push.get('iden') == last_push_id:
                    continue

                if push.get('type') == 'note':
                    title = push.get('title', '')
                    body = push.get('body', '')

                    # 은행 관련 알림 확인
                    bank_keywords = ['입금', '송금', '입금자', '입금 확인', '은행', '토스', '계좌']
                    is_bank_notification = any(kw in title or kw in body for kw in bank_keywords)

                    if is_bank_notification:
                        buyer_name = extract_buyer_name(title + " " + body)
                        deposit_amount = extract_amount(title + " " + body)

                        if buyer_name:
                            print(f"\n[입금 감지] {buyer_name}님 - {deposit_amount}원")

                            # 주문 처리 요청
                            try:
                                response = requests.post(
                                    f"{API_URL}/check-deposit-internal",
                                    json={
                                        "buyer_name": buyer_name,
                                        "deposit_amount": deposit_amount
                                    },
                                    timeout=10
                                )
                                result = response.json()
                                print(f"  처리 결과: {result}")

                                if response.status_code == 200:
                                    print(f"  ✅ 자동 처리 시작됨")
                                else:
                                    print(f"  ⚠️ 처리 실패: {result.get('error', '알 수 없음')}")

                            except requests.exceptions.ConnectionError:
                                print(f"  ❌ 서버 연결 실패 (서버가 꺼져있을 수 있음)")
                            except Exception as e:
                                print(f"  ❌ 처리 요청 실패: {e}")
                        else:
                            print(f"\n[입금 알림] 입금자명 추출 실패: {title} - {body}")

                last_push_id = push.get('iden')

            time.sleep(10)  # 10초마다 체크

        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("리스너 종료")
            print("=" * 60)
            break
        except Exception as e:
            print(f"오류 발생: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
