function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    document.getElementById(`tab-${tabId}`).classList.remove('hidden');
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('bg-white/5', 'text-white');
        link.classList.add('text-slate-300');
    });
    
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('bg-white/5', 'text-white');
        event.currentTarget.classList.remove('text-slate-300');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchMedicines();
    fetchAllergies();
});

function showSafetyAlert(title, message, type) {
    const container = document.getElementById('alertContainer');
    const alertEl = document.createElement('div');
    
    const isHigh = type.toLowerCase().includes('allergy');
    const colorClass = isHigh ? 'border-rose-500/50 bg-rose-500/10 text-rose-400' : 'border-amber-500/50 bg-amber-500/10 text-amber-400';
    
    alertEl.className = `p-4 rounded-xl border backdrop-blur-md shadow-lg transition-all transform animate-fade-in-up ${colorClass}`;
    alertEl.innerHTML = `
        <div class="flex justify-between items-start mb-1">
            <h4 class="font-bold text-sm"><i class="fa-solid fa-triangle-exclamation mr-1"></i> ${title}</h4>
            <button onclick="this.parentElement.parentElement.remove()" class="text-xs hover:text-white"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <p class="text-xs text-slate-300 leading-relaxed">${message}</p>
    `;
    
    container.appendChild(alertEl);
    
    setTimeout(() => {
        if (alertEl.parentElement) {
            alertEl.classList.add('opacity-0', 'translate-x-full');
            setTimeout(() => alertEl.remove(), 300);
        }
    }, 8000);
}

async function fetchMedicines() {
    try {
        const res = await fetch('/api/medicines');
        const meds = await res.json();
        
        const countEl = document.getElementById('count-meds');
        if(countEl) countEl.innerText = meds.length;
        
        const list = document.getElementById('medsList');
        if (!list) return;

        if (meds.length === 0) {
            list.innerHTML = `<p class="text-slate-500 text-sm col-span-full">No active medicines found.</p>`;
            return;
        }

        list.innerHTML = meds.map(m => `
            <div class="glass-card p-5 rounded-2xl relative border-l-4 border-l-teal-400">
                <button onclick="deleteMedicine(${m.id})" class="absolute top-4 right-4 text-slate-500 hover:text-rose-400 transition-colors"><i class="fa-solid fa-trash text-sm"></i></button>
                <h4 class="text-lg font-bold text-white">${m.name}</h4>
                <p class="text-sm text-teal-300 mb-2 font-medium">${m.dosage} • ${m.frequency}</p>
                <p class="text-xs text-slate-400"><i class="fa-solid fa-calendar-day mr-1"></i> Started: ${m.start_date}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
    }
}

async function fetchAllergies() {
    try {
        const res = await fetch('/api/allergies');
        const allergies = await res.json();
        
        const countEl = document.getElementById('count-allergies');
        if(countEl) countEl.innerText = allergies.length;
        
        const list = document.getElementById('allergiesList');
        if (!list) return;

        if (allergies.length === 0) {
            list.innerHTML = `<p class="text-slate-500 text-sm col-span-full">No allergies recorded.</p>`;
            return;
        }

        list.innerHTML = allergies.map(a => `
            <div class="glass-card p-5 rounded-2xl border border-rose-500/30 bg-rose-500/5">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="text-lg font-bold text-white flex items-center gap-2"><i class="fa-solid fa-triangle-exclamation text-rose-500"></i> ${a.name}</h4>
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400">${a.severity}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
    }
}

async function previewAndRunOCR(event) {
    const file = event.target.files[0];
    if (!file) return;

    const preview = document.getElementById('imagePreview');
    const loading = document.getElementById('ocrLoading');
    const editForm = document.getElementById('ocrEditForm');

    preview.src = URL.createObjectURL(file);
    preview.classList.remove('hidden');
    
    loading.classList.remove('hidden');
    editForm.classList.add('opacity-50', 'pointer-events-none');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/ocr/scan', {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        
        if (result.success && result.data.medicines.length > 0) {
            const med = result.data.medicines[0];
            document.getElementById('ocrMedName').value = med.name;
            document.getElementById('ocrDosage').value = med.dosage;
            document.getElementById('ocrFrequency').value = med.frequency;
        } else {
            alert('Could not confidently extract structured medicine details. Please fill the form manually.');
        }
    } catch (err) {
        alert('OCR processing failed. Ensure the image is clear and try again.');
    } finally {
        loading.classList.add('hidden');
        editForm.classList.remove('opacity-50', 'pointer-events-none');
    }
}

async function saveExtractedMedicine() {
    const payload = {
        medicine_name: document.getElementById('ocrMedName').value,
        dosage: document.getElementById('ocrDosage').value,
        frequency: document.getElementById('ocrFrequency').value
    };

    if(!payload.medicine_name) return alert("Medicine name is required");

    try {
        const res = await fetch('/api/medicines', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.success) {
            if (data.alerts && data.alerts.length > 0) {
                data.alerts.forEach(alert => showSafetyAlert(alert.title, alert.message, alert.type));
            }
            
            document.getElementById('ocrEditForm').reset();
            document.getElementById('imagePreview').classList.add('hidden');
            
            fetchMedicines();
            switchTab('medicines');
        } else {
            alert(data.error || 'Failed to save medicine');
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteMedicine(id) {
    if(!confirm("Are you sure you want to delete this medication?")) return;
    
    try {
        await fetch(`/api/medicines/${id}`, { method: 'DELETE' });
        fetchMedicines();
    } catch (err) {
        console.error(err);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    const chatContainer = document.getElementById('chatMessages');
    
    chatContainer.innerHTML += `
        <div class="flex gap-3 flex-row-reverse animate-fade-in-up">
            <div class="w-8 h-8 rounded-full bg-slate-700 border border-white/10 flex items-center justify-center text-xs"><i class="fa-solid fa-user"></i></div>
            <div class="bg-blue-600 p-3 rounded-2xl text-sm max-w-md text-white shadow-lg shadow-blue-900/20">
                ${msg}
            </div>
        </div>
    `;
    
    input.value = '';
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        
        setTimeout(() => {
            chatContainer.innerHTML += `
                <div class="flex gap-3 animate-fade-in-up">
                    <div class="w-8 h-8 rounded-full bg-blue-600 shadow-lg shadow-blue-600/30 flex items-center justify-center text-xs"><i class="fa-solid fa-robot"></i></div>
                    <div class="bg-white/10 border border-white/10 p-3 rounded-2xl text-sm max-w-md leading-relaxed text-slate-200">
                        ${data.reply}
                    </div>
                </div>
            `;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 400); 
        
    } catch (err) {
        console.error(err);
    }
}

async function logoutUser() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/';
    } catch(err) {
        console.error(err);
    }
}

const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in-up {
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
`;
document.head.appendChild(style);