"""
AI Scam Detection Chatbot - Backend Server (Python Flask)
Supports Text Messages and Screenshot Image Uploads for AI scam detection.
"""

import os
import base64
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

load_dotenv()

from modules.nlp_processor import NLPProcessor
from modules.dataset_examples import get_example_prompts
from modules.gemini_analyzer import GeminiScamAnalyzer
from modules.db_manager import DatabaseManager

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

if CORS_AVAILABLE:
    CORS(app)
else:
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

nlp_processor = NLPProcessor()
gemini_analyzer = GeminiScamAnalyzer()
db_manager = DatabaseManager()

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def is_allowed_image(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
@app.route("/api/analyze", methods=["POST"])
def analyze_chat_message():
    try:
        user_message = ""
        image_bytes = None
        mime_type = "image/png"

        # 1. Check for Multipart Screenshot Upload
        if request.files and "image" in request.files:
            file = request.files["image"]
            if file and file.filename and is_allowed_image(file.filename):
                image_bytes = file.read()
                mime_type = file.mimetype or "image/png"
            user_message = (request.form.get("message") or request.form.get("user_input") or "").strip()

        # 2. Check for JSON Payload
        elif request.is_json:
            data = request.get_json(silent=True) or {}
            user_message = (data.get("message") or data.get("user_input") or "").strip()
            
            b64_img = data.get("image_base64") or data.get("image")
            if b64_img and isinstance(b64_img, str) and b64_img.startswith("data:image"):
                try:
                    header, encoded = b64_img.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                    image_bytes = base64.b64decode(encoded)
                except Exception:
                    pass

        if not user_message and not image_bytes:
            return jsonify({
                "success": False,
                "error": "Please enter a message or upload a screenshot to analyze."
            }), 400

        nlp_context = nlp_processor.process(user_message) if user_message else {}

        if image_bytes:
            analysis_result = gemini_analyzer.analyze_multimodal(
                image_bytes=image_bytes,
                mime_type=mime_type,
                user_caption=user_message,
                nlp_context=nlp_context
            )
            logged_input = user_message if user_message else "[Uploaded Screenshot Image]"
        else:
            analysis_result = gemini_analyzer.analyze(user_message, nlp_context)
            logged_input = user_message

        try:
            db_manager.save_analysis(logged_input, analysis_result)
        except Exception:
            pass

        return jsonify({
            "success": True,
            "data": analysis_result
        })

    except Exception as e:
        app.logger.error(f"Error in /api/chat: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while analyzing the content. Please try again."
        }), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        limit = min(int(request.args.get("limit", 15)), 50)
        history = db_manager.get_history(limit=limit)
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        return jsonify({"success": False, "error": "Unable to load scan history."}), 500


@app.route("/api/examples", methods=["GET"])
def get_examples():
    return jsonify({
        "success": True,
        "examples": get_example_prompts()
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    has_gemini = bool(
        os.getenv("GEMINI_API_KEY") 
        and os.getenv("GEMINI_API_KEY") not in ["your_key", "your_gemini_api_key_here", ""]
    )
    has_supabase = bool(
        os.getenv("SUPABASE_URL") 
        and not os.getenv("SUPABASE_URL").startswith("https://your-project")
        and os.getenv("SUPABASE_KEY") not in ["your_key", ""]
    )
    
    return jsonify({
        "status": "healthy",
        "gemini_configured": has_gemini,
        "supabase_configured": has_supabase,
        "mode": "Gemini 1.5 Flash (Multimodal & Text)" if has_gemini else "Rule-based Analyzer (Set GEMINI_API_KEY to activate AI)"
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    print("================================================================")
    print(f"  AI Scam Detection Chatbot Server is Starting")
    print(f"  Open in Browser: http://localhost:{port}")
    print("================================================================")
    app.run(host="0.0.0.0", port=port, debug=debug)