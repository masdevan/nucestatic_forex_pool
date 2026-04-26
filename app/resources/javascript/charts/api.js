import { chartState } from './state.js';

export async function fetchOHLC(timeframe, symbol, page, limit) {
    const url = `/api/ohlc/${timeframe}?symbol=${encodeURIComponent(symbol)}&page=${page}&limit=${limit}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        const data = result.data || [];
        const hasMore = result.pagination?.has_next || false;
        return { data, hasMore };
    } catch (error) {
        console.error('Error fetching OHLC:', error);
        return { data: [], hasMore: false };
    }
}

export async function fetchPositionHistory(symbol) {
    const url = `/api/positions/chart/history?symbol=${encodeURIComponent(symbol)}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching position history:', error);
        return [];
    }
}

export async function fetchSwingDetection(timeframe, symbol) {
    const url = `/api/swings/charts/${timeframe}?symbol=${encodeURIComponent(symbol)}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching swing detection:', error);
        return [];
    }
}

export async function loadConfig() {
    try {
        const config = await fetch('/api/config').then(r => r.json());
        if (config && config.trade_pair) {
            const symbolInput = document.getElementById('symbol-input');
            if (symbolInput) {
                symbolInput.value = config.trade_pair.split(',')[0].trim();
            }
            if (config.symbols && config.symbols.length > 1) {
                createSymbolDropdown(config.symbols);
            }
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

function createSymbolDropdown(symbols) {
    const symbolInput = document.getElementById('symbol-input');
    if (!symbolInput) return;

    const container = symbolInput.parentElement;
    const select = document.createElement('select');
    select.id = 'symbol-select';
    select.className = 'control';

    symbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        select.appendChild(option);
    });

    container.replaceChild(select, symbolInput);

    const label = container.querySelector('label');
    if (label) label.setAttribute('for', 'symbol-select');
}
