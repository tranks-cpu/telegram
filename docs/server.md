# 오라클 서버 설정 정보

## 서버 정보

- **Provider**: Oracle Cloud (Always Free Tier)
- **OS**: Rocky Linux 9 (RESF-Rocky-9-x86_64-Base-9.6)
- **Shape**: VM.Standard.E2.1.Micro (1 OCPU, 1GB RAM)
- **Public IP**: 140.245.67.6 (Ephemeral)
- **Private IP**: 10.0.0.37
- **Hostname**: tranks-network
- **SSH User**: rocky
- **Swap**: 6GB (기본 4GB + 추가 2GB)

## SSH 접속

```bash
ssh -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" rocky@140.245.67.6
```

## 프로젝트 경로

- **프로젝트**: `/home/rocky/telegram/`
- **Python**: `/usr/bin/python3.11`
- **Claude CLI**: `/usr/local/bin/claude`
- **Node.js**: v20 (`/usr/bin/node`)
- **세션 파일**: `/home/rocky/telegram/data/telegram_news.session`
- **.env**: `/home/rocky/telegram/.env`
- **Claude 인증**: `/home/rocky/.claude/.credentials.json`

## 설치된 것들

```
# Python 패키지
telethon, python-dotenv, httpx, trafilatura, playwright, lxml_html_clean

# Playwright 브라우저
~/.cache/ms-playwright/chromium_headless_shell-1208/

# Playwright 시스템 라이브러리
atk, at-spi2-atk, cups-libs, libdrm, mesa-libgbm, libXcomposite,
libXdamage, libXrandr, pango, alsa-lib, nss, libxkbcommon, libXfixes, libXext
```

## Cron 스케줄

```
30 23 * * *  (UTC 23:30 = 한국시간 08:30)
```

확인:
```bash
ssh -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" rocky@140.245.67.6 "crontab -l"
```

## 로그 확인

```bash
# 서버 접속해서
ssh -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" rocky@140.245.67.6 "tail -50 ~/telegram/data/cron.log"
```

## 수동 실행

```bash
ssh -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" rocky@140.245.67.6 "cd ~/telegram && python3.11 -m scripts.run"
```

## 코드 업데이트 (git pull)

```bash
ssh -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" rocky@140.245.67.6 "cd ~/telegram && git pull"
```

## 트러블슈팅

### 텔레그램 세션 만료
로컬에서 재인증 후 세션 파일 복사:
```bash
python3 -m scripts.auth  # 로컬에서
scp -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" data/telegram_news.session rocky@140.245.67.6:~/telegram/data/
```

### Claude CLI 인증 만료
로컬 인증 파일 복사:
```bash
scp -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" ~/.claude/.credentials.json rocky@140.245.67.6:~/.claude/
```

### Playwright 크래시 (메모리 부족)
swap 확인:
```bash
ssh -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" rocky@140.245.67.6 "free -h"
```

### .env 변경 (채널 추가 등)
로컬에서 수정 후 복사:
```bash
scp -i "/Users/tranks/Downloads/ssh-key-2026-02-13 (1).key" .env rocky@140.245.67.6:~/telegram/
```

### Public IP 변경됨 (Ephemeral)
Oracle Cloud 콘솔 → Compute → Instances → VNIC → IPv4 Addresses에서 새 IP 확인.
이 문서의 IP도 업데이트할 것.
