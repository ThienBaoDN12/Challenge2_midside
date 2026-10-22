const STEPS = [
  { title: "TideCloak access", sub: "Sign in securely" },
  { title: "Trade side", sub: "Choose your market role" },
  { title: "Organization profile", sub: "Tell partners about you" },
];

export default function Stepper({ current }) {
  return (
    <ol className="stepper">
      {STEPS.map((s, i) => {
        const n = i + 1;
        const cls = n === current ? "is-active" : n < current ? "is-done" : "";
        return (
          <li key={n} className={`stepper__item ${cls}`}>
            <span className="stepper__dot">{n < current ? "✓" : n}</span>
            <span className="stepper__text">
              <b>{s.title}</b>
              <small>{s.sub}</small>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
