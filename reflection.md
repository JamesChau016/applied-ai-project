# Reflection: Music Recommender Testing & Experiments

## Profile Comparison Analysis

### My Taste Profile vs. Pop Fan

**My Taste:** Alternative rock, moody, 0.45 energy, acoustic=True  
**Pop Fan:** Pop, happy, 0.8 energy, acoustic=False

**Key Difference:** My profile's top recommendation is "Night Drive Loop" (5.00 pts), a synthwave track with the exact moody mood match (+4.0), while Pop Fan's top is "Sunrise City" (7.75 pts), a pop song with happy mood match (+2.0 from halved importance). Pop Fan achieves higher scores because:

- Happy mood is more common in the catalog's high-energy songs (avg 0.82 energy)
- Energy proximity to 0.8 yields maximum points (2.5 pts) for many songs
- Pop genre has 3 dedicated songs; alternative rock has none

This reveals the system favors energetic, upbeat listeners over introspective ones.

---

### My Taste Profile vs. Lo-Fi Chill

**My Taste:** Alternative rock, moody, 0.45 energy, acoustic=True  
**Lo-Fi Chill:** Lo-fi, chill, 0.4 energy, acoustic=True

**Key Difference:** Lo-Fi Chill scores drastically higher (top: 9.20 pts vs. 5.00 pts). Both users want low energy, but Lo-Fi Chill benefits from:

- Genre match: 2 dedicated lofi + chill songs in the catalog (Midnight Coding, Library Rain)
- Perfect energy matches: both songs hit exactly 0.35-0.42 energy
- My Taste has no alternative rock songs in the catalog, so it gets 0 pts for genre match and must settle for "related genre" songs

This shows how **genre representation determines recommendation quality**—users with niche tastes (alternative rock) get worse scores than users with well-stocked genres (lofi).

---

### Lo-Fi Chill vs. Indie Melancholic

**Lo-Fi Chill:** Lofi, chill, 0.4 energy, acoustic=True  
**Indie Melancholic:** Indie rock, melancholic, 0.65 energy, acoustic=True

**Key Difference:** Lo-Fi Chill peaks at 9.20 pts while Indie Melancholic peaks at 8.60 pts, but they share the same "likes*acoustic" preference. The gap stems from energy availability: Lo-Fi Chill's target energy (0.4) has 8/20 songs within ±0.3 range, while Indie Melancholic's target (0.65) competes with 17/20 songs. Paradoxically, Indie Melancholic has \_more* matching songs available, but they're spread across many moods/genres, diluting the top scores. Additionally, Indie Melancholic's 2 indie rock + melancholic matches (505, Broken Hearts) are forced to be ranked #1 and #2 because no other songs satisfy both constraints—creating a **echo chamber effect**.

---

### Pop Fan vs. Lo-Fi Chill

**Pop Fan:** Pop, happy, 0.8 energy, acoustic=False  
**Lo-Fi Chill:** Lofi, chill, 0.4 energy, acoustic=True

**Key Difference:** Pop Fan and Lo-Fi Chill have zero overlapping top-5 songs, demonstrating how strongly energy and genre separate the recommendation space. Pop Fan's recommendations (Sunrise City, Rooftop Lights, Dancing Queen) all cluster around 0.76–0.88 energy with happy moods, while Lo-Fi Chill's (Midnight Coding, Library Rain) sit at 0.35–0.42 energy with chill moods. The 0.4 energy gap between them eliminates all shared matches—each user literally inhabits a different sub-catalog. This shows the energy bandwidth is acting as a **hard partition**, not a soft preference.

---

### Pop Fan vs. Indie Melancholic

**Pop Fan:** Pop, happy, 0.8 energy, acoustic=False  
**Indie Melancholic:** Indie rock, melancholic, 0.65 energy, acoustic=True

**Key Difference:** Pop Fan's top songs all exceed 7.0 pts (high scores), while Indie Melancholic's drop to 2.25 pts for #5. Pop Fan benefits from an abundance of happy, high-energy songs (9 songs at 0.8+ energy), while Indie Melancholic must accept mood mismatches to fill its top-5. Notably, they share almost no songs: Pop Fan avoids indie rock (related genre, only 0.75 pts) and moody sounds, while Indie Melancholic rejects pop (0 pts match) and high-valence songs (-0.25 penalty). The mood weight (4.0 pts) creates such a strong barrier that genre similarity cannot overcome it.

---

### My Taste Profile vs. Indie Melancholic

**My Taste:** Alternative rock, moody, 0.45 energy, acoustic=True  
**Indie Melancholic:** Indie rock, melancholic, 0.65 energy, acoustic=True

**Key Difference:** Both profiles love moody-adjacent moods and acoustic sounds, but Indie Melancholic scores 70% higher (8.60 vs. 5.00). The reason: energy fit. Indie Melancholic's 0.65 target energy perfectly matches the two indie rock songs (505: 0.65, Broken Hearts: 0.68), unlocking the maximum 2.5 energy bonus. My Taste's 0.45 energy target misses all indie rock songs (which average 0.66), forcing it to settle for "similar mood" matches with non-indie songs like Night Drive Loop (synthwave, not indie rock). This reveals how **energy acts as a hard constraint that can override genre preference**, even for users with compatible mood tastes.

---

## Key Insight: The Energy Bandwidth Problem

Across all comparisons, the ±0.3 energy tolerance creates invisible walls between user groups. Users at energy 0.4 never see songs at 0.8; users at 0.8 rarely venture below 0.65. This explains why the conflicting profile (sad mood + 0.95 energy) scores so poorly—**the energy requirement (0.95) filters away all sad songs (avg 0.56–0.75)**, creating the mathematical impossibility we observed.

---

## Plain Language Example: Why "Gym Hero" Shows Up for "Happy Pop" Users

Imagine you tell the recommender: "I want happy pop music." You'd think it would only show you pop songs that sound happy and upbeat. But "Gym Hero" by Max Pulse keeps appearing in the results even though it's labeled "intense," not "happy."

**Here's why:** The recommender uses a point system with multiple criteria:

1. **Genre match** (pop): +1.5 points ✓
2. **Energy match** (0.93 vs your target 0.8): +1.5 points ✓
3. **Mood match** (intense vs happy): 0 points ✗
4. **Valence penalty** (too happy/bright): -0.25 points

So "Gym Hero" scores ~2.75 points. The problem is that it still beats out many other songs because it nails two major criteria (genre and energy), even though it fails on mood. The system doesn't say "no mood match = reject"; it says "no mood match = 0 points, but let's still compare you to other songs."

For users wanting sad + high-energy music (the conflicting profile), "Gym Hero" actually ranks #1—not because it's sad, but because no truly sad songs exist at that energy level, so the system picks the best available match, which is a pop song with the right energy.

**The lesson:** Recommender systems can't always satisfy all preferences at once. When you want an impossible combination (sad + maximum energy), the system has to compromise, and you get recommendations that feel off-theme.
