import os
from flask import Flask, jsonify

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "4.2.0")
FORCE_HEALTH_FAIL = os.getenv("FORCE_HEALTH_FAIL", "false").lower() == "true"


@app.route("/")
def home():
    return jsonify({
        "application": "Retail Platform",
        "version": VERSION,
        "status": "running"
    })


@app.route("/health")
def health():
    if FORCE_HEALTH_FAIL:
        return jsonify({
            "status": "unhealthy",
            "version": VERSION,
            "reason": "Failure injection enabled"
        }), 500

    return jsonify({
        "status": "healthy",
        "version": VERSION
    }), 200


@app.route("/payment")
def payment():
    return jsonify({
        "payment_status": "success",
        "message": "Payment processed successfully",
        "version": VERSION
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)