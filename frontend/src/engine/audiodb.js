/**
 * JS client for TheAudioDB free API (v1).
 * Port of src/audiodb_client.py — fetches and normalizes tracks.
 */

const BASE_URL = "https://www.theaudiodb.com/api/v1/json/123";

let lastRequestTime = 0;

async function rateLimitedFetch(url) {
  const now = Date.now();
  const elapsed = now - lastRequestTime;
  if (elapsed < 2000) {
    await new Promise((r) => setTimeout(r, 2000 - elapsed));
  }
  const resp = await fetch(url);
  lastRequestTime = Date.now();
  if (!resp.ok) return null;
  return resp.json();
}

// ── Genre mapping from AudioDB free-text to app genres ──

const GENRE_MAP = {
  "hip-hop": "pop",
  "hip-hop/rap": "pop",
  rap: "pop",
  "r&b": "pop",
  rnb: "pop",
  soul: "jazz",
  blues: "jazz",
  country: "rock",
  folk: "indie rock",
  electronic: "synth-pop",
  edm: "synth-pop",
  house: "disco",
  techno: "synth-pop",
  dance: "disco",
  punk: "rock",
  "punk rock": "rock",
  "post-punk": "alternative rock",
  grunge: "alternative rock",
  alternative: "alternative rock",
  "alternative rock": "alternative rock",
  indie: "indie rock",
  "indie rock": "indie rock",
  "indie pop": "indie pop",
  rock: "rock",
  "hard rock": "rock",
  metal: "metal",
  "heavy metal": "metal",
  pop: "pop",
  "synth-pop": "synth-pop",
  synthwave: "synthwave",
  "new wave": "synth-pop",
  jazz: "jazz",
  funk: "funk",
  disco: "disco",
  classical: "classical",
  ambient: "ambient",
  lofi: "lofi",
  "lo-fi": "lofi",
  reggae: "reggae",
  ska: "reggae",
  latin: "pop",
};

const MOOD_MAP = {
  happy: "happy",
  sad: "melancholic",
  melancholy: "melancholic",
  melancholic: "melancholic",
  angry: "aggressive",
  aggressive: "aggressive",
  chill: "chill",
  relaxed: "relaxed",
  calm: "relaxed",
  peaceful: "relaxed",
  energetic: "energetic",
  upbeat: "upbeat",
  dark: "moody",
  moody: "moody",
  dreamy: "dreamy",
  nostalgic: "nostalgic",
  intense: "intense",
  euphoric: "euphoric",
  focused: "focused",
};

// ── Heuristic defaults for numeric features by genre ──

const GENRE_DEFAULTS = {
  rock: {
    energy: 0.72,
    acousticness: 0.2,
    valence: 0.55,
    danceability: 0.5,
    instrumentalness: 0.1,
    production_complexity: 0.7,
    lyrical_sentiment: 0.0,
  },
  "alternative rock": {
    energy: 0.65,
    acousticness: 0.25,
    valence: 0.45,
    danceability: 0.45,
    instrumentalness: 0.12,
    production_complexity: 0.65,
    lyrical_sentiment: -0.1,
  },
  "indie rock": {
    energy: 0.6,
    acousticness: 0.35,
    valence: 0.5,
    danceability: 0.45,
    instrumentalness: 0.1,
    production_complexity: 0.55,
    lyrical_sentiment: -0.05,
  },
  "indie pop": {
    energy: 0.55,
    acousticness: 0.4,
    valence: 0.6,
    danceability: 0.55,
    instrumentalness: 0.08,
    production_complexity: 0.5,
    lyrical_sentiment: 0.15,
  },
  pop: {
    energy: 0.7,
    acousticness: 0.2,
    valence: 0.65,
    danceability: 0.7,
    instrumentalness: 0.05,
    production_complexity: 0.65,
    lyrical_sentiment: 0.3,
  },
  "synth-pop": {
    energy: 0.75,
    acousticness: 0.1,
    valence: 0.6,
    danceability: 0.72,
    instrumentalness: 0.15,
    production_complexity: 0.75,
    lyrical_sentiment: 0.2,
  },
  synthwave: {
    energy: 0.7,
    acousticness: 0.08,
    valence: 0.55,
    danceability: 0.65,
    instrumentalness: 0.3,
    production_complexity: 0.8,
    lyrical_sentiment: 0.1,
  },
  metal: {
    energy: 0.92,
    acousticness: 0.05,
    valence: 0.3,
    danceability: 0.35,
    instrumentalness: 0.2,
    production_complexity: 0.85,
    lyrical_sentiment: -0.35,
  },
  jazz: {
    energy: 0.4,
    acousticness: 0.7,
    valence: 0.5,
    danceability: 0.45,
    instrumentalness: 0.4,
    production_complexity: 0.7,
    lyrical_sentiment: 0.05,
  },
  funk: {
    energy: 0.75,
    acousticness: 0.25,
    valence: 0.7,
    danceability: 0.8,
    instrumentalness: 0.15,
    production_complexity: 0.65,
    lyrical_sentiment: 0.2,
  },
  disco: {
    energy: 0.8,
    acousticness: 0.15,
    valence: 0.75,
    danceability: 0.85,
    instrumentalness: 0.1,
    production_complexity: 0.6,
    lyrical_sentiment: 0.3,
  },
  lofi: {
    energy: 0.35,
    acousticness: 0.55,
    valence: 0.4,
    danceability: 0.4,
    instrumentalness: 0.5,
    production_complexity: 0.4,
    lyrical_sentiment: 0.0,
  },
  ambient: {
    energy: 0.25,
    acousticness: 0.6,
    valence: 0.4,
    danceability: 0.2,
    instrumentalness: 0.7,
    production_complexity: 0.55,
    lyrical_sentiment: 0.0,
  },
  classical: {
    energy: 0.3,
    acousticness: 0.9,
    valence: 0.45,
    danceability: 0.15,
    instrumentalness: 0.85,
    production_complexity: 0.8,
    lyrical_sentiment: 0.0,
  },
  reggae: {
    energy: 0.55,
    acousticness: 0.35,
    valence: 0.65,
    danceability: 0.7,
    instrumentalness: 0.1,
    production_complexity: 0.45,
    lyrical_sentiment: 0.15,
  },
};

const DEFAULT_FEATURES = {
  energy: 0.55,
  acousticness: 0.3,
  valence: 0.5,
  danceability: 0.5,
  instrumentalness: 0.15,
  production_complexity: 0.6,
  lyrical_sentiment: 0.0,
};

function mapGenre(raw) {
  if (!raw) return null;
  const key = raw.toLowerCase().trim();
  if (GENRE_MAP[key]) return GENRE_MAP[key];
  // partial match
  for (const [pattern, genre] of Object.entries(GENRE_MAP)) {
    if (key.includes(pattern) || pattern.includes(key)) return genre;
  }
  return null;
}

function mapMood(raw) {
  if (!raw) return null;
  const key = raw.toLowerCase().trim();
  if (MOOD_MAP[key]) return MOOD_MAP[key];
  for (const [pattern, mood] of Object.entries(MOOD_MAP)) {
    if (key.includes(pattern) || pattern.includes(key)) return mood;
  }
  return null;
}

function estimatePopularity(totalPlays, totalListeners) {
  if (!totalPlays && !totalListeners) return 50;
  const combined = (totalPlays || 0) + (totalListeners || 0) * 2;
  if (combined > 5000000) return 90;
  if (combined > 1000000) return 75;
  if (combined > 500000) return 65;
  if (combined > 100000) return 55;
  if (combined > 10000) return 40;
  return 30;
}

function safeInt(val) {
  const n = parseInt(val, 10);
  return isNaN(n) ? 0 : n;
}

export function normalizeTrack(
  raw,
  fallbackGenre = "pop",
  fallbackMood = "chill",
) {
  const genre = mapGenre(raw.strGenre) || fallbackGenre;
  const mood = mapMood(raw.strMood) || fallbackMood;
  const defaults = GENRE_DEFAULTS[genre] || DEFAULT_FEATURES;
  const totalPlays = safeInt(raw.intTotalPlays);
  const totalListeners = safeInt(raw.intTotalListeners);

  return {
    id: `audiodb_${raw.idTrack}`,
    title: raw.strTrack || "Unknown",
    artist: raw.strArtist || "Unknown",
    genre,
    mood,
    energy: defaults.energy,
    acousticness: defaults.acousticness,
    valence: defaults.valence,
    danceability: defaults.danceability,
    instrumentalness: defaults.instrumentalness,
    production_complexity: defaults.production_complexity,
    lyrical_sentiment: defaults.lyrical_sentiment,
    popularity: estimatePopularity(totalPlays, totalListeners),
    release_year: safeInt(raw.intYearReleased) || 2015,
    tempo_bpm: 120,
    source: "audiodb",
    music_video: raw.strMusicVid || "",
  };
}

export async function getTopTracks(artistName, fallbackGenre, fallbackMood) {
  const encoded = encodeURIComponent(artistName);
  const data = await rateLimitedFetch(
    `${BASE_URL}/track-top10.php?s=${encoded}`,
  );
  if (!data || !data.track) return [];
  return data.track.map((t) => normalizeTrack(t, fallbackGenre, fallbackMood));
}

// Well-known artists by genre — used as fallback when playlist artists are
// fictional or return no results from AudioDB.
const GENRE_ARTISTS = {
  lofi: ["Nujabes", "J Dilla", "Tomppabeats", "Idealism"],
  ambient: ["Brian Eno", "Tycho", "Boards of Canada", "Aphex Twin"],
  "indie rock": ["Arctic Monkeys", "Tame Impala", "Radiohead", "The Strokes"],
  "indie pop": ["Clairo", "Alvvays", "Mac DeMarco", "Beach House"],
  "synth-pop": ["The Weeknd", "Depeche Mode", "CHVRCHES", "M83"],
  synthwave: ["The Midnight", "FM-84", "Gunship", "Kavinsky"],
  pop: ["Dua Lipa", "Harry Styles", "Taylor Swift", "Billie Eilish"],
  rock: ["Foo Fighters", "Muse", "Queens of the Stone Age", "Led Zeppelin"],
  "alternative rock": [
    "Radiohead",
    "Pixies",
    "The Smashing Pumpkins",
    "Nirvana",
  ],
  metal: ["Metallica", "Tool", "Gojira", "Mastodon"],
  jazz: ["Miles Davis", "John Coltrane", "Kamasi Washington", "Robert Glasper"],
  funk: ["Vulfpeck", "Jamiroquai", "Earth Wind and Fire", "Prince"],
  disco: ["Daft Punk", "Bee Gees", "Donna Summer", "Chic"],
  classical: ["Ludovico Einaudi", "Max Richter", "Olafur Arnalds", "Yiruma"],
  reggae: ["Bob Marley", "Chronixx", "Protoje", "Damian Marley"],
};

export function getFallbackArtists(genre, exclude) {
  const pool = GENRE_ARTISTS[genre] || GENRE_ARTISTS["pop"];
  return pool.filter((a) => !exclude.has(a));
}
