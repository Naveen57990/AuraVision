/**
 * AuraVision 3D Spatial Radar & Physical AI Engine Client
 */

// Presets
const SCENARIOS = {
  worker_hazard: {
    name: "Factory Worker Ingress",
    objects: [
      { id: "WORKER_42", class: "Human Operator", conf: 0.98, x: 0.1, z: 4.5, vx: -0.2, vz: -5.0, color: "#ef4444" },
      { id: "STATIC_BIN_01", class: "Static Infrastructure", conf: 0.99, x: 3.5, z: 12.0, vx: 0.0, vz: 0.0, color: "#94a3b8" }
    ]
  },
  forklift_cross: {
    name: "Blind-Spot Forklift Cross-Traffic",
    objects: [
      { id: "FORKLIFT_09", class: "Autonomous Vehicle", conf: 0.96, x: 4.5, z: 9.0, vx: -3.5, vz: -2.5, color: "#f97316" },
      { id: "PALLET_STACK", class: "Static Obstacle", conf: 0.95, x: -3.0, z: 15.0, vx: 0.0, vz: 0.0, color: "#94a3b8" }
    ]
  },
  multi_swarm: {
    name: "Multi-Entity Dense Fleet Cluster",
    objects: [
      { id: "AGV_FLEET_A", class: "Autonomous AGV", conf: 0.94, x: -1.2, z: 14.0, vx: 0.5, vz: -4.0, color: "#eab308" },
      { id: "AGV_FLEET_B", class: "Autonomous AGV", conf: 0.92, x: 2.8, z: 18.0, vx: -0.8, vz: -3.5, color: "#06b6d4" },
      { id: "TECHNICIAN_07", class: "Human Operator", conf: 0.97, x: -4.0, z: 22.0, vx: 0.2, vz: 1.0, color: "#22c55e" }
    ]
  },
  clear_corridor: {
    name: "Unobstructed Safety Corridor",
    objects: [
      { id: "OVERHEAD_CRANE", class: "Infrastructure", conf: 0.99, x: 5.0, z: 25.0, vx: 0.0, vz: 0.0, color: "#22c55e" },
      { id: "RECEDING_SCOUT", class: "Autonomous Drone", conf: 0.95, x: 0.0, z: 12.0, vx: 0.0, vz: 4.0, color: "#22c55e" }
    ]
  }
};

let currentObjects = JSON.parse(JSON.stringify(SCENARIOS.worker_hazard.objects));
let audioEnabled = true;
let audioCtx = null;
let animationFrameId = null;
let frameCounter = 100;

// Web Audio Synth
function playProximityTone(threat) {
  if (!audioEnabled) return;
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (threat === 'CRITICAL') {
      osc.frequency.setValueAtTime(960, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.18, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.15);
    } else if (threat === 'WARNING') {
      osc.frequency.setValueAtTime(540, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.12);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.12);
    }
  } catch (e) {}
}

// DOM Elements
const elements = {
  canvas: document.getElementById('spatialCanvas'),
  scenarioPreset: document.getElementById('scenarioPreset'),
  radarViewToggle: document.getElementById('radarViewToggle'),
  audioToggle: document.getElementById('audioToggle'),
  audioIcon: document.getElementById('audioIcon'),
  resetSimBtn: document.getElementById('resetSimBtn'),

  input_posX: document.getElementById('input_posX'),
  val_posX: document.getElementById('val_posX'),
  input_posZ: document.getElementById('input_posZ'),
  val_posZ: document.getElementById('val_posZ'),
  input_velZ: document.getElementById('input_velZ'),
  val_velZ: document.getElementById('val_velZ'),
  input_velX: document.getElementById('input_velX'),
  val_velX: document.getElementById('val_velX'),

  threatBanner: document.getElementById('threatBanner'),
  threatBadge: document.getElementById('threatBadge'),
  threatDesc: document.getElementById('threatDesc'),
  metric_ttc: document.getElementById('metric_ttc'),
  interp_ttc: document.getElementById('interp_ttc'),
  metric_speed: document.getElementById('metric_speed'),
  interp_speed: document.getElementById('interp_speed'),
  metric_lateral: document.getElementById('metric_lateral'),
  interp_lateral: document.getElementById('interp_lateral'),
  metric_flow: document.getElementById('metric_flow'),
  mqttTopic: document.getElementById('mqttTopic'),
  awsPayloadBox: document.getElementById('awsPayloadBox'),
  exportSafetyPassBtn: document.getElementById('exportSafetyPassBtn'),
  copyMqttBtn: document.getElementById('copyMqttBtn')
};

const ctx = elements.canvas.getContext('2d');

function project3D(x, y, z, width, height) {
  // Perspective projection with vanishing point at center
  const fov = 380;
  const cx = width / 2;
  const cy = height * 0.65;
  const scale = fov / Math.max(0.5, z);
  const px = cx + (x * scale);
  const py = cy - (y * scale);
  return { px, py, scale };
}

function renderScene() {
  const w = elements.canvas.width;
  const h = elements.canvas.height;
  ctx.clearRect(0, 0, w, h);

  // Background Gradient
  const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
  bgGrad.addColorStop(0, '#030712');
  bgGrad.addColorStop(1, '#091024');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, w, h);

  // 3D Perspective Ground Grid
  ctx.strokeStyle = 'rgba(6, 182, 212, 0.15)';
  ctx.lineWidth = 1;

  // Longitudinal lines (Z-depth)
  for (let gx = -10; gx <= 10; gx += 2) {
    const near = project3D(gx, 0, 1.0, w, h);
    const far = project3D(gx, 0, 40.0, w, h);
    ctx.beginPath();
    ctx.moveTo(near.px, near.py);
    ctx.lineTo(far.px, far.py);
    ctx.stroke();
  }

  // Lateral lines (X-width)
  for (let gz = 2; gz <= 40; gz += 4) {
    const left = project3D(-10, 0, gz, w, h);
    const right = project3D(10, 0, gz, w, h);
    ctx.beginPath();
    ctx.moveTo(left.px, left.py);
    ctx.lineTo(right.px, right.py);
    ctx.stroke();
  }

  // Safety Corridor (1.5m lateral boundary)
  ctx.strokeStyle = 'rgba(34, 197, 94, 0.4)';
  ctx.fillStyle = 'rgba(34, 197, 94, 0.05)';
  const scNearL = project3D(-1.5, 0, 1.0, w, h);
  const scNearR = project3D(1.5, 0, 1.0, w, h);
  const scFarR = project3D(1.5, 0, 35.0, w, h);
  const scFarL = project3D(-1.5, 0, 35.0, w, h);

  ctx.beginPath();
  ctx.moveTo(scNearL.px, scNearL.py);
  ctx.lineTo(scNearR.px, scNearR.py);
  ctx.lineTo(scFarR.px, scFarR.py);
  ctx.lineTo(scFarL.px, scFarL.py);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Optical Flow Particle Field
  const time = Date.now() * 0.002;
  for (let i = 0; i < 20; i++) {
    const fx = Math.sin(time + i) * 6;
    const fz = ((time * 4 + i * 2) % 35) + 2;
    const p = project3D(fx, 0.5, fz, w, h);
    ctx.fillStyle = 'rgba(6, 182, 212, 0.3)';
    ctx.fillRect(p.px, p.py, 2, 2);
  }

  // Draw Objects
  currentObjects.forEach(obj => {
    const p = project3D(obj.x, 0, obj.z, w, h);
    const boxW = Math.max(16, 60 * (p.scale / 100));
    const boxH = Math.max(30, 110 * (p.scale / 100));

    // Trajectory prediction vector
    if (obj.vz < 0) {
      const predTTC = obj.z / Math.abs(obj.vz);
      const predX = obj.x + (obj.vx * predTTC);
      const predP = project3D(predX, 0, 0.5, w, h);

      ctx.strokeStyle = obj.color;
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(p.px, p.py);
      ctx.lineTo(predP.px, predP.py);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 3D Bounding Frustum Box
    ctx.strokeStyle = obj.color;
    ctx.lineWidth = 2;
    ctx.strokeRect(p.px - boxW / 2, p.py - boxH, boxW, boxH);
    ctx.fillStyle = obj.color + '22';
    ctx.fillRect(p.px - boxW / 2, p.py - boxH, boxW, boxH);

    // Label
    ctx.font = 'bold 11px monospace';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(`${obj.id} [Z:${obj.z.toFixed(1)}m]`, p.px - boxW / 2, p.py - boxH - 6);
  });

  animationFrameId = requestAnimationFrame(renderScene);
}

function updateTelemetry() {
  const primary = currentObjects[0];
  primary.x = parseFloat(elements.input_posX.value);
  primary.z = parseFloat(elements.input_posZ.value);
  primary.vx = parseFloat(elements.input_velX.value);
  primary.vz = parseFloat(elements.input_velZ.value);

  elements.val_posX.textContent = `${primary.x.toFixed(1)} m`;
  elements.val_posZ.textContent = `${primary.z.toFixed(1)} m`;
  elements.val_velX.textContent = `${primary.vx.toFixed(1)} m/s`;
  elements.val_velZ.textContent = `${primary.vz.toFixed(1)} m/s`;

  // Calculate TTC and threat
  let ttc = null;
  let threat = "CLEAR";
  let bannerClass = "clear";
  let badgeText = "OPERATIONAL CORRIDOR CLEAR";
  let descText = "All Projected Trajectories Clear of Safety Buffer Zone";

  if (primary.vz < -0.05) {
    const approachingSpeed = Math.abs(primary.vz);
    ttc = primary.z / approachingSpeed;
    const predX = primary.x + (primary.vx * ttc);

    if (Math.abs(predX) <= 1.5) {
      if (ttc <= 1.2) {
        threat = "CRITICAL";
        bannerClass = "critical";
        badgeText = "CRITICAL THREAT • EMERGENCY BRAKE ACTIVE";
        descText = `Trajectory Intersects Safety Corridor (TTC: ${ttc.toFixed(2)}s < 1.20s Threshold)`;
        primary.color = "#ef4444";
      } else if (ttc <= 3.0) {
        threat = "WARNING";
        bannerClass = "warning";
        badgeText = "WARNING • HAZARD ENTERING BOUNDARY";
        descText = `Object Approaching Dynamic Safety Zone (TTC: ${ttc.toFixed(2)}s)`;
        primary.color = "#f97316";
      } else {
        threat = "ADVISORY";
        bannerClass = "advisory";
        badgeText = "ADVISORY • DISTANT CONE DETECTED";
        descText = `Trajectory Intersects at Range (TTC: ${ttc.toFixed(2)}s)`;
        primary.color = "#eab308";
      }
    } else {
      primary.color = "#22c55e";
    }
  } else {
    primary.color = "#22c55e";
  }

  // Update UI Elements
  elements.threatBanner.className = `threat-status-banner ${bannerClass}`;
  elements.threatBadge.textContent = badgeText;
  elements.threatDesc.textContent = descText;

  elements.metric_ttc.innerHTML = ttc ? `${ttc.toFixed(2)}<span class="sub-denom">s</span>` : `--<span class="sub-denom">s</span>`;
  elements.interp_ttc.textContent = threat === "CRITICAL" ? "Emergency Interception Required" : (threat === "WARNING" ? "Deceleration Advisory" : "Corridor Clear");

  const speed = Math.sqrt(primary.vx**2 + primary.vz**2);
  elements.metric_speed.innerHTML = `${speed.toFixed(2)}<span class="sub-denom">m/s</span>`;
  elements.interp_speed.textContent = `${(speed * 3.6).toFixed(1)} km/h Relative Vector`;

  elements.metric_lateral.innerHTML = `${Math.abs(primary.x).toFixed(2)}<span class="sub-denom">m</span>`;
  elements.interp_lateral.textContent = Math.abs(primary.x) <= 1.5 ? "Inside 1.5m Safety Zone" : "Outside Critical Buffer";

  const flowMag = Math.max(1.2, speed * 1.35).toFixed(2);
  elements.metric_flow.innerHTML = `${flowMag}<span class="sub-denom">px/f</span>`;

  // AWS IoT Core Payload
  frameCounter++;
  const isEmergency = threat === "CRITICAL";
  elements.mqttTopic.textContent = isEmergency ? "auravision/edge/hazards/critical [QoS 1]" : "auravision/edge/telemetry/stream [QoS 0]";
  elements.mqttTopic.style.color = isEmergency ? "#ef4444" : "#06b6d4";

  const payload = {
    frame_id: frameCounter,
    timestamp_ms: Date.now(),
    highest_threat: threat,
    emergency_brake_triggered: isEmergency,
    flow_magnitude: parseFloat(flowMag),
    fps: 60.0,
    tracked_objects: currentObjects.map(o => ({
      id: o.id,
      class: o.class,
      confidence: o.conf,
      pos: { x: o.x, z: o.z },
      vel: { vx: o.vx, vz: o.vz },
      ttc_sec: ttc ? parseFloat(ttc.toFixed(2)) : null
    }))
  };

  elements.awsPayloadBox.textContent = JSON.stringify(payload, null, 2);
  playProximityTone(threat);
}

// Preset Loader
function loadScenario(presetKey) {
  const p = SCENARIOS[presetKey];
  if (!p) return;
  currentObjects = JSON.parse(JSON.stringify(p.objects));
  const primary = currentObjects[0];
  elements.input_posX.value = primary.x;
  elements.input_posZ.value = primary.z;
  elements.input_velX.value = primary.vx;
  elements.input_velZ.value = primary.vz;
  updateTelemetry();
}

// Event Listeners
[elements.input_posX, elements.input_posZ, elements.input_velX, elements.input_velZ].forEach(input => {
  input.addEventListener('input', updateTelemetry);
  input.addEventListener('change', updateTelemetry);
});

elements.scenarioPreset.addEventListener('change', (e) => {
  loadScenario(e.target.value);
});

elements.audioToggle.addEventListener('click', () => {
  audioEnabled = !audioEnabled;
  elements.audioIcon.textContent = audioEnabled ? "🔊 PROXIMITY ALARMS ON" : "🔇 AUDIO MUTED";
  elements.audioToggle.style.opacity = audioEnabled ? "1" : "0.6";
});

elements.resetSimBtn.addEventListener('click', () => {
  loadScenario('worker_hazard');
  elements.scenarioPreset.value = 'worker_hazard';
});

elements.copyMqttBtn.addEventListener('click', () => {
  navigator.clipboard.writeText(elements.awsPayloadBox.textContent);
  elements.copyMqttBtn.textContent = "COPIED MQTT JSON!";
  setTimeout(() => { elements.copyMqttBtn.textContent = "COPY MQTT PAYLOAD"; }, 2000);
});

elements.exportSafetyPassBtn.addEventListener('click', () => {
  alert("Exported AuraVision Spatial Safety & Kinematic Audit Log (JSON).");
});

// Start loop
renderScene();
updateTelemetry();
