import requests
from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Slack Bot Token
SLACK_BOT_TOKEN = 'xoxb-4623672403523-8417666825604-gQ3S1ruJ5Z0JWVgwqHVAXaBa'
SLACK_HEADERS = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

# 한국 시간대 설정 (KST)
KST = timezone(timedelta(hours=9))

# Slack 이벤트 리스너 활성화 여부
event_listener_active = False

# 감지할 리마인더 메시지
TARGET_MESSAGE = "데일리를 작성해주세요(Condition/한 일/할 일/Blocker)"

# 자동 댓글 내용
AUTO_REPLY_TEXT = """
[Condition]
- 

[한 일]
- 

[할 일]
- 

[Blocker]
- 
"""

def enable_event_listener():
    """이벤트 리스너 활성화"""
    global event_listener_active
    event_listener_active = True
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"✅ [{now}] 이벤트 리스너 활성화 (이제 Slack 이벤트를 처리합니다)")

def disable_event_listener():
    """이벤트 리스너 비활성화"""
    global event_listener_active
    event_listener_active = False
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚫 [{now}] 이벤트 리스너 비활성화 (이제 Slack 이벤트를 무시합니다)")

# APScheduler 인스턴스 생성
scheduler = BackgroundScheduler(timezone="Asia/Seoul")
scheduler.add_job(enable_event_listener, 'cron', hour=15, minute=0, timezone="Asia/Seoul")
scheduler.add_job(disable_event_listener, 'cron', hour=17, minute=5, timezone="Asia/Seoul")

try:
    scheduler.start()
    print("✅ APScheduler 스케줄러 시작됨")
except Exception as e:
    print(f"⚠️ 스케줄러 시작 오류: {e}")

@app.route("/", methods=["GET"])
def home():
    return "Slack Bot is running!", 200

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Slack URL 검증 요청 처리 (앱 등록 과정)
    if data.get("type") == "url_verification":
        challenge_response = {"challenge": data["challenge"]}
        print(f"✅ [{now}] Slack URL 검증 성공! 응답: {challenge_response}")  # 디버깅 로그 추가
        return jsonify(challenge_response), 200  # 올바른 JSON 형식으로 반환

    # ✅ 현재 이벤트 리스너가 비활성화된 경우 즉시 반환
    if not event_listener_active:
        print(f"⏳ [{now}] 현재 이벤트 리스너가 비활성화 상태. 이벤트를 무시합니다.")
        return jsonify({"status": "ignored", "reason": "event_listener_disabled"}), 200

    print(f"🔵 [{now}] 받은 데이터: {data}")  # Slack 이벤트 데이터 출력

    # ✅ 메시지 이벤트 감지
    event = data.get("event", {})
    if event.get("type") == "message":
        text = event.get("text", "").strip()
        channel = event.get("channel")
        ts = event.get("ts")
        bot_id = event.get("bot_id")  # Slackbot 메시지 여부 확인

        print(f"🔍 [디버깅] bot_id: {bot_id}, text: {text}")

        # ✅ Slackbot이 보낸 메시지이고, TARGET_MESSAGE가 포함된 경우 자동 댓글 추가
        if bot_id and TARGET_MESSAGE in text:
            print(f"🟢 [{now}] 리마인더 감지됨! 자동 댓글 추가")
            post_reply(channel, ts)

    return jsonify({"status": "ok"})

def post_reply(channel, thread_ts):
    """지정된 메시지에 자동으로 댓글 추가"""
    url = "https://slack.com/api/chat.postMessage"
    data = {
        "channel": channel,
        "thread_ts": thread_ts,
        "text": AUTO_REPLY_TEXT  # 댓글 내용
    }
    response = requests.post(url, headers=SLACK_HEADERS, json=data)
    print(f"🔵 댓글 응답 결과: {response.json()}")  # API 응답 로그 추가
    return response.json()

if __name__ == "__main__":
    print("🚀 Flask 서버 시작...")
    app.run(host="0.0.0.0", port=3000)
