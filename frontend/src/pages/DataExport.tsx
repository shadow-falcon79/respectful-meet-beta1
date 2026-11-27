import { useState } from "react";
import SubPageHeader from "../components/SubPageHeader";
import { fetchMyDataExport } from "../api/privacy";

function download(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function DataExport() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleExport() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyDataExport();
      const stamp = new Date().toISOString().slice(0, 10);
      download(`respectful-meet-data-export-${stamp}.json`, data);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't generate your export. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <SubPageHeader title="Export my data" backTo="/profile/settings" />
      <div className="stack" style={{ marginTop: 16 }}>
        <article className="card" style={{ padding: 18 }}>
          <p>
            Download a copy of everything tied to your account: your profile, photos, likes, matches,
            blocked users, reports you've filed, message metadata, subscriptions, payments, and
            notifications — as a single JSON file.
          </p>
        </article>
        {error && <span className="error-text">{error}</span>}
        {done && !error && <span>Your export downloaded successfully.</span>}
        <button className="btn btn-primary" onClick={handleExport} disabled={loading}>
          {loading ? "Preparing your export..." : "Download my data"}
        </button>
      </div>
    </section>
  );
}
