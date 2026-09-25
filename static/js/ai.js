function push(role, text) {
    const el = document.createElement("div");
    el.className = `bubble ${role}`;
    el.textContent = text;
    document.getElementById("chat-log").appendChild(el);
    el.scrollIntoView({behavior:"smooth"});
}

async function sendMsg() {
    const input = document.getElementById("msg");
    const q = input.value.trim(); if (!q) return;
    push("user", q); input.value = "";
    push("bot", "…");
    const r = await fetch("/api/ai/chat", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({message: q})
    });
    const d = await r.json();
    const bubbles = document.querySelectorAll(".bubble.bot");
    bubbles[bubbles.length-1].textContent = d.reply || d.error || "Error";
}