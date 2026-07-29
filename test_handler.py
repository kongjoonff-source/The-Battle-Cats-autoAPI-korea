"""
bcsfe_handler_full.py 테스트 스크립트
bcsfe CLI의 작동 원리를 따라 핸들러가 제대로 동작하는지 테스트합니다.
"""
import sys
import traceback

def test_import():
    """핸들러 임포트 테스트"""
    try:
        from bcsfe_handler_full import process_all_items
        print("[OK] bcsfe_handler_full import 성공")
        return True
    except Exception as e:
        print(f"[FAIL] bcsfe_handler_full import 실패: {e}")
        traceback.print_exc()
        return False

def test_app_import():
    """app.py 임포트 테스트"""
    try:
        import app
        print("[OK] app.py import 성공")
        return True
    except Exception as e:
        print(f"[FAIL] app.py import 실패: {e}")
        traceback.print_exc()
        return False

def test_bcsfe_init():
    """bcsfe 초기화 테스트"""
    try:
        from bcsfe.core import core_data
        core_data.init_data()
        print("[OK] bcsfe core_data.init_data() 성공")
        return True
    except Exception as e:
        print(f"[FAIL] bcsfe core_data.init_data() 실패: {e}")
        traceback.print_exc()
        return False

def test_savefile_methods():
    """SaveFile 메서드 테스트"""
    try:
        import bcsfe.core
        sh = bcsfe.core.SaveFile
        methods = ['get_catfood', 'set_catfood', 'get_xp', 'set_xp',
                   'get_rare_tickets', 'set_rare_tickets', 'get_normal_tickets',
                   'set_normal_tickets', 'get_legend_tickets', 'set_legend_tickets',
                   'get_platinum_tickets', 'set_platinum_tickets',
                   'get_platinum_shards', 'set_platinum_shards',
                   'get_leadership', 'set_leadership', 'get_np', 'set_np',
                   'unlock_equip_menu', 'calculate_user_rank']
        missing = [m for m in methods if not hasattr(sh, m)]
        if missing:
            print(f"[FAIL] 누락된 메서드: {missing}")
            return False
        print("[OK] 모든 SaveFile 메서드 존재")
        return True
    except Exception as e:
        print(f"[FAIL] SaveFile 메서드 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_serverhandler_api():
    """ServerHandler API 테스트"""
    try:
        from bcsfe.core import ServerHandler
        methods = ['from_codes', 'get_codes', 'get_save_key', 'get_auth_token',
                   'upload_save_data', 'get_save_key_new', 'get_stored_save_key_data']
        missing = [m for m in methods if not hasattr(ServerHandler, m)]
        if missing:
            print(f"[FAIL] 누락된 ServerHandler 메서드: {missing}")
            return False
        print("[OK] 모든 ServerHandler 메서드 존재")

        # get_codes 시그니처 확인
        import inspect
        sig = inspect.signature(ServerHandler.get_codes)
        print(f"[INFO] get_codes 시그니처: {sig}")
        return True
    except Exception as e:
        print(f"[FAIL] ServerHandler API 테스트 실패: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("bcsfe 핸들러 테스트")
    print("=" * 60)

    results = []
    results.append(("Import 테스트", test_import()))
    results.append(("App Import 테스트", test_app_import()))
    results.append(("bcsfe 초기화 테스트", test_bcsfe_init()))
    results.append(("SaveFile 메서드 테스트", test_savefile_methods()))
    results.append(("ServerHandler API 테스트", test_serverhandler_api()))

    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    all_pass = all(r for _, r in results)
    print(f"\n전체: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
    sys.exit(0 if all_pass else 1)
