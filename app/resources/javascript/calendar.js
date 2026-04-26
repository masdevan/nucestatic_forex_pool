let currentPage = 1;

function formatTime(timeStr) {
    if (!timeStr) return '-';
    try {
        const date = new Date(timeStr);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const time = `${hours}:${minutes}`;
        const options = { month: 'short', day: 'numeric', year: 'numeric' };
        return `${date.toLocaleDateString('en-US', options)} ${time}`;
    } catch {
        return timeStr;
    }
}

function renderEventRow(event) {
    const impactClass = event.impact ? event.impact.toLowerCase() : 'none';
    const impactDisplay = event.impact ? event.impact : 'none';
    return `
        <tr>
            <td>${formatTime(event.time)}</td>
            <td>${event.currency}</td>
            <td>${event.event}</td>
            <td><span class="status status-${impactClass}">${impactDisplay}</span></td>
            <td>${event.actual || '-'}</td>
            <td>${event.forecast || '-'}</td>
            <td>${event.previous || '-'}</td>
            <td title="${event.description || ''}" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 0;">${event.description || '-'}</td>
        </tr>
    `;
}

async function loadCalendarToday() {
    const calendar = await fetchAPI('/calendar/today');
    const tbody = document.getElementById('calendar-today-table');
    
    if (calendar && calendar.data && calendar.data.length > 0) {
        tbody.innerHTML = calendar.data.map(renderEventRow).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No events today</td></tr>';
    }
}

async function loadCalendar(page = 1) {
    currentPage = page;
    
    const url = `/calendar?page=${page}&limit=50`;
    
    const calendar = await fetchAPI(url);
    const tbody = document.getElementById('calendar-table');
    
    if (calendar && calendar.data && calendar.data.length > 0) {
        tbody.innerHTML = calendar.data.map(renderEventRow).join('');
        
        updatePagination(calendar.pagination);
    } else {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No events</td></tr>';
        document.getElementById('pagination').innerHTML = '';
    }
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
        html += `<button class="pagination-btn" onclick="loadCalendar(${pagination.page - 1})">Previous</button>`;
    }
    
    if (pagination.has_next) {
        html += `<button class="pagination-btn" onclick="loadCalendar(${pagination.page + 1})">Next</button>`;
    }
    
    html += `</div>`;
    
    paginationEl.innerHTML = html;
}

loadCalendarToday();
loadCalendar();
