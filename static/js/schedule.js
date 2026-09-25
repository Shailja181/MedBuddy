function toggleTaken(id) {
    const key = `taken_${new Date().toDateString()}_${id}`;
    localStorage.setItem(key, localStorage.getItem(key) === "1" ? "0" : "1");
    render();
}

async function render() {
    const r = await fetch("/api/schedule/today");
    const data = await r.json();
    document.getElementById("today-date").textContent = new Date(data.date).toDateString();

    const now = new Date();
    let taken = 0, missed = 0, upcoming = 0;

    const el = document.getElementById("slot-list");
    if (!data.slots.length) {
        el.innerHTML = `<div class="empty">No medicines scheduled today. Add active medicines from the Medicines page.</div>`;
        document.getElementById("ss-total").textContent = 0;
        document.getElementById("ss-taken").textContent = 0;
        document.getElementById("ss-upcoming").textContent = 0;
        document.getElementById("ss-missed").textContent = 0;
        return;
    }

    el.innerHTML = data.slots.map((s, i) => {
        const key = `taken_${new Date().toDateString()}_${i}`;
        const isTaken = localStorage.getItem(key) === "1";
        const [h, m] = s.time.split(":");
        const slotTime = new Date(); slotTime.setHours(+h, +m, 0);
        const past = slotTime < now;
        const status = isTaken ? "taken" : past ? "missed" : "upcoming";
        if (isTaken) taken++; else if (past) missed++; else upcoming++;
        return `
            <div class="slot-card status-${status}">
                <div class="slot-time">${s.time}</div>
                <h3>${s.name}</h3>
                <p class="muted">${s.dosage} · ${s.purpose}</p>
                <button class="btn ${isTaken?'':'primary'}" style="margin-top:12px;width:100%;justify-content:center" onclick="toggleTaken(${i})">
                    ${isTaken ? '✓ Taken' : 'Mark taken'}
                </button>
            </div>`;
    }).join("");

    document.getElementById("ss-total").textContent = data.slots.length;
    document.getElementById("ss-taken").textContent = taken;
    document.getElementById("ss-upcoming").textContent = upcoming;
    document.getElementById("ss-missed").textContent = missed;
}
render();
setInterval(render, 60000);