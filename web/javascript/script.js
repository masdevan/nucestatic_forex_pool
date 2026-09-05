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
        const serverNames = Object.keys(groups).sort((a, b) => a.localeCompare(b));
        const pathParts = window.location.pathname.split('/').filter(Boolean);
        const activeName = pathParts.length >= 2 ? decodeURIComponent(pathParts[0]) : null;
        const activeServer = pathParts.length >= 2 ? decodeURIComponent(pathParts[1]) : null;
        container.classList.add('fading');
        await new Promise(r => setTimeout(r, 300));
        container.classList.remove('fading');
        container.classList.add('fading-in');
        container.innerHTML = '';
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
                if (name === activeName && server === activeServer) {
                    a.classList.add('active');
                }
                li.appendChild(a);
                ul.appendChild(li);
            });
            container.appendChild(ul);
        });
        setTimeout(() => container.classList.remove('fading-in'), 400);
    } catch (e) {
        container.innerHTML = '<li>Gagal memuat symbols</li>';
    }
}

document.addEventListener('DOMContentLoaded', async () => {
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
