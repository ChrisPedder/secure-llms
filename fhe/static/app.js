const statusEl = document.getElementById("status");
const uploadZone = document.getElementById("upload-zone");
const fileInput = document.getElementById("file-input");
const resultsDiv = document.getElementById("results");
const summaryDiv = document.getElementById("summary");
const tbody = document.querySelector("#results-table tbody");
const fheToggle = document.getElementById("fhe-toggle");

async function checkStatus() {
  try {
    const res = await fetch("/status");
    const data = await res.json();
    if (data.ready) {
      statusEl.textContent = `Ready (${data.fhe_mode} mode)`;
      statusEl.className = "status ready";
      uploadZone.classList.remove("disabled");
    }
  } catch {
    statusEl.textContent = "Connection error";
    statusEl.className = "status error";
  }
}

fheToggle.addEventListener("change", async () => {
  const mode = fheToggle.checked ? "execute" : "simulate";
  await fetch("/mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  checkStatus();
});

uploadZone.addEventListener("click", () => fileInput.click());

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  statusEl.innerHTML = '<span class="spinner"></span>Running inference...';
  statusEl.className = "status loading";
  uploadZone.classList.add("disabled");

  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/predict", { method: "POST", body: form });
    const data = await res.json();

    if (data.error) {
      statusEl.textContent = data.error;
      statusEl.className = "status error";
      return;
    }

    renderResults(data);
    const mode = data.summary.fhe_mode;
    statusEl.textContent = `Ready (${mode} mode)`;
    statusEl.className = "status ready";
  } catch (err) {
    statusEl.textContent = "Request failed: " + err.message;
    statusEl.className = "status error";
  } finally {
    uploadZone.classList.remove("disabled");
    fileInput.value = "";
  }
}

function renderResults(data) {
  const s = data.summary;

  let html = `
    <div class="stat"><div class="value">${s.total}</div><div class="label">Samples</div></div>
    <div class="stat fraud"><div class="value">${s.fraud}</div><div class="label">Fraud</div></div>
    <div class="stat ok"><div class="value">${s.legitimate}</div><div class="label">Legitimate</div></div>
    <div class="stat"><div class="value">${s.inference_time_s}s</div><div class="label">Inference</div></div>
    <div class="stat"><div class="value">${s.per_sample_s}s</div><div class="label">Per sample</div></div>
  `;

  if (s.accuracy !== null) {
    html += `<div class="stat"><div class="value">${(s.accuracy * 100).toFixed(1)}%</div><div class="label">Accuracy</div></div>`;
  }

  summaryDiv.innerHTML = html;

  const hasActual = data.results.some((r) => r.actual !== undefined);
  const headerRow = document.querySelector("#results-table thead tr");
  headerRow.innerHTML = `<th>#</th><th>Prediction</th>`;
  if (hasActual) headerRow.innerHTML += `<th>Actual</th><th>Correct</th>`;

  tbody.innerHTML = data.results
    .map((r) => {
      const cls = [
        r.prediction === 1 ? "fraud" : "",
        hasActual ? (r.correct ? "correct" : "incorrect") : "",
      ]
        .filter(Boolean)
        .join(" ");
      let row = `<td>${r.index}</td><td>${r.label}</td>`;
      if (hasActual) {
        const actual = r.actual === 1 ? "FRAUD" : "legitimate";
        row += `<td>${actual}</td><td>${r.correct ? "yes" : "NO"}</td>`;
      }
      return `<tr class="${cls}">${row}</tr>`;
    })
    .join("");

  resultsDiv.hidden = false;
}

checkStatus();
