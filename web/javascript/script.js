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
    const container = document.getElementById('symbol-list');
    try {
        const res = await fetch('/api/symbols');
        const data = await res.json();
        const groups = {};
        data.symbols.forEach(sym => {
            const key = sym.server || 'Unknown';
            if (!groups[key]) groups[key] = [];
            groups[key].push(sym.name);
        });
        Object.keys(groups).forEach(server => {
            groups[server].sort((a, b) => a.localeCompare(b));
        });
        container.innerHTML = '';
        const serverNames = Object.keys(groups).sort((a, b) => a.localeCompare(b));
        serverNames.forEach(server => {
            const header = document.createElement('div');
            header.className = 'symbol-group-header';
            header.textContent = server;
            header.addEventListener('click', () => {
                header.classList.toggle('collapsed');
            });
            container.appendChild(header);

            const ul = document.createElement('ul');
            ul.className = 'symbol-group-list';
            groups[server].forEach(name => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.className = 'symbol-link';
                a.textContent = name;
                a.href = '/' + encodeURIComponent(name) + '/' + encodeURIComponent(server);
                li.appendChild(a);
                ul.appendChild(li);
            });
            container.appendChild(ul);
        });
    } catch (e) {
        container.innerHTML = '<li>Gagal memuat symbols</li>';
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
