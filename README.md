# Telegram Crypto News Aggregator

크립토 관련 텔레그램 채널들의 콘텐츠를 자동 수집 → 크롤링 → Claude로 요약 → 내 채널에 전송하는 파이프라인.

## 파이프라인

```
소스 채널 읽기 (Telethon)
  → URL 추출 + 메시지 텍스트 수집
    → 크롤링 (Twitter: Playwright / Article: HTTPX+Trafilatura)
      → Claude CLI로 요약 생성
        → 내 텔레그램 채널로 전송
```

## 설정

1. https://my.telegram.org/apps 에서 API credentials 발급
2. `.env` 작성:
```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef...
TELEGRAM_PHONE=+821012345678
SOURCE_CHANNELS=channel1,channel2
OUTPUT_CHANNEL=my_channel
```
3. 의존성 설치:
```bash
pip install -e .
playwright install chromium
```
4. 텔레그램 인증 (최초 1회):
```bash
python -m scripts.auth
```

## 사용법

```bash
# 수동 실행
python -m scripts.run

# 스케줄 등록 (매일 08:30)
cp com.tranks.telegram-news.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.tranks.telegram-news.plist

# 스케줄 해제
launchctl unload ~/Library/LaunchAgents/com.tranks.telegram-news.plist
```

## 테스트

```bash
# 크롤링 테스트
python -m scripts.test_crawl https://x.com/someone/status/123

# 채널 읽기 테스트
python -m scripts.test_read channel_name 24
```

## 구조

```
src/
├── main.py               # 파이프라인 오케스트레이터
├── config.py             # 환경변수 설정
├── state.py              # 실행 상태 관리
├── telegram_reader.py    # 채널 메시지 읽기
├── link_extractor.py     # URL/텍스트 추출
├── crawlers/
│   ├── article.py        # HTTPX + Trafilatura
│   ├── twitter.py        # Playwright
│   └── router.py         # 크롤러 라우팅
├── summarizer.py         # Claude CLI 호출
└── telegram_sender.py    # 요약 전송
```
