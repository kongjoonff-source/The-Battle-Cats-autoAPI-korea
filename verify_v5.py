"""v5.0 기능 복구 확인"""
from app import app, get_item_definitions
from bcsfe_handler_full import process_all_items
import inspect

items = get_item_definitions()

# 고양이 업그레이드/도감 관련 아이템 확인
cats = [i for i in items if "업그레이드" in i["category"] or "고양이" in i["category"] or "도감" in i["category"]]
print(f"고양이/도감 관련 아이템 수: {len(cats)}")
for c in cats:
    print(f"  - {c['name']} ({c['id']})")

print()
print("전체 카테고리:")
categories = set(i["category"] for i in items)
for cat in categories:
    count = len([i for i in items if i["category"] == cat])
    print(f"  - {cat}: {count}개")

# bcsfe_handler_full.py 기능 확인
print()
print("bcsfe_handler_full.py 기능 확인:")
src = inspect.getsource(process_all_items)
checks = ["unlock_all_cats", "true_form", "fourth_form", "upgrade_cat", "talents", "cat_guide", "unlock_cat"]
for check in checks:
    print(f"  {check}: {'있음' if check in src else '없음'}")