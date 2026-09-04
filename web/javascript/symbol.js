(function () {
    const parts = window.location.pathname.split('/').filter(Boolean);
    if (parts.length < 2) return;

    const name = decodeURIComponent(parts[0]);

    fetch('/api/symbols/' + encodeURIComponent(name) + '/range')
        .then(r => r.json())
        .then(data => {
            const el = document.getElementById('chart-range');
            if (!data.ranges || data.ranges.length === 0) {
                el.innerHTML = '<p class="range-empty">Belum ada data chart.</p>';
                return;
            }
            let html = '<table class="range-table"><tr><th>Timeframe</th><th>Data pertama</th><th>Data terakhir</th><th>Jumlah</th></tr>';
            data.ranges.forEach(rg => {
                html += '<tr><td>' + rg.timeframe + '</td><td>' + rg.first +
                    '</td><td>' + rg.last + '</td><td>' + rg.count + '</td></tr>';
            });
            html += '</table>';
            el.innerHTML = html;
        })
        .catch(() => {
            document.getElementById('chart-range').innerHTML = '<p class="range-empty">Gagal memuat.</p>';
        });
})();
