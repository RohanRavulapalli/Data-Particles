# app.py
# Flask app — handles file uploads, chat requests, and document management.
# Run with: python app.py
# Then open http://localhost:5000

import os
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
import storage
import retriever
import generator

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-in-production")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files are accepted"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        chunk_count = storage.store_document(filepath, filename)
        # Set this file as the active document for the current session
        session["active_document"] = filename
        session["chat_history"] = []
        return jsonify({
            "success": True,
            "filename": filename,
            "chunks": chunk_count,
            "message": f"'{filename}' indexed ({chunk_count} chunks)"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "").strip()
    filename = data.get("filename") or session.get("active_document")

    if not query:
        return jsonify({"error": "No question provided"}), 400
    if not filename:
        return jsonify({"error": "No document selected"}), 400
    if filename not in storage.list_documents():
        return jsonify({"error": f"'{filename}' not found. Please re-upload."}), 404

    try:
        context = retriever.get_context(query, filename, top_k=5)
        history = session.get("chat_history", [])
        answer = generator.generate_answer(query, context, history)

        # Append to history and cap it so we don't blow up the context window
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        session["chat_history"] = history[-20:]

        return jsonify({"answer": answer, "filename": filename})
    except EnvironmentError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/documents", methods=["GET"])
def documents():
    return jsonify({
        "documents": storage.list_documents(),
        "active": session.get("active_document")
    })


@app.route("/select", methods=["POST"])
def select_document():
    data = request.get_json()
    filename = data.get("filename")
    if filename not in storage.list_documents():
        return jsonify({"error": "Document not found"}), 404
    session["active_document"] = filename
    session["chat_history"] = []  # clear history when switching documents
    return jsonify({"success": True, "filename": filename})


@app.route("/delete", methods=["POST"])
def delete_document():
    data = request.get_json()
    filename = data.get("filename")
    storage.delete_document(filename)
    if session.get("active_document") == filename:
        session.pop("active_document", None)
        session["chat_history"] = []
    return jsonify({"success": True})


@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
