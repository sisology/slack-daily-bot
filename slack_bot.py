import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Slack Bot Token
SLACK_BOT_TOKEN = 'xoxb-4623672403523-8417666825604-gQ3S1ruJ5Z0JWVgwqHVAXaBa'
SLACK_HEADERS = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

# 감지할 리마인더 메시지
TARGET_MESSAGE = "리마인더: 데일리를 작성해주세요(Condition/한 일/할 일/Blocker)"

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

@app.route("/", methods=["GET"])
def home():
    return "Slack Bot is running!", 200

def post_reply(channel, thread_ts):
    """지정된 메시지에 자동으로 댓글 추가"""
    url = "https://slack.com/api/chat.postMessage"
    data = {
        "channel": channel,
        "thread_ts": thread_ts,
        "text": AUTO_REPLY_TEXT  # 댓글 내용 변경
    }
    response = requests.post(url, headers=SLACK_HEADERS, json=data)
    print(f"🔵 댓글 응답 결과: {response.json()}")  # API 응답 로그 추가
    return response.json()

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()
    print(f"🔵 받은 데이터: {data}")  # Slack 이벤트 데이터 출력

    # ✅ Slack Challenge 요청 처리
    if "challenge" in data:
        return data["challenge"], 200, {"Content-Type": "text/plain"}

    # ✅ 메시지 이벤트 감지
    event = data.get("event", {})
    if event.get("type") == "message":
        text = event.get("text", "").strip()
        channel = event.get("channel")
        ts = event.get("ts")
        bot_id = event.get("bot_id")

        print(f"🔵 감지된 메시지: {text}, bot_id: {bot_id}, channel: {channel}, ts: {ts}")

        # ✅ bot_id가 없고, 메시지가 정확히 일치하는 경우에만 댓글 달기
        if bot_id is None and text == TARGET_MESSAGE:
            print("🟢 리마인더 메시지 감지됨! 자동 댓글 추가")
            post_reply(channel, ts)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
