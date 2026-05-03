import { motion } from "motion/react";

export default function ScoreBar({ score, maxScore = 15 }) {
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
