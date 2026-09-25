async function loadVitals() {
    const res = await fetch("/api/vitals");
    const data = await res.json();
    renderCharts(data);
    renderList(data);
}

function renderCharts(data) {
    const byKind = (kind) => data.filter(d => d.kind.toLowerCase().includes(kind));
    
    const bp = byKind("pressure");
    const sugar = byKind("sugar");
    const weight = byKind("weight");
    const hr = byKind("heart");

    const commonOptions = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { color: "rgba(255,255,255,0.6)" }, grid: { display: false } },
            y: { ticks: { color: "rgba(255,255,255,0.6)" }, grid: { color: "rgba(255,255,255,0.1)" } }
        }
    };

    if (bp.length) {
        new Chart(document.getElementById("chart-bp"), {
            type: "line",
            data: {
                labels: bp.map(d => new Date(d.recorded_at).toLocaleDateString()),
                datasets: [
                    { label: "Systolic", data: bp.map(d => parseInt(d.value.split("/")[0])), borderColor: "#fca5a5", tension: 0.3 },
                    { label: "Diastolic", data: bp.map(d => parseInt(d.value.split("/")[1])), borderColor: "#ef4444", tension: 0.3 }
                ]
            },
            options: commonOptions
        });
    }

    if (sugar.length) {
        new Chart(document.getElementById("chart-sugar"), {
            type: "line",
            data: {
                labels: sugar.map(d => new Date(d.recorded_at).toLocaleDateString()),
                datasets: [{ label: "mg/dL", data: sugar.map(d => parseFloat(d.value)), borderColor: "#fbbf24", backgroundColor: "rgba(251, 191, 36, 0.2)", fill: true, tension: 0.3 }]
            },
            options: commonOptions
        });
    }

    if (weight.length) {
        new Chart(document.getElementById("chart-weight"), {
            type: "line",
            data: {
                labels: weight.map(d => new Date(d.recorded_at).toLocaleDateString()),
                datasets: [{ label: "kg", data: weight.map(d => parseFloat(d.value)), borderColor: "#a5b4fc", backgroundColor: "rgba(165, 180, 252, 0.2)", fill: true, tension: 0.3 }]
            },
            options: commonOptions
        });
    }

    if (hr.length) {
        new Chart(document.getElementById("chart-hr"), {
            type: "line",
            data: {
                labels: hr.map(d => new Date(d.recorded_at).toLocaleDateString()),
                datasets: [{ label: "BPM", data: hr.map(d => parseFloat(d.value)), borderColor: "#6ee7b7", backgroundColor: "rgba(110, 231, 183, 0.2)", fill: true, tension: 0.3 }]
            },
            options: commonOptions
        });
    }
}

function renderList(data) {
    const list = document.getElementById("v-list");
    if (!data.length) {
        list.innerHTML = `<p class="muted">No vitals logged yet.</p>`;
        return;
    }
    
    list.innerHTML = [...data].reverse().slice(0, 10).map(v => `
        <div class="feedback-item ok" style="margin-bottom:8px;background:rgba(255,255,255,0.05)">
            <div>
                <strong>${v.kind}</strong>: ${v.value} <span class="muted">${v.unit}</span>
                ${v.notes ? `<div style="font-size:13px;opacity:0.8;margin-top:4px">${v.notes}</div>` : ''}
            </div>
            <div class="muted" style="font-size:12px">${new Date(v.recorded_at).toLocaleString()}</div>
        </div>
    `).join("");
}

async function saveVital() {
    const sel = document.getElementById("v-kind");
    const kindText = sel.options[sel.selectedIndex].text;
    const kind = kindText.split(" (")[0].replace(/[🩺🍬⚖💗🫁]/g, "").trim();
    const unit = kindText.includes("(") ? kindText.split("(")[1].replace(")", "") : "";
    const val = document.getElementById("v-value").value;
    const notes = document.getElementById("v-notes").value;

    if (!val) return alert("Enter a value");

    const res = await fetch("/api/vitals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind, value: val, unit, notes })
    });
    
    if (res.ok) {
        document.getElementById('v-modal').classList.add('hidden');
        window.location.reload();
    } else {
        alert("Failed to save");
    }
}

loadVitals();
