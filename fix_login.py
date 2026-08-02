# admin_login.html 생성 + app.py admin_logout/중복코드 수정
admin_login_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>관리자 로그인 - 냥코 충전소</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#05060f;color:#f1f5f9;font-family:sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-box{background:rgba(26,26,46,0.72);border:1.5px solid rgba(168,85,247,0.2);border-radius:18px;padding:32px;width:100%;max-width:380px}
.login-box h1{font-family:Orbitron,sans-serif;font-size:1.3rem;font-weight:900;background:linear-gradient(135deg,#c084fc,#06b6d4,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:24px}
.input-wrap{position:relative;margin-bottom:14px}
input{width:100%;padding:13px 15px;border-radius:12px;border:1.5px solid rgba(168,85,247,0.18);background:rgba(255,255,255,0.03);color:#f1f5f9;outline:none;font-size:.88rem}
input:focus{border-color:#a855f7;box-shadow:0 0 0 4px rgba(168,85,247,0.12)}
.btn{display:flex;align-items:center;justify-content:center;gap:8px;padding:14px;border-radius:14px;border:none;font-size:.9rem;font-weight:800;cursor:pointer;width:100%;background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff;transition:all .25s}
.btn:hover{box-shadow:0 8px 30px rgba(168,85,247,0.4);transform:translateY(-2px)}
.error{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#ef4444;padding:10px;border-radius:10px;margin-bottom:12px;font-size:.78rem;text-align:center}
</style>
</head>
<body>
<div class="login-box">
  <h1>관리자 로그인</h1>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST" action="/admin/panel">
    <div class="input-wrap"><input type="password" name="password" placeholder="비밀번호" autocomplete="off"></div>
    <button class="btn" type="submit">로그인</button>
  </form>
</div>
</body>
</html>'''

with open('templates/admin_login.html', 'w', encoding='utf-8') as f:
    f.write(admin_login_html)
print("1. templates/admin_login.html 생성 완료")

# app.py 수정
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# admin_logout 리다이렉트 수정
content = content.replace("return redirect(url_for('admin_login'))", "return redirect(url_for('admin_panel'))")

# show_admin_dashboard 중복 코드 제거 (두 번째 블록만 제거)
marker = "    orders = load_orders()\n    deposits = load_deposits()\n    prices = get_all_prices()\n    access_keys = load_access_keys()\n\n    # 만료 여부 표시\n    now = datetime.now()\n    for k in access_keys:\n        k['is_expired'] = datetime.fromisoformat(k['expires_at']) < now\n\n    # 통계\n    total_orders = len(orders)\n    completed_orders = len([o for o in orders if o.get('status') == 'completed'])\n    pending_orders = len([o for o in orders if o.get('status') == 'pending'])\n    failed_orders = len([o for o in orders if o.get('status') == 'failed'])\n    total_revenue = sum(o.get('total_price', 0) for o in orders if o.get('status') == 'completed')\n\n    return render_template(\"admin.html\",\n        orders=orders,\n        deposits=deposits,\n        prices=prices,\n        access_keys=access_keys,\n        total_orders=total_orders,\n        completed_orders=completed_orders,\n        pending_orders=pending_orders,\n        failed_orders=failed_orders,\n        total_revenue=total_revenue,\n        key_purchase_enabled=is_key_purchase_enabled(),\n        key_prices=KEY_PRICES,\n        key_purchases=load_key_purchases()\n    )"
idx = content.find(marker)
if idx != -1:
    content = content[:idx] + content[idx + len(marker):]
    print("2. show_admin_dashboard 중복코드 제거 완료")
else:
    print("2. 중복코드 없음 (이미 정상)")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("3. app.py 수정 완료")