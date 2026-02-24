# Discord Member Sync Bot

Discord 서버 멤버 목록을 조회해 외부 시스템으로 동기화하는 Python 봇입니다.
기본 동기화 대상은 Supabase이고, 필요하면 API 엔드포인트로도 전송할 수 있습니다.

## 기능

- Discord 길드 전체 멤버 조회
- 멤버 데이터 정규화(display name, username, avatar, join date)
- Supabase `members` 테이블 비교 동기화 (`discord_id` 기준)
- 변경/신규 멤버만 upsert, 누락 멤버는 `is_active=false` 처리
- 기존에 `is_active=false`인 멤버는 재동기화 시에도 `false` 유지
- 옵션으로 API (`/api/sync/userlist`) 전송

## 요구사항

- Python 3.11+
- Discord Bot Token
- Discord Guild ID
- Supabase 프로젝트 (기본 모드)

## 빠른 실행 (Windows PowerShell)

중요: 패키지 실행을 위해 **`Discord_User_Bot` 폴더의 상위 폴더**에서 실행해야 합니다.

### 1) 가상환경 생성 및 의존성 설치

```powershell
python -m venv .\Discord_User_Bot\.venv
.\Discord_User_Bot\.venv\Scripts\python.exe -m pip install -r .\Discord_User_Bot\requirements.txt
```

### 2) `.env` 설정

`Discord_User_Bot/.env` 파일을 만들고 값을 채웁니다.

```env
# Common
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=123456789012345678
SYNC_TARGET=supabase

# For SYNC_TARGET=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# For SYNC_TARGET=api
API_BASE_URL=https://your-api-domain.com
BOT_TOKEN=your_bot_token
```

### 3) 실행

```powershell
.\Discord_User_Bot\.venv\Scripts\python.exe -m Discord_User_Bot.main
```

## Supabase 테이블 예시

`public.members` 테이블에 upsert 합니다.
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

## 동기화 규칙 (Supabase 모드)

- 신규 멤버: insert (`is_active=true`)
- 기존 멤버: 필드가 바뀐 경우만 update
- 기존 `is_active=false` 멤버: 상태를 `false`로 유지(자동 재활성화하지 않음)
- 이번 수집 목록에 없는 기존 활성 멤버(`is_active=true`): `is_active=false`로 비활성화

## Discord 설정 체크리스트

- Discord Developer Portal에서 Bot의 `SERVER MEMBERS INTENT` 활성화
- 봇이 대상 서버에 초대되어 있어야 함
- `.env`의 `DISCORD_GUILD_ID`가 봇이 들어가 있는 서버 ID와 일치해야 함

## 트러블슈팅

- `No module named 'bot'`
  - 이전 문서의 구버전 실행 명령입니다. `-m Discord_User_Bot.main`을 사용하세요.
- `discord.errors.NotFound: 404 ... Unknown Guild`
  - `DISCORD_GUILD_ID`가 잘못되었거나, 봇이 해당 서버에 초대되지 않았습니다.
- `Supabase sync failed: 401 ... row-level security policy`
  - `SUPABASE_SERVICE_ROLE_KEY`에 anon 키가 들어간 경우입니다.
  - Supabase Dashboard > Project Settings > API의 **service_role key**로 교체하세요.
- `Missing env var: ...`
  - `.env` 값 누락입니다.
- `getaddrinfo failed`
  - DNS/네트워크 문제입니다.
