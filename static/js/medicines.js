let editId = null;

async function loadMeds() {
  const r = await fetch("/api/medicines");
  const meds = await r.json();
  const el = document.getElementById("med-list");
  if (!meds.length) {
    el.innerHTML = `<div class="empty">No medicines yet. Add one to get started.</div>`;
    return;
  }
  el.innerHTML = meds.map(m => `
    <div class="med-card ${m.is_active ? '' : 'inactive'}">
      <h3>${m.name}</h3>
      <p class="dosage">${m.dosage || ''} · ${m.frequency || ''}</p>
      <p class="muted">${m.purpose || ''}</p>
      <p class="dates">${m.start_date || ''} → ${m.end_date || 'ongoing'}</p>
      <div class="card-actions">
        <button onclick='editMed(${JSON.stringify(m)})'>Edit</button>
        <button class="danger" onclick="removeMed(${m.id})">Delete</button>
      </div>
    </div>`).join("");
}

function openMedModal() {
  editId = null;
  document.getElementById("med-modal-title").textContent = "Add Medicine";
  ["m-name","m-dosage","m-frequency","m-start","m-end","m-purpose","m-notes"]
    .forEach(id => document.getElementById(id).value = "");
  document.getElementById("med-modal").classList.remove("hidden");
}

function closeMedModal() { document.getElementById("med-modal").classList.add("hidden"); }

function editMed(m) {
  editId = m.id;
  document.getElementById("med-modal-title").textContent = "Edit Medicine";
  document.getElementById("m-name").value = m.name || "";
  document.getElementById("m-dosage").value = m.dosage || "";
  document.getElementById("m-frequency").value = m.frequency || "";
  document.getElementById("m-start").value = m.start_date || "";
  document.getElementById("m-end").value = m.end_date || "";
  document.getElementById("m-purpose").value = m.purpose || "";
  document.getElementById("m-notes").value = m.notes || "";
  document.getElementById("med-modal").classList.remove("hidden");
}

async function saveMed() {
  const body = {
    name: document.getElementById("m-name").value.trim(),
    dosage: document.getElementById("m-dosage").value,
    frequency: document.getElementById("m-frequency").value,
    start_date: document.getElementById("m-start").value,
    end_date: document.getElementById("m-end").value,
    purpose: document.getElementById("m-purpose").value,
    notes: document.getElementById("m-notes").value,
  };
  if (!body.name) return toast("Name required", "error");

  const url = editId ? `/api/medicines/${editId}` : "/api/medicines";
  const method = editId ? "PUT" : "POST";
  const r = await fetch(url, {
    method, headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)
  });
  const data = await r.json();

  if (data.conflicts && data.conflicts.length) showConflicts(data.conflicts);
  closeMedModal(); loadMeds(); toast("Saved");
}

async function removeMed(id) {
  if (!confirm("Delete this medicine?")) return;
  await fetch(`/api/medicines/${id}`, {method: "DELETE"});
  loadMeds(); toast("Deleted");
}

function showConflicts(list) {
    const el = document.getElementById("conflict-banner");
    el.innerHTML = `<h3>⚠ Potential Safety Alert</h3>` +
        list.map(c => `
            <div class="conflict-item severity-${(c.severity||'moderate').toLowerCase()}">
                <strong>${c.medicine}</strong> ↔ <strong>${c.conflict_with || c.type}</strong>
                <span class="badge">${c.severity}</span>
                <p style="margin-top:6px">${c.reason || c.message}</p>
                <p class="muted" style="font-size:13px;margin-top:4px">${c.recommendation || ''}</p>
                ${c.alternatives ? `
                    <p class="muted" style="margin-top:10px;font-size:12px;text-transform:uppercase;letter-spacing:1px">Safer alternatives (Click to find stores nearby):</p>
                    <div class="alt-chips">${c.alternatives.map(a => `<a href="https://www.google.com/maps/search/${encodeURIComponent(a)}+pharmacy+near+me" target="_blank" class="alt-chip" style="text-decoration:none; cursor:pointer;" title="Find ${a} in nearby stores">${a} 📍</a>`).join('')}</div>
                ` : ''}
            </div>`).join("");
    el.classList.remove("hidden");
}

function toast(msg, type="ok") {
  const t = document.createElement("div");
  t.className = `toast ${type}`; t.textContent = msg;
  document.getElementById("toast-root").appendChild(t);
  setTimeout(() => t.remove(), 2500);
}

loadMeds();