async function loadComponent(selector, url) {
    const slot = document.querySelector(selector);
    const res = await fetch(url);
    slot.innerHTML = await res.text();
}

async function checkMt5() {
    const container = document.getElementById('mt5');
    const dot = container.querySelector('.dot');
    const label = container.querySelector('.label');
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        const connected = data.mt5_connected;
        dot.classList.remove('skeleton');
        label.classList.remove('skeleton', 'skeleton-text');
        dot.style.backgroundColor = connected ? '#22c55e' : '#ef4444';
        label.textContent = 'MT5: ' + (connected ? 'Connected' : 'Disconnected');
    } catch (e) {
        dot.classList.remove('skeleton');
        label.classList.remove('skeleton', 'skeleton-text');
        dot.style.backgroundColor = '#ef4444';
        label.textContent = 'MT5: Tidak dapat terhubung';
    }
}

async function loadSymbols() {
    const list = document.getElementById('symbol-list');
    try {
        const res = await fetch('/api/symbols');
        const data = await res.json();
        const symbols = data.symbols.slice().sort((a, b) => a.localeCompare(b));
        list.innerHTML = '';
        symbols.forEach(sym => {
            const li = document.createElement('li');
            li.textContent = sym;
            list.appendChild(li);
        });
    } catch (e) {
        list.innerHTML = '<li>Gagal memuat symbols</li>';
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadComponent('#header-slot', '/components/header.html');
    await loadComponent('#sidebar-slot', '/components/sidebar.html');
    checkMt5();
    loadSymbols();
    initSidebarToggle();
});

function initSidebarToggle() {
    const toggle = document.getElementById('menu-toggle');
    const overlay = document.querySelector('.overlay');
    if (!toggle || !overlay) return;
    toggle.addEventListener('click', () => {
        document.body.classList.toggle('sidebar-open');
    });
    overlay.addEventListener('click', () => {
        document.body.classList.remove('sidebar-open');
    });
}
