from flask import Flask, request, jsonify
from gemini import Gemini
import os
import threading

app = Flask(__name__)

GEMINI_PSID = os.getenv("GEMINI_PSID")

if not GEMINI_PSID:
    raise RuntimeError(
        "GEMINI_PSID is not set.\n"
        "Set the Vercel environment variable GEMINI_PSID."
    )


try:
    client = Gemini(
        cookies={
            "__Secure-1PSID": GEMINI_PSID
        },
        target_cookies=[
            "__Secure-1PSID"
        ]
    )

except Exception as e:
    print("Failed to initialize Gemini:")
    print(e)
    raise


gemini_lock = threading.Lock()


def ask_gemini(prompt):

    with gemini_lock:

        try:

            response = client.generate_content(prompt)

            if response is None:
                return {
                    "success": False,
                    "error": "Gemini returned no response."
                }

            text = getattr(response, "text", None)

            if not text:
                return {
                    "success": False,
                    "error": "Gemini returned an empty response."
                }

            return {
                "success": True,
                "response": text
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }


@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "status": "online",
        "service": "Gemini Web API",
        "version": "1.0"
    })


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "status": "healthy"
    })


@app.route("/chat", methods=["GET", "POST"])
def chat():

    if request.method == "GET":

        prompt = request.args.get("prompt")

    else:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "error": "Invalid JSON body."
            }), 400

        prompt = data.get("prompt")


    if prompt is None:

        return jsonify({
            "success": False,
            "error": "Missing prompt."
        }), 400

    if not isinstance(prompt, str):

        return jsonify({
            "success": False,
            "error": "Prompt must be a string."
        }), 400

    prompt = prompt.strip()

    if not prompt:

        return jsonify({
            "success": False,
            "error": "Prompt cannot be empty."
        }), 400


    result = ask_gemini(prompt)

    if not result["success"]:

        return jsonify(result), 500

    return jsonify(result)
