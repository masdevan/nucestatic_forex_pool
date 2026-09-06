(function () {
    var parts = window.location.pathname.split('/').filter(Boolean);
    if (parts.length < 2) return;

    var name = decodeURIComponent(parts[0]);
    var currentTf = null;
    var tfState = {};

    function loadDetails() {
        fetch('/api/symbols/' + encodeURIComponent(name) + '/range')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var el = document.getElementById('tab-details');
                if (!data.ranges || data.ranges.length === 0) {
                    el.innerHTML = '<p class="range-empty">Belum ada data.</p>';
                    return;
                }
                var html = '<div class="table-scroll"><table class="range-table"><thead><tr><th>Timeframe</th><th>Data pertama</th><th>Data terakhir</th><th>Jumlah</th></tr></thead><tbody>';
                data.ranges.forEach(function (rg) {
                    html += '<tr><td>' + rg.timeframe + '</td><td>' + rg.first +
                        '</td><td>' + rg.last + '</td><td>' + rg.count + '</td></tr>';
                });
                html += '</tbody></table></div>';
                el.innerHTML = html;
            })
            .catch(function () {
                document.getElementById('tab-details').innerHTML = '<p class="range-empty">Gagal memuat.</p>';
            });
    }

    function formatTime(val) {
        if (typeof val === 'number') return new Date(val * 1000).toLocaleString();
        if (typeof val === 'string') return val.replace('T', ' ').substring(0, 19);
        return val;
    }

    function buildRowsHtml(data) {
        var html = '';
        data.forEach(function (row) {
            var t = formatTime(row.time);
            html += '<tr><td>' + row.symbol + '</td><td>' + row.open +
                '</td><td>' + row.high + '</td><td>' + row.low +
                '</td><td>' + row.close + '</td><td>' + t + '</td></tr>';
        });
        return html;
    }

    function initOhlcTab(tf) {
        var el = document.getElementById('tab-' + tf);
        el.innerHTML =
            '<div class="table-scroll"><table class="ohlc-table"><thead><tr>' +
            '<th>Symbol</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Time</th>' +
            '</tr></thead><tbody></tbody></table></div>' +
            '<div class="load-sentinel"></div>';
        tfState[tf] = { page: 0, totalPages: 1, loading: false };
    }

    function loadOhlcPage(tf) {
        var s = tfState[tf];
        if (s.loading || s.page >= s.totalPages) return;
        s.loading = true;
        var nextPage = s.page + 1;

        fetch('/api/ohlc/' + tf + '?symbol=' + encodeURIComponent(name) + '&page=' + nextPage + '&limit=50')
            .then(function (r) { return r.json(); })
            .then(function (res) {
                s.page = res.pagination.page;
                s.totalPages = res.pagination.total_pages;
                s.loading = false;

                var tbody = document.querySelector('#tab-' + tf + ' .ohlc-table tbody');
                if (res.data.length === 0 && s.page === 1) {
                    tbody.innerHTML = '<tr><td colspan="6" class="range-empty">Tidak ada data.</td></tr>';
                } else {
                    tbody.insertAdjacentHTML('beforeend', buildRowsHtml(res.data));
                }

                if (s.page >= s.totalPages) {
                    var sentinel = document.querySelector('#tab-' + tf + ' .load-sentinel');
                    if (sentinel) sentinel.remove();
                }
            })
            .catch(function () {
                s.loading = false;
                var sentinel = document.querySelector('#tab-' + tf + ' .load-sentinel');
                if (sentinel) sentinel.remove();
            });
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting && currentTf && currentTf !== 'details') {
                loadOhlcPage(currentTf);
            }
        });
    }, { root: document.getElementById('tab-content'), threshold: 0.1 });

    function observeSentinel(tf) {
        var sentinel = document.querySelector('#tab-' + tf + ' .load-sentinel');
        if (sentinel) observer.observe(sentinel);
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
                if (!tfState[tf]) initOhlcTab(tf);
                if (tfState[tf].page === 0) loadOhlcPage(tf);
                observeSentinel(tf);
            }
        });
    });

    loadDetails();
})();
