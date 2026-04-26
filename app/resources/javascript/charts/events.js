import { resetAndLoadChart } from './loader.js';
import { chart, chartState } from './state.js';

export function setupEventListeners() {
    const timeframeSelect        = document.getElementById('timeframe-select');
    const reloadBtn              = document.getElementById('reload-btn');
    const analyticsBtn           = document.getElementById('analytics-btn');
    const analyticsDropdown      = document.getElementById('analytics-dropdown');
    const marketStructureCheckbox = document.getElementById('market-structure-checkbox');
    const swingDetectionCheckbox  = document.getElementById('swing-detection-checkbox');
    const positionHistoryCheckbox = document.getElementById('position-history-checkbox');

    if (!timeframeSelect || !reloadBtn) return;

    const getCurrentSymbol = () => {
        const symbolSelect = document.getElementById('symbol-select');
        const symbolInput  = document.getElementById('symbol-input');
        return symbolSelect ? symbolSelect.value : (symbolInput ? symbolInput.value.trim() : 'USDJPYm');
    };

    const reloadChart = () => {
        const timeframe = timeframeSelect.value;
        const symbol    = getCurrentSymbol();
        resetAndLoadChart(timeframe, symbol);
    };

    timeframeSelect.addEventListener('change', reloadChart);
    reloadBtn.addEventListener('click', reloadChart);

    if (analyticsBtn && analyticsDropdown) {
        analyticsBtn.addEventListener('click', () => {
            analyticsDropdown.style.display = analyticsDropdown.style.display === 'none' ? 'block' : 'none';
        });

        document.addEventListener('click', (e) => {
            if (!analyticsBtn.contains(e.target) && !analyticsDropdown.contains(e.target)) {
                analyticsDropdown.style.display = 'none';
            }
        });
    }

    if (marketStructureCheckbox) {
        marketStructureCheckbox.addEventListener('change', () => {
            chartState.showMarketStructure = marketStructureCheckbox.checked;
            reloadChart();
        });
    }

    if (swingDetectionCheckbox) {
        swingDetectionCheckbox.addEventListener('change', () => {
            chartState.showSwingDetection = swingDetectionCheckbox.checked;
            reloadChart();
        });
    }

    if (positionHistoryCheckbox) {
        positionHistoryCheckbox.addEventListener('change', () => {
            chartState.showPositionHistory = positionHistoryCheckbox.checked;
            reloadChart();
        });
    }

    const symbolSelect = document.getElementById('symbol-select');
    const symbolInput  = document.getElementById('symbol-input');

    if (symbolSelect) {
        symbolSelect.addEventListener('change', reloadChart);
    }
    if (symbolInput) {
        symbolInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') reloadChart();
        });
    }

    window.addEventListener('resize', () => {
        if (!chart) return;
        const container = document.getElementById('chart-container');
        const header     = document.getElementById('header-container');
        const headerHeight = header ? header.offsetHeight : 60;
        chart.applyOptions({
            width: container.clientWidth,
            height: Math.max(400, window.innerHeight - headerHeight - 40),
        });
    });
}