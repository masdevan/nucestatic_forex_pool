let performanceData = {};

async function loadPerformanceData() {
    try {
        const response = await fetch('/api/positions/performance');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        performanceData = await response.json();
        renderPerformanceData();
    } catch (error) {
        console.error('Error loading performance data:', error);
        performanceData = {};
        renderPerformanceData();
    }
}

function formatProfit(value) {
    const formatted = value.toFixed(2);
    if (value > 0) {
        return `<span class="positive">+${formatted}</span>`;
    } else if (value < 0) {
        return `<span class="negative">${formatted}</span>`;
    }
    return `<span>0.00</span>`;
}

function renderPerformanceData() {
    const container = document.getElementById('performance-container');
    const symbols = Object.keys(performanceData);
    
    if (symbols.length === 0) {
        container.innerHTML = '<p style="color: #888; padding: 20px;">No performance data available</p>';
        return;
    }
    
    let html = '';
    
    if (performanceData['_total']) {
        const total = performanceData['_total'];
        html += `
        <div class="total-section">
            <div class="total-header">Accumulations</div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Today</div>
                    <div class="stat-value">${formatProfit(total.daily.profit)}</div>
                    <div class="small-text">${total.daily.trades} trades</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Week</div>
                    <div class="stat-value">${formatProfit(total.weekly.profit)}</div>
                    <div class="small-text">${total.weekly.trades} trades</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Month</div>
                    <div class="stat-value">${formatProfit(total.monthly.profit)}</div>
                    <div class="small-text">${total.monthly.trades} trades</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Year</div>
                    <div class="stat-value">${formatProfit(total.yearly.profit)}</div>
                    <div class="small-text">${total.yearly.trades} trades</div>
                </div>
            </div>
            
            <div class="summary-row">
                <div class="summary-item">
                    <div class="stat-label">Net Profit</div>
                    <div class="stat-value ${total.overall.net_profit >= 0 ? 'positive' : 'negative'}">${total.overall.net_profit >= 0 ? '+' : ''}${total.overall.net_profit.toFixed(2)}</div>
                </div>
                <div class="summary-item">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value">${total.overall.win_rate}%</div>
                    <div class="win-loss-bar">
                        <div class="win-bar" style="width: ${total.overall.win_rate}%"></div>
                        <div class="loss-bar" style="width: ${100 - total.overall.win_rate}%"></div>
                    </div>
                    <div class="small-text">${total.overall.wins}W / ${total.overall.losses}L</div>
                </div>
                <div class="summary-item">
                    <div class="stat-label">Total P/L</div>
                    <div class="stat-value positive">+${total.overall.total_profit.toFixed(2)}</div>
                    <div class="stat-value negative">${total.overall.total_loss.toFixed(2)}</div>
                </div>
            </div>
        </div>
        `;
    }
    
    if (performanceData['_average']) {
        const avg = performanceData['_average'];
        html += `
        <div class="total-section">
            <div class="total-header">Average</div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Daily Average</div>
                    <div class="stat-value">${formatProfit(avg.daily.profit)}</div>
                    <div class="small-text">${avg.daily.trades} trades avg</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Weekly Average</div>
                    <div class="stat-value">${formatProfit(avg.weekly.profit)}</div>
                    <div class="small-text">${avg.weekly.trades} trades avg</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Monthly Average</div>
                    <div class="stat-value">${formatProfit(avg.monthly.profit)}</div>
                    <div class="small-text">${avg.monthly.trades} trades avg</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Yearly Average</div>
                    <div class="stat-value">${formatProfit(avg.yearly.profit)}</div>
                    <div class="small-text">${avg.yearly.trades} trades avg</div>
                </div>
            </div>
        </div>
        `;
    }
    
    symbols.forEach(symbol => {
        if (symbol === '_total' || symbol === '_average') return; 
        
        const data = performanceData[symbol];
        
        html += `
        <div class="symbol-section">
            <div class="symbol-header">${symbol}</div>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-label">Today</div>
                    <div class="stat-value">${formatProfit(data.daily.profit)}</div>
                    <div class="small-text">${data.daily.trades} trades</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Week</div>
                    <div class="stat-value">${formatProfit(data.weekly.profit)}</div>
                    <div class="small-text">${data.weekly.trades} trades</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Month</div>
                    <div class="stat-value">${formatProfit(data.monthly.profit)}</div>
                    <div class="small-text">${data.monthly.trades} trades</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">This Year</div>
                    <div class="stat-value">${formatProfit(data.yearly.profit)}</div>
                    <div class="small-text">${data.yearly.trades} trades</div>
                </div>
            </div>
            
            <div class="summary-row">
                <div class="summary-item">
                    <div class="stat-label">Net Profit</div>
                    <div class="stat-value ${data.overall.net_profit >= 0 ? 'positive' : 'negative'}">${data.overall.net_profit >= 0 ? '+' : ''}${data.overall.net_profit.toFixed(2)}</div>
                </div>
                <div class="summary-item">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value">${data.overall.win_rate}%</div>
                    <div class="win-loss-bar">
                        <div class="win-bar" style="width: ${data.overall.win_rate}%"></div>
                        <div class="loss-bar" style="width: ${100 - data.overall.win_rate}%"></div>
                    </div>
                    <div class="small-text">${data.overall.wins}W / ${data.overall.losses}L</div>
                </div>
                <div class="summary-item">
                    <div class="stat-label">Total P/L</div>
                    <div class="stat-value positive">+${data.overall.total_profit.toFixed(2)}</div>
                    <div class="stat-value negative">${data.overall.total_loss.toFixed(2)}</div>
                </div>
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

window.addEventListener('load', () => {
    loadPerformanceData();
    
    setInterval(loadPerformanceData, 60000);
});
