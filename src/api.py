"""Minimal Flask API exposing the RAG agent's discover endpoint."""

import json
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from .rag_agent import RAGRecommender
except ImportError:
    from rag_agent import RAGRecommender

app = Flask(__name__)
CORS(app)

ROOT_DIR = Path(__file__).resolve().parents[1]
PLAYLIST_PATH = ROOT_DIR / "data" / "playlist.json"

# Lazy-init: the model loads on first request so startup stays fast.
_recommender = None


def _get_recommender() -> RAGRecommender:
    global _recommender
    if _recommender is None:
        print("[API] Loading RAG agent (first request — embedding model will be downloaded)...")
        _recommender = RAGRecommender()
    return _recommender


@app.route("/api/discover", methods=["POST"])
def discover():
    """Discover new songs using the RAG agent.

    Expects JSON body: { "playlist": [ { title, artist, genre, ... }, ... ] }
    Returns JSON:      { "recommendations": [...], "overall_explanation": "..." }
    """
    body = request.get_json(silent=True) or {}
    playlist = body.get("playlist", [])

    if not playlist:
        return jsonify({"error": "playlist is required and must be non-empty"}), 400

    k = body.get("k", 10)
    recommender = _get_recommender()
    result = recommender.discover(playlist, k=k)
    return jsonify(result)


def _read_playlist_file():
    if not PLAYLIST_PATH.exists():
        return []
    try:
        with PLAYLIST_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_playlist_file(playlist):
    PLAYLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = PLAYLIST_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(playlist, handle, indent=2)
        handle.write("\n")
    tmp_path.replace(PLAYLIST_PATH)


@app.route("/api/playlist", methods=["GET"])
def get_playlist():
    return jsonify({"playlist": _read_playlist_file()})


@app.route("/api/playlist", methods=["POST"])
def save_playlist():
    body = request.get_json(silent=True) or {}
    playlist = body.get("playlist", [])
    if not isinstance(playlist, list):
        return jsonify({"error": "playlist must be a list"}), 400
    _write_playlist_file(playlist)
    return jsonify({"status": "ok", "count": len(playlist)})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=True, use_reloader=False)
