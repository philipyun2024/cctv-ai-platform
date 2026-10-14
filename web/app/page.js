"use client";

import { useEffect, useState } from "react";

const API = "http://localhost:8000";

export default function Home() {
  const [alarms, setAlarms] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [debugError, setDebugError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  async function load() {
    try {
      const [a, c] = await Promise.all([
        fetch(`${API}/api/v1/alarms`),
        fetch(`${API}/api/v1/cameras`),
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
    await fetch(`${API}/api/v1/alarms/${id}/acknowledge`, {
      method: "POST",
    });
    await load();
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <main style={{ padding: 32, fontFamily: "Arial", background: "#f4f6f8", minHeight: "100vh" }}>
      <h1>CCTV AI Monitoring</h1>
      <p>Remote Security Operations Dashboard</p>
      <p style={{ color: "#666", fontSize: 12 }}>Last successful refresh: {lastUpdated || "not yet"}</p>
      {debugError && (
        <section role="alert" style={{ marginTop: 16, padding: 16, background: "#fff0f0", border: "1px solid #e0a0a0", borderRadius: 8 }}>
          <strong>Dashboard/API error</strong>
          <div>{debugError}</div>
          <div style={{ marginTop: 8, fontSize: 12 }}>Check that Cloud API is running at {API}, then inspect `docker compose logs -f cloud-api`.</div>
          <button onClick={load} style={{ marginTop: 8 }}>Retry now</button>
        </section>
      )}
      <div style={{ display: "flex", gap: 16 }}>
        <Card title="CAMERAS" value={cameras.length} />
        <Card title="ACTIVE ALARMS" value={alarms.filter((a) => a.status === "NEW").length} />
        <Card title="TOTAL ALARMS" value={alarms.length} />
      </div>
      <section style={{ marginTop: 32, background: "white", padding: 24, borderRadius: 12 }}>
        <h2>Recent Alarms</h2>
        {alarms.length === 0 && <p>No alarms</p>}
        {alarms.map((alarm) => (
          <div key={alarm.id} style={{ display: "flex", justifyContent: "space-between", padding: 16, borderBottom: "1px solid #eee" }}>
            <div>
              <strong>{alarm.severity} ALERT</strong>
              <div>{alarm.id.slice(0, 8)} · {alarm.status}</div>
            </div>
            {alarm.status === "NEW" && (
              <button onClick={() => acknowledge(alarm.id)}>Acknowledge</button>
            )}
          </div>
        ))}
      </section>
    </main>
  );
}

function Card({ title, value }) {
  return (
    <div style={{ background: "white", padding: 24, borderRadius: 12, minWidth: 180 }}>
      <div>{title}</div>
      <strong style={{ fontSize: 32 }}>{value}</strong>
    </div>
  );
}
