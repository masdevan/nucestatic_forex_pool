let currentPage = 1;

const MONTHS_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
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
        return dateStr;
    }
}

function getStatusLabel(status) {
    if (status === 0) return '<span class="status status-none">Pending</span>';
    if (status === 1) return '<span class="status" style="background-color: #22c55e; color: white;">Done</span>';
    if (status === 2) return '<span class="status status-medium">Failed</span>';
    return '-';
}

function truncateDescription(text, maxLength = 100) {
    if (!text) return '-';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function renderNewsRow(news) {
    const desc = news.description || '';
    const truncDesc = truncateDescription(desc);
    const reason = news.reason || '-';
    const pairImpact = news.pair_impact || '-';
    const direction = news.direction || '-';
    const fullTitle = news.title.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    return `
        <tr>
            <td>${formatDate(news.time)}</td>
            <td title="${fullTitle}" style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${news.title}</td>
            <td data-full-text="${desc.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}" onclick="showModal('Description', this.dataset.fullText)" style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; color: #666;">${truncDesc}</td>
            <td>${getStatusLabel(news.description_status)}</td>
            <td>${news.score || 0}</td>
            <td data-full-text="${pairImpact.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}" onclick="showModal('Pair Impact', this.dataset.fullText)" style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; color: #666;">${pairImpact}</td>
            <td>${direction}</td>
            <td data-full-text="${reason.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}" onclick="showModal('Reason', this.dataset.fullText)" style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; color: #666;">${reason}</td>
        </tr>
    `;
}

async function loadNewsToday() {
    const tbody = document.getElementById('news-today-table');
    if (!tbody) return;
    
    const news = await fetchAPI('/news/today');
    
    if (news && news.data && news.data.length > 0) {
        tbody.innerHTML = news.data.map(renderNewsRow).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No news today</td></tr>';
    }
}

async function loadNews(page = 1) {
    currentPage = page;
    
    const url = `/news?page=${page}&limit=50`;
    
    const news = await fetchAPI(url);
    const tbody = document.getElementById('news-table');
    if (!tbody) return;
    
    if (news && news.data && news.data.length > 0) {
        tbody.innerHTML = news.data.map(renderNewsRow).join('');
        
        updatePagination(news.pagination);
    } else {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No news</td></tr>';
        const paginationEl = document.getElementById('pagination');
        if (paginationEl) paginationEl.innerHTML = '';
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
        html += `<button class="pagination-btn" onclick="loadNews(${pagination.page - 1})">Previous</button>`;
    }
    
    if (pagination.has_next) {
        html += `<button class="pagination-btn" onclick="loadNews(${pagination.page + 1})">Next</button>`;
    }
    
    html += `</div>`;
    
    paginationEl.innerHTML = html;
}

function showModal(title, text) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-content').textContent = text;
    document.getElementById('modal-overlay').style.display = 'block';
}

function closeModal(event) {
    if (event.target.id === 'modal-overlay') {
        document.getElementById('modal-overlay').style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadNewsToday();
    loadNews();
});
