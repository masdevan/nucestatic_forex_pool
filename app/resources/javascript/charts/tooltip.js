const SESSION_LABELS = [
    { label: 'Asia',     hourStart: 6,  hourEnd: 14 },
    { label: 'London',   hourStart: 14, hourEnd: 19 },
    { label: 'New York', hourStart: 19, hourEnd: 30 },
];

const SESSION_COLORS = {
    'Asia':     '#2196F3',
    'London':   '#FFC107',
    'New York': '#F44336',
};

function _getSession(timestamp) {
    const hour = new Date(timestamp * 1000).getUTCHours();
    for (const s of SESSION_LABELS) {
        const end = s.hourEnd > 24 ? s.hourEnd - 24 : s.hourEnd;
        if (s.hourEnd > 24) {
            if (hour >= s.hourStart || hour < end) return s.label;
        } else {
            if (hour >= s.hourStart && hour < s.hourEnd) return s.label;
        }
    }
    return 'New York';
}

function _formatTime(timestamp) {
    const d = new Date(timestamp * 1000);
    const pad = n => String(n).padStart(2, '0');
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} `
         + `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

function _fmt(val) {
    return Number(val).toFixed(5);
}

function _createBar() {
    const existing = document.getElementById('ohlc-bar');
    if (existing) return existing;

    const bar = document.createElement('div');
    bar.id = 'ohlc-bar';
    bar.style.cssText = `
        position: absolute;
        top: 6px;
        left: 200px;
        z-index: 200;
        display: none;
        align-items: center;
        gap: 14px;
        font-size: 12px;
        font-family: Trebuchet MS, Roboto, Ubuntu, sans-serif;
        color: #d1d4dc;
        pointer-events: none;
        user-select: none;
        white-space: nowrap;
        background: rgba(26,26,26,0.6);
        padding: 3px 8px;
        border-radius: 3px;
    `;

    const container = document.getElementById('chart-container');
    if (container) container.appendChild(bar);

    return bar;
}

function _span(label, value, color) {
    return `<span style="color:#888;margin-right:2px">${label}</span>`
         + `<span style="color:${color}">${value}</span>`;
}

export function initTooltip(chart, candleSeries) {
    const bar = _createBar();

    chart.subscribeCrosshairMove(param => {
        if (!param || !param.time || !param.point || param.point.x < 0 || param.point.y < 0) {
            bar.style.display = 'none';
            return;
        }

        const prices = param.seriesPrices.get(candleSeries);
        if (!prices) {
            bar.style.display = 'none';
            return;
        }

        const { open, high, low, close } = prices;
        const isBull = close >= open;
        const candleColor = isBull ? '#00C853' : '#FF1744';

        const session = _getSession(param.time);
        const sessionColor = SESSION_COLORS[session] || '#d1d4dc';
        const timeStr = _formatTime(param.time);

        bar.style.display = 'flex';
        bar.innerHTML = [
            _span('Time',    timeStr,      '#d1d4dc'),
            _span('Session', session,      sessionColor),
            _span('O',       _fmt(open),   candleColor),
            _span('H',       _fmt(high),   candleColor),
            _span('L',       _fmt(low),    candleColor),
            _span('C',       _fmt(close),  candleColor),
        ].join('');
    });
}