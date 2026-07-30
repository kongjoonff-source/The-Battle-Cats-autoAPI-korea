# 🚀 Render 배포 가이드 — 다른 계정으로 실행 + 5분 핑 유지

이 문서는 `battle-cats-shop` (냥코 충전소)를 **다른 Render 계정**에 배포하고, **5분마다 자동 핑**으로 슬립을 방지하는 방법을 설명합니다.

---

## 📋 사전 준비

1. **GitHub 계정** (코드를 올릴 저장소 — 기존 계정 또는 새 계정)
2. **새 Render 계정** (https://render.com — GitHub로 가입)
3. 로컬에 Git 설치

---

## 1단계: 코드를 새 GitHub 저장소에 올리기

> 기존 저장소(`kongjoonff-source/The-Battle-Cats-autoAPI-korea`)를 그대로 써도 되고, **새 계정의 새 저장소**로 올려도 됩니다. 새 계정으로 갈아서 배포하려면 아래처럼 새 저장소를 만드세요.

```bash
cd battle-cats-shop

# 기존 원격 제거 (필요한 경우)
git remote remove origin

# 새 GitHub 저장소 연결 (본인 새 계정)
git remote add origin https://github.com/<새계정아이디>/battle-cats-shop.git

git add .
git commit -m "Render 배포 준비 (keep-alive 5분 핑 추가)"
git branch -M main
git push -u origin main
```

> ⚠️ `.env` 파일과 `data/*.json`은 `.gitignore`로 인해 업로드되지 않습니다 (안전).

---

## 2단계: 새 Render 계정에서 웹 서비스 생성

### 방법 A: render.yaml Blueprint 사용 (권장)

1. **새 Render 계정**으로 로그인 (https://render.com)
2. 대시보드 → **New +** → **Blueprint**
3. 새 GitHub 계정의 저장소 `battle-cats-shop` 선택
   - 처음이면 GitHub 연결 권한 승인 필요
4. `render.yaml`이 자동으로 인식됨 → **Apply** 클릭
5. 아래 환경변수는 대시보드에서 직접 입력:
   - `PUSHBULLET_API_KEY` → 본인 Pushbullet 키
   - `ADMIN_PASSWORD` → 관리자 비밀번호
   - `SECRET_KEY` → 세션 암호화 키 (아무 긴 문자열이나 OK, 예: `python -c "import secrets; print(secrets.token_hex(32))"`)

### 방법 B: 수동 생성

1. **새 Render 계정**으로 로그인
2. 대시보드 → **New +** → **Web Service**
3. GitHub 저장소 연결
4. 설정:
   - **Name**: `nyanko-charge` (또는 원하는 이름)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`
   - **Health Check Path**: `/health`
   - **Plan**: `Free` 또는 `Starter`

---

## 3단계: 환경변수 설정

Render 대시보드 → 해당 서비스 → **Environment** 탭:

| 키 | 값 | 비고 |
|----|----|----|
| `PUSHBULLET_API_KEY` | `o.xxxx...` | 본인 키 입력 |
| `ADMIN_PASSWORD` | `********` | 관리자 비밀번호 |
| `SECRET_KEY` | `<랜덤문자열>` | 세션 암호화용 (새 계정은 새 값 권장) |
| `BANK_NAME` | `토스뱅크` | 기본값 있음 |
| `BANK_ACCOUNT` | `1908-9467-3821` | 기본값 있음 |
| `ACCOUNT_HOLDER` | `공예준` | 기본값 있음 |
| `ADMIN_ALLOWED_IPS` | `127.0.0.1,::1,localhost` | 필요시 본인 IP 추가 |
| `DATA_DIR` | `data` | 기본값 |
| `KEEP_ALIVE_PATH` | `/health` | 핑을 보낼 경로 (기본값) |
| `KEEP_ALIVE_INTERVAL` | `300` | 핑 간격(초), 300=5분 |

> 💡 `RENDER_EXTERNAL_URL`은 Render가 자동으로 주입하므로 직접 설정할 필요 없습니다.

---

## ⏱️ 5분마다 핑 (Keep-Alive) — 자동 구현됨

이 프로젝트는 **앱 내 자가 핑(self-ping)** 기능이 내장되어 있습니다. 별도 설정 없이 Render에 배포하면:

1. 앱 시작 시 `RENDER_EXTERNAL_URL` 환경변수를 읽음
2. **5분(300초)마다** `https://본인서비스.onrender.com/health`에 GET 요청
3. Render 로그에 `[KEEP-ALIVE] 핑 전송: 09:30:00 -> 200` 형태로 기록

### 핑 간격/경로 커스터마이즈

환경변수로 조절 가능:

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `KEEP_ALIVE_PATH` | `/health` | 핑을 보낼 경로 |
| `KEEP_ALIVE_INTERVAL` | `300` | 핑 간격(초) |
| `KEEP_ALIVE_URL` | (자동) | 수동 지정 시 해당 URL로 핑 (다른 서비스 핑 가능) |

### 외부 크론 서비스와 병행 (더 확실하게)

Render 무료 플랜은 자가 핑만으로 100% 보장이 어려울 수 있으므로, 외부 모니터링 서비스를 같이 쓰면 더 안정적입니다:

1. https://uptimerobot.com 가입 (무료)
2. **New Monitor** → **HTTP(s)** 선택
3. URL: `https://본인서비스.onrender.com/health`
4. 모니터링 간격: **5 minutes**
5. 저장

또는 https://cron-job.org 에서 5분마다 `https://본인서비스.onrender.com/health` 호출 설정.

---

## ⚠️ Render 무료 플랜 제약 (중요)

| 항목 | Free 플랜 | Starter 플랜 ($7/월) |
|------|----------|---------------------|
| 24시간 실행 | ❌ 15분 트래픽 없으면 슬립 | ✅ 항상 실행 |
| 월 실행 시간 | 750시간 제한 | 무제한 |
| 콜드스타트 | 있음 (~30초) | 없음 |
| 데이터 영속성 | ❌ 재배포 시 초기화 | ⚠️ 디스크 필요 |

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
2. **헬스체크 확인**: `https://nyanko-charge.onrender.com/health` → `{"status":"ok",...}` 반환
3. **핑 확인**: `https://nyanko-charge.onrender.com/ping` → `pong` 반환
4. Render 대시보드 → **Logs**에서 확인:
   - `bcsfe 초기화 완료`
   - `[KEEP-ALIVE] 활성화: https://nyanko-charge.onrender.com/health (300초 간격)`
   - 5분마다 `[KEEP-ALIVE] 핑 전송: 09:30:00 -> 200`

---

## 🔧 로컬 vs Render 차이점

| 항목 | 로컬 (Windows) | Render (Linux) |
|------|---------------|----------------|
| 실행 명령 | `python app.py` | `gunicorn app:app` |
| 포트 | 5000 | `$PORT` 환경변수 |
| bcsfe 경로 | `C:\Users\...\bcsfe` | `~/bcsfe` (자동) |
| 데이터 | `data/*.json` | `data/*.json` (디스크 권장) |
| 디버그 | `SERVER_DEBUG=true` | `false` |
| Keep-Alive | 비활성화 (로컬) | 자동 활성화 (RENDER_EXTERNAL_URL 감지) |

---

## 🆘 문제 해결

### `bcsfe 초기화 실패` 로그가 떠요
- Render Logs에서 상세 오류 확인
- `requirements.txt`에 `bcsfe`가 있는지 확인
- bcsfe 패키지가 리눅스에서 데이터 다운로드를 필요로 할 수 있음 — 첫 배포 시 1~2분 소요 정상

### 15분 후 사이트가 안 들어가져요
- 무료 플랜 슬립 상태. 접속 시 30초 대기 후 복구됨 (콜드스타트)
- Keep-Alive가 정상 작동 중인지 Logs에서 `[KEEP-ALIVE] 핑 전송` 확인
- 외부 크론(UptimeRobot)을 같이 설정하면 더 안정적

### Keep-Alive 로그가 안 보여요
- `RENDER_EXTERNAL_URL` 환경변수가 있는지 확인 (Render가 자동 주입)
- 수동으로 `KEEP_ALIVE_URL` 환경변수에 서비스 URL 설정
- `/health` 엔드포인트가 200을 반환하는지 브라우저로 직접 확인

### 주문 내역이 사라져요
- Render 재배포 시 파일 초기화 때문
- Render Disk 추가 또는 외부 DB 사용

### 다른 Render 계정으로 옮기고 싶어요
1. 새 계정으로 GitHub 저장소 연결 (1단계 참고)
2. 새 계정에서 Blueprint 또는 수동 생성 (2단계 참고)
3. 환경변수 재입력 (3단계 참고) — `SECRET_KEY`는 새 값 권장
4. 기존 계정의 서비스는 삭제하거나 그대로 두셔도 됩니다

---

## 📞 요약 체크리스트

- [ ] 새 GitHub 저장소에 코드 푸시 (또는 기존 저장소 사용)
- [ ] 새 Render 계정에서 Blueprint 또는 수동으로 웹 서비스 생성
- [ ] 환경변수 (`PUSHBULLET_API_KEY`, `ADMIN_PASSWORD`, `SECRET_KEY`) 입력
- [ ] 배포 완료 후 `/health` 접속 확인
- [ ] Logs에서 `[KEEP-ALIVE] 핑 전송` 확인 (5분마다)
- [ ] (선택) UptimeRobot 외부 핑 추가
- [ ] 24시간 유지 필요시 → **Starter 플랜($7/월) 업그레이드**
- [ ] 데이터 보존 필요시 → Render Disk 또는 외부 DB 연동