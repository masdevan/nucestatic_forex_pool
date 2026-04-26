export const chartState = {
    currentTimeframe: 'M1',
    currentSymbol: 'USDJPYm',
    limit: 50,
    page: 1,
    allData: [],
    allVolumeData: [],
    hasMore: true,
    isLoading: false,
    visibleRange: null,
    showMarketStructure: false,
    showSwingDetection: false,
    showPositionHistory: false,
    candleSeries: null,
};

export let chart = null;
export let candlestickSeries = null;
export let volumeSeries = null;

export function setChartInstance(instance) {
    chart = instance;
}

export function setCandlestickSeries(instance) {
    candlestickSeries = instance;
    chartState.candleSeries = instance;
}

export function setVolumeSeries(instance) {
    volumeSeries = instance;
}
