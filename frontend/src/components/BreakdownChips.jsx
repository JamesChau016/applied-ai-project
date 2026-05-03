export default function BreakdownChips({ breakdown }) {
  return (
    <div className="chips">
      {breakdown.map((b, i) => (
        <span key={i} className={`chip ${b.pts < 0 ? "chip--neg" : ""}`}>
          {b.label}{" "}
          <strong>
            {b.pts > 0 ? "+" : ""}
            {b.pts}
          </strong>
        </span>
      ))}
    </div>
  );
}
