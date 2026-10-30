"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [alarms, setAlarms] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [debugError, setDebugError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [selectedAlarm, setSelectedAlarm] = useState(null);

  async function load() {
    try {
      const [a, c] = await Promise.all([
        fetch(`${API}/api/v1/alarms`, { cache: "no-store" }),
        fetch(`${API}/api/v1/cameras`, { cache: "no-store" }),
      ]);
      if (!a.ok || !c.ok) {
        throw new Error(`API request failed: alarms=${a.status}, cameras=${c.status}`);
      }
      const [alarmData, cameraData] = await Promise.all([a.json(), c.json()]);
      setAlarms(alarmData);
      setCameras(cameraData);
      setDebugError("");
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Dashboard refresh failed", error);
      setDebugError(error instanceof Error ? error.message : String(error));
    }
  }

  async function acknowledge(id) {
    const response = await fetch(`${API}/api/v1/alarms/${id}/acknowledge`, { method: "POST" });
    if (!response.ok) throw new Error(`Acknowledge failed: ${response.status}`);
    await load();
  }

  async function showDetails(id) {
    const response = await fetch(`${API}/api/v1/alarms/${id}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Alarm details failed: ${response.status}`);
    setSelectedAlarm(await response.json());
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  const activeCount = alarms.filter((a) => a.status === "NEW").length;
  return (
    <main style={{ padding: 32, fontFamily: "Arial, sans-serif", background: "#f4f6f8", minHeight: "100vh", color: "#17202a" }}>
      <h1>CCTV AI Monitoring</h1>
      <p>Remote Security Operations Dashboard</p>
      <p style={{ color: "#666", fontSize: 12 }}>Last successful refresh: {lastUpdated || "not yet"}</p>
      {debugError && <section role="alert" style={{ marginTop: 16, padding: 16, background: "#fff0f0", border: "1px solid #e0a0a0", borderRadius: 8 }}><strong>Dashboard/API error</strong><div>{debugError}</div><button onClick={load} style={{ marginTop: 8 }}>Retry now</button></section>}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <Card title="CAMERAS" value={cameras.length} />
        <Card title="ACTIVE ALARMS" value={activeCount} />
        <Card title="TOTAL ALARMS" value={alarms.length} />
      </div>
      <section style={{ marginTop: 32, background: "white", padding: 24, borderRadius: 12 }}>
        <h2>Recent Alarms</h2>
        {alarms.length === 0 && <p>No alarms</p>}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {alarms.map((alarm) => (
            <article key={alarm.id} style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 14, minWidth: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                <strong>{(alarm.event_type || "AI").toUpperCase()} ALERT</strong>
                <span style={{ fontSize: 12, padding: "4px 8px", borderRadius: 12, background: alarm.status === "NEW" ? "#fee2e2" : "#e5e7eb" }}>{alarm.status}</span>
            </div>
              <div style={{ color: "#666", fontSize: 12, marginTop: 6 }}>{new Date(alarm.triggered_at).toLocaleString()}</div>
              <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <Snapshot label="Original" src={alarm.snapshot_url} />
                <Snapshot label="AI Annotated" src={alarm.annotated_snapshot_url} />
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                <button onClick={() => showDetails(alarm.id)}>View details</button>
                {alarm.status === "NEW" && <button onClick={() => acknowledge(alarm.id)}>Acknowledge</button>}
          </div>
            </article>
        ))}
        </div>
      </section>
      {selectedAlarm && (
        <div role="dialog" aria-modal="true" aria-label="Alarm details" onClick={() => setSelectedAlarm(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.55)", display: "grid", placeItems: "center", padding: 20, zIndex: 10 }}>
          <section onClick={(event) => event.stopPropagation()} style={{ background: "white", borderRadius: 12, padding: 24, width: "min(900px, 100%)", maxHeight: "90vh", overflow: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><h2>Alarm details</h2><button onClick={() => setSelectedAlarm(null)}>Close</button></div>
            <p><strong>Event:</strong> {selectedAlarm.event.event_type} · <strong>Confidence:</strong> {(selectedAlarm.event.confidence * 100).toFixed(1)}%</p>
            <p><strong>Camera:</strong> {selectedAlarm.event.camera_id} · <strong>Time:</strong> {new Date(selectedAlarm.event.timestamp).toLocaleString()}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
              <Snapshot label="Original snapshot" src={selectedAlarm.event.snapshot_url} large />
              <Snapshot label="AI annotated snapshot" src={selectedAlarm.event.annotated_snapshot_url} large />
            </div>
            <h3>Detection metadata</h3><pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", background: "#f4f6f8", padding: 12, borderRadius: 8 }}>{JSON.stringify(selectedAlarm.event.metadata || {}, null, 2)}</pre>
          </section>
        </div>
      )}
    </main>
  );
}

function Snapshot({ label, src, large = false }) {
  return <div style={{ minWidth: 0 }}><div style={{ fontSize: 12, color: "#555", marginBottom: 5 }}>{label}</div>{src ? <a href={src} target="_blank" rel="noreferrer"><img src={src} alt={label} loading="lazy" style={{ width: "100%", height: large ? "auto" : 130, maxHeight: large ? "none" : 160, objectFit: "contain", background: "#111", borderRadius: 6 }} /></a> : <div style={{ height: large ? 180 : 130, display: "grid", placeItems: "center", background: "#eef0f2", color: "#777", borderRadius: 6, fontSize: 12 }}>Snapshot unavailable</div>}</div>;
}

function Card({ title, value }) {
  return <div style={{ background: "white", padding: 24, borderRadius: 12, minWidth: 180 }}><div>{title}</div><strong style={{ fontSize: 32 }}>{value}</strong></div>;
}
