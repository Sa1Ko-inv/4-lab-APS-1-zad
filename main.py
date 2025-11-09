from flask import Flask, request, jsonify
import os
from urllib.parse import urlparse

try:
	from psycopg2 import connect
except Exception:
	connect = None  # type: ignore


app = Flask(__name__)


@app.route("/")
def hello():
	return "Hello, Serverless! 🚀\n", 200, {"Content-Type": "text/plain"}


@app.route("/echo", methods=["POST"])
def echo():
	data = request.get_json()
	return jsonify(
		{
			"status": "received",
			"you_sent": data,
			"length": len(str(data)) if data else 0,
		}
	)


def create_db_connection():
	database_url = os.environ.get("DATABASE_URL")
	if not database_url or connect is None:
		return None
	url = urlparse(database_url)
	return connect(
		database=url.path[1:],
		user=url.username,
		password=url.password,
		host=url.hostname,
		port=url.port,
	)


conn = create_db_connection()

if conn:
	with conn.cursor() as cur:
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS messages (
				id SERIAL PRIMARY KEY,
				content TEXT NOT NULL,
				created_at TIMESTAMP DEFAULT NOW()
			)
			"""
		)
		conn.commit()


@app.route("/save", methods=["POST"])
def save_message():
	if not conn:
		return jsonify({"error": "DB not connected"}), 500
	data = request.get_json(silent=True) or {}
	message = data.get("message", "")
	with conn.cursor() as cur:
		cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
		conn.commit()
	return jsonify({"status": "saved", "message": message})


@app.route("/messages")
def get_messages():
	if not conn:
		return jsonify({"error": "DB not connected"}), 500
	with conn.cursor() as cur:
		cur.execute(
			"SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10"
		)
		rows = cur.fetchall()
	messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
	return jsonify(messages)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000)


