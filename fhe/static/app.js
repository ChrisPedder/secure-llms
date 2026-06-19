const FEATURES = [];
for (let i = 1; i <= 28; i++) FEATURES.push("V" + i);
FEATURES.push("Time", "Amount");

const HIGHLIGHT = new Set(["Amount", "Time"]);

const statusEl = document.getElementById("status");
const sampleSelect = document.getElementById("sample-select");
const featureGrid = document.getElementById("feature-grid");
const predictBtn = document.getElementById("predict-btn");
const pipeline = document.getElementById("pipeline");

let samplesData = [];
let currentActual = null;

function buildFeatureInputs() {
  featureGrid.innerHTML = "";
  for (const name of FEATURES) {
    const div = document.createElement("div");
    div.className = "feature-field" + (HIGHLIGHT.has(name) ? " highlight" : "");
    div.innerHTML = `
      <label for="f-${name}">${name}</label>
      <input type="number" step="any" id="f-${name}" value="0">
    `;
    featureGrid.appendChild(div);
  }
}

function setFeatures(obj) {
  for (const name of FEATURES) {
    const el = document.getElementById("f-" + name);
    if (el && obj[name] !== undefined) {
      el.value = parseFloat(obj[name].toFixed(6));
    }
  }
}

function getFeatures() {
  const features = {};
  for (const name of FEATURES) {
    features[name] = parseFloat(document.getElementById("f-" + name).value) || 0;
  }
  return features;
}

async function loadSamples() {
  const res = await fetch("/samples");
  const data = await res.json();
  samplesData = data.samples;
  sampleSelect.innerHTML = '<option value="">-- select --</option>';
  for (const s of samplesData) {
    const opt = document.createElement("option");
    opt.value = s.index;
    opt.textContent = `#${s.index} - ${s.label} ($${s.amount})`;
    sampleSelect.appendChild(opt);
  }
}

sampleSelect.addEventListener("change", () => {
  const idx = sampleSelect.value;
  if (idx === "") return;
  const sample = samplesData.find((s) => s.index === parseInt(idx));
  if (sample) {
    setFeatures(sample.features);
    currentActual = sample.actual;
  }
});

function formatHex(hex) {
  const chunks = hex.match(/.{1,2}/g) || [];
  const lines = [];
  for (let i = 0; i < chunks.length; i += 16) {
    lines.push(chunks.slice(i, i + 16).join(" "));
  }
  return lines.join("\n") + "\n...";
}

function setStepState(id, state) {
  const el = document.getElementById(id);
  el.classList.remove("active", "done");
  if (state) el.classList.add(state);
}

async function runPrediction() {
  predictBtn.disabled = true;
  statusEl.innerHTML = '<span class="spinner"></span>Running FHE pipeline...';
  statusEl.className = "status working";
  pipeline.hidden = false;

  ["step-quantize", "step-encrypt", "step-compute", "step-decrypt", "step-result"].forEach(
    (id) => setStepState(id, null)
  );

  const features = getFeatures();

  try {
    setStepState("step-quantize", "active");
    const res = await fetch("/predict-steps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ features }),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    const s = data.steps;

    // Quantize
    setStepState("step-quantize", "done");
    document.getElementById("time-quantize").textContent = s.quantized.time_ms + " ms";
    document.getElementById("data-quantize").textContent = s.quantized.values.join(", ");

    // Encrypt
    setStepState("step-encrypt", "done");
    document.getElementById("time-encrypt").textContent = s.encrypted.time_ms + " ms";
    document.getElementById("size-encrypt").textContent = s.encrypted.size_bytes + " bytes";
    document.getElementById("data-encrypt").textContent = formatHex(s.encrypted.hex_preview);

    // Compute
    setStepState("step-compute", "done");
    document.getElementById("time-compute").textContent = s.computed.time_ms + " ms";
    document.getElementById("size-compute").textContent = s.computed.size_bytes + " bytes";
    document.getElementById("data-compute").textContent = formatHex(s.computed.hex_preview);

    // Decrypt
    setStepState("step-decrypt", "done");
    document.getElementById("time-decrypt").textContent = s.decrypted.time_ms + " ms";
    document.getElementById("data-decrypt").textContent = "raw integers: [" + s.decrypted.raw.join(", ") + "]";

    // Result
    setStepState("step-result", "done");
    const isFraud = s.output.prediction === 1;
    let html = `
      <div class="verdict ${isFraud ? "fraud" : "legit"}">
        ${isFraud ? "FRAUD DETECTED" : "LEGITIMATE"}
      </div>
      <div class="probs">
        class probabilities: [${s.output.probabilities.map((p) => p.toFixed(2)).join(", ")}]
      </div>
    `;
    if (currentActual !== null) {
      const correct = s.output.prediction === currentActual;
      html += `
        <div class="actual ${correct ? "correct" : "incorrect"}">
          Ground truth: ${currentActual === 1 ? "FRAUD" : "legitimate"}
          &mdash; ${correct ? "Correct" : "Incorrect"}
        </div>
      `;
    }
    document.getElementById("prediction").innerHTML = html;

    statusEl.textContent = "Ready";
    statusEl.className = "status ready";
  } catch (err) {
    statusEl.textContent = "Error: " + err.message;
    statusEl.className = "status error";
  } finally {
    predictBtn.disabled = false;
  }
}

predictBtn.addEventListener("click", runPrediction);

async function init() {
  try {
    const res = await fetch("/status");
    const data = await res.json();
    if (data.ready) {
      statusEl.textContent = "Ready";
      statusEl.className = "status ready";
      predictBtn.disabled = false;
      await loadSamples();
    }
  } catch {
    statusEl.textContent = "Connection error";
    statusEl.className = "status error";
  }
}

buildFeatureInputs();
init();
