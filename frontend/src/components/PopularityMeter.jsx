export default function PopularityMeter({ value }) {
  const segments = 10;
  const filled = Math.round((value / 100) * segments);
  return (
    <div className="pop-meter" title={`Popularity: ${value}`}>
      {Array.from({ length: segments }, (_, i) => (
        <div
          key={i}
          className={`pop-seg ${i < filled ? "pop-seg--lit" : ""}`}
          style={{ animationDelay: `${i * 0.04}s` }}
        />
      ))}
      <span className="pop-val">{value}</span>
    </div>
  );
}
