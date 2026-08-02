"""bcsfe 버전 호환성 확인"""
import zipfile
import re

# 3.6.0 확인
print("=== bcsfe 3.6.0 game_version.py ===")
z = zipfile.ZipFile(r"C:\Users\USER\Desktop\bcsfe_check\bcsfe-3.6.0-py3-none-any.whl")
content = z.read("bcsfe/core/game_version.py").decode("utf-8")
# 버전 문자열 패턴 찾기
versions = re.findall(r'"(\d+\.\d+\.\d+)"', content)
print(f"지원 버전 수: {len(versions)}")
print(f"버전 목록: {versions[:20]}")
print(f"12.5.0 포함: {'12.5.0' in versions}")
print(f"최신 버전: {versions[-5:] if versions else 'N/A'}")