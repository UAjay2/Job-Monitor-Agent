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
  "Good Match": "#f9a825",  // yellow
  Stretch: "#c62828",       // red
};

function App() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanMessage, setScanMessage] = useState("");

  // Profile form state -- what gets sent to POST /api/profile
  const [profile, setProfile] = useState({
    skills: "",
    target_roles: "",
    location: "",
    resume_text: "",
  });
  const [profileMessage, setProfileMessage] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [showProfileForm, setShowProfileForm] = useState(false);

  // Load listings AND any previously saved profile once when the page opens
  useEffect(() => {
    fetchListings();
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await axios.get(`${API_BASE}/profile`, { timeout: 90000 });
      setProfile(res.data);
    } catch (err) {
      // A 404 here just means no profile has been saved yet -- not an error
      // worth showing the user, so we stay quiet and leave the form empty.
    }
  };

  const handleProfileChange = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const saveProfile = async () => {
    setSavingProfile(true);
    setProfileMessage("Saving...");
    try {
      await axios.post(`${API_BASE}/profile`, profile, { timeout: 90000 });
      setProfileMessage("Profile saved. You can now run a scan.");
    } catch (err) {
      setProfileMessage("Failed to save -- check that all fields are filled in and try again.");
    } finally {
      setSavingProfile(false);
    }
  };

  const fetchListings = async () => {
    try {
      const res = await axios.get(`${API_BASE}/listings`);
      setListings(res.data);
    } catch (err) {
      console.error("Failed to load listings:", err);
    }
  };

  // Calls the Flask "run now" endpoint, waits for the agent cycle to
  // finish, then refreshes the table with whatever it found. Render's free
  // tier can take 30-60s to wake from sleep, so we allow a long timeout
  // and tell the user what's happening instead of failing immediately.
  const triggerScan = async () => {
    setLoading(true);
    setScanMessage("Waking up server (can take up to a minute if it was idle)...");
    try {
      const res = await axios.post(`${API_BASE}/trigger-scan`, {}, { timeout: 90000 });
      if (res.data.error) {
        setScanMessage(`Scan couldn't run: ${res.data.error}. Try re-saving your profile.`);
      } else {
        setScanMessage(
          `Found ${res.data.listings_found} listings, ${res.data.new_matches} new matches.`
        );
      }
      await fetchListings();
    } catch (err) {
      setScanMessage(
        "Scan failed -- the server may still be waking up. Wait a few seconds and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // Optimistically updates the UI, then tells the backend the new status.
  const updateStatus = async (id, status) => {
    setListings((prev) =>
      prev.map((l) => (l.id === id ? { ...l, status } : l))
    );
    await axios.post(`${API_BASE}/listings/${id}/status`, { status });
  };

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 900, margin: "2rem auto" }}>
      <h1>Job Monitor Dashboard</h1>

      <button onClick={() => setShowProfileForm((prev) => !prev)}>
        {showProfileForm ? "Hide Profile Form" : "Edit My Profile"}
      </button>

      {showProfileForm && (
        <div style={formStyle}>
          <h3>Your Profile</h3>
          <p style={{ fontSize: "0.85rem", color: "#555" }}>
            This is what the agent compares job listings against. Fill this in
            once, then update it any time your target roles or skills change.
          </p>

          <label style={labelStyle}>Skills (comma-separated)</label>
          <input
            style={inputStyle}
            type="text"
            value={profile.skills}
            placeholder="Python, Flask, React, SQL, NLP"
            onChange={(e) => handleProfileChange("skills", e.target.value)}
          />

          <label style={labelStyle}>Target Roles (comma-separated)</label>
          <input
            style={inputStyle}
            type="text"
            value={profile.target_roles}
            placeholder="Business Analyst, Data Analyst, Junior Developer"
            onChange={(e) => handleProfileChange("target_roles", e.target.value)}
          />

          <label style={labelStyle}>Location</label>
          <input
            style={inputStyle}
            type="text"
            value={profile.location}
            placeholder="Hyderabad"
            onChange={(e) => handleProfileChange("location", e.target.value)}
          />

          <label style={labelStyle}>Resume Text (paste your full resume content)</label>
          <textarea
            style={{ ...inputStyle, height: "160px" }}
            value={profile.resume_text}
            placeholder="Paste your resume text here -- skills, projects, education, experience..."
            onChange={(e) => handleProfileChange("resume_text", e.target.value)}
          />

          <button onClick={saveProfile} disabled={savingProfile} style={{ marginTop: "0.5rem" }}>
            {savingProfile ? "Saving..." : "Save Profile"}
          </button>
          {profileMessage && <p>{profileMessage}</p>}
        </div>
      )}

      <div style={{ marginTop: "1.5rem" }}>
        <button onClick={triggerScan} disabled={loading}>
          {loading ? "Scanning..." : "Run Scan Now"}
        </button>
        {scanMessage && <p>{scanMessage}</p>}
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
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
              <td style={{ ...cellStyle, color: CATEGORY_COLORS[job.category] }}>
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

      {listings.length === 0 && <p>No listings yet -- click "Run Scan Now" to start.</p>}
    </div>
  );
}

const cellStyle = {
  border: "1px solid #ddd",
  padding: "8px",
  textAlign: "left",
};

const formStyle = {
  border: "1px solid #ddd",
  borderRadius: "8px",
  padding: "1rem",
  marginTop: "1rem",
  backgroundColor: "#fafafa",
};

const labelStyle = {
  display: "block",
  marginTop: "0.75rem",
  marginBottom: "0.25rem",
  fontWeight: "bold",
  fontSize: "0.9rem",
};

const inputStyle = {
  width: "100%",
  padding: "8px",
  boxSizing: "border-box",
  fontFamily: "sans-serif",
};

export default App;
