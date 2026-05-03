/**
 * Music recommender scoring engine — ported from src/recommender.py.
 * Implements the same weighted point-based scoring system.
 */

const MOOD_SIMILARITY = {
  moody: ["melancholic", "sad", "dark", "introspective"],
  melancholic: ["moody", "sad", "dark", "introspective"],
  chill: ["relaxed", "focused", "peaceful", "calm"],
  relaxed: ["chill", "peaceful", "calm"],
  happy: ["euphoric", "upbeat", "energetic"],
  energetic: ["happy", "intense", "euphoric"],
  intense: ["energetic", "aggressive"],
  euphoric: ["happy", "energetic", "upbeat"],
  upbeat: ["happy", "euphoric", "energetic"],
  focused: ["chill", "relaxed"],
  dreamy: ["chill", "relaxed", "nostalgic"],
  nostalgic: ["melancholic", "dreamy", "moody"],
  aggressive: ["intense", "energetic"],
};

const GENRE_RELATIONS = {
  "alternative rock": ["indie rock", "rock", "indie pop"],
  "indie rock": ["alternative rock", "rock", "indie pop"],
  rock: ["alternative rock", "indie rock", "metal"],
  "synth-pop": ["pop", "electronic", "new wave", "synthwave"],
  synthwave: ["synth-pop", "electronic", "pop"],
  pop: ["synth-pop", "indie pop", "disco"],
  "indie pop": ["pop", "indie rock", "alternative rock"],
  lofi: ["ambient", "chill", "jazz"],
  ambient: ["lofi", "chill", "classical"],
  jazz: ["lofi", "funk", "soul"],
  funk: ["disco", "jazz", "pop"],
  disco: ["funk", "pop", "dance"],
  classical: ["ambient", "jazz"],
  metal: ["rock", "alternative rock"],
  reggae: ["funk", "pop"],
};

const SCORING_MODES = {
  mood_priority: {
    mood_exact: 4.0,
    mood_similar: 2.0,
    genre_exact: 1.5,
    genre_related: 0.75,
  },
  genre_priority: {
    mood_exact: 2.0,
    mood_similar: 1.0,
    genre_exact: 4.0,
    genre_related: 2.0,
  },
};

const LYRICAL_SENTIMENT_DEFAULTS = {
  moody: -0.45,
  melancholic: -0.5,
  sad: -0.6,
  dark: -0.55,
  happy: 0.65,
  upbeat: 0.6,
  euphoric: 0.75,
  chill: 0.15,
  relaxed: 0.1,
  focused: 0.05,
  intense: -0.15,
  aggressive: -0.35,
};

function isMoodSimilar(mood1, mood2) {
  const similar = MOOD_SIMILARITY[mood1] || [];
  return similar.includes(mood2);
}

function isGenreRelated(genre1, genre2) {
  const related = GENRE_RELATIONS[genre1] || [];
  return related.includes(genre2);
}

function resolveDefaults(prefs) {
  const mood = prefs.favorite_mood;
  const acoustic = prefs.likes_acoustic;
  return {
    ...prefs,
    target_popularity:
      prefs.target_popularity ??
      (["happy", "upbeat", "euphoric"].includes(mood) ? 70 : 50),
    target_decade: prefs.target_decade ?? 2010,
    target_instrumentalness:
      prefs.target_instrumentalness ?? (acoustic ? 0.65 : 0.3),
    target_lyrical_sentiment:
      prefs.target_lyrical_sentiment ??
      (LYRICAL_SENTIMENT_DEFAULTS[mood] ?? 0.0),
    target_production_complexity:
      prefs.target_production_complexity ?? (acoustic ? 0.45 : 0.7),
  };
}

export function scoreSong(userPrefs, song, scoringMode = "mood_priority") {
  const prefs = resolveDefaults(userPrefs);
  const weights = SCORING_MODES[scoringMode];
  let score = 0;
  const breakdown = [];

  // 1. Mood match
  if (song.mood === prefs.favorite_mood) {
    score += weights.mood_exact;
    breakdown.push({ label: "Mood match", pts: weights.mood_exact });
  } else if (isMoodSimilar(prefs.favorite_mood, song.mood)) {
    score += weights.mood_similar;
    breakdown.push({ label: "Similar mood", pts: weights.mood_similar });
  }

  // 2. Energy proximity
  const eDiff = Math.abs(song.energy - prefs.target_energy);
  let ePts = 0;
  if (eDiff <= 0.1) ePts = 2.5;
  else if (eDiff <= 0.2) ePts = 1.5;
  else if (eDiff <= 0.3) ePts = 1.0;
  if (ePts) {
    score += ePts;
    breakdown.push({ label: "Energy", pts: ePts });
  }

  // 3. Genre match
  if (song.genre === prefs.favorite_genre) {
    score += weights.genre_exact;
    breakdown.push({ label: "Genre match", pts: weights.genre_exact });
  } else if (isGenreRelated(prefs.favorite_genre, song.genre)) {
    score += weights.genre_related;
    breakdown.push({ label: "Related genre", pts: weights.genre_related });
  }

  // 4. Acousticness
  if (prefs.likes_acoustic) {
    let aPts = 0;
    if (song.acousticness > 0.7) aPts = 1.2;
    else if (song.acousticness > 0.4) aPts = 0.6;
    if (aPts) {
      score += aPts;
      breakdown.push({ label: "Acoustic", pts: aPts });
    }
  }

  // 5. Valence
  let vPts = 0;
  if (song.valence < 0.3) vPts = 0.5;
  else if (song.valence > 0.6) vPts = -0.25;
  if (vPts !== 0) {
    score += vPts;
    breakdown.push({ label: "Valence", pts: vPts });
  }

  // 6. Popularity
  const popDiff = Math.abs(song.popularity - prefs.target_popularity);
  let pPts = 0;
  if (popDiff <= 10) pPts = 1.5;
  else if (popDiff <= 20) pPts = 1.0;
  else if (popDiff <= 30) pPts = 0.5;
  if (pPts) {
    score += pPts;
    breakdown.push({ label: "Popularity", pts: pPts });
  }

  // 7. Decade
  const songDecade = Math.floor(song.release_year / 10) * 10;
  const decadeGap = Math.abs(songDecade - prefs.target_decade);
  let dPts = 0;
  if (decadeGap === 0) dPts = 1.0;
  else if (decadeGap <= 10) dPts = 0.6;
  else if (decadeGap <= 20) dPts = 0.2;
  if (dPts) {
    score += dPts;
    breakdown.push({ label: "Decade", pts: dPts });
  }

  // 8. Instrumentalness
  const instDiff = Math.abs(song.instrumentalness - prefs.target_instrumentalness);
  const instPts = Math.max(0, 1.0 - 2.0 * instDiff);
  if (instPts > 0) {
    score += instPts;
    breakdown.push({ label: "Instrumental", pts: +instPts.toFixed(2) });
  }

  // 9. Lyrical sentiment
  const lyrDiff = Math.abs(song.lyrical_sentiment - prefs.target_lyrical_sentiment);
  const lyrPts = Math.max(0, 1.0 - lyrDiff);
  if (lyrPts > 0) {
    score += lyrPts;
    breakdown.push({ label: "Lyrics", pts: +lyrPts.toFixed(2) });
  }

  // 10. Production complexity
  const prodDiff = Math.abs(
    song.production_complexity - prefs.target_production_complexity
  );
  const prodPts = Math.max(0, 0.8 - 1.6 * prodDiff);
  if (prodPts > 0) {
    score += prodPts;
    breakdown.push({ label: "Production", pts: +prodPts.toFixed(2) });
  }

  return { score: +score.toFixed(2), breakdown };
}

export function recommend(userPrefs, songs, k = 5, scoringMode = "mood_priority") {
  const scored = songs.map((song) => ({
    song,
    ...scoreSong(userPrefs, song, scoringMode),
  }));

  scored.sort((a, b) => b.score - a.score);

  // Artist diversity: max one song per artist
  const seen = new Set();
  const results = [];
  for (const entry of scored) {
    if (results.length >= k) break;
    if (!seen.has(entry.song.artist)) {
      seen.add(entry.song.artist);
      results.push(entry);
    }
  }

  // Backfill if not enough unique artists
  if (results.length < k) {
    for (const entry of scored) {
      if (results.length >= k) break;
      if (!results.includes(entry)) {
        results.push(entry);
      }
    }
  }

  return results;
}

export const GENRES = [
  "alternative rock", "ambient", "classical", "disco", "funk",
  "indie pop", "indie rock", "jazz", "lofi", "metal",
  "pop", "reggae", "rock", "synth-pop", "synthwave",
];

export const MOODS = [
  "aggressive", "chill", "dreamy", "energetic", "euphoric",
  "focused", "happy", "intense", "melancholic", "moody",
  "nostalgic", "relaxed", "upbeat",
];
