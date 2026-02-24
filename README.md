# Env Variables

`DISCORD_TOKEN`
`DISCORD_GUILD_ID`
`SUPABASE_URL`
`SUPABASE_SERVICE_ROLE_KEY`
`SYNC_TARGET` -> 없으면 supabase 기본값

# 실행 순서

1. 의존성 설치(최초 1회)

```
python.exe -m pip install -r requirements.txt
```

2. 실행 (이 프로젝트는 패키지 모드로 실행해야 함)
   python.exe -m bot.main
