let authMode = 'login';

function openAuthModal(mode = 'login') {
    authMode = mode;
    const modal = document.getElementById('authModal');
    const title = document.getElementById('authTitle');
    const nameField = document.getElementById('nameField');
    const toggleBtn = document.getElementById('toggleAuthBtn');

    if (authMode === 'register') {
        title.innerText = 'Create your MedBuddy Profile';
        nameField.classList.remove('hidden');
        toggleBtn.innerText = 'Already have an account? Sign in';
    } else {
        title.innerText = 'Sign In to MedBuddy';
        nameField.classList.add('hidden');
        toggleBtn.innerText = 'Need an account? Register here';
    }
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function toggleAuthMode() {
    openAuthModal(authMode === 'login' ? 'register' : 'login');
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('authEmail').value;
    const password = document.getElementById('authPassword').value;
    const name = document.getElementById('authName').value;

    const endpoint = authMode === 'register' ? '/api/auth/register' : '/api/auth/login';
    const payload = authMode === 'register' ? { name, email, password } : { email, password };

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok && data.success) {
            window.location.href = '/dashboard';
        } else {
            alert(data.message || 'Authentication failed');
        }
    } catch (err) {
        alert('Server connection error.');
    }
}