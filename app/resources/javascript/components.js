const API_BASE = '/api';

async function fetchAPI(endpoint) {
    try {
        const fullEndpoint = endpoint.startsWith('/api') ? endpoint : `${API_BASE}${endpoint}`;
        const response = await fetch(fullEndpoint);
        if (!response.ok) throw new Error('API request failed');
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

function navigateTo(page) {
    window.location.href = `/resources/views/${page}.html`;
}

async function loadComponent(elementId, componentPath) {
    try {
        const response = await fetch(componentPath);
        if (!response.ok) throw new Error('Failed to load component');
        const html = await response.text();
        document.getElementById(elementId).innerHTML = html;
    } catch (error) {
        console.error('Component Error:', error);
    }
}

function setPageTitle(title) {
    const titleElement = document.querySelector('#page-header h1');
    if (titleElement) {
        titleElement.textContent = title;
    }
}

function setHeaderActions(html) {
    const actionsContainer = document.getElementById('header-actions');
    if (actionsContainer) {
        const timeEl = actionsContainer.querySelector('#current-time');
        actionsContainer.innerHTML = '';
        if (timeEl) actionsContainer.appendChild(timeEl);
        actionsContainer.insertAdjacentHTML('beforeend', html);
    }
}

function initTimeUpdater() {
    function updateTime() {
        const timeEl = document.getElementById('current-time');
        if (timeEl) {
            const now = new Date();
            const options = { hour: '2-digit', minute: '2-digit', second: '2-digit', day: '2-digit', month: 'short', year: 'numeric' };
            const formatted = now.toLocaleString('en-GB', options).replace(',', '');
            timeEl.textContent = formatted;
        }
    }
    setInterval(updateTime, 1000);
    updateTime();
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadComponent('sidebar-container', '/resources/components/sidebar.html');
    await loadComponent('header-container', '/resources/components/header.html');
    initTimeUpdater();
    
    document.body.classList.add('loaded');
    
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.sidebar-menu a');
    
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentPath || 
            (currentPath === '/' && item.getAttribute('href') === '/')) {
            item.classList.add('active');
        }
    });
});

async function loadPositions() {
    return await fetchAPI('/positions');
}

async function loadAccount() {
    return await fetchAPI('/account');
}

async function loadHistory(fromDate, toDate) {
    return await fetchAPI(`/positions/history?from_date=${fromDate}&to_date=${toDate}`);
}

async function loadHistoryToday() {
    return await fetchAPI('/positions/history/today');
}

async function callAIReason() {
    return await fetchAPI('/ai/reason');
}
