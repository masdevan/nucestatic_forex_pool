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
        var active = container.querySelector('.symbol-link.active');
        if (active) {
            var sc = container.closest('.sidebar-container');
            if (sc) {
                var top = active.offsetTop - sc.offsetTop - sc.clientHeight / 2 + active.clientHeight / 2;
                sc.scrollTop = Math.max(0, top);
            }
        }
    } catch (e) {
        container.innerHTML = '<li>Gagal memuat symbols</li>';
    }
}

function initThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    const stored = localStorage.getItem('theme');
    if (stored === 'dark') document.body.classList.add('dark-mode');
    toggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    loadSymbols();
    initSidebarToggle();
    initApiTester();
    initThemeToggle();
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

function initApiTester() {
    var paramsDiv = document.getElementById('api-params');
    var resultDiv = document.getElementById('api-result');
    var runBtn = document.getElementById('api-run');
    var urlDiv = document.getElementById('api-url');
    var items = document.querySelectorAll('.api-endpoint-item');
    if (!items.length) return;

    var currentEp = '';
    var symbols = [];
    fetch('/api/symbols').then(function(r){return r.json()}).then(function(d){
        symbols = d.symbols.map(function(s){return s.name});
    });

    function updateUrl() {
        var url = '';
        if (currentEp === 'health') url = '/api/health';
        else if (currentEp === 'symbols') {
            var srch = (document.getElementById('p-search') || {}).value || '';
            url = '/api/symbols' + (srch ? '?search=' + encodeURIComponent(srch) : '');
        }
        else if (currentEp === 'range' || currentEp === 'date-range') {
            var sym = (document.getElementById('p-symbol') || {}).value || 'EURUSDm';
            url = '/api/symbols/' + encodeURIComponent(sym) + '/' + currentEp;
            if (currentEp === 'date-range') {
                var tf = (document.getElementById('p-timeframe') || {}).value || 'm1';
                var sd = (document.getElementById('p-start') || {}).value || '';
                var ed = (document.getElementById('p-end') || {}).value || '';
                var lm = (document.getElementById('p-limit') || {}).value || '50';
                url += '?timeframe=' + encodeURIComponent(tf);
                if (sd) url += '&start_date=' + encodeURIComponent(sd.replace('T', ' '));
                if (ed) url += '&end_date=' + encodeURIComponent(ed.replace('T', ' '));
                url += '&limit=' + encodeURIComponent(lm);
            }
        } else if (currentEp === 'ohlc') {
            var tf = (document.getElementById('p-timeframe') || {}).value || 'm1';
            var sym2 = (document.getElementById('p-symbol') || {}).value || 'EURUSDm';
            var pg = (document.getElementById('p-page') || {}).value || '1';
            var lm = (document.getElementById('p-limit') || {}).value || '50';
            url = '/api/ohlc/' + tf + '?symbol=' + encodeURIComponent(sym2) + '&page=' + pg + '&limit=' + lm;
        }
        urlDiv.textContent = url || '-';
    }

    function renderParams() {
        var html = '';
        if (currentEp === 'symbols') {
            html += '<div class="tester-row"><label>search</label><input id="p-search" placeholder="contoh: btc"></div>';
        }
        if (currentEp === 'range' || currentEp === 'ohlc' || currentEp === 'date-range') {
            html += '<div class="tester-row"><label>symbol</label><input id="p-symbol" value="EURUSDm"></div>';
        }
        if (currentEp === 'ohlc' || currentEp === 'date-range') {
            html += '<div class="tester-row"><label>timeframe</label><select id="p-timeframe">' +
                '<option>m1</option><option>m5</option><option>m15</option><option>m30</option>' +
                '<option>h1</option><option>h4</option><option>d1</option><option>w1</option><option>mn1</option>' +
                '</select></div>';
        }
        if (currentEp === 'date-range') {
            html += '<div class="tester-row"><label>start_date</label><input id="p-start" type="datetime-local"></div>';
            html += '<div class="tester-row"><label>end_date</label><input id="p-end" type="datetime-local"></div>';
            html += '<div class="tester-row"><label>limit</label><input id="p-limit" type="number" value="50" min="1" max="1000"></div>';
        }
        if (currentEp === 'ohlc') {
            html += '<div class="tester-row"><label>timeframe</label><select id="p-timeframe">' +
                '<option>m1</option><option>m5</option><option>m15</option><option>m30</option>' +
                '<option>h1</option><option>h4</option><option>d1</option><option>w1</option><option>mn1</option>' +
                '</select></div>';
            html += '<div class="tester-row"><label>page</label><input id="p-page" type="number" value="1" min="1"></div>';
            html += '<div class="tester-row"><label>limit</label><input id="p-limit" type="number" value="50" min="1" max="100"></div>';
        }
        paramsDiv.innerHTML = html;
        updateUrl();

        paramsDiv.querySelectorAll('input, select').forEach(function(el) {
            el.addEventListener('input', updateUrl);
            el.addEventListener('change', updateUrl);
        });
    }

    items.forEach(function(item) {
        item.addEventListener('click', function() {
            items.forEach(function(i){i.classList.remove('active')});
            item.classList.add('active');
            currentEp = item.getAttribute('data-ep');
            resultDiv.className = 'api-result';
            resultDiv.textContent = '';
            renderParams();
        });
    });

    runBtn.addEventListener('click', function() {
        if (!currentEp) return;
        var url = urlDiv.textContent;
        resultDiv.innerHTML = '<span class="tester-loading">Loading...</span>';
        resultDiv.className = 'api-result loaded';
        fetch(url).then(function(r){return r.json()}).then(function(data){
            resultDiv.textContent = JSON.stringify(data, null, 2);
            resultDiv.className = 'api-result loaded';
        }).catch(function(e){
            resultDiv.textContent = 'Error: ' + e.message;
            resultDiv.className = 'api-result error';
        });
    });

    items[0].click();
}
