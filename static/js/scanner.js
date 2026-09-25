const dz = document.getElementById("dropzone");
const fileInput = document.getElementById("scan-file");
let ttsOn = false;

["dragenter", "dragover"].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add("dragover"); }));
["dragleave", "drop"].forEach(ev =>
    dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove("dragover"); }));

dz.addEventListener("drop", e => {
    fileInput.files = e.dataTransfer.files;
    showPreview();
});
fileInput.addEventListener("change", showPreview);

function showPreview() {
    const f = fileInput.files[0];
    if (f && f.type.startsWith("image/")) {
        document.getElementById("scan-preview").innerHTML =
            `<img src="${URL.createObjectURL(f)}" style="max-width:100%;border-radius:12px;margin-top:16px">`;
    }
}

async function runScan() {
    const f = fileInput.files[0];
    if (!f) return alert("Choose a file first");
    const fd = new FormData(); fd.append("file", f);
    document.getElementById("scan-status").innerHTML =
        `<span class="pulse-dot"></span>Extracting text with OCR…`;

    const r = await fetch("/api/scan", { method: "POST", body: fd });
    const d = await r.json();
    document.getElementById("scan-status").innerHTML =
        `<span style="color:var(--brand-light)">✓ Text extracted. Review below.</span>`;

    const p = d.parsed || {};
    
    let html = "";
    if (p.diagnosisPlain) {
        html = `
        <div class="glass-card" style="grid-column:1/-1; background:rgba(0,212,184,0.05); border-color:var(--brand)">
            <h3 style="color:var(--brand-light);margin-bottom:8px">🩺 ${p.diagnosis || 'Diagnosis'}</h3>
            <p style="font-size:15px;line-height:1.6">${p.diagnosisPlain}</p>
            <p style="margin-top:12px;font-size:13px;font-style:italic;color:var(--text-muted)">"${p.familyOneliner || ''}"</p>
        </div>
        <div class="glass-card">
            <h4 style="margin-bottom:12px">💊 Medications</h4>
            <div style="display:flex;flex-direction:column;gap:8px">
                ${(p.medicines || []).map(m => `
                    <div style="background:rgba(255,255,255,0.03);padding:8px;border-radius:8px">
                        <strong style="color:var(--brand-light)">${m.name}</strong> ${m.dosage || ''}<br>
                        <span style="font-size:12px;color:var(--text-muted)">${m.timing || m.frequency || ''} · ${m.days || m.duration || ''}</span>
                    </div>
                `).join("")}
            </div>
        </div>
        <div class="glass-card">
            <h4 style="margin-bottom:12px">✅ Action Plan</h4>
            <ul style="padding-left:18px;margin:0;font-size:13px;line-height:1.6;color:var(--text-muted)">
                ${(p.checklist || []).map(c => `<li>${c}</li>`).join("")}
            </ul>
            
            <h4 style="margin-top:16px;margin-bottom:8px">🚨 Side Effects</h4>
            ${(p.sideEffectsRed || []).map(s => `<div style="color:#fca5a5;font-size:12px;margin-bottom:4px">• ${s}</div>`).join("")}
            ${(p.sideEffectsAmber || []).map(s => `<div style="color:#fbbf24;font-size:12px;margin-bottom:4px">• ${s}</div>`).join("")}
            ${(p.sideEffectsGreen || []).map(s => `<div style="color:#a7f3d0;font-size:12px;margin-bottom:4px">• ${s}</div>`).join("")}
        </div>
        <input type="hidden" id="pf-medicine" value="${p.medicines && p.medicines.length > 0 ? p.medicines[0].name : ''}">
        `;
    } else {
        html = Object.entries(p).map(([k, v]) => {
            if (k === 'medicines') {
                let lis = "<li>None detected</li>";
                if (Array.isArray(v) && v.length > 0) {
                    if (typeof v[0] === 'object') {
                        lis = v.map(m => `<li><strong>${m.name || 'Unknown'}</strong> ${m.dosage || ''} ${m.frequency || ''}</li>`).join('');
                    } else {
                        lis = v.map(m => `<li>${m}</li>`).join('');
                    }
                }
                return `
                <div class="glass-card">
                    <label style="text-transform:capitalize">${k.replace(/_/g,' ')}</label>
                    <ul style="padding-left:20px;margin-top:8px;font-size:14px;color:var(--text-muted)">
                        ${lis}
                    </ul>
                </div>`;
            }
            
            let valStr = "";
            if (Array.isArray(v)) {
                valStr = v.length === 0 ? "None detected" : v.join(', ');
            } else {
                valStr = (v || '').toString();
            }
            return `
            <div class="glass-card">
                <label style="text-transform:capitalize">${k.replace(/_/g,' ')}</label>
                <input value="${valStr.replace(/"/g,'&quot;')}" id="pf-${k}">
            </div>`;
        }).join("");
    }
    
    document.getElementById("parsed-fields").innerHTML = html + `
        <div style="grid-column:1/-1;display:flex;gap:10px;flex-wrap:wrap;margin-top:8px">
            <button class="btn primary" onclick='saveParsed(${JSON.stringify(Object.keys(p))})'>💾 Save to Profile</button>
            <button class="btn" id="btn-diet">🥗 Generate Diet Plan</button>
            <button class="btn" id="btn-alt">🔄 Find Alternatives</button>
        </div>`;
        
    document.getElementById("btn-diet").onclick = () => generateDiet(d.text || "");
    const medName = Array.isArray(p.medicines) && p.medicines.length > 0 ? p.medicines[0].name : p.medicine || "";
    document.getElementById("btn-alt").onclick = () => checkAlternatives(medName);

    if (d.saved_items && d.saved_items.length > 0) {
        alert(`${d.saved_items.length} items auto-added!\n` + d.saved_items.join('\n'));
    }
}

async function saveParsed(keys) {
    const vals = {}; 
    keys.forEach(k => {
        const el = document.getElementById(`pf-${k}`);
        if (el) vals[k] = el.value;
    });
    
    if (vals.medicine) {
        await fetch("/api/medicines", {
            method:"POST", headers:{"Content-Type":"application/json"},
            body: JSON.stringify({ name: vals.medicine, dosage: vals.dosage,
                                   frequency: vals.frequency, purpose: vals.diagnosis, notes: vals.notes })
        });
    }
    if (vals.allergy) {
        await fetch("/api/allergies", {
            method:"POST", headers:{"Content-Type":"application/json"},
            body: JSON.stringify({ name: vals.allergy })
        });
    }
    alert("Saved to your profile");
}

async function generateDiet(ocrText) {
    const condition = prompt("Health condition? (e.g. Diabetes, Hypertension, General)", "General Health");
    if (!condition) return;

    const out = document.getElementById("diet-output");
    out.classList.remove("hidden");
    out.innerHTML = `<div class="glass-card"><p><span class="pulse-dot"></span>Generating personalized diet chart…</p></div>`;

    const r = await fetch("/api/diet/generate", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ ocr_text: ocrText, condition })
    });
    const d = await r.json();

    out.innerHTML = `
        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
                <h3 style="margin:0">📋 ${d.summary}</h3>
                <div style="display:flex;gap:8px">
                    <button class="btn" onclick="speakAll(${JSON.stringify(d).replace(/"/g,'&quot;')})">🔊 Read Aloud</button>
                    <button class="btn" onclick="toggleDietMic()" id="diet-mic">🎤 Ask</button>
                </div>
            </div>
        </div>
        <div class="diet-grid">
            <div class="diet-meal"><div class="meal-icon">🌅</div><h4>Breakfast</h4><p>${d.diet_chart.breakfast}</p></div>
            <div class="diet-meal"><div class="meal-icon">☀️</div><h4>Lunch</h4><p>${d.diet_chart.lunch}</p></div>
            <div class="diet-meal"><div class="meal-icon">🌙</div><h4>Dinner</h4><p>${d.diet_chart.dinner}</p></div>
            <div class="diet-meal"><div class="meal-icon">🍎</div><h4>Snacks</h4><p>${d.diet_chart.snacks}</p></div>
            <div class="diet-meal avoid"><div class="meal-icon">🚫</div><h4>Avoid</h4><p>${d.diet_chart.foods_to_avoid}</p></div>
        </div>

        <div class="magnet-card">
            <h3>Daily Fridge Magnet</h3>
            <div class="magnet-slot"><div class="when">Morning</div><div class="what">${d.fridge_magnet.morning}</div></div>
            <div class="magnet-slot"><div class="when">Afternoon</div><div class="what">${d.fridge_magnet.afternoon}</div></div>
            <div class="magnet-slot"><div class="when">Evening</div><div class="what">${d.fridge_magnet.evening}</div></div>
            <div class="magnet-slot"><div class="when">Night</div><div class="what">${d.fridge_magnet.night}</div></div>
            <div class="magnet-slot"><div class="when">🔑 Key</div><div class="what" style="color:#fbbf24">${d.fridge_magnet.key_notes}</div></div>
        </div>`;

    window._lastDiet = d;
}

function speakAll(d) {
    speechSynthesis.cancel();
    const text = `${d.summary}. Breakfast: ${d.diet_chart.breakfast}. Lunch: ${d.diet_chart.lunch}. Dinner: ${d.diet_chart.dinner}. Snacks: ${d.diet_chart.snacks}. Foods to avoid: ${d.diet_chart.foods_to_avoid}. Daily schedule: ${d.fridge_magnet.morning}, ${d.fridge_magnet.afternoon}, ${d.fridge_magnet.evening}, ${d.fridge_magnet.night}. Key note: ${d.fridge_magnet.key_notes}.`;
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.95;
    speechSynthesis.speak(u);
}

let dietRecog = null;
function toggleDietMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice input needs Chrome/Edge.");
    if (!dietRecog) {
        dietRecog = new SR();
        dietRecog.onresult = async e => {
            const q = e.results[0][0].transcript;
            const r = await fetch("/api/ai/chat", {
                method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify({message: q + " (context: my diet chart)"})
            });
            const d = await r.json();
            const u = new SpeechSynthesisUtterance(d.reply);
            speechSynthesis.speak(u);
            alert(`You asked: "${q}"\n\nMedBuddy: ${d.reply}`);
        };
    }
    dietRecog.start();
    document.getElementById("diet-mic").textContent = "🎙 Listening…";
    setTimeout(() => document.getElementById("diet-mic").textContent = "🎤 Ask", 5000);
}

async function checkAlternatives(medName) {
    if (!medName) return alert("No medicine name detected.");
    const out = document.getElementById("diet-output");
    out.classList.remove("hidden");
    out.innerHTML = `<div class="glass-card"><p><span class="pulse-dot"></span>Finding safer alternatives with AI…</p></div>`;

    const r = await fetch("/api/medicines/smart-alternatives", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({name: medName})
    });
    const d = await r.json();
    const ai = d.ai_enhanced;
    out.innerHTML = `
        <div class="glass-card">
            <h3 style="margin-bottom:12px">🔄 Alternatives for ${d.medicine}</h3>
            <p class="muted" style="margin-bottom:12px">${ai.reasoning || ''} ${ai.source === 'ai' ? '<span class="diet-badge" style="margin-left:6px">AI</span>' : ''}</p>
            <p class="muted" style="margin-bottom:12px; font-size: 13px;">(Click to find stores nearby)</p>
            <div class="alt-chips">
                ${(ai.alternatives || []).map(a => `<a href="https://www.google.com/maps/search/${encodeURIComponent(a)}+pharmacy+near+me" target="_blank" class="alt-chip" style="text-decoration:none; cursor:pointer;" title="Find ${a} in nearby stores">${a} 📍</a>`).join("")}
            </div>
            ${ai.warnings ? `<p style="margin-top:14px;color:#fca5a5;font-size:13px">⚠ ${ai.warnings}</p>` : ''}
        </div>`;
}