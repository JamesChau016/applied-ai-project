import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { discoverSongs } from "../engine/discover.js";
import SongCard from "../components/SongCard.jsx";
import VinylSpinner from "../components/VinylSpinner.jsx";

export default function DiscoverView({
  playlistSongs,
  playlistIds,
  onToggleSave,
  onSaveDiscoveredSong,
}) {
  const [state, setState] = useState("idle"); // idle | loading | done | error
  const [results, setResults] = useState([]);
  const [explanation, setExplanation] = useState("");
  const [error, setError] = useState("");

  const handleDiscover = useCallback(async () => {
    setState("loading");
    setResults([]);
    setError("");
    try {
      const { recommendations, explanation: exp } =
        await discoverSongs(playlistSongs, 10);
      if (recommendations.length === 0) {
        setError(
          "No new songs found. Try adding more songs to your playlist for better results.",
        );
        setState("error");
      } else {
        setResults(recommendations);
        setExplanation(exp);
        setState("done");
      }
    } catch (err) {
      console.error("Discover error:", err);
      setError(
        err.message ||
          "Something went wrong while fetching songs. Make sure the backend is running (python -m src.api).",
      );
      setState("error");
    }
  }, [playlistSongs]);

  const handleToggleSave = useCallback(
    (id) => {
      const song = results.find((r) => r.song.id === id)?.song;
      if (song && onSaveDiscoveredSong) {
        onSaveDiscoveredSong(song);
      }
      onToggleSave(id);
    },
    [results, onToggleSave, onSaveDiscoveredSong],
  );

  return (
    <motion.section
      className="catalog-section"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.35 }}
    >
      <h2 className="section-title">Discover New Music</h2>

      {state === "idle" && (
        <motion.div
          className="discover-prompt"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <p className="discover-desc">
            The RAG agent will analyze your playlist, search TheAudioDB for
            songs across related artists and genres, then rank them using
            semantic similarity (all-MiniLM-L6-v2 embeddings).
          </p>
          {playlistSongs.length === 0 ? (
            <p className="discover-empty">
              Save some songs to your playlist first, then come back to discover
              new music.
            </p>
          ) : (
            <>
              <p className="discover-stats">
                Based on <strong>{playlistSongs.length}</strong> songs from{" "}
                <strong>
                  {new Set(playlistSongs.map((s) => s.artist)).size}
                </strong>{" "}
                artists in your playlist
              </p>
              <button className="cta" onClick={handleDiscover}>
                Discover New Songs
              </button>
            </>
          )}
        </motion.div>
      )}

      {state === "loading" && (
        <motion.div
          className="discover-loading"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <VinylSpinner spinning />
          <p className="discover-loading-text">
            RAG agent is searching and ranking songs...
          </p>
          <p className="discover-loading-progress">
            This may take a moment on the first run while the embedding model
            loads.
          </p>
        </motion.div>
      )}

      {state === "error" && (
        <motion.div
          className="discover-error"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <p className="discover-error-text">{error}</p>
          <button
            className="cta"
            onClick={() => {
              setState("idle");
              setError("");
            }}
          >
            Try Again
          </button>
        </motion.div>
      )}

      {state === "done" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <p className="results-hint">
            {results.length} new songs discovered — tap a card to expand
          </p>
          {explanation && (
            <p className="discover-explanation">{explanation}</p>
          )}
          <div className="card-list">
            <AnimatePresence>
              {results.map((entry, i) => (
                <SongCard
                  key={entry.song.id}
                  entry={entry}
                  index={i}
                  isSaved={playlistIds.includes(entry.song.id)}
                  onToggleSave={handleToggleSave}
                />
              ))}
            </AnimatePresence>
          </div>
          <div className="discover-actions">
            <button className="cta" onClick={handleDiscover}>
              Discover Again
            </button>
          </div>
        </motion.div>
      )}
    </motion.section>
  );
}
