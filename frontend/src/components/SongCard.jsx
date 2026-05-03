import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import ScoreBar from "./ScoreBar.jsx";
import BreakdownChips from "./BreakdownChips.jsx";

export default function SongCard({ entry, index, isSaved, onToggleSave }) {
  const { song, score, breakdown } = entry;
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{
        duration: 0.5,
        delay: index * 0.08,
        ease: [0.22, 1, 0.36, 1],
      }}
      layout
    >
      <div className="card-rank">#{index + 1}</div>
      <div className="card-body" onClick={() => setExpanded(!expanded)}>
        <div className="card-header">
          <div>
            <h3 className="card-title">{song.title}</h3>
            <p className="card-artist">{song.artist}</p>
          </div>
          <div className="card-header-right">
            <button
              className={`save-btn ${isSaved ? "save-btn--active" : ""}`}
              onClick={(e) => {
                e.stopPropagation();
                onToggleSave(song.id);
              }}
              title={isSaved ? "Remove from playlist" : "Add to playlist"}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path
                  d="M9 15.5s-6.5-4.2-6.5-8.3C2.5 4.6 4.2 3 6.2 3c1.2 0 2.3.7 2.8 1.7C9.5 3.7 10.6 3 11.8 3c2 0 3.7 1.6 3.7 4.2 0 4.1-6.5 8.3-6.5 8.3z"
                  stroke="currentColor"
                  strokeWidth="1.3"
                  fill={isSaved ? "currentColor" : "none"}
                />
              </svg>
            </button>
            <div className="card-score">{score.toFixed(1)}</div>
          </div>
        </div>
        <ScoreBar score={score} />
        <div className="card-tags">
          <span className="tag tag--genre">{song.genre}</span>
          <span className="tag tag--mood">{song.mood}</span>
          <span className="tag tag--energy">
            {(song.energy * 100).toFixed(0)}% energy
          </span>
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
