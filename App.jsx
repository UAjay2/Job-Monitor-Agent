/**
 * App.jsx
 * -------
 * The dashboard UI. Fetches listings from the Flask API, displays them in a
 * color-coded table, and lets the user trigger a manual scan or mark a
 * listing's status. Written as a single component to keep the starter
 * project simple -- split into smaller components once it grows.
 *
 * Setup: this expects a Vite or Create-React-App project. Drop this file
 * in as src/App.jsx and make sure axios is installed (npm install axios).
 */

import { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://localhost:5000/api";

// Maps each category to a color so the table is scannable at a glance.
const CATEGORY_COLORS = {
  "Apply First": "#2e7d32", // green
  "Good Match": "#f9a825", // yellow
  Stretch: "#c62828", // red
};

function App() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanMessage, setScanMessage] = useState("");

  // Load listings once when the page first opens
  useEffect(() => {
    fetchListings();
  }, []);

  const fetchListings = async () => {
    try {
      const res = await axios.get(`${API_BASE}/listings`);
      setListings(res.data);
    } catch (err) {
      console.error("Failed to load listings:", err);
    }
  };

  // Calls the Flask "run now" endpoint, waits for the agent cycle to
  // finish, then refreshes the table with whatever it found.
  const triggerScan = async () => {
    setLoading(true);
    setScanMessage("");
    try {
      const res = await axios.post(`${API_BASE}/trigger-scan`);
      setScanMessage(
        `Found ${res.data.listings_found} listings, ${res.data.new_matches} new matches.`,
      );
      await fetchListings();
    } catch (err) {
      setScanMessage("Scan failed -- check the Flask server logs.");
    } finally {
      setLoading(false);
    }
  };

  // Optimistically updates the UI, then tells the backend the new status.
  const updateStatus = async (id, status) => {
    setListings((prev) =>
      prev.map((l) => (l.id === id ? { ...l, status } : l)),
    );
    await axios.post(`${API_BASE}/listings/${id}/status`, { status });
  };

  return (
    <div
      style={{ fontFamily: "sans-serif", maxWidth: 900, margin: "2rem auto" }}
    >
      <h1>Job Monitor Dashboard</h1>

      <button onClick={triggerScan} disabled={loading}>
        {loading ? "Scanning..." : "Run Scan Now"}
      </button>
      {scanMessage && <p>{scanMessage}</p>}

      <table
        style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}
      >
        <thead>
          <tr>
            <th style={cellStyle}>Title</th>
            <th style={cellStyle}>Company</th>
            <th style={cellStyle}>Fit Score</th>
            <th style={cellStyle}>Category</th>
            <th style={cellStyle}>Status</th>
            <th style={cellStyle}>Apply</th>
          </tr>
        </thead>
        <tbody>
          {listings.map((job) => (
            <tr key={job.id}>
              <td style={cellStyle}>{job.title}</td>
              <td style={cellStyle}>{job.company}</td>
              <td style={cellStyle}>{job.fit_score}%</td>
              <td
                style={{ ...cellStyle, color: CATEGORY_COLORS[job.category] }}
              >
                {job.category}
              </td>
              <td style={cellStyle}>
                <select
                  value={job.status}
                  onChange={(e) => updateStatus(job.id, e.target.value)}
                >
                  <option value="new">New</option>
                  <option value="applied">Applied</option>
                  <option value="ignored">Ignored</option>
                </select>
              </td>
              <td style={cellStyle}>
                <a href={job.apply_link} target="_blank" rel="noreferrer">
                  Open
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {listings.length === 0 && (
        <p>No listings yet -- click "Run Scan Now" to start.</p>
      )}
    </div>
  );
}

const cellStyle = {
  border: "1px solid #ddd",
  padding: "8px",
  textAlign: "left",
};

export default App;
