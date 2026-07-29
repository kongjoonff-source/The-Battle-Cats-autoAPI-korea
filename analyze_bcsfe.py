"""
bcsfe 구조 분석 스크립트
실제 bcsfe 동작을 분석하여 정확한 호출 방식을 찾습니다.
"""
import subprocess
import sys

def analyze_bcsfe():
    """bcsfe CLI를 실행하여 메뉴 구조 출력"""
    print("=== bcsfe 메뉴 구조 분석 ===")
    print("아래 순서로 입력해보세요:")
    print("1. bcsfe 실행")
    print("2. 화면에 표시되는 메뉴 번호 기록")
    print("3. 다운로드 (3번) → 전송코드 입력 → 확인코드 입력 → y")
    print("4. 아이템 수정 (2번) → 통조림 수량 입력")  
    print("5. 저장 (3번) → 새 전송코드 확인")
    
    print("\n분석을 시작하려면 Enter를 누르세요...")
    input()
    
    # bcsfe 실행 (한 줄씩 입력받도록)
    proc = subprocess.Popen(
        "bcsfe",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True
    )
    
    print("\n--- bcsfe 실행 중 ---")
    print("메뉴 번호를 확인하고, Ctrl+C로 종료한 후 알려주세요.")
    
    try:
        # 첫 화면 대기
        import time
        time.sleep(2)
    except KeyboardInterrupt:
        proc.kill()


def test_serverhandler():
    """ServerHandler 직접 호출 테스트"""
    print("\n=== ServerHandler 직접 호출 테스트 ===")
    
    # bcsfe 초기화 필요
    from bcsfe.core import ServerHandler, CountryCode, core_data
    from bcsfe.core.game_version import GameVersion
    
    # core_data 초기화
    try:
        core_data.init_data()
    except Exception as e:
        print(f"core_data.init_data() 실패: {e}")
    
    cc = CountryCode.from_code("kr")
    gv = GameVersion.from_string("1")
    
    print(f"CountryCode: {cc}")
    print(f"GameVersion: {gv}")
    
    # from_codes 호출 (테스트)
    try:
        result = ServerHandler.from_codes(
            "TEST_CODE",
            "TEST_CONFIRM", 
            cc,
            gv,
            print=False,
            save_backup=False
        )
        print(f"from_codes 결과: {result}")
    except Exception as e:
        print(f"from_codes 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_serverhandler()