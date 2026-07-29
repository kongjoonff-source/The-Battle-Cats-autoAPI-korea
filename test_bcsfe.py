"""
BCSFE 모듈 테스트
"""
import bcsfe.core
sh = bcsfe.core.SaveFile

tests = [
    ('get_normal_tickets', hasattr(sh, 'get_normal_tickets'), hasattr(sh, 'set_normal_tickets')),
    ('get_leadership', hasattr(sh, 'get_leadership'), hasattr(sh, 'set_leadership')),
    ('get_np', hasattr(sh, 'get_np'), hasattr(sh, 'set_np')),
    ('get_platinum_shards', hasattr(sh, 'get_platinum_shards'), hasattr(sh, 'set_platinum_shards')),
    ('unlock_equip_menu', hasattr(sh, 'unlock_equip_menu'), False),
    ('calculate_user_rank', hasattr(sh, 'calculate_user_rank'), False),
]

for name, getter, setter in tests:
    print(f"{name}: get={getter}, set={setter}")