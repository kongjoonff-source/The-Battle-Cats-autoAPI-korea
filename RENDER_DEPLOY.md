# 🚀 Render 배포 가이드 — 24시간 운영

이 문서는 `battle-cats-shop` (냥코 충전소)를 Render에 배포하고 24시간 내내 실행하는 방법을 설명합니다.

---

## 📋 사전 준비

1. **GitHub 계정** (코드를 올릴 저장소)
2. **Render 계정** (https://render.com — GitHub 계정으로 가입)
3. 로컬에 Git 설치

---

## 1단계: 코드를 GitHub에 올리기

프로젝트 폴더에서 다음 명령어 실행:

```bash
cd battle-cats-shop
git init
git add .
git commit -m "Render 배포 준비"
git branch -M main
git remote add origin https://github.com/<본인GitHub아이디>/battle-cats-shop.git
git push -u origin main
```

> ⚠️ `.env` 파일과 `data/*.json`은 `.gitignore`로 인해 업로드되지 않습니다 (안전).

---

## 2단계: Render에서 웹 서비스 생성

### 방법 A: render.yaml Blueprint 사용 (권장)

1. Render 대시보드 → **New +** → **Blueprint**
2. GitHub 저장소 `battle-cats-shop` 선택
3. `render.yaml`이 자동으로 인식됨 → **Apply** 클릭
4. 아래 환경변수 2개는 대시보드에서 직접 입력:
   - `PUSHBULLET_API_KEY` → 본인 Pushbullet 키
   - `ADMIN_PASSWORD` → 관리자 비밀번호

### 방법 B: 수동 생성

1. Render 대시보드 → **New +** → **Web Service**
2. GitHub 저장소 연결
3. 설정:
   - **Name**: `nyanko-charge`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`
   - **Plan**: `Free` 또는 `Starter` (24시간 운영은 Starter 필요 — 아래 참고)

---

## 3단계: 환경변수 설정

Render 대시보드 → 해당 서비스 → **Environment** 탭:

| 키 | 값 | 비고 |
|----|----|----|
| `PUSHBULLET_API_KEY` | `o.xxxx...` | 본인 키 입력 |
| `ADMIN_PASSWORD` | `********` | 관리자 비밀번호 |
| `BANK_NAME` | `토스뱅크` | 기본값 있음 |
| `BANK_ACCOUNT` | `1908-9467-3821` | 기본값 있음 |
| `ACCOUNT_HOLDER` | `공예준` | 기본값 있음 |
| `ADMIN_ALLOWED_IPS` | `127.0.0.1,::1,localhost` | 필요시 본인 IP 추가 |
| `DATA_DIR` | `data` | 기본값 |

---

## ⚠️ 24시간 내내 실행하려면? (중요)

### Render 무료 플랜의 제약

| 항목 | Free 플랜 | Starter 플랜 ($7/월) |
|------|----------|---------------------|
| 24시간 실행 | ❌ 15분 트래픽 없으면 슬립 | ✅ 항상 실행 |
| 월 실행 시간 | 750시간 제한 | 무제한 |
| 콜드스타트 | 있음 (~30초) | 없음 |
| 데이터 영속성 | ❌ 재배포 시 초기화 | ⚠️ 디스크 필요 |

### 옵션 1: Starter 플랜 사용 (가장 확실)

- 월 $7 (약 9,000원)
- 24시간 365일 항상 켜짐
- 콜드스타트 없음
- **추천** — "24시간 내내"가 필수라면 이 방법뿐

### 옵션 2: 무료 플랜 + Keep-Alive (우회 방법)

무료 플랜에서 24시간 유지를 시도하는 방법. **Render 약관상 회색지대**이며 안정성을 보장하지 않음.

**방법 A: 외부 크론 서비스로 5분마다 핑**

1. https://cron-job.org 또는 https://uptimerobot.com 가입 (무료)
2. URL에 `https://본인서비스.onrender.com/` 등록
3. 5분 간격으로 HTTP GET 요청 설정

**방법 B: 앱 내 자가 핑 (self-ping)**

`app.py`에 아래 코드 추가 (이미 추가되어 있지 않다면):

```python
import threading, time, requests, os

def keep_alive():
    while True:
        try:
            url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000")
            requests.get(url + "/", timeout=10)
            print("[KEEP-ALIVE] 핑 전송")
        except: pass
        time.sleep(300)  # 5분

if not os.environ.get("RENDER_EXTERNAL_URL") is None:
    threading.Thread(target=keep_alive, daemon=True).start()
```

> ⚠️ Render 무료 플랜은 월 750시간 제한이 있어, 한 서비스가 24시간 돌면 한 달 안에 한도 초과로 멈출 수 있습니다. 진짜 24시간이 필요하면 Starter 이상을 추천합니다.

---

## 4단계: 데이터 영속성 (주문 내역 보존)

Render 무료/Starter 플랜은 **재배포 시 파일 시스템이 초기화**됩니다. 주문 내역을 보존하려면:

### 옵션 A: Render Disk (Starter 플랜 필요)
- Render 대시보드 → 서비스 → **Disks** → 추가
- Mount path: `/opt/render/project/src/data`
- `DATA_DIR` 환경변수를 위 경로로 설정

### 옵션 B: 외부 데이터베이스 사용 (권장)
- MongoDB Atlas (무료 512MB) 또는 PostgreSQL 사용
- `app.py`의 `load_orders/save_orders`를 DB 연동으로 변경 필요
- 현재 코드는 JSON 파일 기반이므로 별도 작업 필요

---

## 5단계: 배포 확인

1. 배포 완료 후 Render가 제공하는 URL 접속:
   - `https://nyanko-charge.onrender.com`
2. 메인 페이지가 뜨는지 확인
3. `/api/items` 호출 시 JSON 반환 확인
4. Render 대시보드 → **Logs**에서 `bcsfe 초기화 완료` 로그 확인

---

## 🔧 로컬 vs Render 차이점

| 항목 | 로컬 (Windows) | Render (Linux) |
|------|---------------|----------------|
| 실행 명령 | `python app.py` | `gunicorn app:app` |
| 포트 | 5000 | `$PORT` 환경변수 |
| bcsfe 경로 | `C:\Users\...\bcsfe` | `~/bcsfe` (자동) |
| 데이터 | `data/*.json` | `data/*.json` (디스크 권장) |
| 디버그 | `SERVER_DEBUG=true` | `false` |

---

## 🆘 문제 해결

### `bcsfe 초기화 실패` 로그가 떠요
- Render Logs에서 상세 오류 확인
- `requirements.txt`에 `bcsfe`가 있는지 확인
- bcsfe 패키지가 리눅스에서 데이터 다운로드를 필요로 할 수 있음 — 첫 배포 시 1~2분 소요 정상

### 15분 후 사이트가 안 들어가져요
- 무료 플랜 슬립 상태. 접속 시 30초 대기 후 복구됨 (콜드스타트)
- 24시간 유지하려면 Starter 플랜 업그레이드

### 주문 내역이 사라져요
- Render 재배포 시 파일 초기화 때문
- Render Disk 추가 또는 외부 DB 사용

---

## 📞 요약 체크리스트

- [ ] GitHub에 코드 푸시
- [ ] Render에서 Blueprint 또는 수동으로 웹 서비스 생성
- [ ] 환경변수 (`PUSHBULLET_API_KEY`, `ADMIN_PASSWORD`) 입력
- [ ] 배포 완료 후 URL 접속 확인
- [ ] 24시간 유지 필요시 → **Starter 플랜($7/월) 업그레이드**
- [ ] 데이터 보존 필요시 → Render Disk 또는 외부 DB 연동