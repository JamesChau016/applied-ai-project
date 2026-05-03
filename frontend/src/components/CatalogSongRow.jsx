import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import PopularityMeter from "./PopularityMeter.jsx";

export default function CatalogSongRow({ song, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      className="catalog-row"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{
        duration: 0.35,
        delay: index * 0.03,
        ease: [0.22, 1, 0.36, 1],
      }}
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
        <div
          className={`catalog-chevron ${expanded ? "catalog-chevron--open" : ""}`}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path
              d="M4 5.5L7 8.5L10 5.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
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
                <span className="stat-value">
                  {(song.acousticness * 100).toFixed(0)}%
                </span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Dance</span>
                <span className="stat-value">
                  {(song.danceability * 100).toFixed(0)}%
                </span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Instrumental</span>
                <span className="stat-value">
                  {(song.instrumentalness * 100).toFixed(0)}%
                </span>
              </div>
              <div className="stat-pill">
                <span className="stat-label">Production</span>
                <span className="stat-value">
                  {(song.production_complexity * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
