let editAId = null;

async function loadAllergies() {
    const r = await fetch("/api/allergies");
    const list = await r.json();
    const el = document.getElementById("allergy-list");
    if (!list.length) {
        el.innerHTML = `<div class="empty">No allergies recorded yet. Add one to help MedBuddy warn you about conflicts.</div>`;
        return;
    }
    el.innerHTML = list.map(a => `
        <div class="allergy-card ${a.severity}">
            <h3>${a.name}</h3>
            <p class="muted">Severity: <strong>${a.severity}</strong></p>
            ${a.notes ? `<p class="muted">${a.notes}</p>` : ''}
            <div class="card-actions" style="display:flex;gap:8px;margin-top:12px">
                <button onclick='editAllergy(${JSON.stringify(a)})'>Edit</button>
                <button class="danger" onclick="removeAllergy(${a.id})">Delete</button>
            </div>
        </div>`).join("");
}

function openAllergyModal() {
    editAId = null;
    document.getElementById("a-modal-title").textContent = "Add Allergy";
    document.getElementById("a-name").value = "";
    document.getElementById("a-severity").value = "moderate";
    document.getElementById("a-notes").value = "";
    document.getElementById("a-modal").classList.remove("hidden");
}

function closeAllergyModal() {
    document.getElementById("a-modal").classList.add("hidden");
}

function editAllergy(a) {
    editAId = a.id;
    document.getElementById("a-modal-title").textContent = "Edit Allergy";
    document.getElementById("a-name").value = a.name;
    document.getElementById("a-severity").value = a.severity;
    document.getElementById("a-notes").value = a.notes || "";
    document.getElementById("a-modal").classList.remove("hidden");
}

async function saveAllergy() {
    const body = {
        name: document.getElementById("a-name").value.trim(),
        severity: document.getElementById("a-severity").value,
        notes: document.getElementById("a-notes").value,
    };
    if (!body.name) return alert("Enter an allergen name");

    const url = editAId ? `/api/allergies/${editAId}` : "/api/allergies";
    const method = editAId ? "PUT" : "POST";
    await fetch(url, {
        method, headers: {"Content-Type":"application/json"},
        body: JSON.stringify(body)
    });
    closeAllergyModal();
    loadAllergies();
}

async function removeAllergy(id) {
    if (!confirm("Delete this allergy?")) return;
    await fetch(`/api/allergies/${id}`, {method: "DELETE"});
    loadAllergies();
}

loadAllergies();