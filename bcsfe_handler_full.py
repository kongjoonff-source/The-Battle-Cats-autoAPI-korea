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

                # ===== 스테이지 클리어 (BCSFE) =====
                elif item_type == "clear_stages":
                    chapter_id = int(item.get("chapter_id", 0))
                    # 챕터별 스테이지 클리어 처리
                    # 1-3: 제1~3장 (Empire of Cats)
                    # 4-6: 미래편 1~3장 (Into the Future)
                    # 7-9: 우주편 1~3장 (Cats of the Cosmos)
                    cleared = _clear_chapter_stages(save_file, chapter_id)
                    if cleared:
                        result.update({"success": True, "message": f"챕터 {chapter_id} 스테이지 클리어 완료"})
                    else:
                        result.update({"message": f"챕터 {chapter_id} 스테이지 클리어 실패"})

                elif item_type == "clear_all_stages":
                    # 모든 챕터 (제1장 ~ 우주편 제3장) 스테이지 클리어
                    cleared_count = 0
                    for ch_id in range(1, 10):
                        if _clear_chapter_stages(save_file, ch_id):
                            cleared_count += 1
                    if cleared_count > 0:
                        result.update({"success": True, "message": f"전체 {cleared_count}개 챕터 스테이지 클리어 완료"})
                    else:
                        result.update({"message": "스테이지 클리어 실패"})

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

        # 3. 업로드 및 새 코드 발급 (v5.0과 동일: get_codes() 한 번 호출)
        print(f"[BCSFE] 서버 업로드 및 새 코드 발급 시작...")

        try:
            # v5.0과 완전히 동일: upload_managed_items=False, 단일 호출
            codes = server.get_codes(upload_managed_items=False)
            if codes:
                new_transfer, new_confirm = codes
                print(f"[BCSFE] ✅ 새 코드 발급 성공!")
                print(f"[BCSFE]    새 전송코드: {new_transfer}")
                print(f"[BCSFE]    새 인증번호: {new_confirm}")
                return True, new_transfer, new_confirm, None, results
            else:
                print(f"[BCSFE] ❌ get_codes()가 None 반환")
                return False, None, None, "새 코드 발급 실패 - get_codes()가 None을 반환했습니다", results
        except Exception as e:
            print(f"[BCSFE] ❌ get_codes() 예외: {e}")
            traceback.print_exc()
            return False, None, None, f"새 코드 발급 실패: {str(e)}", results

    except Exception as e:
        print(f"[BCSFE] ⚠️ 시스템 오류 발생!")
        traceback.print_exc()
        return False, None, None, f"시스템 오류: {str(e)}", []


def _clear_chapter_stages(save_file, chapter_id: int) -> bool:
    """
    특정 챕터의 모든 스테이지를 클리어 처리합니다.
    
    챕터 매핑:
    - 1~3: 제1~3장 (Empire of Cats)
    - 4~6: 미래편 1~3장 (Into the Future)
    - 7~9: 우주편 1~3장 (Cats of the Cosmos)
    
    bcsfe SaveFile의 스테이지 클리어 관련 속성을 직접 설정합니다.
    """
    try:
        # 챕터별 스테이지 데이터 구조 확인
        # bcsfe SaveFile에는 chapter/level 클리어 상태가 저장됨
        # 각 챕터는 48개 스테이지 (1~48)
        
        # SaveFile의 스테이지 클리어 속성 접근 시도
        # 다양한 bcsfe 버전 호환을 위해 try/except로 처리
        cleared = False
        
        # 방법 1: save_file.chapters 또는 save_file.levels 접근
        if hasattr(save_file, 'chapters'):
            chapters = save_file.chapters
            if chapter_id <= len(chapters):
                chapter = chapters[chapter_id - 1]
                # 챕터의 모든 스테이지 클리어 처리
                if hasattr(chapter, 'clear_all'):
                    chapter.clear_all()
                    cleared = True
                elif hasattr(chapter, 'stages'):
                    for stage in chapter.stages:
                        stage.cleared = True
                    cleared = True
                elif hasattr(chapter, 'cleared'):
                    chapter.cleared = True
                    cleared = True
        
        # 방법 2: save_file.stages 접근
        if not cleared and hasattr(save_file, 'stages'):
            stages = save_file.stages
            # 챕터 범위에 해당하는 스테이지 클리어
            start = (chapter_id - 1) * 48
            end = start + 48
            for i in range(start, min(end, len(stages))):
                stages[i].cleared = True
            cleared = True
        
        # 방법 3: save_file.level_cleared 또는 유사 속성
        if not cleared:
            # bcsfe의 SaveFile에서 스테이지 클리어 상태를 직접 설정
            # 일반적인 속성명들 시도
            attr_names = [
                f'chapter_{chapter_id}_cleared',
                f'chapter{chapter_id}_cleared',
                f'cleared_chapter_{chapter_id}',
                'all_stages_cleared'
            ]
            for attr in attr_names:
                if hasattr(save_file, attr):
                    setattr(save_file, attr, True)
                    cleared = True
                    break
        
        # 방법 4: bcsfe의 Chapter/Level 클래스 사용
        if not cleared:
            try:
                from bcsfe.core import Chapter, Level
                # 챕터별 스테이지 클리어 처리
                # bcsfe의 save_file에서 챕터 데이터 접근
                if hasattr(save_file, 'get_chapter'):
                    chapter = save_file.get_chapter(chapter_id)
                    if chapter:
                        chapter.clear_all()
                        cleared = True
            except Exception:
                pass
        
        # 방법 5: 직접 스테이지 클리어 배열 설정
        if not cleared:
            # bcsfe SaveFile의 스테이지 클리어 배열 직접 조작
            # 일반적인 속성: cleared_stages, stage_clears, etc.
            for attr in ['cleared_stages', 'stage_clears', 'cleared_levels', 'level_clears']:
                if hasattr(save_file, attr):
                    data = getattr(save_file, attr)
                    start = (chapter_id - 1) * 48
                    end = start + 48
                    if isinstance(data, list):
                        for i in range(start, min(end, len(data))):
                            data[i] = True
                        cleared = True
                    elif isinstance(data, dict):
                        for i in range(start, end):
                            data[i] = True
                        cleared = True
                    break
        
        if cleared:
            print(f"  🗺️ 챕터 {chapter_id} 스테이지 클리어 완료")
        else:
            print(f"  ⚠️ 챕터 {chapter_id} 스테이지 클리어 처리 실패 (속성 미발견)")
        
        return cleared
        
    except Exception as e:
        print(f"  ❌ 챕터 {chapter_id} 스테이지 클리어 오류: {e}")
        traceback.print_exc()
        return False
