import { chartState, candlestickSeries, volumeSeries } from './state.js';
import { fetchOHLC } from './api.js';
import { transformCandle, transformVolume, removeDuplicatesAndSort } from './utils.js';
import { renderPositionHistory } from './positions.js';
import { renderSwingDetection } from './swings.js';

export async function loadMoreIfNeeded() {
    const { isLoading, hasMore, allData, visibleRange } = chartState;
    if (isLoading || !hasMore) return;
    if (!visibleRange || allData.length === 0) return;
    const firstTime = allData[0]?.time;
    if (firstTime == null) return;
    if (visibleRange.from <= firstTime) {
        await loadMoreData();
    }
}

export async function loadMoreData() {
    const { currentTimeframe, currentSymbol, page, limit, hasMore, isLoading } = chartState;
    if (isLoading || !hasMore) return;

    chartState.isLoading = true;

    try {
        const { data, hasMore: more } = await fetchOHLC(currentTimeframe, currentSymbol, page + 1, limit);
        if (!data.length) {
            chartState.hasMore = false;
            return;
        }

        let newCandles = data.map(transformCandle).filter(c => c !== null);
        let newVolumes = data.map(transformVolume).filter(v => v !== null);

        if (newCandles.length === 0) {
            chartState.hasMore = false;
            return;
        }

        const combinedCandles = [...newCandles, ...chartState.allData];
        const combinedVolumes = volumeSeries ? [...newVolumes, ...chartState.allVolumeData] : [];

        const sortedCandles = removeDuplicatesAndSort(combinedCandles);
        const sortedVolumes = volumeSeries ? removeDuplicatesAndSort(combinedVolumes) : [];

        chartState.allData = sortedCandles;
        if (volumeSeries) chartState.allVolumeData = sortedVolumes;

        if (candlestickSeries) candlestickSeries.setData(chartState.allData);
        if (volumeSeries && chartState.allVolumeData.length > 0) volumeSeries.setData(chartState.allVolumeData);

        chartState.page = page + 1;
        chartState.hasMore = more;
    } catch (error) {
        console.error('Error loading more data:', error);
        chartState.hasMore = false;
    } finally {
        chartState.isLoading = false;
    }
}

export async function resetAndLoadChart(timeframe, symbol) {
    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer) return;

    if (chartContainer.clientWidth === 0 || chartContainer.clientHeight === 0) {
        setTimeout(() => resetAndLoadChart(timeframe, symbol), 500);
        return;
    }

    const { createChartIfNeeded } = await import('./init.js');
    createChartIfNeeded();

    await new Promise(resolve => setTimeout(resolve, 50));

    chartState.currentTimeframe = timeframe;
    chartState.currentSymbol = symbol;
    chartState.page = 1;
    chartState.allData = [];
    chartState.allVolumeData = [];
    chartState.hasMore = true;
    chartState.isLoading = false;

    try {
        const { data, hasMore } = await fetchOHLC(timeframe, symbol, 1, chartState.limit);
        if (!data.length) {
            console.warn('No data available');
            return;
        }

        let candles = data.map(transformCandle).filter(c => c !== null);
        let volumes = data.map(transformVolume).filter(v => v !== null);

        if (candles.length === 0) {
            console.warn('No valid candle data');
            return;
        }

        candles = removeDuplicatesAndSort(candles);
        if (volumeSeries) volumes = removeDuplicatesAndSort(volumes);

        chartState.allData = candles;
        if (volumeSeries) chartState.allVolumeData = volumes;
        chartState.hasMore = hasMore;

        if (candlestickSeries) candlestickSeries.setData(candles);
        if (volumeSeries && volumes.length > 0) volumeSeries.setData(volumes);

        setTimeout(async () => {
            const { chart } = await import('./state.js');
            const { updateSessionOverlay } = await import('./sessions.js');
            if (!chart) return;
            chart.timeScale().fitContent();
            const header = document.getElementById('header-container');
            const headerHeight = header ? header.offsetHeight : 60;
            chart.applyOptions({
                width: chartContainer.clientWidth,
                height: Math.max(400, window.innerHeight - headerHeight - 40),
            });
            updateSessionOverlay();
            renderPositionHistory();
            renderSwingDetection();
        }, 100);
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}