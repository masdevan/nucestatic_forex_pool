async function loadDashboard() {
    const account = await fetchAPI('/account');
    if (account) {
        const balanceEl = document.getElementById('balance');
        const equityEl = document.getElementById('equity');
        const profitEl = document.getElementById('profit');
        const openPositionsEl = document.getElementById('open-positions');
        const connectionStatusEl = document.getElementById('connection-status');
        
        if (balanceEl) balanceEl.textContent = account.balance.toFixed(2);
        if (equityEl) equityEl.textContent = account.equity.toFixed(2);
        if (profitEl) profitEl.textContent = account.profit.toFixed(2);
        if (openPositionsEl) openPositionsEl.textContent = account.positions;
        if (connectionStatusEl) {
            connectionStatusEl.textContent = 'Connected';
            connectionStatusEl.style.color = '#2ecc71';
        }
    }
}

loadDashboard();
