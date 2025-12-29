from flask import Flask, Response
import time

app = Flask(__name__)

@app.route("/")
def home():
    return "Server is running"

@app.route("/sse")
def sse():
    def event_stream():
        # 1️⃣ 첫 메시지
        yield "data: SSE connection established\n\n"
        time.sleep(1)

        # 2️⃣ 실제 보낼 데이터
        yield "data: hello from server\n\n"
        time.sleep(1)

        # 3️⃣ 🔴 반드시 종료 이벤트 보내기
        yield "event: end\ndata: done\n\n"

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
