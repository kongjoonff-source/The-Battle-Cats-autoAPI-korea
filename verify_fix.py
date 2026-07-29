"""
bcsfe_handler_full.py 수정 검증 스크립트
bcsfe CLI의 작동 원리와 비교하여 핸들러가 올바르게 수정되었는지 검증합니다.
"""
import inspect
import sys

def check_no_redundant_upload():
    """중복 업로드 코드가 제거되었는지 확인"""
    from bcsfe_handler_full import process_all_items
    source = inspect.getsource(process_all_items)

    # 이전 방식의 중복 코드가 없는지 확인
    old_patterns = [
        "get_stored_save_key_data()",
        "get_save_key_new(server.get_auth_token())",
        "server.upload_save_data(save_key)",
    ]

    found_old = []
    for pattern in old_patterns:
        if pattern in source:
            found_old.append(pattern)

    if found_old:
        print(f"[FAIL] 중복 업로드 코드가 아직 존재: {found_old}")
        return False

    print("[OK] 중복 업로드 코드가 제거되었습니다")
    return True


def check_get_codes_direct():
    """get_codes()가 직접 호출되는지 확인"""
    from bcsfe_handler_full import process_all_items
    source = inspect.getsource(process_all_items)

    if "server.get_codes(upload_managed_items=False)" in source:
        print("[OK] server.get_codes(upload_managed_items=False)가 직접 호출됩니다")
        return True

    print("[FAIL] get_codes() 호출을 찾을 수 없습니다")
    return False


def check_direct_property_access():
    """직접 속성 접근을 사용하는지 확인"""
    from bcsfe_handler_full import process_all_items
    source = inspect.getsource(process_all_items)

    # bcsfe CLI의 basic_items.py에서 사용하는 방식과 일치하는지 확인
    property_patterns = [
        "save_file.catfood",
        "save_file.xp",
        "save_file.rare_tickets",
        "save_file.legend_tickets",
        "save_file.platinum_tickets",
        "save_file.normal_tickets",
        "save_file.platinum_shards",
        "save_file.leadership",
        "save_file.np",
    ]

    # get_*/set_* 메서드가 아닌 직접 속성 접근 확인
    old_method_patterns = [
        "save_file.get_catfood()",
        "save_file.set_catfood(",
        "save_file.get_xp()",
        "save_file.set_xp(",
        "save_file.get_rare_tickets()",
        "save_file.set_rare_tickets(",
    ]

    found_old_methods = [p for p in old_method_patterns if p in source]
    if found_old_methods:
        print(f"[FAIL] get_*/set_* 메서드가 아직 사용 중: {found_old_methods}")
        return False

    found_properties = [p for p in property_patterns if p in source]
    if len(found_properties) >= 5:
        print(f"[OK] 직접 속성 접근 사용 중 ({len(found_properties)}개 속성)")
        return True

    print("[FAIL] 직접 속성 접근을 찾을 수 없습니다")
    return False


def check_bcsfe_cli_pattern():
    """bcsfe CLI의 save_management.py 패턴과 비교"""
    # bcsfe CLI의 save_management.py에서 사용하는 패턴:
    # result = core.ServerHandler(save_file).get_codes()
    from bcsfe_handler_full import process_all_items
    source = inspect.getsource(process_all_items)

    # get_codes가 upload_managed_items=False로 호출되어야 합니다
    # (bcsfe CLI는 기본값 True를 사용하지만, 쇼핑몰에서는 False가 안전)
    if "get_codes(upload_managed_items=False)" in source:
        print("[OK] bcsfe CLI 패턴과 일치 (get_codes 호출)")
        return True

    print("[FAIL] bcsfe CLI 패턴과 불일치")
    return False


def check_from_codes():
    """from_codes가 올바르게 호출되는지 확인"""
    from bcsfe_handler_full import process_all_items
    source = inspect.getsource(process_all_items)

    if "ServerHandler.from_codes(" in source:
        print("[OK] ServerHandler.from_codes() 호출 확인")
        return True

    print("[FAIL] from_codes 호출을 찾을 수 없습니다")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("bcsfe 핸들러 수정 검증")
    print("=" * 60)

    results = []
    results.append(("중복 업로드 제거", check_no_redundant_upload()))
    results.append(("get_codes 직접 호출", check_get_codes_direct()))
    results.append(("직접 속성 접근", check_direct_property_access()))
    results.append(("bcsfe CLI 패턴 일치", check_bcsfe_cli_pattern()))
    results.append(("from_codes 호출", check_from_codes()))

    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    all_pass = all(r for _, r in results)
    print(f"\n전체: {'✅ ALL PASS' if all_pass else '❌ SOME FAILED'}")
    sys.exit(0 if all_pass else 1)
