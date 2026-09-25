let allExercises = [];

async function loadExercises(cat = "") {
    const r = await fetch(`/api/exercises${cat ? `?category=${cat}` : ""}`);
    allExercises = await r.json();
    const el = document.getElementById("exercise-list");
    if (!allExercises.length) {
        el.innerHTML = `<div class="empty">No exercises in this category yet.</div>`;
        return;
    }
    el.innerHTML = allExercises.map(e => {
        const hasCamera = !!e.pose_key;
        return `
        <div class="glass-card exercise-card">
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px">
                <div style="font-size:34px">${getIcon(e.category)}</div>
                <div style="display:flex;gap:6px;flex-direction:column;align-items:flex-end">
                    <span class="diet-badge" style="background:rgba(99,102,241,0.15);color:#a5b4fc">${e.level}</span>
                    ${hasCamera ? '<span class="diet-badge camera-badge">🎥 AI Coach</span>' : ''}
                </div>
            </div>
            <h3>${e.title}</h3>
            <p class="muted" style="margin:6px 0 12px;font-size:13px">${e.category}</p>
            <p style="font-size:13px;line-height:1.6">${e.description}</p>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.06)">
                <span style="color:var(--brand-light);font-weight:600;font-size:13px">⏱ ${e.duration}</span>
                <div style="display:flex;gap:6px">
                    <button class="btn" onclick="openExercise(${e.id})" style="padding:6px 12px;font-size:12px">Details</button>
                    <a class="btn primary" href="/exercise/practice/${e.id}" style="padding:6px 14px;font-size:13px">
                        ${hasCamera ? '🎥 Practice' : '▶ Start'}
                    </a>
                </div>
            </div>
        </div>`;
    }).join("");
}

function getIcon(category) {
    const icons = {
        "Yoga": "🧘", "Stretching": "🤸", "Strength": "💪",
        "Breathing": "🫁", "Relaxation": "😌", "Mobility": "🔄"
    };
    return icons[category] || "🧘";
}

function openExercise(id) {
    const e = allExercises.find(x => x.id === id);
    if (!e) return;
    document.getElementById("e-modal-body").innerHTML = `
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px">
            <div style="width:52px;height:52px;background:linear-gradient(135deg,rgba(16,185,129,0.25),rgba(110,231,183,0.1));border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:26px">${getIcon(e.category)}</div>
            <div>
                <h2 style="margin:0">${e.title}</h2>
                <p class="muted" style="font-size:13px;margin-top:2px">${e.category} · ${e.level} · ⏱ ${e.duration}</p>
            </div>
        </div>

        <h4 style="margin-top:16px;color:#fff">📖 Description</h4>
        <p style="line-height:1.6">${e.description}</p>

        ${e.target_conditions ? `
            <h4 style="margin-top:16px;color:#fff">🎯 Helps with</h4>
            <p style="line-height:1.6">${e.target_conditions}</p>
        ` : ''}

        <h4 style="margin-top:16px;color:#fff">📋 Instructions</h4>
        <p style="line-height:1.8;white-space:pre-line">${e.instructions || e.description}</p>

        <p class="disclaimer" style="margin-top:16px">Stop immediately if you feel pain. Consult a doctor before starting new routines.</p>
        <div class="modal-actions">
            <button class="btn" onclick="document.getElementById('e-modal').classList.add('hidden')">Close</button>
            <a class="btn primary" href="/exercise/practice/${e.id}">
                ${e.pose_key ? '🎥 Practice with Camera' : '▶ Start Guided Session'}
            </a>
        </div>`;
    document.getElementById("e-modal").classList.remove("hidden");
}

document.getElementById("filter-bar").addEventListener("click", e => {
    if (!e.target.classList.contains("filter-chip")) return;
    document.querySelectorAll(".filter-chip").forEach(b => b.classList.remove("active"));
    e.target.classList.add("active");
    loadExercises(e.target.dataset.cat);
});

loadExercises();