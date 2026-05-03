import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import songs from "../data/songs.json";
import { GENRES } from "../engine/recommender.js";
import CatalogSongRow from "../components/CatalogSongRow.jsx";

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

export default function CatalogView() {
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
          s.artist.toLowerCase().includes(q),
      );
    }

    const [field, dir] = sort.split("_");
    list.sort((a, b) => {
      let va;
      let vb;
      if (field === "popularity") {
        va = a.popularity;
        vb = b.popularity;
      } else if (field === "title") {
        va = a.title;
        vb = b.title;
      } else if (field === "energy") {
        va = a.energy;
        vb = b.energy;
      } else if (field === "year") {
        va = a.release_year;
        vb = b.release_year;
      }
      if (typeof va === "string")
        return dir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
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
          <svg
            className="catalog-search-icon"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
          >
            <circle
              cx="7"
              cy="7"
              r="5"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="10.5"
              y1="10.5"
              x2="14"
              y2="14"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
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
                <option key={g} value={g}>
                  {g}
                </option>
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
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
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
              <button
                className="tier-pill tier-pill--active"
                onClick={() => {
                  setTier(0);
                  setGenreFilter("all");
                  setSearch("");
                }}
              >
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
