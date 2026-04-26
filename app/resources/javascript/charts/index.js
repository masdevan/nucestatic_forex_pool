import { loadConfig } from './api.js';
import { resetAndLoadChart } from './loader.js';
import { setupEventListeners } from './events.js';

window.addEventListener('load', async () => {
    setTimeout(async () => {
        await loadConfig();
        const symbolSelect = document.getElementById('symbol-select');
        const symbolInput = document.getElementById('symbol-input');
        const initialSymbol = symbolSelect ? symbolSelect.value : (symbolInput ? symbolInput.value.trim() : 'USDJPYm');
        await resetAndLoadChart('M1', initialSymbol);
        setupEventListeners();
    }, 100);
});
