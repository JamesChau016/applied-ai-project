/**
 * Discovery pipeline — calls the backend RAG agent to find new songs.
 *
 * The RAG agent (src/rag_agent.py) handles:
 *   1. Profile analysis from the user's playlist
 *   2. Broad retrieval from TheAudioDB (favorite + genre-related artists)
 *   3. Semantic ranking via sentence-transformers (all-MiniLM-L6-v2)
 *   4. Artist diversity filtering
 *   5. Excluding all 20 local catalog songs
 */

/**
 * Discover new songs by sending the user's playlist to the RAG agent.
 * @param {Array} playlistSongs - full song objects from the playlist
 * @param {number} k - number of results to return
 * @param {object} preferences - optional discovery preferences
 * @returns {Promise<{recommendations: Array, explanation: string}>}
 */
export async function discoverSongs(playlistSongs, k = 10, preferences = null) {
  const resp = await fetch("http://localhost:5000/api/discover", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playlist: playlistSongs, k, preferences }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `Server error ${resp.status}`);
  }

  const data = await resp.json();
  return {
    recommendations: (data.recommendations || []).map((rec, i) => ({
      song: {
        id: `discover_${i}_${rec.title}`,
        title: rec.title,
        artist: rec.artist,
        genre: rec.genre || "unknown",
        mood: rec.mood || "unknown",
        energy: typeof rec.energy === "number" ? rec.energy : 0.5,
        tempo_bpm: rec.tempo_bpm ?? 120,
        valence: rec.valence ?? 0.5,
        danceability: rec.danceability ?? 0.5,
        acousticness: rec.acousticness ?? 0.3,
        popularity: rec.popularity ?? 50,
        release_year: rec.release_year ?? 2020,
        instrumentalness: rec.instrumentalness ?? 0.1,
        lyrical_sentiment: rec.lyrical_sentiment ?? 0.0,
        production_complexity: rec.production_complexity ?? 0.5,
        source: rec.source || "audiodb",
      },
      score: +(rec.similarity * 10).toFixed(1),
      breakdown: [
        { label: "Semantic match", pts: +(rec.similarity * 10).toFixed(2) },
      ],
      reason: rec.reason,
    })),
    explanation: data.overall_explanation || "",
  };
}
