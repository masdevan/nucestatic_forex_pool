import { chartState, setChartInstance, setCandlestickSeries, setVolumeSeries, chart, candlestickSeries, volumeSeries } from './state.js';
import { loadMoreIfNeeded } from './loader.js';
import { initSessionBackground } from './sessions.js';
import { initTooltip } from './tooltip.js';

export function createChartIfNeeded() {
    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer || chart) return;

    if (typeof LightweightCharts === 'undefined') {
        console.error('LightweightCharts not found');
        return;
    }

    const header = document.getElementById('header-container');
    const headerHeight = header ? header.offsetHeight : 60;
    const availableHeight = window.innerHeight - headerHeight - 40;

    const chartInstance = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: Math.max(400, availableHeight),
        layout: {
            backgroundColor: '#1a1a1a',
            textColor: '#d1d4dc',
            fontSize: 12,
            fontFamily: 'Trebuchet MS, Roboto, Ubuntu, sans-serif',
        },
        grid: {
            vertLines: { color: '#2a2e39' },
            horzLines: { visible: false },
        },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: {
            borderColor: '#2a2e39',
            textColor: '#d1d4dc',
            autoScale: true,
            scaleMargins: { top: 0.05, bottom: 0.05 },
            entireTextOnly: true,
            ticksVisible: true,
            minimumWidth: 60,
        },
        timeScale: {
            borderColor: '#2a2e39',
            textColor: '#d1d4dc',
        },
    });

    setChartInstance(chartInstance);
    initSessionBackground(chartInstance);

    const candleSeries = chartInstance.addCandlestickSeries({
        upColor: '#00C853',
        downColor: '#FF1744',
        borderVisible: false,
        wickUpColor: '#00C853',
        wickDownColor: '#FF1744',
        priceFormat: {
            type: 'price',
            precision: 5,
            minMove: 0.00001,
        },
    });

    setCandlestickSeries(candleSeries);
    initTooltip(chartInstance, candleSeries);

    try {
        const volSeries = chartInstance.addHistogramSeries({
            color: '#00C853',
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
            scaleMargins: { top: 0.8, bottom: 0 },
        });
        setVolumeSeries(volSeries);
    } catch (e) {
        console.warn('Volume series not supported:', e);
        setVolumeSeries(null);
    }

    chartInstance.timeScale().subscribeVisibleTimeRangeChange(newRange => {
        if (!newRange) return;
        chartState.visibleRange = newRange;
        loadMoreIfNeeded();
    });
}