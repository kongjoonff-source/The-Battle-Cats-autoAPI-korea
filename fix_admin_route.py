# admin_login.html action을 /admin으로 변경
with open('templates/admin_login.html', 'r', encoding='utf-8') as f:
    content = f.read()

# action="/admin/panel" -> action="/admin"
content = content.replace('action="/admin/panel"', 'action="/admin"')

with open('templates/admin_login.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("admin_login.html action 변경 완료")