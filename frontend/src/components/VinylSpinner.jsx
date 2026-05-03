export default function VinylSpinner({ spinning }) {
  return (
    <div className={`vinyl ${spinning ? "vinyl--spin" : ""}`}>
      <div className="vinyl-groove vinyl-groove--1" />
      <div className="vinyl-groove vinyl-groove--2" />
      <div className="vinyl-groove vinyl-groove--3" />
      <div className="vinyl-label">
        <div className="vinyl-hole" />
      </div>
    </div>
  );
}
