import { motion, AnimatePresence } from "motion/react";

export default function PlaylistView({ playlistSongs, onRemove, onExport }) {
  return (
    <motion.section
      className="catalog-section"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5 }}
    >
      <div className="playlist-header">
        <h2 className="section-title">My Playlist</h2>
        {playlistSongs.length > 0 && (
          <button
            className="export-btn"
            onClick={onExport}
            title="Export playlist as JSON"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 2v8M4.5 7L8 10.5 11.5 7"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M3 12.5h10"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
              />
            </svg>
            Export JSON
          </button>
        )}
      </div>

      {playlistSongs.length === 0 ? (
        <div className="catalog-empty">
          <p>Your playlist is empty</p>
          <p className="playlist-hint">
            Save songs from your recommendations to build your playlist
          </p>
        </div>
      ) : (
        <>
          <div className="playlist-list">
            <AnimatePresence mode="popLayout">
              {playlistSongs.map((song, i) => (
                <motion.div
                  key={song.id}
                  className="playlist-row"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{
                    opacity: 0,
                    x: 20,
                    height: 0,
                    marginBottom: 0,
                    padding: 0,
                  }}
                  transition={{ duration: 0.35, delay: i * 0.03 }}
                  layout
                >
                  <div className="playlist-num">
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="catalog-info">
                    <span className="catalog-title">{song.title}</span>
                    <span className="catalog-artist">{song.artist}</span>
                  </div>
                  <div className="catalog-tags-col">
                    <span className="tag tag--genre">{song.genre}</span>
                    <span className="tag tag--mood">{song.mood}</span>
                  </div>
                  <div className="playlist-energy">
                    {(song.energy * 100).toFixed(0)}% energy
                  </div>
                  <button
                    className="remove-btn"
                    onClick={() => onRemove(song.id)}
                    title="Remove from playlist"
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <line
                        x1="4"
                        y1="4"
                        x2="12"
                        y2="12"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                      <line
                        x1="12"
                        y1="4"
                        x2="4"
                        y2="12"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                    </svg>
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <div className="catalog-count">
            {playlistSongs.length}{" "}
            {playlistSongs.length === 1 ? "song" : "songs"} saved
          </div>
        </>
      )}
    </motion.section>
  );
}
