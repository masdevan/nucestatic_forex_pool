let dbPositionsPage = 1;
let dbTodayPage = 1;
let dbHistoryPage = 1;

function formatTimeAgo(timeStr) {
    if (!timeStr) return '-';
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return timeStr;
}

function formatProfit(profit) {
    const val = parseFloat(profit);
    if (val > 0) return `<span class="profit-positive">+${val.toFixed(2)}</span>`;
    if (val < 0) return `<span class="profit-negative">${val.toFixed(2)}</span>`;
    return `<span class="profit-zero">0.00</span>`;
}

function formatDateTime(timeStr) {
    if (!timeStr) return '-';
    const date = new Date(timeStr);
    const options = { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    };
    return date.toLocaleString('en-US', options);
}

function getProfitClass(profit) {
    if (profit > 0) return 'profit-positive';
    if (profit < 0) return 'profit-negative';
    return 'profit-zero';
}

function formatProfitDisplay(profit) {
    const val = parseFloat(profit);
    if (val > 0) return '+' + val.toFixed(2);
    return val.toFixed(2);
}

function getStatusBadge(isRunning) {
    if (isRunning === 1) return '<span class="status status-open">Open</span>';
    if (isRunning === 2) return '<span class="status status-pending">Pending</span>';
    return '<span class="status status-closed">Closed</span>';
}

function renderPagination(containerId, page, total_pages, total, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = `
        <div class="pagination-info">
            Page ${page} of ${total_pages} (${total} total)
        </div>
        <div class="pagination-buttons">
    `;
    
    if (page > 1) {
        html += `<button class="pagination-btn" onclick="${callback}(${page - 1})">Previous</button>`;
    }
    
    if (page < total_pages) {
        html += `<button class="pagination-btn" onclick="${callback}(${page + 1})">Next</button>`;
    }
    
    html += `</div>`;
    container.innerHTML = html;
}

async function loadDBPositions(page = 1) {
    dbPositionsPage = page;
    const tbody = document.getElementById('positions-table');
    
    try {
        const data = await fetchAPI(`/positions/db?page=${page}&per_page=10&is_running=1`);
        const positions = data.positions || [];
        
        if (positions.length > 0) {
            tbody.innerHTML = positions.map(pos => `
                <tr>
                    <td>${pos.ticket}</td>
                    <td class="symbol">${pos.symbol}</td>
                    <td><span class="status status-${pos.type}">${pos.type}</span></td>
                    <td>${pos.volume}</td>
                    <td>${pos.price}</td>
                    <td>${pos.sl || '-'}</td>
                    <td>${pos.tp || '-'}</td>
                    <td class="${getProfitClass(pos.profit)}">${formatProfitDisplay(pos.profit)}</td>
                    <td>${formatTimeAgo(pos.time)}</td>
                </tr>
            `).join('');
            
            renderPagination('positions-pagination', page, data.total_pages, data.total || 0, 'loadDBPositions');
        } else {
            tbody.innerHTML = '<tr><td colspan="9" class="loading">No positions</td></tr>';
            document.getElementById('positions-pagination').innerHTML = '';
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="9" class="loading">Error: ${error.message}</td></tr>`;
        document.getElementById('positions-pagination').innerHTML = '';
    }
}

async function loadDBToday(page = 1) {
    dbTodayPage = page;
    const tbody = document.getElementById('history-table');
    
    try {
        const data = await fetchAPI(`/positions/db/today?page=${page}&per_page=10`);
        const positions = data.positions || [];
        
        if (positions.length > 0) {
            tbody.innerHTML = positions.map(pos => `
                <tr>
                    <td>${pos.ticket}</td>
                    <td class="symbol">${pos.symbol}</td>
                    <td><span class="status status-${pos.type}">${pos.type}</span></td>
                    <td>${pos.volume}</td>
                    <td>${pos.price}</td>
                    <td>${pos.sl || '-'}</td>
                    <td>${pos.tp || '-'}</td>
                    <td class="${getProfitClass(pos.profit)}">${formatProfitDisplay(pos.profit)}</td>
                    <td>${formatDateTime(pos.time)}</td>
                    <td>${getStatusBadge(pos.is_running)}</td>
                </tr>
            `).join('');
            
            renderPagination('history-pagination', page, data.total_pages, data.total || 0, 'loadDBToday');
        } else {
            tbody.innerHTML = '<tr><td colspan="10" class="loading">No history</td></tr>';
            document.getElementById('history-pagination').innerHTML = '';
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="10" class="loading">Error: ${error.message}</td></tr>`;
        document.getElementById('history-pagination').innerHTML = '';
    }
}

async function loadDBHistory(page = 1) {
    dbHistoryPage = page;
    const tbody = document.getElementById('full-history-table');
    
    try {
        const data = await fetchAPI(`/positions/db?page=${page}&per_page=10`);
        const positions = data.positions || [];
        
        if (positions.length > 0) {
            tbody.innerHTML = positions.map(pos => `
                <tr>
                    <td>${pos.ticket}</td>
                    <td class="symbol">${pos.symbol}</td>
                    <td><span class="status status-${pos.type}">${pos.type}</span></td>
                    <td>${pos.volume}</td>
                    <td>${pos.price}</td>
                    <td>${pos.sl || '-'}</td>
                    <td>${pos.tp || '-'}</td>
                    <td class="${getProfitClass(pos.profit)}">${formatProfitDisplay(pos.profit)}</td>
                    <td>${formatDateTime(pos.time)}</td>
                    <td>${getStatusBadge(pos.is_running)}</td>
                </tr>
            `).join('');
            
            renderPagination('full-history-pagination', page, data.total_pages, data.total || 0, 'loadDBHistory');
        } else {
            tbody.innerHTML = '<tr><td colspan="10" class="loading">No history</td></tr>';
            document.getElementById('full-history-pagination').innerHTML = '';
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="10" class="loading">Error: ${error.message}</td></tr>`;
        document.getElementById('full-history-pagination').innerHTML = '';
    }
}

loadDBPositions();
loadDBToday();
loadDBHistory();

setInterval(() => loadDBPositions(dbPositionsPage), 2000);
setInterval(() => loadDBToday(dbTodayPage), 5000);
setInterval(() => loadDBHistory(dbHistoryPage), 5000);
