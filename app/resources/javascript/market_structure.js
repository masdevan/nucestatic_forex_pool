let TIMEFRAME = 'M1';
let PAIR = '';
let currentPage = 1;

const STRUCTURE_COLORS = {
    'HH': '#22c55e',
    'HL': '#3b82f6',
    'LH': '#f97316',
    'LL': '#ef4444'
};

const LABEL_MAP = {
    'HH': 'Higher High',
    'HL': 'Higher Low',
    'LH': 'Lower High',
    'LL': 'Lower Low'
};

function getStructureColor(type) {
    return STRUCTURE_COLORS[type] || 'gray';
}

function getStructureLabel(type) {
    return LABEL_MAP[type] || type;
}

function formatDuration(seconds) {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
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

function renderMarketStructureRow(item) {
    const color = getStructureColor(item.structure_type);
    const bgColor = color + '20';
    return `
        <tr>
            <td style="font-weight: bold;">${item.symbol || '-'}</td>
            <td style="color: ${color}; font-weight: bold;">${item.structure_type || '-'}</td>
            <td>${item.is_break_structure ? '<span style="color: #22c55e;">Yes</span>' : '<span style="color: gray;">No</span>'}</td>
            <td style="color: ${color}; background: ${bgColor};">${item.previous_swing_high_price || '-'}</td>
            <td style="color: ${color}; background: ${bgColor}; white-space: nowrap;">${formatDateTime(item.previous_swing_high_time)}</td>
            <td style="color: ${color}; background: ${bgColor};">${item.current_swing_high_price || '-'}</td>
            <td style="color: ${color}; background: ${bgColor}; white-space: nowrap;">${formatDateTime(item.current_swing_high_time)}</td>
            <td style="color: ${color}; background: ${bgColor};">${item.previous_swing_low_price || '-'}</td>
            <td style="color: ${color}; background: ${bgColor}; white-space: nowrap;">${formatDateTime(item.previous_swing_low_time)}</td>
            <td style="color: ${color}; background: ${bgColor};">${item.current_swing_low_price || '-'}</td>
            <td style="color: ${color}; background: ${bgColor}; white-space: nowrap;">${formatDateTime(item.current_swing_low_time)}</td>
            <td style="color: ${color};">${formatDuration(item.duration_seconds)}</td>
            <td style="color: ${color}; font-weight: bold;">${item.trend_bias || '-'}</td>
            <td><span style="color: ${item.speed === 'fast' ? '#22c55e' : '#f97316'};">${item.speed || 'None'}</span></td>
            <td style="font-weight: bold;">${item.move_size ? Number(item.move_size).toFixed(1) : '0.0'}</td>
            <td>${item.liquidity_sweep ? `<span style="color: ${item.liquidity_sweep === 'high' ? '#22c55e' : '#ef4444'}; font-weight: bold;">${item.liquidity_sweep}</span>` : 'None'}</td>
            <td>${item.max_sweep_strength ? Number(item.max_sweep_strength).toFixed(2) : '0.00'}</td>
            <td>${item.sweep_high_count || 0}</td>
            <td>${item.sweep_low_count || 0}</td>
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
        html += `<button class="pagination-btn" onclick="loadMarketStructure(${pagination.page - 1})">Previous</button>`;
    }
    
    if (pagination.has_next) {
        html += `<button class="pagination-btn" onclick="loadMarketStructure(${pagination.page + 1})">Next</button>`;
    }
    
    html += `</div>`;
    paginationEl.innerHTML = html;
}

async function loadMarketStructure(page = 1) {
    currentPage = page;
    
    let url = `/api/market_structure/${TIMEFRAME}?page=${page}&limit=50`;
    if (PAIR) {
        url += `&symbol=${PAIR}`;
    }
    
    const data = await fetchAPI(url);
    const tbody = document.getElementById('market-structure-table');
    if (!tbody) return;
    
    if (data && data.data && data.data.length > 0) {
        tbody.innerHTML = data.data.map(renderMarketStructureRow).join('');
        updatePagination(data.pagination);
    } else {
        tbody.innerHTML = '<tr><td colspan="19" class="loading">No data</td></tr>';
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
            loadMarketStructure(1);
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
                loadMarketStructure(1);
            }
        });

        pairSelect.addEventListener('change', function() {
            PAIR = this.value;
            currentPage = 1;
            loadMarketStructure(1);
        });
    } else {
        loadMarketStructure();
    }
});