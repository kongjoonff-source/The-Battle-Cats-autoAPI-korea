"""
실시간 테스트 스크립트
사용자가 직접 전송코드와 인증번호를 입력하여 테스트합니다.
"""
from bcsfe_handler_full import process_all_items

def main():
    print("=" * 70)
    print("BCSFE 실시간 테스트")
    print("=" * 70)
    print()
    
    transfer_code = input("전송코드 입력: ").strip()
    confirmation_code = input("인증번호 입력: ").strip()
    
    if not transfer_code or not confirmation_code:
        print("전송코드와 인증번호를 모두 입력해주세요.")
        return
    
    print()
    print("테스트 아이템: 통조림 1,000개")
    print()
    
    items = [{"type": "catfood", "amount": 1000}]
    
    success, new_tf, new_cc, error, details = process_all_items(
        transfer_code, confirmation_code, items
    )
    
    print()
    print("=" * 70)
    print("결과:")
    print("=" * 70)
    print(f"성공: {success}")
    print(f"새 기기이전코드: {new_tf}")
    print(f"새 인증번호: {new_cc}")
    print(f"오류: {error}")
    if details:
        print("상세:")
        for d in details:
            print(f"  - {d}")

if __name__ == "__main__":
    main()