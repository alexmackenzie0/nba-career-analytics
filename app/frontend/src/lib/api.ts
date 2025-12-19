const base = import.meta.env.VITE_API_BASE ?? "";

export async function fetchPlayers() {
  const res = await fetch(`${base}/players`);
  if (!res.ok) throw new Error(`players ${res.status}`);
  return res.json();
}

export async function fetchTrajectory(id: number) {
  const res = await fetch(`${base}/player/${id}/trajectory`);
  if (!res.ok) throw new Error(`trajectory ${res.status}`);
  return res.json();
}

export async function fetchComps(id: number) {
  const res = await fetch(`${base}/player/${id}/comps`);
  if (!res.ok) throw new Error(`comps ${res.status}`);
  return res.json();
}

export async function fetchCompsCounting(id: number) {
  const res = await fetch(`${base}/player/${id}/comps_counting`);
  if (!res.ok) throw new Error(`comps_counting ${res.status}`);
  return res.json();
}

export async function fetchCountingGeometry(id: number) {
  const res = await fetch(`${base}/player/${id}/counting_geometry`);
  if (!res.ok) throw new Error(`counting_geometry ${res.status}`);
  return res.json();
}

export async function fetchLabel(id: number) {
  const res = await fetch(`${base}/player/${id}/label`);
  if (!res.ok) throw new Error(`label ${res.status}`);
  return res.json();
}

export async function fetchProjection(id: number) {
  const res = await fetch(`${base}/player/${id}/projection`);
  if (!res.ok) throw new Error(`projection ${res.status}`);
  return res.json();
}

export async function fetchRadar(id: number) {
  const res = await fetch(`${base}/player/${id}/radar`);
  if (!res.ok) throw new Error(`radar ${res.status}`);
  return res.json();
}

export async function fetchForecast(id: number) {
  const res = await fetch(`${base}/player/${id}/forecast`);
  if (!res.ok) throw new Error(`forecast ${res.status}`);
  return res.json();
}
