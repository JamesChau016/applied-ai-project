# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**MoodMatch 1.0**

A simple content-based music recommender that scores songs based on mood, energy, and genre preferences.

---

## 2. Intended Use

**What it does:** MoodMatch suggests 5 songs from a small catalog (20 songs) based on what mood, genre, and energy level you tell it you want.

**Who it's for:** This is for learning and classroom exploration. It's a toy system, not a real app.

**Key assumption:** The model assumes your taste is based on three things: favorite genre, favorite mood, target energy level, and whether you like acoustic sounds. It doesn't know about artist loyalty, lyrics, or cultural trends.

---

## 3. How the Model Works

Think of MoodMatch like a grading system for songs:

1. **Mood match** (up to 4 points): Does the song's mood match what you want? Perfect match = 4 pts. Similar mood (e.g., melancholic vs. moody) = 2 pts. No match = 0 pts.

2. **Energy proximity** (up to 2.5 points): Is the song's energy close to your target? Within ±0.1 = 2.5 pts. Within ±0.2 = 1.5 pts. Within ±0.3 = 1.0 pt. Too far away = 0 pts and the song is basically hidden.

3. **Genre** (up to 1.5 points): Does the genre match? Exact match = 1.5 pts. Related genre = 0.75 pts. Different = 0 pts.

4. **Acousticness** (up to 1.2 points): If you like acoustic sounds, songs with high acousticness get a bonus (1.2 pts for >0.7, 0.6 pts for 0.4–0.7).

5. **Valence** (mood brightness): Songs with very low emotional brightness (+0.5 pts) or very high brightness (-0.25 pts).

The system adds up all the points for every song, then shows you the top 5 in order. That's it!

---

## 4. Data

**Size:** 20 songs in the catalog.

**Genres:** Pop, lofi, alternative rock, indie rock, synthwave, ambient, jazz, funk, classical, metal, reggae, disco.

**Moods:** Happy, chill, moody, melancholic, intense, energetic, upbeat, euphoric, relaxed, focused, dreamy, aggressive, nostalgic.

**What's missing:** Only 3 songs with low energy (0.0–0.4). No songs labeled "sad." No heavy metal or K-pop. No songs with conflicting properties (like sad music that's also high-energy). This skews the recommender toward happy, high-energy users.

---

## 5. Strengths

**Works great for:** Pop fans (happy, high-energy), lo-fi study session lovers, and indie rock fans who want moody recommendations.

**What it gets right:** If you want "happy pop at 0.8 energy," it nails it. The top recommendation will almost always match your mood and genre. Energy proximity scoring is smart for users whose target energy is common (0.5–0.8 range has 55–85% of songs).

**Transparency:** You can see exactly why each song was recommended because every point category is explained. No black box.

---

## 6. Limitations and Bias

**Energy Gap Filter Bubble:** Songs outside ±0.3 of your target energy get zero points and disappear. Only 15% of songs are low-energy (0.0–0.4), but 45% are high-energy (0.8–1.0). This creates a 3x disparity: a high-energy user sees 14–17 options, while a low-energy user sees 6. If you want "moody + high-energy," there are zero songs that satisfy both (moody songs average 0.56–0.75 energy).

**Genre and Mood Echo Chambers:** Only 2 genre-mood combinations have multiple songs: indie rock + melancholic (2 songs), and lofi + chill (2 songs). Users asking for these exact preferences will see the same 2 songs ranked #1 and #2 every time.

**Acousticness Bias:** The 1.2-point acoustic bonus is the 3rd-biggest scoring component. It concentrates recommendations to just 6 acoustic songs, especially hurting users who like both acoustic AND high-energy (most high-energy songs are synthesizers, not guitars).

**Mood Dominance:** Because mood is worth 4 points (40% of max score), a mood mismatch is hard to overcome. "Happy pop" users will never see an "intense" song in the top 5, even if it's a perfect energy match.

---

## 7. Evaluation

**Profiles tested:**

- Your Taste: Alternative rock, moody, 0.45 energy, acoustic=True
- Pop Fan: Pop, happy, 0.8 energy, acoustic=False
- Lo-Fi Chill: Lofi, chill, 0.4 energy, acoustic=True
- Indie Melancholic: Indie rock, melancholic, 0.65 energy, acoustic=True
- Conflicting Mood-Energy: Pop, sad, 0.95 energy, acoustic=False

**What I looked for:** Did the top songs make sense? Did users with similar tastes get similar recommendations? Did opposite preferences get opposite results?

**Biggest surprise:** The conflicting profile (sad mood + 0.95 energy) scored extremely low (3.0–3.75 pts vs. 7–9 for others). I expected mood to win, but energy constraint was so strict it filtered away all sad songs, leaving only high-energy happy/intense songs. The math literally makes that combination impossible.

**Key finding:** Energy acts as a hard wall, not a soft preference. Users at 0.4 energy and users at 0.8 energy see completely different catalogs with zero overlap.

---

## 8. Future Work

1. **Soften the energy penalty.** Instead of 0 points for >0.3 gap, use a sliding scale (1.0 pt for 0.3 gap, 0.5 for 0.45 gap). This would help low-energy users see more songs.

2. **Expand the dataset.** Add more low-energy songs, more sad/moody songs, and songs that break stereotypes (sad + high-energy, chill + electronic). Right now the data reflects only narrow taste profiles.

3. **Handle contradictions.** For users asking for impossible combinations, explicitly say "I can only find X out of Y preferences" instead of silently showing wrong data.

4. **Add artist diversity.** Right now if a song is perfect, you'll see the same artist multiple times. Add a "don't repeat artists too much" rule.

---

## 9. Personal Reflection

Building this recommender taught me that **systems aren't neutral—they encode human choices that become invisible.** I thought mood was the most important factor (giving it 4 points), but the energy tolerance ±0.3 turned out to be the real kingmaker. It silently filters away 70% of songs before mood even gets considered.

The conflicting profile was the aha moment. I designed it thinking "let's see if the system can be tricked." But it wasn't a trick—it revealed that some user combinations are **mathematically unsolvable** by the algorithm. That's not a bug; it's a feature of my choices.

Most eye-opening: **the system doesn't lie, but it hides.** It shows you the "best matches," but you don't see the thousands of songs it rejected at the energy filter. Real Spotify or Apple Music probably have the same problem, just at a much larger scale. The difference is they have millions of songs, so there's always _something_ that fits. I have 20 songs, so the gaps become obvious.

This changed how I think about recommendations: **they're not objective rankings of similarity; they're reflections of what data the designer had and what tradeoffs they chose to make.**
