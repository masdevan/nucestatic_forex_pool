import { chartState, chart } from './state.js';
import { fetchSwingDetection } from './api.js';

let swingMarkers = [];

export async function renderSwingDetection() {
    if (!chart || !chartState.showSwingDetection) {
        clearSwingDetection();
        return;
    }

    try {
        const data = await fetchSwingDetection(chartState.currentTimeframe, chartState.currentSymbol);
        
        clearSwingDetection();

        const MAX_RENDER = 100;
        const limitedData = data.slice(-MAX_RENDER);

        limitedData.forEach(swing => {
            try {
                if (!swing.time || !swing.price) {
                    return;
                }
                
                const color = swing.type === 'high' ? '#FF1744' : '#00C853';
                
                const marker = chart.addLineSeries({
                    color: color,
                    lineWidth: 1,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    lineStyle: 2,
                    opacity: 0.5,
                });

                marker.setData([
                    { time: swing.time - 180, value: swing.price },
                    { time: swing.time + 180, value: swing.price }
                ]);

                swingMarkers.push(marker);
            } catch (e) {
                console.warn('Skipping invalid swing entry:', e);
            }
        });
    } catch (e) {
        console.error('Failed to render swing detection:', e);
        clearSwingDetection();
    }
}

export function clearSwingDetection() {
    try {
        swingMarkers.forEach(marker => {
            if (chart && marker) {
                chart.removeSeries(marker);
            }
        });
    } catch (e) {
        console.warn('Error clearing swing markers:', e);
    }
    swingMarkers = [];
}
