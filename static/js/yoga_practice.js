// ==================== STATE ====================
const HOLD_SECONDS = POSE_DATA.hold_seconds || 30;
let pose, camera;
let ttsEnabled = false;
let micActive = false;
let recognition = null;
let sessionActive = false;
let holdStartTime = null;
let lastSpokenMessage = "";
let lastSpokenTime = 0;

// Landmark index map (MediaPipe pose has 33 landmarks)
const LM = {
    nose: 0,
    left_shoulder: 11, right_shoulder: 12,
    left_elbow: 13, right_elbow: 14,
    left_wrist: 15, right_wrist: 16,
    left_hip: 23, right_hip: 24,
    left_knee: 25, right_knee: 26,
    left_ankle: 27, right_ankle: 28
};


// ==================== INIT ====================
async function initPose() {
    pose = new Pose({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/[email protected]/${file}`
    });
    pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });
    pose.onResults(onPoseResults);

    const video = document.getElementById("cam");
    camera = new Camera(video, {
        onFrame: async () => { if (sessionActive) await pose.send({ image: video }); },
        width: 640, height: 480
    });
    await camera.start();
    document.getElementById("cam-loading").style.display = "none";
}

initPose().catch(err => {
    document.getElementById("cam-loading").innerHTML =
        `⚠ Camera access denied or MediaPipe blocked.<br>Please allow camera and reload.`;
});


// ==================== RULE EVALUATION ====================
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
            const angle = angleBetween(points[0], points[1], points[2]);
            ok = angle >= check.min_angle && angle <= check.max_angle;
        } else if (check.type === "vertical_alignment") {
            const avgX = points.slice(1).reduce((s, p) => s + p.x, 0) / (points.length - 1);
            ok = Math.abs(points[0].x - avgX) <= check.tolerance;
        } else if (check.type === "horizontal_alignment") {
            ok = Math.abs(points[0].y - points[1].y) <= check.tolerance;
        } else if (check.type === "relative_height") {
            const diff = points[1].y - points[0].y; // remember: y grows downward
            ok = diff >= check.min_diff;
        } else if (check.type === "line_alignment") {
            // check if 3 points are roughly collinear
            const [a, b, c] = points;
            const cross = Math.abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x));
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

function angleBetween(a, b, c) {
    const ab = { x: a.x - b.x, y: a.y - b.y };
    const cb = { x: c.x - b.x, y: c.y - b.y };
    const dot = ab.x * cb.x + ab.y * cb.y;
    const magA = Math.hypot(ab.x, ab.y);
    const magC = Math.hypot(cb.x, cb.y);
    const rad = Math.acos(Math.min(1, Math.max(-1, dot / (magA * magC))));
    return (rad * 180) / Math.PI;
}


// ==================== RENDER ====================
function onPoseResults(results) {
    const canvas = document.getElementById("overlay");
    const video = document.getElementById("cam");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!results.poseLandmarks) return;

    // draw skeleton
    drawSkeleton(ctx, results.poseLandmarks, canvas.width, canvas.height);

    // evaluate rules
    const { results: checks, accuracy } = evalChecks(results.poseLandmarks);
    updateFeedback(checks, accuracy);

    // update timer if accuracy is high
    if (accuracy >= 70) {
        if (!holdStartTime) holdStartTime = Date.now();
        const held = (Date.now() - holdStartTime) / 1000;
        const remaining = Math.max(0, HOLD_SECONDS - held);
        document.getElementById("timer").textContent = `${Math.ceil(remaining)}s`;
        if (remaining <= 0 && sessionActive) completeSession(accuracy);
    } else {
        holdStartTime = null;
        document.getElementById("timer").textContent = `${HOLD_SECONDS}s`;
    }
}

function drawSkeleton(ctx, lms, w, h) {
    const connections = [
        [11,12],[11,13],[13,15],[12,14],[14,16],  // arms
        [11,23],[12,24],[23,24],                    // torso
        [23,25],[25,27],[24,26],[26,28]            // legs
    ];
    ctx.strokeStyle = "#6ee7b7";
    ctx.lineWidth = 3;
    connections.forEach(([a, b]) => {
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

function updateFeedback(checks, accuracy) {
    document.getElementById("accuracy").textContent = `${accuracy}%`;
    const ring = document.getElementById("ring");
    const circumference = 2 * Math.PI * 42;
    ring.style.strokeDasharray = circumference;
    ring.style.strokeDashoffset = circumference * (1 - accuracy / 100);
    ring.style.stroke = accuracy >= 70 ? "#10b981" : accuracy >= 40 ? "#f59e0b" : "#ef4444";

    document.getElementById("feedback-list").innerHTML = checks.map(c => `
        <div class="feedback-item ${c.status}">
            <span class="fb-icon">${c.status === 'ok' ? '✓' : c.status === 'unclear' ? '?' : '⚠'}</span>
            <span>${c.message}</span>
        </div>`).join("");

    // speak the top fix message
    const firstFix = checks.find(c => c.status === "fix");
    if (firstFix && ttsEnabled) speak(firstFix.message);
}


// ==================== SESSION CONTROL ====================
function startPractice() {
    sessionActive = true;
    holdStartTime = null;
    document.getElementById("start-btn").textContent = "⏸ Pause";
    document.getElementById("start-btn").onclick = pausePractice;
    if (ttsEnabled) speak(`Starting ${POSE_DATA.name}. Hold for ${HOLD_SECONDS} seconds when aligned.`);
}
function pausePractice() {
    sessionActive = false;
    document.getElementById("start-btn").textContent = "▶ Resume";
    document.getElementById("start-btn").onclick = startPractice;
}
function restartPractice() {
    document.getElementById("completion-modal").classList.add("hidden");
    holdStartTime = null;
    document.getElementById("timer").textContent = `${HOLD_SECONDS}s`;
    startPractice();
}

async function completeSession(accuracy) {
    sessionActive = false;
    if (ttsEnabled) speak("Great work! You held the pose successfully.");
    document.getElementById("completion-summary").textContent =
        `You held ${POSE_DATA.name} for ${HOLD_SECONDS}s with ${accuracy}% alignment.`;
    document.getElementById("completion-modal").classList.remove("hidden");

    // log to backend
    await fetch("/api/yoga/log", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            pose_key: POSE_KEY,
            pose_name: POSE_DATA.name,
            hold_seconds: HOLD_SECONDS,
            accuracy
        })
    });
}


// ==================== VOICE (TTS + STT) ====================
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    document.getElementById("tts-btn").textContent = ttsEnabled ? "🔊 Voice On" : "🔇 Voice Off";
    if (ttsEnabled) speak(`Voice guidance enabled for ${POSE_DATA.name}`);
    else speechSynthesis.cancel();
}

function speak(text) {
    if (!ttsEnabled) return;
    const now = Date.now();
    if (text === lastSpokenMessage && now - lastSpokenTime < 4000) return;
    lastSpokenMessage = text;
    lastSpokenTime = now;
    speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1.0;
    utter.pitch = 1.0;
    speechSynthesis.speak(utter);
}

function toggleMic() {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
        alert("Voice input not supported in this browser. Try Chrome.");
        return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
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
    if (t.includes("start") || t.includes("begin")) startPractice();
    else if (t.includes("stop") || t.includes("pause")) pausePractice();
    else if (t.includes("restart") || t.includes("again")) restartPractice();
    else if (t.includes("help") || t.includes("instructions")) {
        speak(POSE_DATA.instructions.join(". "));
    }
}