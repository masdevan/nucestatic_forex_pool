(function () {
    var parts = window.location.pathname.split('/').filter(Boolean);
    if (parts.length < 2) return;

    var name = decodeURIComponent(parts[0]);
    var tfCache = {};
    var currentTf = null;

    function loadDetails() {
        fetch('/api/symbols/' + encodeURIComponent(name) + '/range')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var el = document.getElementById('tab-details');
                if (!data.ranges || data.ranges.length === 0) {
                    el.innerHTML = '<p class="range-empty">Belum ada data.</p>';
                    return;
                }
                var html = '<div class="table-scroll"><table class="range-table"><tr><th>Timeframe</th><th>Data pertama</th><th>Data terakhir</th><th>Jumlah</th></tr>';
                data.ranges.forEach(function (rg) {
                    html += '<tr><td>' + rg.timeframe + '</td><td>' + rg.first +
                        '</td><td>' + rg.last + '</td><td>' + rg.count + '</td></tr>';
                });
                html += '</table></div>';
                el.innerHTML = html;
            })
            .catch(function () {
                document.getElementById('tab-details').innerHTML = '<p class="range-empty">Gagal memuat.</p>';
            });
    }

    function renderOhlcTable(data, page, totalPages) {
        var html = '<table class="ohlc-table"><thead><tr>' +
            '<th>Symbol</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Time</th>' +
            '</tr></thead><tbody>';
        if (data.length === 0) {
            html += '<tr><td colspan="6" class="range-empty">Tidak ada data.</td></tr>';
        } else {
            data.forEach(function (row) {
                var t = row.time;
                if (typeof t === 'number') {
                    t = new Date(t * 1000).toLocaleString();
                } else if (typeof t === 'string') {
                    t = t.replace('T', ' ').substring(0, 19);
                }
                html += '<tr><td>' + row.symbol + '</td><td>' + row.open +
                    '</td><td>' + row.high + '</td><td>' + row.low +
                    '</td><td>' + row.close + '</td><td>' + t + '</td></tr>';
            });
        }
        html += '</tbody></table>';
        if (totalPages > 1) {
            html += '<div class="pagination">';
            html += '<button class="pg-btn" data-pg="' + (page - 1) + '"' + (page <= 1 ? ' disabled' : '') + '>&laquo; Prev</button>';
            html += '<span class="pg-info">Halaman ' + page + ' / ' + totalPages + '</span>';
            html += '<button class="pg-btn" data-pg="' + (page + 1) + '"' + (page >= totalPages ? ' disabled' : '') + '>Next &raquo;</button>';
            html += '</div>';
        }
        return html;
    }

    function loadOhlc(tf, page) {
        page = page || 1;
        var cacheKey = tf + '_' + page;
        if (tfCache[cacheKey]) {
            var c = tfCache[cacheKey];
            document.getElementById('tab-' + tf).innerHTML = renderOhlcTable(c.data, c.pagination.page, c.pagination.total_pages);
            return;
        }
        var el = document.getElementById('tab-' + tf);
        el.innerHTML = '<p class="range-empty">Memuat...</p>';
        fetch('/api/ohlc/' + tf + '?symbol=' + encodeURIComponent(name) + '&page=' + page + '&limit=50')
            .then(function (r) { return r.json(); })
            .then(function (res) {
                tfCache[cacheKey] = res;
                el.innerHTML = renderOhlcTable(res.data, res.pagination.page, res.pagination.total_pages);
            })
            .catch(function () {
                el.innerHTML = '<p class="range-empty">Tabel tidak tersedia.</p>';
            });
    }

    document.querySelectorAll('.tab').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.querySelector('.tab.active').classList.remove('active');
            btn.classList.add('active');
            var tf = btn.getAttribute('data-tab');
            var activePanel = document.querySelector('.tab-panel.active');
            if (activePanel) activePanel.classList.remove('active');
            currentTf = tf;
            document.getElementById('tab-' + tf).classList.add('active');
            if (tf === 'details') {
                loadDetails();
            } else {
                loadOhlc(tf, 1);
            }
        });
    });

    document.getElementById('tab-content').addEventListener('click', function (e) {
        var btn = e.target.closest('.pg-btn');
        if (!btn || btn.disabled || !currentTf) return;
        var pg = parseInt(btn.getAttribute('data-pg'));
        if (isNaN(pg) || pg < 1) return;
        loadOhlc(currentTf, pg);
    });

    loadDetails();
})();
