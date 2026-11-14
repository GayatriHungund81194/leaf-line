// Leaf-Line frontend: polls the backend for one plant's status and
// shows the matching pixel-art sprite. No build step, no framework -
// plain HTML/CSS/JS, matching the rest of this project's lightweight
// style.

const BACKEND_URL = "http://192.168.1.164:8000"; // update to your backend's LAN IP
const PLANT_ID = 1;
const POLL_INTERVAL_MS = 5000;

const SPRITES = {
  happy: "../assets/sprites/happy.gif",
  needs_water: "../assets/sprites/needs_water.gif",
  overwatered: "../assets/sprites/overwatered.gif",
};

const STATUS_LABELS = {
  happy: "Happy 😊",
  needs_water: "Needs water 💧",
  overwatered: "Overwatered 🌊",
};

const spriteEl = document.getElementById("sprite");
const nameEl = document.getElementById("plant-name");
const moistureEl = document.getElementById("moisture");
const statusEl = document.getElementById("status-label");
const updatedEl = document.getElementById("last-updated");
const errorEl = document.getElementById("error");

function statusFromFlags(needsWater, overwatered) {
  if (needsWater) return "needs_water";
  if (overwatered) return "overwatered";
  return "happy";
}

function render(data) {
  const status = statusFromFlags(data.needs_water, data.overwatered);

  spriteEl.src = SPRITES[status];
  nameEl.textContent = data.name;

  const moisture = data.latest_moisture;
  moistureEl.textContent =
    moisture === null || moisture === undefined
      ? "Moisture: no readings yet"
      : `Moisture: ${moisture.toFixed(1)}%`;

  statusEl.textContent = STATUS_LABELS[status];
  statusEl.className = `status-label ${status}`;

  updatedEl.textContent = `Last checked: ${new Date().toLocaleTimeString()}`;
  errorEl.textContent = "";
}

async function poll() {
  try {
    const response = await fetch(`${BACKEND_URL}/plants/${PLANT_ID}/status`);
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    const data = await response.json();
    render(data);
  } catch (err) {
    errorEl.textContent = `Couldn't reach the backend: ${err.message}`;
  }
}

poll();
setInterval(poll, POLL_INTERVAL_MS);
