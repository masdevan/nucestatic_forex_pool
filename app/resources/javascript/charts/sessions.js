const SESSIONS = [
    { color: 'rgba(33, 150, 243, 0.05)',  hourStart: 6,  hourEnd: 14 },
    { color: 'rgba(255, 193, 7, 0.05)',   hourStart: 14, hourEnd: 19 },
    { color: 'rgba(244, 67, 54, 0.05)',   hourStart: 19, hourEnd: 30 },
];

const LEGEND = [
    { label: 'Asia',     color: 'rgba(33,  150, 243, 0.9)' },
    { label: 'London',   color: 'rgba(255, 193,   7, 0.9)' },
    { label: 'New York', color: 'rgba(244,  67,  54, 0.9)' },
];

let overlayCanvas = null;
let chartRef = null;

export function initSessionBackground(chart) {
    chartRef = chart;

    const container = document.getElementById('chart-container');
    if (!container) return;

    const existing = document.getElementById('session-overlay');
    if (existing) existing.remove();

    overlayCanvas = document.createElement('canvas');
    overlayCanvas.id = 'session-overlay';
    overlayCanvas.style.position = 'absolute';
    overlayCanvas.style.top = '0';
    overlayCanvas.style.left = '0';
    overlayCanvas.style.pointerEvents = 'none';
    overlayCanvas.style.zIndex = '100';

    container.appendChild(overlayCanvas);

    _resize(container);
    _draw();

    chart.timeScale().subscribeVisibleTimeRangeChange(() => _draw());

    window.addEventListener('resize', () => {
        _resize(container);
        _draw();
    });
}

export function updateSessionOverlay() {
    const container = document.getElementById('chart-container');
    if (!container) return;
    _resize(container);
    _draw();
}

function _resize(container) {
    if (!overlayCanvas || !container) return;
    overlayCanvas.width  = container.clientWidth;
    overlayCanvas.height = container.clientHeight;
}

function _getSessionColor(timestamp) {
    const hour = new Date(timestamp * 1000).getUTCHours();
    for (const s of SESSIONS) {
        const end = s.hourEnd > 24 ? s.hourEnd - 24 : s.hourEnd;
        if (s.hourEnd > 24) {
            if (hour >= s.hourStart || hour < end) return s.color;
        } else {
            if (hour >= s.hourStart && hour < end) return s.color;
        }
    }
    return null;
}

function _draw() {
    if (!overlayCanvas || !chartRef) return;

    const ctx = overlayCanvas.getContext('2d');
    const W = overlayCanvas.width;
    const H = overlayCanvas.height;
    ctx.clearRect(0, 0, W, H);

    const visibleRange = chartRef.timeScale().getVisibleRange();
    if (!visibleRange) return;

    let currentColor = null;
    let blockStart = 0;

    for (let x = 0; x <= W; x++) {
        const time = chartRef.timeScale().coordinateToTime(x);
        const color = time !== null ? _getSessionColor(time) : null;

        if (color !== currentColor) {
            if (currentColor !== null && x > blockStart) {
                ctx.fillStyle = currentColor;
                ctx.fillRect(blockStart, 0, x - blockStart, H);
            }
            currentColor = color;
            blockStart = x;
        }
    }

    if (currentColor !== null && W > blockStart) {
        ctx.fillStyle = currentColor;
        ctx.fillRect(blockStart, 0, W - blockStart, H);
    }

    _drawLegend(ctx);
}

function _drawLegend(ctx) {
    let x = 10;
    const gap = 15;

    ctx.font = '11px Trebuchet MS, sans-serif';

    for (const item of LEGEND) {
        ctx.fillStyle = item.color;
        ctx.fillRect(x, 10, 10, 10);

        ctx.fillStyle = '#d1d4dc';
        ctx.fillText(item.label, x + 15, 19);

        x += 15 + ctx.measureText(item.label).width + gap;
    }
}