# Discord Member Sync Bot

Discord 서버의 멤버 목록을 가져와 DB로 동기화하는 Python 봇입니다.
기본 동기화 대상은 Supabase이며, 필요하면 Next.js API 엔드포인트로도 전송할 수 있습니다.

## 기능

- Discord 길드의 전체 멤버 조회
- 멤버 데이터 정규화(display name, username, avatar, join date)
- Supabase `members` 테이블에 upsert (`on_conflict=discord_id`)
- 옵션으로 API (`/api/sync/userlist`) 전송 지원

## 요구사항

- Python 3.11+
- Discord Bot Token
- Discord 서버 ID (Guild ID)
- Supabase 프로젝트 (기본 모드)

## 환경변수

`.env.example`를 복사해서 `.env`를 만든 뒤 값 채우기:

```powershell
Copy-Item .env.example .env
```

### 공통

- `DISCORD_TOKEN`
- `DISCORD_GUILD_ID`
- `SYNC_TARGET` (선택, 기본값: `supabase`)

### `SYNC_TARGET=supabase`일 때

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

### `SYNC_TARGET=api`일 때

- `API_BASE_URL`
- `BOT_TOKEN`

## 설치

```powershell
cd "C:\Users\aerof\OneDrive\문서\Github workspace\bot"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 실행

중요: 이 프로젝트는 패키지 모드로 실행해야 하므로 `bot`의 상위 폴더에서 실행합니다.

```powershell
cd "C:\Users\aerof\OneDrive\문서\Github workspace"
.\bot\.venv\Scripts\python.exe -m bot.main
```

## Supabase 테이블 예시

코드는 `public.members` 테이블에 upsert 합니다.
`discord_id`는 반드시 `PRIMARY KEY` 또는 `UNIQUE`여야 합니다.

```sql
create table if not exists public.members (
  discord_id bigint primary key,
  display_name text not null,
  username text not null,
  avatar_url text,
  discord_joined_at timestamptz,
  is_active boolean not null default true,
  updated_at timestamptz not null default now()
);
```

## Discord 설정 체크리스트

- Discord Developer Portal에서 Bot의 `SERVER MEMBERS INTENT` 활성화
- 봇이 대상 서버에 초대되어 있어야 함

## 자동 실행(Windows Task Scheduler)

- Program/script:
  - `C:\Users\aerof\OneDrive\문서\Github workspace\bot\.venv\Scripts\python.exe`
- Add arguments:
  - `-m bot.main`
- Start in:
  - `C:\Users\aerof\OneDrive\문서\Github workspace`

## 빈 레포로 업로드

```powershell
cd "C:\Users\aerof\OneDrive\문서\Github workspace\bot"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<YOUR_ID>/<YOUR_REPO>.git
git push -u origin main
```

## 트러블슈팅

- `No module named 'bot'`
  - 실행 위치가 잘못된 경우입니다. `bot` 상위 폴더에서 `-m bot.main`으로 실행하세요.
- `Missing env var: ...`
  - `.env` 값 누락입니다.
- Supabase `401/403`
  - `SUPABASE_SERVICE_ROLE_KEY` 또는 URL 확인이 필요합니다.
- `getaddrinfo failed`
  - DNS/네트워크 문제입니다.
