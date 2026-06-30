import os
import json
import re

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

from prompts import build_prioritization_prompt, build_what_if_prompt

# Load environment variables (for local dev; Cloud Run injects them directly)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)


def strip_markdown_json(text: str) -> str:
    """Removes ```json or ``` code fences if Gemini adds them despite instructions."""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def get_prioritized_plan(task_input: str, user_context: str = "") -> dict:
    """
    Sends the user's task dump to Gemini and returns a structured,
    prioritized plan as a Python dict.
    """
    try:
        prompt = build_prioritization_prompt(task_input, user_context)

        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(prompt)

        raw_text = response.text
        cleaned_text = strip_markdown_json(raw_text)

        try:
            parsed = json.loads(cleaned_text)
            return parsed
        except json.JSONDecodeError as json_err:
            return {
                "error": "Failed to parse Gemini response as JSON.",
                "details": str(json_err),
                "raw_response": raw_text
            }

    except Exception as api_err:
        print("GEMINI ERROR:", str(api_err))   # ADD THIS LINE
        return {
            "error": "Gemini API call failed.",
            "details": str(api_err)
        }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/prioritize", methods=["POST"])
def prioritize():
    data = request.get_json(silent=True) or {}

    task_input = data.get("task_input", "").strip()
    user_context = data.get("user_context", "").strip()

    if not task_input:
        return jsonify({"error": "task_input is required."}), 400

    result = get_prioritized_plan(task_input, user_context)

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result), 200


@app.route("/api/what-if", methods=["POST"])
def what_if():
    data = request.get_json(silent=True) or {}
    task_input = data.get("task_input", "").strip()

    if not task_input:
        return jsonify({"error": "task_input is required."}), 400

    try:
        prompt = build_what_if_prompt(task_input)
        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(prompt)
        return jsonify({"consequence": response.text}), 200
    except Exception as api_err:
        print("GEMINI WHAT-IF ERROR:", str(api_err))
        return jsonify({
            "error": "Failed to generate consequences.",
            "details": str(api_err)
        }), 500


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)