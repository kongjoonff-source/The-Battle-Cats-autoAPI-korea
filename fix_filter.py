"""index.html의 아이템 ID 필터링 문제 수정"""
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old = ".filter(([k]) => !k.includes('_'))"
new = ".filter(([k]) => items.some(i => i.id === k))"

count = content.count(old)
content = content.replace(old, new)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("완료: " + str(count) + "곳의 filter가 items.some로 변경되었습니다")