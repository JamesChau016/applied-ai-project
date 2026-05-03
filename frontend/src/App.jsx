import { useState, useRef, useMemo, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import songs from "./data/songs.json";
import seedPlaylist from "../../data/playlist.json";
import { recommend, GENRES, MOODS } from "./engine/recommender.js";
import EnergySlider from "./components/EnergySlider.jsx";
import SongCard from "./components/SongCard.jsx";
import VinylSpinner from "./components/VinylSpinner.jsx";
import CatalogView from "./views/CatalogView.jsx";
import PlaylistView from "./views/PlaylistView.jsx";
import "./App.css";

const PLAYLIST_KEY = "vibefinder_playlist";

const seedPlaylistById = new Map(seedPlaylist.map((song) => [song.id, song]));

function getPlaylistSong(id) {
  return (
    seedPlaylistById.get(id) || songs.find((song) => song.id === id) || null
  );
}

function loadPlaylist() {
  try {
    const raw = localStorage.getItem(PLAYLIST_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {
    // fall through to seed
  }
  return seedPlaylist.map((s) => s.id);
}

function savePlaylist(ids) {
  localStorage.setItem(PLAYLIST_KEY, JSON.stringify(ids));
}

function exportPlaylist(ids) {
  const data = ids
    .map((id) => {
      const song = getPlaylistSong(id);
      if (!song) return null;
      return {
        ...song,
        added_at: song.added_at ?? new Date().toISOString(),
      };
    })
    .filter(Boolean);
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "playlist.json";
  a.click();
  URL.revokeObjectURL(url);
}

const INITIAL = {
  favorite_genre: "lofi",
  favorite_mood: "chill",
  target_energy: 0.45,
  target_popularity: 60,
  likes_acoustic: true,
};

export default function App() {
  const [prefs, setPrefs] = useState(INITIAL);
  const [results, setResults] = useState(null);
  const [mode, setMode] = useState("mood_priority");
  const [tab, setTab] = useState("recommend");
  const [playlistIds, setPlaylistIds] = useState(loadPlaylist);
  const resultsRef = useRef(null);
  const playlistSongs = useMemo(
    () => playlistIds.map((id) => getPlaylistSong(id)).filter(Boolean),
    [playlistIds],
  );

  useEffect(() => {
    savePlaylist(playlistIds);
  }, [playlistIds]);

  const toggleSave = useCallback((id) => {
    setPlaylistIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const update = (key) => (e) => {
    const val = e.target
      ? e.target.type === "checkbox"
        ? e.target.checked
        : e.target.type === "range"
          ? +e.target.value
          : e.target.value
      : e;
    setPrefs((p) => ({ ...p, [key]: val }));
  };

  const handleRecommend = () => {
    const recs = recommend(prefs, songs, 5, mode);
    setResults(recs);
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 100);
  };

  return (
    <div className="app">
      <div className="grain" />

      <header className="hero">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <VinylSpinner spinning={tab === "recommend" && !!results} />
          <h1 className="logo">VibeFinder</h1>
          <p className="tagline">
            Discover your sound from 20 handpicked tracks
          </p>
        </motion.div>
      </header>

      <nav className="tab-bar">
        <button
          className={`tab-btn ${tab === "recommend" ? "tab-btn--active" : ""}`}
          onClick={() => setTab("recommend")}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 1L10.2 5.5L15 6.2L11.5 9.6L12.3 14.4L8 12.1L3.7 14.4L4.5 9.6L1 6.2L5.8 5.5L8 1Z"
              stroke="currentColor"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
          </svg>
          Recommend
        </button>
        <button
          className={`tab-btn ${tab === "catalog" ? "tab-btn--active" : ""}`}
          onClick={() => setTab("catalog")}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect
              x="2"
              y="2"
              width="5"
              height="5"
              rx="1"
              stroke="currentColor"
              strokeWidth="1.2"
            />
            <rect
              x="9"
              y="2"
              width="5"
              height="5"
              rx="1"
              stroke="currentColor"
              strokeWidth="1.2"
            />
            <rect
              x="2"
              y="9"
              width="5"
              height="5"
              rx="1"
              stroke="currentColor"
              strokeWidth="1.2"
            />
            <rect
              x="9"
              y="9"
              width="5"
              height="5"
              rx="1"
              stroke="currentColor"
              strokeWidth="1.2"
            />
          </svg>
          All Songs
        </button>
        <button
          className={`tab-btn ${tab === "playlist" ? "tab-btn--active" : ""}`}
          onClick={() => setTab("playlist")}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 13.5s-5-3.2-5-6.4C3 4.8 4.3 3.5 5.9 3.5c.9 0 1.7.5 2.1 1.3.4-.8 1.2-1.3 2.1-1.3C11.7 3.5 13 4.8 13 7.1c0 3.2-5 6.4-5 6.4z"
              stroke="currentColor"
              strokeWidth="1.2"
              fill="none"
            />
          </svg>
          My Playlist
          {playlistIds.length > 0 && (
            <span className="tab-badge">{playlistIds.length}</span>
          )}
        </button>
        <div
          className="tab-indicator tab-indicator--three"
          style={{
            transform: `translateX(${tab === "recommend" ? "0" : tab === "catalog" ? "100" : "200"}%)`,
          }}
        />
      </nav>

      <main className="main">
        <AnimatePresence mode="wait">
          {tab === "recommend" ? (
            <motion.div
              key="recommend"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.35 }}
            >
              <motion.section
                className="form-section"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <h2 className="section-title">Your Taste Profile</h2>

                <div className="form-grid">
                  <div className="field">
                    <label className="label">Genre</label>
                    <select
                      className="select"
                      value={prefs.favorite_genre}
                      onChange={update("favorite_genre")}
                    >
                      {GENRES.map((g) => (
                        <option key={g} value={g}>
                          {g}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="field">
                    <label className="label">Mood</label>
                    <select
                      className="select"
                      value={prefs.favorite_mood}
                      onChange={update("favorite_mood")}
                    >
                      {MOODS.map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="field field--full">
                    <label className="label">Energy Level</label>
                    <EnergySlider
                      value={prefs.target_energy}
                      onChange={(v) =>
                        setPrefs((p) => ({ ...p, target_energy: v }))
                      }
                    />
                  </div>

                  <div className="field field--full">
                    <label className="label">Preferred Popularity</label>
                    <div className="slider-wrap">
                      <div className="slider-track">
                        <div
                          className="slider-fill"
                          style={{ width: `${prefs.target_popularity}%` }}
                        />
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="5"
                        value={prefs.target_popularity}
                        onChange={update("target_popularity")}
                      />
                      <div className="slider-labels">
                        <span>Underground</span>
                        <span className="slider-value">
                          {prefs.target_popularity}
                        </span>
                        <span>Mainstream</span>
                      </div>
                    </div>
                  </div>

                  <div className="field">
                    <label className="toggle-label">
                      <input
                        type="checkbox"
                        checked={prefs.likes_acoustic}
                        onChange={update("likes_acoustic")}
                      />
                      <span className="toggle-switch" />
                      <span>Prefer acoustic sounds</span>
                    </label>
                  </div>

                  <div className="field">
                    <label className="label">Scoring Mode</label>
                    <div className="mode-toggle">
                      <button
                        className={`mode-btn ${mode === "mood_priority" ? "mode-btn--active" : ""}`}
                        onClick={() => setMode("mood_priority")}
                      >
                        Mood Priority
                      </button>
                      <button
                        className={`mode-btn ${mode === "genre_priority" ? "mode-btn--active" : ""}`}
                        onClick={() => setMode("genre_priority")}
                      >
                        Genre Priority
                      </button>
                    </div>
                  </div>
                </div>

                <motion.button
                  className="cta"
                  onClick={handleRecommend}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  Find My Vibe
                </motion.button>
              </motion.section>

              <AnimatePresence mode="wait">
                {results && (
                  <motion.section
                    ref={resultsRef}
                    className="results-section"
                    key={JSON.stringify(results.map((r) => r.song.id))}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.4 }}
                  >
                    <h2 className="section-title">Top 5 Recommendations</h2>
                    <p className="results-hint">
                      Click a card to see the scoring breakdown
                    </p>
                    <div className="card-list">
                      {results.map((entry, i) => (
                        <SongCard
                          key={entry.song.id}
                          entry={entry}
                          index={i}
                          isSaved={playlistIds.includes(entry.song.id)}
                          onToggleSave={toggleSave}
                        />
                      ))}
                    </div>
                  </motion.section>
                )}
              </AnimatePresence>
            </motion.div>
          ) : tab === "catalog" ? (
            <CatalogView key="catalog" />
          ) : (
            <PlaylistView
              key="playlist"
              playlistSongs={playlistSongs}
              onRemove={toggleSave}
              onExport={() => exportPlaylist(playlistIds)}
            />
          )}
        </AnimatePresence>
      </main>

      <footer className="footer">
        <p>
          VibeFinder &mdash; Music Recommender Simulation &mdash; {songs.length}{" "}
          tracks in catalog
        </p>
      </footer>
    </div>
  );
}
