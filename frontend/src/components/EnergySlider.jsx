export default function EnergySlider({ value, onChange }) {
  const pct = value * 100;
  return (
    <div className="slider-wrap">
      <div className="slider-track">
        <div className="slider-fill" style={{ width: `${pct}%` }} />
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        onChange={(e) => onChange(+e.target.value)}
      />
      <div className="slider-labels">
        <span>Calm</span>
        <span className="slider-value">{value.toFixed(2)}</span>
        <span>Intense</span>
      </div>
    </div>
  );
}
