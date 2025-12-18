type Props = { label: string };

export default function LabelCard({ label }: Props) {
  return (
    <section className="card">
      <h3>Label</h3>
      <p className="label">{label || "—"}</p>
    </section>
  );
}
