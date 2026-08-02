with open('render.yaml', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# line 19 (0-indexed 18): ADMIN_PASSWORD 아래 줄 수정
lines[18] = '      value: "zizer731!!"\n'
with open('render.yaml', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("완료: ADMIN_PASSWORD = zizer731!!")