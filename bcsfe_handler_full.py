"""
BCSFE 모든 기능을 지원하는 핸들러 (풀버전 v5.0)

지원 기능:
- 아이템 지급 (통조림, XP, 티켓, NP, 리더십, 조각 등)
- 고양이 추가 (언락)
- 고양이 진화 (3진화/4진화)
- 고양이 강화 (레벨업)
- 고양이 특수 스킬 (특훈)

bcsfe CLI의 작동 원리를 따릅니다:
- 아이템 수정: SaveFile의 get_*/set_* 메서드 사용
- 고양이 수정: Cat/Cats 클래스 메서드 사용
- 업로드: ServerHandler.get_codes() 한 번 호출로
  인증토큰 → 세이브키 → 업로드 → 새 코드 발급을 모두 처리
"""
from typing import Optional, Tuple
import traceback
import sys


def process_all_items(
    transfer_code: str,
    confirmation_code: str,
    items: list,
    country_code: str = "kr",
    upload_managed_items: bool = False,
    max_retries: int = 3
) -> Tuple[bool, Optional[str], Optional[str], Optional[str], list]:
    """
    여러 아이템과 고양이 조작을 한 번에 처리합니다.
    bcsfe CLI의 ServerHandler.get_codes() 방식을 따라 업로드합니다.
    
    Args:
        transfer_code: 기기이전 코드
        confirmation_code: 인증번호
        items: 작업 목록 [{"type": "...", ...}, ...]
        country_code: 국가 코드 (기본: kr)
        upload_managed_items: managed items 업로드 여부
        max_retries: get_codes 최대 재시도 횟수
        
    Returns:
        (성공여부, 새_전송코드, 새_인증번호, 오류메시지, 상세결과)
    """
    print(f"\n{'='*60}")
    print(f"[BCSFE] process_all_items 시작")
    print(f"[BCSFE] transfer_code: {transfer_code}")
    print(f"[BCSFE] confirmation_code: {confirmation_code}")
    print(f"[BCSFE] items: {items}")
    print(f"{'='*60}")
    
    try:
        from bcsfe.core import ServerHandler, CountryCode, core_data
        from bcsfe.core.game_version import GameVersion

        # bcsfe 데이터 초기화
        print("[BCSFE] core_data.init_data() 호출...")
        core_data.init_data()
        print("[BCSFE] 초기화 완료")
        
        cc = CountryCode.from_code(country_code) if country_code else None
        gv = GameVersion.from_string("12.5.0")
        print(f"[BCSFE] CountryCode: {cc}, GameVersion: {gv}")

        # 1. 다운로드 - 전송코드로 세이브 가져오기 (v5와 동일: print=False)
        print(f"[BCSFE] ServerHandler.from_codes() 호출...")
        server, req_result = ServerHandler.from_codes(
            transfer_code, confirmation_code, cc, gv,
            print=False, save_backup=False
        )

        if server is None:
            print(f"[BCSFE] ❌ 세이브 다운로드 실패 - 코드를 확인해주세요")
            return False, None, None, "세이브 다운로드 실패 - 코드를 확인해주세요", []

        save_file = server.save_file
        print(f"[BCSFE] ✅ 세이브 다운로드 성공")
        print(f"[BCSFE] inquiry_code: {save_file.inquiry_code}")
        
        results = []

        # 2. 아이템 및 고양이 수정
        print(f"[BCSFE] 수정 작업 시작...")
        for item in items:
            item_type = item.get("type", "")
            result = {"type": item_type, "success": False, "message": ""}

            try:
                # ===== 아이템 지급 =====
                if item_type == "catfood":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_catfood()
                    save_file.set_catfood(current + amount)
                    print(f"  📈 통조림: {current:,} → {current+amount:,}")
                    result.update({"success": True, "message": f"통조림 {current:,} → {current+amount:,}개"})

                elif item_type == "xp":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_xp()
                    save_file.set_xp(current + amount)
                    print(f"  📈 XP: {current:,} → {current+amount:,}")
                    result.update({"success": True, "message": f"XP {current:,} → {current+amount:,}"})

                elif item_type == "rare_ticket":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_rare_tickets()
                    save_file.set_rare_tickets(current + amount)
                    print(f"  📈 레어티켓: {current} → {current+amount}")
                    result.update({"success": True, "message": f"레어티켓 {current} → {current+amount}개"})

                elif item_type == "legend_ticket":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_legend_tickets()
                    save_file.set_legend_tickets(current + amount)
                    print(f"  📈 레전드티켓: {current} → {current+amount}")
                    result.update({"success": True, "message": f"레전드티켓 {current} → {current+amount}개"})

                elif item_type == "platinum_ticket":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_platinum_tickets()
                    save_file.set_platinum_tickets(current + amount)
                    print(f"  📈 플래티넘티켓: {current} → {current+amount}")
                    result.update({"success": True, "message": f"플래티넘티켓 {current} → {current+amount}개"})

                elif item_type == "normal_ticket":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_normal_tickets()
                    save_file.set_normal_tickets(current + amount)
                    print(f"  📈 노멀티켓: {current} → {current+amount}")
                    result.update({"success": True, "message": f"노멀티켓 {current} → {current+amount}개"})

                elif item_type == "platinum_shard":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_platinum_shards()
                    save_file.set_platinum_shards(current + amount)
                    print(f"  📈 플래티넘조각: {current} → {current+amount}")
                    result.update({"success": True, "message": f"플래티넘조각 {current} → {current+amount}개"})

                elif item_type == "leadership":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_leadership()
                    save_file.set_leadership(current + amount)
                    print(f"  📈 리더십: {current} → {current+amount}")
                    result.update({"success": True, "message": f"리더십 {current} → {current+amount}개"})

                elif item_type == "np":
                    amount = int(item.get("amount", 0))
                    current = save_file.get_np()
                    save_file.set_np(current + amount)
                    print(f"  📈 NP: {current:,} → {current+amount:,}")
                    result.update({"success": True, "message": f"NP {current:,} → {current+amount:,}"})

                elif item_type == "user_rank":
                    save_file.calculate_user_rank()
                    result.update({"success": True, "message": "유저랭크 재계산 완료"})

                elif item_type == "unlock_equip":
                    save_file.unlock_equip_menu()
                    result.update({"success": True, "message": "장비 메뉴 해제 완료"})

                # ===== 고양이 추가 (언락) =====
                elif item_type == "unlock_cat":
                    cat_id = int(item.get("cat_id", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None:
                        cat.unlock(save_file)
                        print(f"  🐱 고양이 언락: ID {cat_id}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 언락 완료"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                elif item_type == "unlock_all_cats":
                    cats = save_file.cats.get_all_cats()
                    for cat in cats:
                        cat.unlock(save_file)
                    print(f"  🐱 모든 고양이 언락: {len(cats)}마리")
                    result.update({"success": True, "message": f"모든 고양이 언락 완료 ({len(cats)}마리)"})

                elif item_type == "unlock_all_obtainable_cats":
                    cats = save_file.cats.get_cats_obtainable(save_file)
                    if cats:
                        for cat in cats:
                            cat.unlock(save_file)
                        print(f"  🐱 획득 가능한 고양이 언락: {len(cats)}마리")
                        result.update({"success": True, "message": f"획득 가능한 고양이 언락 완료 ({len(cats)}마리)"})
                    else:
                        result.update({"message": "획득 가능한 고양이 목록을 불러올 수 없음"})

                # ===== 고양이 진화 =====
                elif item_type == "true_form_cat":
                    cat_id = int(item.get("cat_id", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None:
                        cat.true_form(save_file)
                        print(f"  🐱 고양이 3진화: ID {cat_id}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 3진화 완료"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                elif item_type == "true_form_all_cats":
                    cats = save_file.cats.get_all_cats()
                    save_file.cats.true_form_cats(save_file, cats, force=True)
                    print(f"  🐱 모든 고양이 3진화: {len(cats)}마리")
                    result.update({"success": True, "message": f"모든 고양이 3진화 완료 ({len(cats)}마리)"})

                elif item_type == "fourth_form_cat":
                    cat_id = int(item.get("cat_id", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None:
                        cat.unlock_fourth_form(save_file)
                        print(f"  🐱 고양이 4진화: ID {cat_id}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 4진화 완료"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                elif item_type == "fourth_form_all_cats":
                    cats = save_file.cats.get_all_cats()
                    save_file.cats.fourth_form_cats(save_file, cats, force=True)
                    print(f"  🐱 모든 고양이 4진화: {len(cats)}마리")
                    result.update({"success": True, "message": f"모든 고양이 4진화 완료 ({len(cats)}마리)"})

                # ===== 고양이 강화 (레벨업) =====
                elif item_type == "upgrade_cat":
                    cat_id = int(item.get("cat_id", -1))
                    base_level = int(item.get("base_level", -1))
                    plus_level = int(item.get("plus_level", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None:
                        from bcsfe.core import Upgrade
                        cat.unlock(save_file)
                        if base_level >= 0:
                            cat.upgrade.base = base_level
                        if plus_level >= 0:
                            cat.upgrade.plus = plus_level
                        print(f"  🐱 고양이 강화: ID {cat_id} → base={cat.upgrade.base}, plus={cat.upgrade.plus}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 강화 완료 (base={cat.upgrade.base}, plus={cat.upgrade.plus})"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                elif item_type == "upgrade_all_cats_max":
                    cats = save_file.cats.get_all_cats()
                    count = 0
                    for cat in cats:
                        cat.unlock(save_file)
                        cat.upgrade.base = 60
                        cat.upgrade.plus = 90
                        count += 1
                    print(f"  🐱 모든 고양이 최대 강화: {count}마리")
                    result.update({"success": True, "message": f"모든 고양이 최대 강화 완료 ({count}마리)"})

                elif item_type == "upgrade_cat_max":
                    cat_id = int(item.get("cat_id", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None:
                        cat.unlock(save_file)
                        cat.upgrade.base = 60
                        cat.upgrade.plus = 90
                        print(f"  🐱 고양이 최대 강화: ID {cat_id}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 최대 강화 완료"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                # ===== 고양이 특훈 (재능) =====
                elif item_type == "upgrade_talents_cat":
                    cat_id = int(item.get("cat_id", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None and cat.talents is not None:
                        cat.unlock(save_file)
                        for talent in cat.talents:
                            talent.level = 10
                        print(f"  🐱 고양이 특훈 최대: ID {cat_id}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 특훈 최대 완료"})
                    elif cat is not None:
                        result.update({"message": f"고양이 ID {cat_id}에 특훈 데이터 없음"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                elif item_type == "upgrade_talents_all_cats":
                    cats = save_file.cats.get_all_cats()
                    count = 0
                    for cat in cats:
                        if cat.talents is not None:
                            cat.unlock(save_file)
                            for talent in cat.talents:
                                talent.level = 10
                            count += 1
                    print(f"  🐱 모든 고양이 특훈 최대: {count}마리")
                    result.update({"success": True, "message": f"모든 고양이 특훈 최대 완료 ({count}마리)"})

                # ===== 고양이 도감 =====
                elif item_type == "unlock_cat_guide_cat":
                    cat_id = int(item.get("cat_id", -1))
                    cat = save_file.cats.get_cat_by_id(cat_id)
                    if cat is not None:
                        cat.unlock(save_file)
                        cat.catguide_collected = True
                        print(f"  📖 고양이 도감: ID {cat_id}")
                        result.update({"success": True, "message": f"고양이 ID {cat_id} 도감 등록 완료"})
                    else:
                        result.update({"message": f"고양이 ID {cat_id}를 찾을 수 없음"})

                elif item_type == "unlock_all_cat_guide":
                    cats = save_file.cats.get_all_cats()
                    for cat in cats:
                        cat.catguide_collected = True
                    print(f"  📖 모든 고양이 도감: {len(cats)}마리")
                    result.update({"success": True, "message": f"모든 고양이 도감 등록 완료 ({len(cats)}마리)"})

                else:
                    result.update({"message": f"알 수 없는 타입: {item_type}"})

            except Exception as e:
                print(f"  ❌ 처리 오류 ({item_type}): {e}")
                traceback.print_exc()
                result.update({"message": f"처리 오류: {str(e)}"})

            results.append(result)

        # 3. 업로드 및 새 코드 발급
        print(f"[BCSFE] 서버 업로드 및 새 코드 발급 시작...")
        
        codes = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"[BCSFE] get_codes() 시도 {attempt+1}/{max_retries}...")
                codes = server.get_codes(upload_managed_items=upload_managed_items)
                
                if codes:
                    new_transfer, new_confirm = codes
                    print(f"[BCSFE] ✅ 새 코드 발급 성공!")
                    print(f"[BCSFE]    새 전송코드: {new_transfer}")
                    print(f"[BCSFE]    새 인증번호: {new_confirm}")
                    return True, new_transfer, new_confirm, None, results
                else:
                    last_error = f"get_codes()가 None 반환 (시도 {attempt+1}/{max_retries})"
                    print(f"[BCSFE] ❌ {last_error}")
                    import time
                    time.sleep(2)
                    
            except Exception as e:
                last_error = f"get_codes() 예외: {str(e)}"
                print(f"[BCSFE] ❌ {last_error}")
                traceback.print_exc()
                import time
                time.sleep(2)

        # 마지막 시도: upload_managed_items=True로 시도
        if not codes:
            try:
                print(f"[BCSFE] 마지막 시도: upload_managed_items=True로 재시도...")
                codes = server.get_codes(upload_managed_items=True)
                if codes:
                    new_transfer, new_confirm = codes
                    print(f"[BCSFE] ✅ 성공! (upload_managed_items=True)")
                    return True, new_transfer, new_confirm, None, results
            except Exception as e:
                last_error = f"마지막 시도 실패: {str(e)}"
                print(f"[BCSFE] ❌ {last_error}")

        error_msg = last_error or "서버 응답 실패 - 다시 시도해주세요"
        return False, None, None, error_msg, results

    except Exception as e:
        print(f"[BCSFE] ⚠️ 시스템 오류 발생!")
        traceback.print_exc()
        return False, None, None, f"시스템 오류: {str(e)}", []