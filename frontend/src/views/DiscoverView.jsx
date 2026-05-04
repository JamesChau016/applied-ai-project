import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { discoverSongs } from "../engine/discover.js";
import { GENRES, MOODS } from "../engine/recommender.js";
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
  const [prefs, setPrefs] = useState({
    genres: [],
    moods: [],
    artists: "",
    energyMin: 0,
    energyMax: 1,
    popularityMin: 0,
    popularityMax: 100,
  });

  const isBusy = state === "loading";

  const togglePref = (key, value) => {
    setPrefs((prev) => {
      const list = prev[key];
      const next = list.includes(value)
        ? list.filter((item) => item !== value)
        : [...list, value];
      return { ...prev, [key]: next };
    });
  };

  const updatePref = (key) => (e) => {
    const val = e?.target ? e.target.value : e;
    setPrefs((prev) => {
      const next = {
        ...prev,
        [key]: key.includes("energy")
          ? Number(val)
          : key.includes("popularity")
            ? Number(val)
            : val,
      };

      if (key === "energyMin" && next.energyMin > next.energyMax) {
        next.energyMax = next.energyMin;
      }
      if (key === "energyMax" && next.energyMax < next.energyMin) {
        next.energyMin = next.energyMax;
      }
      if (key === "popularityMin" && next.popularityMin > next.popularityMax) {
        next.popularityMax = next.popularityMin;
      }
      if (key === "popularityMax" && next.popularityMax < next.popularityMin) {
        next.popularityMin = next.popularityMax;
      }
      return next;
    });
  };

  const handleDiscover = useCallback(async () => {
    setState("loading");
    setResults([]);
    setError("");
    const artistList = prefs.artists
      .split(",")
      .map((artist) => artist.trim())
      .filter(Boolean);
    try {
      const { recommendations, explanation: exp } = await discoverSongs(
        playlistSongs,
        10,
        {
          genres: prefs.genres,
          moods: prefs.moods,
          artists: artistList,
          energy_min: prefs.energyMin,
          energy_max: prefs.energyMax,
          popularity_min: prefs.popularityMin,
          popularity_max: prefs.popularityMax,
        },
      );
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
  }, [playlistSongs, prefs]);

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

      {playlistSongs.length === 0 ? (
        <motion.div
          className="discover-prompt"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <p className="discover-desc">
            Save some songs to your playlist first, then come back to discover
            new music.
          </p>
        </motion.div>
      ) : (
        <motion.div
          className="discover-preferences"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <p className="discover-desc">
            Choose a few preferences to guide discovery. The RAG agent will
            blend them with your playlist when fetching AudioDB tracks.
          </p>
          <p className="discover-stats">
            Based on <strong>{playlistSongs.length}</strong> songs from{" "}
            <strong>{new Set(playlistSongs.map((s) => s.artist)).size}</strong>{" "}
            artists in your playlist
          </p>

          <div className="discover-preferences-grid">
            <div className="field field--full">
              <label className="label">Genres</label>
              <div className="pill-row">
                {GENRES.map((genre) => (
                  <button
                    key={genre}
                    type="button"
                    className={`tier-pill ${prefs.genres.includes(genre) ? "tier-pill--active" : ""}`}
                    onClick={() => togglePref("genres", genre)}
                    disabled={isBusy}
                  >
                    {genre}
                  </button>
                ))}
              </div>
            </div>

            <div className="field field--full">
              <label className="label">Moods</label>
              <div className="pill-row">
                {MOODS.map((mood) => (
                  <button
                    key={mood}
                    type="button"
                    className={`tier-pill ${prefs.moods.includes(mood) ? "tier-pill--active" : ""}`}
                    onClick={() => togglePref("moods", mood)}
                    disabled={isBusy}
                  >
                    {mood}
                  </button>
                ))}
              </div>
            </div>

            <div className="field field--full">
              <label className="label">Artists (comma separated)</label>
              <input
                className="text-input"
                type="text"
                placeholder="e.g. M83, Radiohead, Clairo"
                value={prefs.artists}
                onChange={updatePref("artists")}
                disabled={isBusy}
              />
              <span className="helper-text">
                These artists will be added to the AudioDB search pool.
              </span>
            </div>

            <div className="field field--full">
              <label className="label">Energy Range</label>
              <div className="range-wrap">
                <div className="range-track">
                  <div
                    className="range-fill"
                    style={{
                      left: `${prefs.energyMin * 100}%`,
                      right: `${100 - prefs.energyMax * 100}%`,
                    }}
                  />
                </div>
                <div className="range-inputs">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={prefs.energyMin}
                    onChange={updatePref("energyMin")}
                    disabled={isBusy}
                  />
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={prefs.energyMax}
                    onChange={updatePref("energyMax")}
                    disabled={isBusy}
                  />
                </div>
                <div className="range-values">
                  <span>Calm</span>
                  <span className="range-value">
                    {prefs.energyMin.toFixed(2)} - {prefs.energyMax.toFixed(2)}
                  </span>
                  <span>Intense</span>
                </div>
              </div>
            </div>

            <div className="field field--full">
              <label className="label">Popularity Range</label>
              <div className="range-wrap">
                <div className="range-track">
                  <div
                    className="range-fill"
                    style={{
                      left: `${prefs.popularityMin}%`,
                      right: `${100 - prefs.popularityMax}%`,
                    }}
                  />
                </div>
                <div className="range-inputs">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={prefs.popularityMin}
                    onChange={updatePref("popularityMin")}
                    disabled={isBusy}
                  />
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={prefs.popularityMax}
                    onChange={updatePref("popularityMax")}
                    disabled={isBusy}
                  />
                </div>
                <div className="range-values">
                  <span>Underground</span>
                  <span className="range-value">
                    {prefs.popularityMin} - {prefs.popularityMax}
                  </span>
                  <span>Mainstream</span>
                </div>
              </div>
            </div>
          </div>

          <button className="cta" onClick={handleDiscover} disabled={isBusy}>
            Discover New Songs
          </button>
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
          {explanation && <p className="discover-explanation">{explanation}</p>}
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
