"use client";

import { useEffect, useState } from "react";

const API = "http://localhost:8000";

export default function Home() {
  const [alarms, setAlarms] = useState([]);
  const [cameras, setCameras] = useState([]);

  async function load() {
    const [a, c] = await Promise.all([
      fetch(`${API}/api/v1/alarms`),
      fetch(`${API}/api/v1/cameras`),
    ]);
    setAlarms(await a.json());
    setCameras(await c.json());
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
