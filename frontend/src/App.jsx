import { useState, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import songs from "./data/songs.json";
import { recommend, GENRES, MOODS } from "./engine/recommender.js";
import "./App.css";

const INITIAL = {
  favorite_genre: "lofi",
  favorite_mood: "chill",
  target_energy: 0.45,
  likes_acoustic: true,
};

function EnergySlider({ value, onChange }) {
  const pct = value * 100;
  return (
    <div className="slider-wrap">
      <div className="slider-track">
        <div className="slider-fill" style={{ width: `${pct}%` }} />
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        onChange={(e) => onChange(+e.target.value)}
      />
      <div className="slider-labels">
        <span>Calm</span>
        <span className="slider-value">{value.toFixed(2)}</span>
        <span>Intense</span>
      </div>
    </div>
  );
}

function ScoreBar({ score, maxScore = 15 }) {
  const pct = Math.min((score / maxScore) * 100, 100);
  return (
    <div className="score-bar">
      <motion.div
        className="score-bar-fill"
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      />
    </div>
  );
}

function BreakdownChips({ breakdown }) {
  return (
    <div className="chips">
      {breakdown.map((b, i) => (
        <span key={i} className={`chip ${b.pts < 0 ? "chip--neg" : ""}`}>
          {b.label} <strong>{b.pts > 0 ? "+" : ""}{b.pts}</strong>
        </span>
      ))}
    </div>
  );
}

function SongCard({ entry, index }) {
  const { song, score, breakdown } = entry;
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
      layout
    >
      <div className="card-rank">#{index + 1}</div>
      <div className="card-body" onClick={() => setExpanded(!expanded)}>
        <div className="card-header">
          <div>
            <h3 className="card-title">{song.title}</h3>
            <p className="card-artist">{song.artist}</p>
          </div>
          <div className="card-score">{score.toFixed(1)}</div>
        </div>
        <ScoreBar score={score} />
        <div className="card-tags">
          <span className="tag tag--genre">{song.genre}</span>
          <span className="tag tag--mood">{song.mood}</span>
          <span className="tag tag--energy">{(song.energy * 100).toFixed(0)}% energy</span>
          <span className="tag tag--year">{song.release_year}</span>
        </div>
        <AnimatePresence>
          {expanded && (
            <motion.div
              className="card-detail"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <BreakdownChips breakdown={breakdown} />
              <div className="card-meta">
                <span>Tempo {song.tempo_bpm} BPM</span>
                <span>Valence {song.valence}</span>
                <span>Acoustic {(song.acousticness * 100).toFixed(0)}%</span>
                <span>Dance {(song.danceability * 100).toFixed(0)}%</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

function VinylSpinner({ spinning }) {
  return (
    <div className={`vinyl ${spinning ? "vinyl--spin" : ""}`}>
      <div className="vinyl-groove vinyl-groove--1" />
      <div className="vinyl-groove vinyl-groove--2" />
      <div className="vinyl-groove vinyl-groove--3" />
      <div className="vinyl-label">
        <div className="vinyl-hole" />
      </div>
    </div>
  );
}

export default function App() {
  const [prefs, setPrefs] = useState(INITIAL);
  const [results, setResults] = useState(null);
  const [mode, setMode] = useState("mood_priority");
  const resultsRef = useRef(null);

  const update = (key) => (e) => {
    const val = e.target ? (e.target.type === "checkbox" ? e.target.checked : e.target.value) : e;
    setPrefs((p) => ({ ...p, [key]: val }));
  };

  const handleRecommend = () => {
    const recs = recommend(prefs, songs, 5, mode);
    setResults(recs);
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
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
          <VinylSpinner spinning={!!results} />
          <h1 className="logo">VibeFinder</h1>
          <p className="tagline">Discover your sound from 20 handpicked tracks</p>
        </motion.div>
      </header>

      <main className="main">
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
                  <option key={g} value={g}>{g}</option>
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
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div className="field field--full">
              <label className="label">Energy Level</label>
              <EnergySlider
                value={prefs.target_energy}
                onChange={(v) => setPrefs((p) => ({ ...p, target_energy: v }))}
              />
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
              <h2 className="section-title">
                Top 5 Recommendations
              </h2>
              <p className="results-hint">Click a card to see the scoring breakdown</p>
              <div className="card-list">
                {results.map((entry, i) => (
                  <SongCard key={entry.song.id} entry={entry} index={i} />
                ))}
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      <footer className="footer">
        <p>VibeFinder &mdash; Music Recommender Simulation &mdash; {songs.length} tracks in catalog</p>
      </footer>
    </div>
  );
}
