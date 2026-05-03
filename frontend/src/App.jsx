import { useState, useRef, useMemo } from "react";
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

const POPULARITY_TIERS = [
  { label: "All", min: 0, max: 100 },
  { label: "Underground", min: 0, max: 65 },
  { label: "Rising", min: 65, max: 80 },
  { label: "Popular", min: 80, max: 95 },
  { label: "Mainstream", min: 95, max: 100 },
];

const SORT_OPTIONS = [
  { value: "popularity_desc", label: "Most Popular" },
  { value: "popularity_asc", label: "Least Popular" },
  { value: "title_asc", label: "Title A-Z" },
  { value: "energy_desc", label: "Highest Energy" },
  { value: "year_desc", label: "Newest First" },
  { value: "year_asc", label: "Oldest First" },
];

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

function PopularityMeter({ value }) {
  const segments = 10;
  const filled = Math.round((value / 100) * segments);
  return (
    <div className="pop-meter" title={`Popularity: ${value}`}>
      {Array.from({ length: segments }, (_, i) => (
        <div
          key={i}
          className={`pop-seg ${i < filled ? "pop-seg--lit" : ""}`}
          style={{ animationDelay: `${i * 0.04}s` }}
        />
      ))}
      <span className="pop-val">{value}</span>
    </div>
  );
}

function CatalogSongRow({ song, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      className="catalog-row"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.35, delay: index * 0.03, ease: [0.22, 1, 0.36, 1] }}
      layout
      onClick={() => setExpanded(!expanded)}
    >
      <div className="catalog-row-main">
        <div className="catalog-num">{String(index + 1).padStart(2, "0")}</div>
        <div className="catalog-info">
          <span className="catalog-title">{song.title}</span>
          <span className="catalog-artist">{song.artist}</span>
        </div>
        <div className="catalog-tags-col">
          <span className="tag tag--genre">{song.genre}</span>
          <span className="tag tag--mood">{song.mood}</span>
        </div>
        <div className="catalog-energy-col">
          <div className="energy-ring" style={{ "--e": song.energy }}>
            <svg viewBox="0 0 36 36" className="energy-svg">
              <circle cx="18" cy="18" r="15.9" className="energy-track" />
              <circle
                cx="18"
                cy="18"
                r="15.9"
                className="energy-fill"
                strokeDasharray={`${song.energy * 100} ${100 - song.energy * 100}`}
              />
            </svg>
            <span className="energy-num">{(song.energy * 100).toFixed(0)}</span>
          </div>
        </div>
        <PopularityMeter value={song.popularity} />
        <div className="catalog-year">{song.release_year}</div>
        <div className={`catalog-chevron ${expanded ? "catalog-chevron--open" : ""}`}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M4 5.5L7 8.5L10 5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="catalog-detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="catalog-stats">
              <div className="stat-pill">
                <span className="stat-label">Tempo</span>
                <span className="stat-value">{song.tempo_bpm} BPM</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Valence</span>
                <span className="stat-value">{song.valence}</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Acoustic</span>
                <span className="stat-value">{(song.acousticness * 100).toFixed(0)}%</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Dance</span>
                <span className="stat-value">{(song.danceability * 100).toFixed(0)}%</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Instrumental</span>
                <span className="stat-value">{(song.instrumentalness * 100).toFixed(0)}%</span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Production</span>
                <span className="stat-value">{(song.production_complexity * 100).toFixed(0)}%</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function CatalogView() {
  const [tier, setTier] = useState(0);
  const [sort, setSort] = useState("popularity_desc");
  const [genreFilter, setGenreFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const { min, max } = POPULARITY_TIERS[tier];
    let list = songs.filter((s) => s.popularity >= min && s.popularity <= max);

    if (genreFilter !== "all") {
      list = list.filter((s) => s.genre === genreFilter);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (s) =>
          s.title.toLowerCase().includes(q) ||
          s.artist.toLowerCase().includes(q)
      );
    }

    const [field, dir] = sort.split("_");
    list.sort((a, b) => {
      let va, vb;
      if (field === "popularity") { va = a.popularity; vb = b.popularity; }
      else if (field === "title") { va = a.title; vb = b.title; }
      else if (field === "energy") { va = a.energy; vb = b.energy; }
      else if (field === "year") { va = a.release_year; vb = b.release_year; }
      if (typeof va === "string") return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      return dir === "asc" ? va - vb : vb - va;
    });

    return list;
  }, [tier, sort, genreFilter, search]);

  return (
    <motion.section
      className="catalog-section"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5 }}
    >
      <div className="catalog-controls">
        <div className="catalog-search-wrap">
          <svg className="catalog-search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
            <line x1="10.5" y1="10.5" x2="14" y2="14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            className="catalog-search"
            type="text"
            placeholder="Search title or artist..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="catalog-filter-row">
          <div className="field catalog-field">
            <label className="label">Popularity</label>
            <div className="tier-pills">
              {POPULARITY_TIERS.map((t, i) => (
                <button
                  key={t.label}
                  className={`tier-pill ${tier === i ? "tier-pill--active" : ""}`}
                  onClick={() => setTier(i)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field catalog-field">
            <label className="label">Genre</label>
            <select
              className="select"
              value={genreFilter}
              onChange={(e) => setGenreFilter(e.target.value)}
            >
              <option value="all">All Genres</option>
              {GENRES.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <div className="field catalog-field">
            <label className="label">Sort By</label>
            <select
              className="select"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="catalog-header-row">
        <span className="catalog-col-num">#</span>
        <span className="catalog-col-info">Track</span>
        <span className="catalog-col-tags">Tags</span>
        <span className="catalog-col-energy">Energy</span>
        <span className="catalog-col-pop">Popularity</span>
        <span className="catalog-col-year">Year</span>
        <span className="catalog-col-chev" />
      </div>

      <div className="catalog-list">
        <AnimatePresence mode="popLayout">
          {filtered.length > 0 ? (
            filtered.map((song, i) => (
              <CatalogSongRow key={song.id} song={song} index={i} />
            ))
          ) : (
            <motion.div
              className="catalog-empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <p>No tracks match your filters</p>
              <button className="tier-pill tier-pill--active" onClick={() => { setTier(0); setGenreFilter("all"); setSearch(""); }}>
                Reset Filters
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="catalog-count">
        Showing {filtered.length} of {songs.length} tracks
      </div>
    </motion.section>
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
  const [tab, setTab] = useState("recommend");
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
          <VinylSpinner spinning={tab === "recommend" && !!results} />
          <h1 className="logo">VibeFinder</h1>
          <p className="tagline">Discover your sound from 20 handpicked tracks</p>
        </motion.div>
      </header>

      <nav className="tab-bar">
        <button
          className={`tab-btn ${tab === "recommend" ? "tab-btn--active" : ""}`}
          onClick={() => setTab("recommend")}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 1L10.2 5.5L15 6.2L11.5 9.6L12.3 14.4L8 12.1L3.7 14.4L4.5 9.6L1 6.2L5.8 5.5L8 1Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
          </svg>
          Recommend
        </button>
        <button
          className={`tab-btn ${tab === "catalog" ? "tab-btn--active" : ""}`}
          onClick={() => setTab("catalog")}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
            <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
            <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
            <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
          </svg>
          All Songs
        </button>
        <div className="tab-indicator" style={{ transform: `translateX(${tab === "recommend" ? "0" : "100"}%)` }} />
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
            </motion.div>
          ) : (
            <CatalogView key="catalog" />
          )}
        </AnimatePresence>
      </main>

      <footer className="footer">
        <p>VibeFinder &mdash; Music Recommender Simulation &mdash; {songs.length} tracks in catalog</p>
      </footer>
    </div>
  );
}
