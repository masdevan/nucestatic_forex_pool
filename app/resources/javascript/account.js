async function loadAccountData() {
    try {
        const account = await fetchAPI('/account');
        if (account) {
            document.getElementById('server').textContent = account.server || '-';
            document.getElementById('currency').textContent = account.currency || '-';
            document.getElementById('company').textContent = account.company || '-';
            document.getElementById('balance').textContent = account.balance.toFixed(2);
            document.getElementById('equity').textContent = account.equity.toFixed(2);
            document.getElementById('profit').textContent = account.profit.toFixed(2);
            document.getElementById('margin').textContent = account.margin.toFixed(2);
            document.getElementById('free-margin').textContent = account.margin_free.toFixed(2);
            document.getElementById('margin-level').textContent = account.margin_level.toFixed(2) + '%';
            document.getElementById('open-positions').textContent = account.positions || 0;
        }
    } catch (error) {
        console.error('Error loading account:', error);
    }
}

loadAccountData();
setInterval(loadAccountData, 2000);
