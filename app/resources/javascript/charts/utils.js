export function transformCandle(item) {
    if (!item || typeof item !== 'object') return null;
    const time = item.time;
    const open = Number(item.open);
    const high = Number(item.high);
    const low = Number(item.low);
    const close = Number(item.close);
    if (time == null || isNaN(open) || isNaN(high) || isNaN(low) || isNaN(close)) return null;
    if (high < low || open <= 0 || close <= 0) return null;
    return { time, open, high, low, close };
}

export function transformVolume(item) {
    if (!item || typeof item !== 'object') return null;
    const time = item.time;
    const open = Number(item.open);
    const close = Number(item.close);
    const volume = Number(item.tick_volume || item.real_volume || 0);
    if (time == null || isNaN(open) || isNaN(close)) return null;
    return {
        time,
        value: isNaN(volume) ? 0 : volume,
        color: close >= open ? '#00C85388' : '#FF174488'
    };
}

export function removeDuplicatesAndSort(arr) {
    const seen = new Set();
    const unique = [];
    const sorted = arr.slice().sort((a, b) => a.time - b.time);
    for (const item of sorted) {
        if (!seen.has(item.time)) {
            seen.add(item.time);
            unique.push(item);
        }
    }
    return unique;
}
