/**
 * Real-time Yoga Pose Detector & Posture Checker
 * Uses MediaPipe Pose + HTML5 Webcam API
 */

let videoElement = null;
let canvasElement = null;
let canvasCtx = null;
let currentTargetAsana = "cobra";

function initYogaCamera(asanaName) {
    currentTargetAsana = asanaName.toLowerCase();
    videoElement = document.getElementById('yoga-webcam');
    canvasElement = document.getElementById('yoga-canvas');
    canvasCtx = canvasElement.getContext('2d');

    const pose = new Pose({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });

    pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    pose.onResults(onPoseResults);

    const camera = new Camera(videoElement, {
        onFrame: async () => {
            await pose.send({ image: videoElement });
        },
        width: 640,
        height: 480
    });
    camera.start();
    speakVoice(`Starting ${asanaName} camera session. Adjust your position.`);
}

function calculateAngle(a, b, c) {
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs((radians * 180.0) / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}

let lastSpokenTime = 0;
function announceFeedback(text) {
    const now = Date.now();
    if (now - lastSpokenTime > 4000) { // Limit feedback rate
        speakVoice(text);
        lastSpokenTime = now;
    }
}

function onPoseResults(results) {
    if (!results.poseLandmarks) return;

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    const landmarks = results.poseLandmarks;

    if (currentTargetAsana.includes("cobra") || currentTargetAsana.includes("bhujangasana")) {
        // Evaluate Shoulder-Elbow-Wrist angle for Cobra pose elevation
        const shoulder = landmarks[11];
        const elbow = landmarks[13];
        const wrist = landmarks[15];
        
        const elbowAngle = calculateAngle(shoulder, elbow, wrist);
        
        if (elbowAngle < 120) {
            announceFeedback("Lift your chest higher and gently straighten your elbows.");
        } else if (elbowAngle > 175) {
            announceFeedback("Do not lock your elbows. Keep a slight soft bend.");
        }
    } else if (currentTargetAsana.includes("plank")) {
        // Evaluate Shoulder-Hip-Ankle alignment
        const shoulder = landmarks[11];
        const hip = landmarks[23];
        const ankle = landmarks[27];
        
        const hipAngle = calculateAngle(shoulder, hip, ankle);
        if (hipAngle < 160) {
            announceFeedback("Lower your hips, maintain a straight line from head to heels.");
        } else if (hipAngle > 190) {
            announceFeedback("Lift your core to prevent sagging your lower back.");
        }
    }

    drawConnectors(canvasCtx, landmarks, POSE_CONNECTIONS, { color: '#0f766e', lineWidth: 4 });
    drawLandmarks(canvasCtx, landmarks, { color: '#f43f5e', lineWidth: 2 });
    canvasCtx.restore();
}