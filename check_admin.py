"""관리자 패널 404 원인 확인"""
from app import app
import re

with app.test_client() as client:
    # 로그인
    client.post('/admin/panel', data={'password': 'zizer731!!'})
    
    # 대시보드 접근
    r = client.get('/admin/panel/dashboard')
    print(f'/admin/panel/dashboard: {r.status_code}')
    
    if r.status_code == 200:
        html = r.data.decode('utf-8')
        # 모든 링크 확인
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        print(f'발견된 링크 수: {len(links)}')
        print('링크 목록:', links)
        
        # 액션 URL 확인
        actions = re.findall(r'action=["\']([^"\']+)["\']', html)
        print(f'발견된 액션 URL: {actions}')
        
        # 관리자 로그아웃 링크 확인
        if '/admin/logout' in html:
            print('✅ 로그아웃 링크 존재')
        else:
            print('❌ 로그아웃 링크 없음')
            
        # 아이템 목록 표시 확인
        if 'item' in html.lower() or 'product' in html.lower():
            print('✅ 아이템 관련 내용 존재')
        else:
            print('❌ 아이템 관련 내용 없음')