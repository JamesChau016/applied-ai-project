"""Minimal Flask API exposing the RAG agent's discover endpoint."""

from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from .rag_agent import RAGRecommender
except ImportError:
    from rag_agent import RAGRecommender

app = Flask(__name__)
CORS(app)

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


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
