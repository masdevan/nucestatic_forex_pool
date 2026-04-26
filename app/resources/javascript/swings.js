let TIMEFRAME = 'M1';
let PAIR = '';
let currentPage = 1;

const SWING_COLORS = {
    'swing_high': '#22c55e',
    'swing_low': '#ef4444'
};

function getSwingColor(type) {
    return SWING_COLORS[type] || 'gray';
}

function formatDateTime(dtStr) {
    if (!dtStr) return '-';
    const dt = new Date(dtStr);
    if (isNaN(dt.getTime())) return dtStr;
    const dd = String(dt.getDate()).padStart(2, '0');
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const yy = String(dt.getFullYear()).slice(-2);
    const hh = String(dt.getHours()).padStart(2, '0');
    const min = String(dt.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${yy} ${hh}:${min}`;
}

function renderSwingRow(item) {
    const color = getSwingColor(item.type);
    return `
        <tr>
            <td style="font-weight: bold;">${item.symbol || 'None'}</td>
            <td style="color: ${color}; font-weight: bold;">${item.type || 'None'}</td>
            <td style="color: ${color};">${item.price ? Number(item.price).toFixed(5) : '0.0'}</td>
            <td style="color: ${color}; white-space: nowrap;">${formatDateTime(item.timestamp)}</td>
            <td>${item.strength ? Number(item.strength).toFixed(2) : '0.0'}</td>
            <td>${item.distance ? Number(item.distance).toFixed(5) : '0.0'}</td>
            <td>${item.is_confirmed ? '<span style="color: #22c55e;">Yes</span>' : '<span style="color: #ef4444;">No</span>'}</td>
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
        html += `<button class="pagination-btn" onclick="loadSwings(${pagination.page - 1})">Previous</button>`;
    }

    if (pagination.has_next) {
        html += `<button class="pagination-btn" onclick="loadSwings(${pagination.page + 1})">Next</button>`;
    }

    html += `</div>`;
    paginationEl.innerHTML = html;
}

async function loadSwings(page = 1) {
    currentPage = page;

    let url = `/api/swings/${TIMEFRAME}?page=${page}&limit=50`;
    if (PAIR) {
        url += `&symbol=${PAIR}`;
    }
    
    const data = await fetchAPI(url);
    const tbody = document.getElementById('swings-table');
    if (!tbody) return;

    if (data && data.data && data.data.length > 0) {
        tbody.innerHTML = data.data.map(renderSwingRow).join('');
        updatePagination(data.pagination);
    } else {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">No data</td></tr>';
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
            loadSwings(1);
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
                loadSwings(1);
            }
        });

        pairSelect.addEventListener('change', function() {
            PAIR = this.value;
            currentPage = 1;
            loadSwings(1);
        });
    } else {
        loadSwings();
    }
});