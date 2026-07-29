"""
냥코 통조림 자동 충전 핸들러
bcsfe Python 모듈을 직접 사용합니다.
통조림, XP, 티켓 등 다양한 아이템 지급 지원

bcsfe CLI의 작동 원리를 따릅니다:
- 아이템 수정: SaveFile의 직접 속성 접근 (save_file.catfood = value)
- 업로드: ServerHandler.get_codes() 한 번 호출로 처리
"""
from typing import Optional, Tuple

def auto_process_item(
    transfer_code: str,
    confirmation_code: str,
    item_info: dict,
    country_code: str = "kr"
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    bcsfe Python API를 직접 호출하여 아이템을 추가합니다.

    Args:
        transfer_code: 기기이전 코드
        confirmation_code: 인증번호
        item_info: {"type": "catfood"/"xp"/"ticket", "amount": 수량, ...}
        country_code: 국가 코드

    Returns: (성공여부, 새_전송코드, 새_확인코드, 오류메시지)
    """
    try:
        from bcsfe.core import ServerHandler, CountryCode, core_data
        from bcsfe.core.game_version import GameVersion

        # bcsfe 초기화
        core_data.init_data()

        # 국가 코드
        cc = CountryCode.from_code(country_code) if country_code else None

        # GameVersion 생성 (12.5.0 -> "120500")
        gv = GameVersion.from_string("12.5.0")

        # 1. 다운로드 - 전송코드로 세이브 가져오기 (bcsfe CLI와 동일)
        server, req_result = ServerHandler.from_codes(
            transfer_code,
            confirmation_code,
            cc,
            gv,
            print=False,
            save_backup=False
        )

        if server is None:
            print(f"다운로드 실패 - RequestResult: {req_result}")
            return False, None, None, "세이브 다운로드 실패 - 코드 오류"

        # 2. SaveFile 가져오기
        save_file = server.save_file

        # 3. 아이템 타입별 처리 (bcsfe CLI의 basic_items.py 방식: 직접 속성 접근)
        item_type = item_info.get("type", "catfood")
        amount = int(item_info.get("amount", 0))

        if item_type == "catfood":
            try:
                current_catfood = int(save_file.catfood)
                save_file.catfood = current_catfood + amount
                print(f"Catfood 수정: {current_catfood} -> {current_catfood + amount}")
            except Exception as e:
                print(f"catfood 수정 실패: {e}")
                return False, None, None, f"catfood 수정 실패: {str(e)}"

        elif item_type == "xp":
            try:
                current_xp = int(save_file.xp)
                save_file.xp = current_xp + amount
                print(f"XP 수정: {current_xp} -> {current_xp + amount}")
            except Exception as e:
                print(f"XP 수정 실패: {e}")
                return False, None, None, f"XP 수정 실패: {str(e)}"

        elif item_type == "ticket":
            ticket_type = item_info.get("ticket_type", "rare")
            try:
                if ticket_type == "rare":
                    current = int(save_file.rare_tickets)
                    save_file.rare_tickets = current + amount
                    print(f"Rare Ticket 수정: {current} -> {current + amount}")
                elif ticket_type == "legend":
                    current = int(save_file.legend_tickets)
                    save_file.legend_tickets = current + amount
                    print(f"Legend Ticket 수정: {current} -> {current + amount}")
                elif ticket_type == "platinum":
                    current = int(save_file.platinum_tickets)
                    save_file.platinum_tickets = current + amount
                    print(f"Platinum Ticket 수정: {current} -> {current + amount}")
            except Exception as e:
                print(f"티켓 수정 실패: {e}")
                return False, None, None, f"티켓 수정 실패: {str(e)}"

        # 4. 업로드 및 새 코드 발급 (bcsfe CLI 방식)
        # ServerHandler.get_codes() 내부에서 인증토큰, 세이브키, 업로드를 모두 처리
        codes = server.get_codes(upload_managed_items=False)
        if codes:
            new_transfer, new_confirm = codes
            return True, new_transfer, new_confirm, None

        return False, None, None, "새 코드 발급 실패"

    except Exception as e:
        print(f"bcsfe 오류: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None, f"오류: {str(e)}"


def process_order(
    transfer_code: str,
    confirmation_code: str,
    buyer_name: str,
    item_info: dict
) -> dict:
    """
    주문을 처리합니다.
    """
    success, new_transfer, new_confirm, error = auto_process_item(
        transfer_code, confirmation_code, item_info
    )

    return {
        "success": success,
        "buyer_name": buyer_name,
        "old_transfer_code": transfer_code,
        "new_transfer_code": new_transfer,
        "new_confirmation_code": new_confirm,
        "item_info": item_info,
        "error": error
    }
