import os

# admin.html 작성
admin = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>관리자 패널</title>
<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#000010;--surface:rgba(20,20,40,0.7);--surface2:rgba(30,30,60,0.6);--primary:#7c3aed;--primary2:#a855f7;--accent:#06b6d4;--success:#10b981;--danger:#ef4444;--text:#f1f5f9;--sub:#94a3b8;--border:rgba(168,85,247,0.25);--radius:16px}
body{background:var(--bg);color:var(--text);font-family:'Exo 2',sans-serif;min-height:100vh;padding:16px}
.container{max-width:1200px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:18px 24px;margin-bottom:20px;background:linear-gradient(135deg,rgba(124,58,237,0.2),rgba(6,182,212,0.15));backdrop-filter:blur(24px);border:1.5px solid rgba(168,85,247,0.4);border-radius:var(--radius);box-shadow:0 8px 40px rgba(124,58,237,0.3)}
.header h1{font-size:1.3rem;font-weight:900;background:linear-gradient(135deg,#fff,var(--primary2),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header a{color:var(--sub);text-decoration:none;font-size:.85rem;padding:8px 16px;border:1.5px solid var(--border);border-radius:10px;transition:all .2s}
.header a:hover{color:var(--text);border-color:var(--primary2)}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.stat-card{background:var(--surface);backdrop-filter:blur(20px);border:1.5px solid var(--border);border-radius:var(--radius);padding:16px;text-align:center}
.stat-card .num{font-size:1.8rem;font-weight:900;color:var(--accent)}
.stat-card .label{font-size:.75rem;color:var(--sub);margin-top:4px}
.card{background:var(--surface);backdrop-filter:blur(20px);border:1.5px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:16px}
.card-title{font-size:1.05rem;font-weight:800;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center}
.card-title i{color:var(--accent);margin-right:8px}
.btn{padding:10px 18px;border-radius:10px;border:none;font-weight:700;cursor:pointer;font-family:'Exo 2',sans-serif;font-size:.82rem;transition:all .2s}
.btn:active{transform:scale(.96)}
.btn-success{background:var(--success);color:#fff}
.btn-danger{background:var(--danger);color:#fff}
.btn-primary{background:var(--primary2);color:#fff}
.btn-mini{padding:6px 12px;font-size:.72rem;border-radius:8px;border:1.5px solid var(--border);background:var(--surface2);color:var(--text);cursor:pointer}
.btn-mini:hover{border-color:var(--primary2)}
input,select{padding:10px 14px;border-radius:10px;border:2px solid var(--border);background:rgba(0,0,0,0.3);color:var(--text);outline:none;font-size:.82rem;font-family:'Exo 2',sans-serif}
input:focus{border-color:var(--accent)}
table{width:100%;border-collapse:collapse;font-size:.8rem}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--sub);font-weight:700;font-size:.72rem;text-transform:uppercase;letter-spacing:1px}
tr:hover{background:rgba(168,85,247,0.05)}
.badge{padding:3px 10px;border-radius:20px;font-size:.68rem;font-weight:700}
.badge.success{background:rgba(16,185,129,0.15);color:var(--success)}
.badge.danger{background:rgba(239,68,68,0.15);color:var(--danger)}
.badge.warning{background:rgba(251,191,36,0.15);color:#fbbf24}
.log-entry{padding:10px 14px;border-bottom:1px solid var(--border);font-size:.8rem;display:flex;gap:10px;align-items:flex-start}
.log-entry:hover{background:rgba(168,85,247,0.05)}
.log-time{color:var(--sub);font-size:.72rem;white-space:nowrap;min-width:140px}
.log-cat{font-weight:700;min-width:80px}
.log-msg{flex:1}
.log-detail{color:var(--sub);font-size:.72rem;margin-top:2px}
.log-delete{background:none;border:none;color:var(--danger);cursor:pointer;font-size:.9rem;opacity:.5}
.log-delete:hover{opacity:1}
.search-box{display:flex;gap:8px;margin-bottom:12px}
.search-box input{flex:1}
.scroll-box{max-height:500px;overflow-y:auto;border:1px solid var(--border);border-radius:10px}
.scroll-box::-webkit-scrollbar{width:6px}
.scroll-box::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.form-row{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.form-row input,.form-row select{flex:1;min-width:120px}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🐱 관리자 패널</h1>
    <a href="/admin/logout">로그아웃</a>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="num">{{ total_orders }}</div><div class="label">총 주문</div></div>
    <div class="stat-card"><div class="num" style="color:var(--success)">{{ completed_orders }}</div><div class="label">완료</div></div>
    <div class="stat-card"><div class="num" style="color:#fbbf24">{{ pending_orders }}</div><div class="label">대기/처리중</div></div>
    <div class="stat-card"><div class="num" style="color:var(--danger)">{{ failed_orders }}</div><div class="label">실패</div></div>
  </div>
  <div class="card">
    <div class="card-title"><span><i class="fas fa-ticket"></i>쿠폰 코드 관리</span><button class="btn-mini" onclick="toggleKeyPurchase()" id="toggleKeyBtn">{{ '활성화' if key_purchase_enabled else '비활성화' }}됨</button></div>
    <div class="form-row">
      <input type="text" id="couponCode" placeholder="쿠폰 코드 (예: NYANKO2024)">
      <select id="couponDays"><option value="1">1일</option><option value="3">3일</option><option value="7">7일</option><option value="30">30일</option></select>
      <input type="text" id="couponLabel" placeholder="라벨 (선택)" style="max-width:150px">
      <button class="btn btn-primary" onclick="createCoupon()">생성</button>
    </div>
    <div id="couponList" class="scroll-box" style="max-height:300px">불러오는 중...</div>
  </div>
  <div class="card">
    <div class="card-title"><span><i class="fas fa-list"></i>활동 로그</span><button class="btn btn-danger" onclick="clearLogs()" style="font-size:.72rem;padding:6px 12px">전체 삭제</button></div>
    <div class="search-box"><input type="text" id="logSearch" placeholder="검색어 입력 (이름, 주문ID, 카테고리 등)" oninput="filterLogs()"></div>
    <div id="logList" class="scroll-box">불러오는 중...</div>
  </div>
  <div class="card">
    <div class="card-title"><span><i class="fas fa-key"></i>접근 키 관리</span><button class="btn btn-primary" onclick="generateKey()" style="font-size:.72rem;padding:6px 12px">키 생성</button></div>
    <div id="keyList" class="scroll-box" style="max-height:300px">불러오는 중...</div>
  </div>
  <div class="card">
    <div class="card-title"><span><i class="fas fa-shopping-cart"></i>주문 내역</span></div>
    <div class="scroll-box" style="max-height:400px">
      <table><thead><tr><th>주문ID</th><th>이름</th><th>상태</th><th>아이템</th><th>시간</th></tr></thead><tbody>
      {% for o in orders|reverse %}
      <tr><td>{{ o.id }}</td><td>{{ o.buyer_name }}</td><td><span class="badge {{ 'success' if o.status=='completed' else 'danger' if o.status=='failed' else 'warning' }}">{{ o.status }}</span></td><td style="font-size:.72rem">{{ o.items|map(attribute='name')|join(', ') }}</td><td style="font-size:.72rem;color:var(--sub)">{{ o.created_at[:19] }}</td></tr>
      {% endfor %}
      </tbody></table>
    </div>
  </div>
</div>
<script>
function loadCoupons(){fetch('/api/admin/coupons/list').then(r=>r.json()).then(data=>{const l=document.getElementById('couponList');if(!data.length){l.innerHTML='<p style="color:var(--sub);text-align:center;padding:20px">쿠폰이 없습니다</p>';return;}l.innerHTML='<table><thead><tr><th>코드</th><th>기간</th><th>상태</th><th>라벨</th><th>생성일</th><th></th></tr></thead><tbody>'+data.map(c=>'<tr><td style="font-weight:700;color:var(--accent)">'+c.code+'</td><td>'+c.days+'일</td><td><span class="badge '+(c.used?'danger':'success')+'">'+(c.used?'사용됨':'미사용')+'</span></td><td style="font-size:.72rem">'+(c.label||'-')+'</td><td style="font-size:.72rem;color:var(--sub)">'+(c.created_at?c.created_at.slice(0,19):'-')+'</td><td><button class="btn btn-danger" style="padding:4px 10px;font-size:.7rem" onclick="deleteCoupon(\\''+c.code+'\\')">삭제</button></td></tr>').join('')+'</tbody></table>';});}
function createCoupon(){const code=document.getElementById('couponCode').value.trim();const days=document.getElementById('couponDays').value;const label=document.getElementById('couponLabel').value.trim();if(!code){alert('코드를 입력하세요');return;}fetch('/api/admin/coupons/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,days:parseInt(days),label})}).then(r=>r.json()).then(data=>{if(data.success){alert('쿠폰 생성 완료!');document.getElementById('couponCode').value='';document.getElementById('couponLabel').value='';loadCoupons();}else{alert(data.error||'생성 실패');}});}
function deleteCoupon(code){if(!confirm('쿠폰을 삭제하시겠습니까?'))return;fetch('/api/admin/coupons/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code})}).then(r=>r.json()).then(data=>{if(data.success)loadCoupons();});}
let allLogs=[];function loadLogs(){fetch('/api/admin/logs').then(r=>r.json()).then(data=>{allLogs=data;renderLogs(data);});}
function renderLogs(logs){const l=document.getElementById('logList');if(!logs.length){l.innerHTML='<p style="color:var(--sub);text-align:center;padding:20px">로그가 없습니다</p>';return;}l.innerHTML=logs.slice().reverse().map(lg=>'<div class="log-entry"><div class="log-time">'+(lg.timestamp?lg.timestamp.slice(0,19):'-')+'</div><div class="log-cat" style="color:'+getCatColor(lg.category)+'">'+lg.category+'</div><div class="log-msg">'+lg.message+(lg.detail?'<div class="log-detail">'+lg.detail+'</div>':'')+'</div><button class="log-delete" onclick="deleteLog(\\''+lg.id+'\\')"><i class="fas fa-times"></i></button></div>').join('');}
function getCatColor(cat){const c={'충전 완료':'var(--success)','충전 실패':'var(--danger)','충전 시작':'#fbbf24','충전 오류':'var(--danger)','쿠폰 생성':'var(--accent)','쿠폰 사용':'var(--primary2)','쿠폰 삭제':'var(--danger)','키 생성':'var(--accent)','키 사용':'var(--primary2)','키 삭제':'var(--danger)','주문 생성':'#fbbf24','관리자':'var(--primary2)','설정':'var(--sub)','로그':'var(--danger)'};return c[cat]||'var(--text)';}
function filterLogs(){const q=document.getElementById('logSearch').value.toLowerCase().trim();if(!q){renderLogs(allLogs);return;}renderLogs(allLogs.filter(l=>(l.category+l.message+l.detail).toLowerCase().includes(q)));}
function deleteLog(id){fetch('/api/admin/logs/'+id+'/delete',{method:'POST'}).then(r=>r.json()).then(data=>{if(data.success)loadLogs();});}
function clearLogs(){if(!confirm('모든 로그를 삭제하시겠습니까?'))return;fetch('/api/admin/logs/clear',{method:'POST'}).then(r=>r.json()).then(data=>{if(data.success)loadLogs();});}
function loadKeys(){fetch('/api/admin/keys').then(r=>r.json()).then(data=>{const l=document.getElementById('keyList');if(!data.length){l.innerHTML='<p style="color:var(--sub);text-align:center;padding:20px">키가 없습니다</p>';return;}l.innerHTML='<table><thead><tr><th>키</th><th>만료</th><th>상태</th><th>라벨</th><th></th></tr></thead><tbody>'+data.map(k=>'<tr><td style="font-size:.72rem;font-family:monospace">'+k.key.slice(0,16)+'...</td><td style="font-size:.72rem">'+(k.expires_at?k.expires_at.slice(0,19):'-')+'</td><td><span class="badge '+(k.is_expired?'danger':'success')+'">'+(k.is_expired?'만료':'유효')+'</span></td><td style="font-size:.72rem">'+(k.label||'-')+'</td><td><button class="btn btn-danger" style="padding:4px 10px;font-size:.7rem" onclick="deleteKey(\\''+k.key+'\\')">삭제</button></td></tr>').join('')+'</tbody></table>';});}
function generateKey(){const days=prompt('키 기간(일):','1');if(!days)return;const label=prompt('라벨 (선택):','')||'';fetch('/api/admin/keys/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({days:parseInt(days),label})}).then(r=>r.json()).then(data=>{if(data.success){alert('키 생성 완료!\\n'+data.key.key);loadKeys();}});}
function deleteKey(key){if(!confirm('키를 삭제하시겠습니까?'))return;fetch('/api/admin/keys/'+key+'/delete',{method:'POST'}).then(r=>r.json()).then(data=>{if(data.success)loadKeys();});}
function toggleKeyPurchase(){fetch('/api/admin/key-purchase/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:!{{ key_purchase_enabled|lower }}})}).then(r=>r.json()).then(data=>{if(data.success)location.reload();});}
loadCoupons();loadLogs();loadKeys();
</script>
</body>
</html>'''

with open(r'C:\Users\USER\Desktop\battle-cats-shop\templates\admin.html', 'w', encoding='utf-8') as f:
    f.write(admin)
print('admin.html OK')

# index.html 수정
with open(r'C:\Users\USER\Desktop\battle-cats-shop\templates\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    '<div class="card-title"><i class="fas fa-key"></i>계정 정보</div>',
    '<div class="card-title"><i class="fas fa-user"></i>이름 & 계정 정보</div><div class="input-wrap"><input type="text" id="buyerName" placeholder="이름 (닉네임)"><i class="fas fa-user input-icon"></i></div><div style="font-size:.72rem;color:var(--accent);margin:-4px 0 12px 4px;"><i class="fas fa-info-circle"></i> 새 기기이전코드를 발급하다가 오류가 나면 적힌 이름으로 확인할 수 있습니다!</div>'
)

c = c.replace(
    "if (!t||!c){toast",
    "const n=document.getElementById('buyerName').value.trim();if(!n){toast('입력 오류','이름을 입력하세요.','var(--danger)');return;}if (!t||!c){toast"
)

c = c.replace("buyer_name:'user'", "buyer_name:n")

with open(r'C:\Users\USER\Desktop\battle-cats-shop\templates\index.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('index.html OK')