from flask import Flask, jsonify

app = Flask(__name__)

VERSION = "4.2.1"


@app.route("/")
def home():
    return jsonify({
        "application": "Retail Platform",
        "version": VERSION,
        "status": "running"
    })


@app.route("/health")
def health():
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

