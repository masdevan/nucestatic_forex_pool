let TIMEFRAME = 'M1';
let PAIR = '';
let currentPage = 1;

const SESSION_NAMES = {
    1: 'Asia',
    2: 'London',
    3: 'New York'
};

const MONTHS_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatTime(timeStr) {
    if (!timeStr) return '-';
    try {
        const date = new Date(timeStr);
        const day = date.getDate();
        const month = MONTHS_EN[date.getMonth()];
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = date.getSeconds();
        if (seconds > 0) {
            const secs = String(seconds).padStart(2, '0');
            return `${day} ${month}, ${hours}:${minutes}:${secs}`;
        }
        return `${day} ${month}, ${hours}:${minutes}`;
    } catch {
        return timeStr;
    }
}

function getSessionName(session) {
    const names = {1: 'Asia', 2: 'London', 3: 'New York'};
    const colors = {1: '#f97316', 2: '#3b82f6', 3: '#8b5cf6'};
    const name = names[session] || '-';
    const color = colors[session] || 'gray';
    return `<span style="color: ${color}; font-weight: bold;">${name}</span>`;
}

function getPriceColor(open, close) {
    if (!open || !close) return 'color: gray;';
    if (close > open) return 'color: #22c55e;';
    if (close < open) return 'color: #ef4444;';
    return 'color: gray;';
}

function renderOHLCRow(ohlc) {
    const symbolColor = getPriceColor(ohlc.open, ohlc.close);
    const isDoneColor = ohlc.is_done ? '#22c55e' : '#eab308';
    return `
        <tr>
            <td style="${symbolColor}; font-weight: bold;">${ohlc.symbol || '-'}</td>
            <td>${formatTime(ohlc.time_str)}</td>
            <td>${getSessionName(ohlc.session)}</td>
            <td style="color: ${isDoneColor}; font-weight: bold;">${ohlc.is_done ? 'Yes' : 'On Progress'}</td>
            <td style="${getPriceColor(ohlc.open, ohlc.open)}">${ohlc.open}</td>
            <td style="${getPriceColor(ohlc.open, ohlc.high)}">${ohlc.high}</td>
            <td style="${getPriceColor(ohlc.open, ohlc.low)}">${ohlc.low}</td>
            <td style="${getPriceColor(ohlc.open, ohlc.close)}">${ohlc.close}</td>
            <td>${ohlc.tick_volume}</td>
            <td>${ohlc.atr !== null && ohlc.atr !== undefined ? Number(ohlc.atr).toFixed(ohlc.atr == 0 ? 1 : 4) : '-'}</td>
            <td>${ohlc.sweep_high ? '<span style="color: #22c55e;">Yes</span>' : '<span style="color: gray;">No</span>'}</td>
            <td>${ohlc.sweep_low ? '<span style="color: #ef4444;">Yes</span>' : '<span style="color: gray;">No</span>'}</td>
            <td>${ohlc.sweep_strength != null ? Number(ohlc.sweep_strength).toFixed(2) : '0.00'}</td>
        </tr>
    `;
}

function updatePagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    if (!paginationEl) return;
    
    let html = `
        <div class="pagination-info">
            Page ${pagination.page} of ${pagination.total_pages} (${pagination.total} total)
        </div>
        <div class="pagination-buttons">
    `;
    
    if (pagination.has_prev) {
        html += `<button class="pagination-btn" onclick="loadOHLC(${pagination.page - 1})">Previous</button>`;
    }
    
    if (pagination.has_next) {
        html += `<button class="pagination-btn" onclick="loadOHLC(${pagination.page + 1})">Next</button>`;
    }
    
    html += `</div>`;
    paginationEl.innerHTML = html;
}

async function loadOHLC(page = 1) {
    currentPage = page;

    if (!PAIR) return;

    const url = `/api/ohlc/${TIMEFRAME}?page=${page}&limit=50&symbol=${PAIR}`;
    const ohlcData = await fetchAPI(url);
    const tbody = document.getElementById('ohlc-table');
    if (!tbody) return;
    
    if (ohlcData && ohlcData.data && ohlcData.data.length > 0) {
        tbody.innerHTML = ohlcData.data.map(renderOHLCRow).join('');
        updatePagination(ohlcData.pagination);
    } else {
        tbody.innerHTML = '<tr><td colspan="13" class="loading">No data</td></tr>';
        const paginationEl = document.getElementById('pagination');
        if (paginationEl) paginationEl.innerHTML = '';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const timeframeSelect = document.getElementById('timeframe-select');
    if (timeframeSelect) {
        TIMEFRAME = timeframeSelect.value;
        timeframeSelect.addEventListener('change', function() {
            TIMEFRAME = this.value;
            currentPage = 1;
            loadOHLC(1);
        });
    }

    const pairSelect = document.getElementById('pair-select');
    if (pairSelect) {
        fetchAPI('/api/ohlc/pairs').then(function(result) {
            if (result && result.pairs && result.pairs.length > 0) {
                pairSelect.innerHTML = result.pairs
                    .map(p => `<option value="${p}">${p}</option>`)
                    .join('');
                PAIR = pairSelect.value;
                loadOHLC(1);
            }
        });

        pairSelect.addEventListener('change', function() {
            PAIR = this.value;
            currentPage = 1;
            loadOHLC(1);
        });
    }

    setInterval(function() {
        loadOHLC(currentPage);
    }, 1000);
});