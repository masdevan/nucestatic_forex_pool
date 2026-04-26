import { chartState, chart } from './state.js';
import { fetchPositionHistory } from './api.js';

let positionMarkers = [];

export async function renderPositionHistory() {
    if (!chart || !chartState.showPositionHistory) {
        clearPositionMarkers();
        return;
    }

    const positions = await fetchPositionHistory(chartState.currentSymbol);
    clearPositionMarkers();

    const seen = new Set();

    positions.forEach(pos => {
        const key = `${pos.entry_time}-${pos.exit_time}-${pos.entry_price}`;
        if (seen.has(key)) return;
        seen.add(key);

        const isBuy = pos.type === 'buy';

        const entry = pos.entry_price;
        const tp = pos.tp;
        const sl = pos.sl;

        const profitColor = 'rgba(0, 200, 83, 0.25)';
        const lossColor = 'rgba(255, 23, 68, 0.25)';

        const profitTop = isBuy ? tp : entry;
        const profitBottom = isBuy ? entry : tp;

        const profitSeries = chart.addBaselineSeries({
            baseValue: { type: 'price', price: profitBottom },
            topFillColor1: profitColor,
            topFillColor2: profitColor,
            topLineColor: 'transparent',
            bottomFillColor1: 'transparent',
            bottomFillColor2: 'transparent',
            bottomLineColor: 'transparent',
            priceLineVisible: false,
            lastValueVisible: false,
        });

        profitSeries.setData([
            { time: pos.entry_time, value: profitTop },
            { time: pos.exit_time, value: profitTop },
        ]);

        const lossTop = isBuy ? entry : sl;
        const lossBottom = isBuy ? sl : entry;

        const lossSeries = chart.addBaselineSeries({
            baseValue: { type: 'price', price: lossBottom },
            topFillColor1: lossColor,
            topFillColor2: lossColor,
            topLineColor: 'transparent',
            bottomFillColor1: 'transparent',
            bottomFillColor2: 'transparent',
            bottomLineColor: 'transparent',
            priceLineVisible: false,
            lastValueVisible: false,
        });

        lossSeries.setData([
            { time: pos.entry_time, value: lossTop },
            { time: pos.exit_time, value: lossTop },
        ]);

        const entryLine = chart.addLineSeries({
            color: 'rgba(255,255,255,0.6)',
            lineWidth: 1,
            lineStyle: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });

        entryLine.setData([
            { time: pos.entry_time, value: entry },
            { time: pos.exit_time, value: entry },
        ]);

        positionMarkers.push(profitSeries, lossSeries, entryLine);
    });
}

export function clearPositionMarkers() {
    positionMarkers.forEach(series => {
        if (chart) chart.removeSeries(series);
    });
    positionMarkers = [];
}