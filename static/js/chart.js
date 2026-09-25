async function loadChart() {
    const r = await fetch("/api/chart");
    const d = await r.json();

    const meds = d.medicines.filter(m => m.start_date);
    const ctx = document.getElementById("med-timeline");
    if (meds.length) {
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: meds.map(m => m.name),
                datasets: [{
                    label: "Duration (days)",
                    data: meds.map(m => {
                        const start = new Date(m.start_date);
                        const end = m.end_date ? new Date(m.end_date) : new Date();
                        return Math.max(1, Math.round((end - start) / 86400000));
                    }),
                    backgroundColor: "rgba(16, 185, 129, 0.6)",
                    borderColor: "rgba(16, 185, 129, 1)",
                    borderWidth: 1, borderRadius: 6,
                }]
            },
            options: {
                indexAxis: "y", responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { title: { display: true, text: "Days", color:"rgba(226,232,240,0.7)" },
                         ticks:{ color:"rgba(226,232,240,0.6)" }, grid:{ color:"rgba(255,255,255,0.05)" }},
                    y: { ticks:{ color:"rgba(226,232,240,0.8)" }, grid:{ color:"rgba(255,255,255,0.05)" }}
                }
            }
        });
    } else {
        ctx.parentElement.innerHTML += `<p class="muted" style="padding:20px">Add medicines with start dates to see timeline.</p>`;
    }

    document.getElementById("allergy-summary").innerHTML = d.allergies.length
        ? d.allergies.map(a => `<p>⚠ <strong>${a.name}</strong> <span class="muted">(${a.severity})</span></p>`).join("")
        : `<p class="muted">No allergies recorded.</p>`;

    document.getElementById("record-summary").innerHTML = d.records.length
        ? d.records.slice(-5).reverse().map(r => `
            <p>📄 <strong>${r.document_name}</strong>
            <span class="muted">· ${new Date(r.uploaded_date).toLocaleDateString()}</span></p>`).join("")
        : `<p class="muted">No documents scanned yet.</p>`;

    document.getElementById("event-summary").innerHTML = d.events.length
        ? d.events.slice(-5).reverse().map(e => `
            <p>📌 <strong>${e.event_type}</strong> <span class="muted">· ${e.date}</span><br>
            <span style="font-size:13px">${e.description || ''}</span></p>`).join("")
        : `<p class="muted">No health events logged yet.</p>`;
}
loadChart();