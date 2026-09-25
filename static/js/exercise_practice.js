// ============================================
// UNIFIED CAMERA HANDLER
// AI Coach mode → uses POSE_DATA rule checks
// Companion mode → skeleton + rep counter / presence / breathing
// ============================================

const LM = {
    nose: 0,
    left_shoulder: 11, right_shoulder: 12,
    left_elbow: 13, right_elbow: 14,
    left_wrist: 15, right_wrist: 16,
    left_hip: 23, right_hip: 24,
    left_knee: 25, right_knee: 26,
    left_ankle: 27, right_ankle: 28
};

let pose, camera;
let ttsEnabled = false;
let micActive = false;
let recognition = null;
let sessionActive = false;

// coach mode state
let holdStartTime = null;
let lastSpokenMessage = "";
let lastSpokenTime = 0;

// companion mode state
let repCount = 0;
let repState = "up";                // "up" or "down"
let lastRepValue = null;
let breathingPositions = [];
let sessionStartTime = null;
let sessionEndTime = null;
let consecutiveDownFrames = 0;
let lastRepTime = 0;

// ==================== INIT ====================
async function initPose() {
    if (typeof window.Pose === 'undefined') {
        document.getElementById("cam-loading").innerHTML =
            `⚠ AI model blocked — check your adblocker or firewall`;
        return;
    }

    try {
        if (navigator.permissions) {
            const status = await navigator.permissions.query({name: 'camera'});
            if (status.state === 'prompt') {
                document.getElementById("cam-loading").innerHTML =
                    `<span class="pulse-dot"></span>Click Allow when Chrome asks for camera`;
            }
        }
    } catch (e) {
        // ignore if permissions api not supported
    }

    pose = new Pose({
        locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${f}`
    });
    pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });
    pose.onResults(onPoseResults);

    const video = document.getElementById("cam");
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        
        // Use Camera util for frame extraction
        camera = new Camera(video, {
            onFrame: async () => { if (sessionActive) await pose.send({ image: video }); },
            width: 640, height: 480
        });
        await camera.start();
        document.getElementById("cam-loading").style.display = "none";
    } catch (err) {
        let msg = "Camera access denied.";
        if (err.name === "NotAllowedError" || err.name === "SecurityError") {
            msg = "Camera access denied. Please allow it in site settings.";
        } else if (err.name === "NotFoundError") {
            msg = "No camera found on this device.";
        } else if (err.name === "NotReadableError") {
            msg = "Camera is already in use by another app.";
        }
        document.getElementById("cam-loading").innerHTML = `⚠ ${msg}`;
    }
}

initPose();

function testCamera() {
    document.getElementById("cam").play();
    document.getElementById("cam-loading").style.display = "none";
}


// ==================== POSE RESULTS ====================
function onPoseResults(results) {
    const canvas = document.getElementById("overlay");
    const video = document.getElementById("cam");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!results.poseLandmarks || results.poseLandmarks.length === 0) {
        if (MODE === "coach") {
            document.getElementById("accuracy").textContent = "0%";
            updateRing(0);
            document.getElementById("feedback-list").innerHTML = `
                <div class="feedback-item unclear">
                    <span class="fb-icon">?</span>
                    <span>No person detected. Step back so your full body is visible.</span>
                </div>`;
            if (ttsEnabled) speak("No person detected. Please step back.");
        } else {
            showCompanionMsg("? No person detected. Step back.", "unclear");
        }
        return;
    }

    drawSkeleton(ctx, results.poseLandmarks, canvas.width, canvas.height);

    if (MODE === "coach") {
        handleCoachMode(results.poseLandmarks);
    } else {
        handleCompanionMode(results.poseLandmarks);
    }
}


// ==================== AI COACH MODE ====================
function handleCoachMode(landmarks) {
    const { results: checks, accuracy } = evalChecks(landmarks);
    updateCoachFeedback(checks, accuracy);

    const HOLD_SECONDS = POSE_DATA.hold_seconds || 30;
    if (accuracy >= 70) {
        if (!holdStartTime) holdStartTime = Date.now();
        const held = (Date.now() - holdStartTime) / 1000;
        const remaining = Math.max(0, HOLD_SECONDS - held);
        document.getElementById("timer").textContent = `${Math.ceil(remaining)}s`;
        if (remaining <= 0 && sessionActive) completeSession({ accuracy, holdSeconds: HOLD_SECONDS });
    } else {
        holdStartTime = null;
        document.getElementById("timer").textContent = `${HOLD_SECONDS}s`;
    }
}

function evalChecks(landmarks) {
    const results = [];
    let passed = 0;
    for (const check of POSE_DATA.checks) {
        const points = check.landmarks.map(name => landmarks[LM[name]]);
        if (points.some(p => !p || p.visibility < 0.5)) {
            results.push({ ...check, status: "unclear", message: "Move so full body is visible" });
            continue;
        }
        let ok = false;
        if (check.type === "angle_range") {
            const a = angleBetween(points[0], points[1], points[2]);
            ok = a >= check.min_angle && a <= check.max_angle;
        } else if (check.type === "vertical_alignment") {
            const avgX = points.slice(1).reduce((s,p) => s+p.x, 0) / (points.length-1);
            ok = Math.abs(points[0].x - avgX) <= check.tolerance;
        } else if (check.type === "horizontal_alignment") {
            ok = Math.abs(points[0].y - points[1].y) <= check.tolerance;
        } else if (check.type === "relative_height") {
            ok = (points[1].y - points[0].y) >= check.min_diff;
        } else if (check.type === "line_alignment") {
            const [a,b,c] = points;
            const cross = Math.abs((b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x));
            ok = cross <= check.tolerance;
        }
        results.push({
            ...check,
            status: ok ? "ok" : "fix",
            message: ok ? check.ok_message : check.fix_message
        });
        if (ok) passed++;
    }
    return { results, accuracy: Math.round((passed / POSE_DATA.checks.length) * 100) };
}

function updateCoachFeedback(checks, accuracy) {
    document.getElementById("accuracy").textContent = `${accuracy}%`;
    updateRing(accuracy);
    document.getElementById("feedback-list").innerHTML = checks.map(c => `
        <div class="feedback-item ${c.status}">
            <span class="fb-icon">${c.status === 'ok' ? '✓' : c.status === 'unclear' ? '?' : '⚠'}</span>
            <span>${c.message}</span>
        </div>`).join("");

    const firstUnclear = checks.find(c => c.status === "unclear");
    const firstFix = checks.find(c => c.status === "fix");
    
    if (firstUnclear && ttsEnabled) {
        speak(firstUnclear.message);
    } else if (firstFix && ttsEnabled) {
        speak(firstFix.message);
    }
}


// ==================== COMPANION MODE ====================
function handleCompanionMode(landmarks) {
    if (GENERIC_MODE.mode === "rep_counter") {
        countReps(landmarks);
    } else if (GENERIC_MODE.mode === "breathing_pace") {
        trackBreathing(landmarks);
    } else {
        trackPresence(landmarks);
    }

    // update countdown
    if (sessionEndTime) {
        const remaining = Math.max(0, Math.floor((sessionEndTime - Date.now()) / 1000));
        const m = Math.floor(remaining / 60), s = remaining % 60;
        document.getElementById("timer").textContent = `${m}:${String(s).padStart(2,'0')}`;
        if (remaining <= 0 && sessionActive) {
            const summary = GENERIC_MODE.mode === "rep_counter"
                ? { reps: repCount, duration: EX_DURATION_MIN * 60 }
                : { duration: EX_DURATION_MIN * 60 };
            completeSession(summary);
        }
    }
}

function countReps(landmarks) {
    const minVis = GENERIC_MODE.min_visibility || 0.6;
    const lm = landmarks[LM[GENERIC_MODE.landmark]];
    if (!lm || lm.visibility < minVis) {
        showCompanionMsg("? Position yourself in view", "unclear");
        return;
    }
    const val = GENERIC_MODE.axis === "y" ? lm.y : lm.x;
    if (lastRepValue === null) lastRepValue = val;

    const diff = val - lastRepValue;
    const hFrames = GENERIC_MODE.hysteresis_frames || 3;
    const cooldown = GENERIC_MODE.cooldown_ms || 500;
    const now = Date.now();

    if (repState === "up" && diff > GENERIC_MODE.threshold) {
        consecutiveDownFrames++;
        if (consecutiveDownFrames >= hFrames) {
            repState = "down";
            lastRepValue = val;
            consecutiveDownFrames = 0;
        }
    } else if (repState === "up") {
        consecutiveDownFrames = Math.max(0, consecutiveDownFrames - 1);
    } else if (repState === "down" && diff < -GENERIC_MODE.threshold) {
        if (now - lastRepTime >= cooldown) {
            repState = "up";
            repCount++;
            lastRepTime = now;
            lastRepValue = val;
            if (ttsEnabled) speak(`${repCount}`);
        }
    }

    document.getElementById("accuracy").textContent = repCount;
    updateRing(Math.min(100, repCount * 5)); // ring fills toward 20 reps
    showCompanionMsg(`✓ Detected ${repCount} reps · ${GENERIC_MODE.instruction}`, "ok");
}

function trackBreathing(landmarks) {
    const shoulder = landmarks[LM[GENERIC_MODE.landmark]];
    if (!shoulder || shoulder.visibility < 0.5) {
        showCompanionMsg("? Sit or stand in view", "unclear");
        return;
    }
    breathingPositions.push({ t: Date.now(), y: shoulder.y });
    breathingPositions = breathingPositions.filter(p => Date.now() - p.t < 60000); // 1 min window

    // count peaks (breaths) in last 60s
    let peaks = 0;
    for (let i = 2; i < breathingPositions.length; i++) {
        if (breathingPositions[i].y < breathingPositions[i-1].y &&
            breathingPositions[i-1].y < breathingPositions[i-2].y) peaks++;
    }
    const bpm = Math.round(peaks / 2); // rough estimate
    document.getElementById("accuracy").textContent = bpm;
    const targetBpm = GENERIC_MODE.target_bpm || 6;
    const score = Math.max(0, 100 - Math.abs(bpm - targetBpm) * 15);
    updateRing(score);

    const msg = bpm < targetBpm - 2 ? "Breathe a little faster"
              : bpm > targetBpm + 2 ? "Slow your breath"
              : `✓ Nice pace — ${bpm} breaths/min`;
    showCompanionMsg(msg, bpm >= targetBpm-2 && bpm <= targetBpm+2 ? "ok" : "fix");
}

function trackPresence(landmarks) {
    const visible = landmarks.filter(p => p && p.visibility > 0.5).length;
    const score = Math.min(100, Math.round((visible / 33) * 100));
    document.getElementById("accuracy").textContent = `${score}%`;
    updateRing(score);
    showCompanionMsg(
        score >= 60 ? `✓ I can see you clearly · ${GENERIC_MODE.instruction}`
                    : "? Position yourself so more of your body is visible",
        score >= 60 ? "ok" : "unclear"
    );
}

function showCompanionMsg(text, status) {
    const box = document.getElementById("companion-status");
    box.style.display = "flex";
    box.className = `feedback-item ${status}`;
    document.getElementById("companion-message").textContent = text;
}


// ==================== SHARED HELPERS ====================
function updateRing(pct) {
    const ring = document.getElementById("ring");
    const c = 2 * Math.PI * 42;
    ring.style.strokeDasharray = c;
    ring.style.strokeDashoffset = c * (1 - pct / 100);
    ring.style.stroke = pct >= 70 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";
}

function angleBetween(a, b, c) {
    const ab = { x: a.x - b.x, y: a.y - b.y };
    const cb = { x: c.x - b.x, y: c.y - b.y };
    const dot = ab.x * cb.x + ab.y * cb.y;
    const mA = Math.hypot(ab.x, ab.y);
    const mC = Math.hypot(cb.x, cb.y);
    return (Math.acos(Math.min(1, Math.max(-1, dot / (mA * mC)))) * 180) / Math.PI;
}

function drawSkeleton(ctx, lms, w, h) {
    const connections = [
        [11,12],[11,13],[13,15],[12,14],[14,16],
        [11,23],[12,24],[23,24],
        [23,25],[25,27],[24,26],[26,28]
    ];
    ctx.strokeStyle = "#6ee7b7";
    ctx.lineWidth = 3;
    connections.forEach(([a,b]) => {
        if (lms[a] && lms[b]) {
            ctx.beginPath();
            ctx.moveTo(lms[a].x * w, lms[a].y * h);
            ctx.lineTo(lms[b].x * w, lms[b].y * h);
            ctx.stroke();
        }
    });
    ctx.fillStyle = "#10b981";
    lms.forEach(p => {
        if (p.visibility > 0.5) {
            ctx.beginPath();
            ctx.arc(p.x * w, p.y * h, 5, 0, Math.PI * 2);
            ctx.fill();
        }
    });
}


// ==================== SESSION CONTROL ====================
function startSession() {
    sessionActive = true;
    sessionStartTime = Date.now();

    if (MODE === "companion") {
        sessionEndTime = Date.now() + (EX_DURATION_MIN * 60 * 1000);
        repCount = 0;
        repState = "up";
        lastRepValue = null;
        breathingPositions = [];
        consecutiveDownFrames = 0;
        lastRepTime = 0;
    }

    const btn = document.getElementById("start-btn");
    btn.textContent = "⏸ Pause";
    btn.onclick = pauseSession;

    if (ttsEnabled) {
        const intro = MODE === "coach"
            ? `Starting ${POSE_DATA.name}. Hold for ${POSE_DATA.hold_seconds} seconds when aligned.`
            : `Starting ${EX_TITLE}. ${GENERIC_MODE.instruction}. ${EX_INSTRUCTIONS}`;
        speak(intro);
    }
}

function pauseSession() {
    sessionActive = false;
    const btn = document.getElementById("start-btn");
    btn.textContent = "▶ Resume";
    btn.onclick = startSession;
}

async function completeSession(summary) {
    sessionActive = false;
    if (ttsEnabled) speak("Great work! Session complete.");

    let text;
    if (summary.reps !== undefined) {
        text = `You completed ${summary.reps} reps of ${EX_TITLE} in ${Math.round(summary.duration/60)} minutes.`;
    } else if (summary.accuracy !== undefined) {
        text = `You held ${POSE_DATA.name} for ${summary.holdSeconds}s with ${summary.accuracy}% alignment.`;
    } else {
        text = `You completed ${EX_TITLE} — ${Math.round(summary.duration/60)} minutes.`;
    }
    document.getElementById("completion-summary").textContent = text;
    document.getElementById("completion-modal").classList.remove("hidden");

    await fetch("/api/yoga/log", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            pose_key: MODE === "coach" ? POSE_KEY : "companion",
            pose_name: EX_TITLE,
            hold_seconds: summary.holdSeconds || summary.duration || 0,
            accuracy: summary.accuracy || (summary.reps ? Math.min(100, summary.reps * 5) : 100)
        })
    });
}


// ==================== VOICE ====================
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    document.getElementById("tts-btn").textContent = ttsEnabled ? "🔊 Voice On" : "🔇 Voice Off";
    if (ttsEnabled) speak(`Voice guidance enabled`);
    else speechSynthesis.cancel();
}

function speak(text) {
    if (!ttsEnabled) return;
    const now = Date.now();
    if (text === lastSpokenMessage && now - lastSpokenTime < 4000) return;
    lastSpokenMessage = text;
    lastSpokenTime = now;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0;
    speechSynthesis.speak(u);
}

function toggleMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice input needs Chrome/Edge.");
    if (!recognition) {
        recognition = new SR();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.onresult = e => {
            const t = e.results[e.results.length - 1][0].transcript.toLowerCase();
            handleVoiceCommand(t);
        };
    }
    micActive = !micActive;
    document.getElementById("mic-btn").textContent = micActive ? "🎙 Listening…" : "🎤 Listen";
    if (micActive) recognition.start(); else recognition.stop();
}

function handleVoiceCommand(t) {
    if (t.includes("start") || t.includes("begin")) startSession();
    else if (t.includes("stop") || t.includes("pause")) pauseSession();
    else if (t.includes("help") || t.includes("instructions")) {
        speak(MODE === "coach" ? POSE_DATA.instructions.join(". ") : EX_INSTRUCTIONS);
    }
}