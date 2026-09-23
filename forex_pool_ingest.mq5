#property version   "2.00"
#property description "ForexPool OHLC ingest EA"
#property strict

input group "Connection"
input string   InpApiBase     = "https://sourcewave.devan.my.id";
input string   InpServer      = "";
input int      InpTimeoutMs   = 15000;

input group "Sync"
input datetime InpMinStartDate = D'2026.09.20 00:00';
input int      InpPollMs       = 2000;
input int      InpBatchSize    = 200;
input bool     InpLogPosts     = true;

string           TIMEFRAME_KEYS[9]    = {"m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1"};
ENUM_TIMEFRAMES  TIMEFRAME_PERIODS[9] = {PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, PERIOD_D1, PERIOD_W1, PERIOD_MN1};

string   g_server        = "";
datetime g_minStart       = 0;
datetime g_lastPosted[9];
double   g_lastOhlc[36];
int      g_failures       = 0;
string   g_lastError      = "";
datetime g_lastRejectLog  = 0;
datetime g_lastHistoryLog = 0;
datetime g_heartbeat      = 0;
int      g_timerMs        = 0;

int OnInit()
{
    g_server = InpServer == "" ? AccountInfoString(ACCOUNT_SERVER) : InpServer;
    ArrayInitialize(g_lastPosted, 0);
    ArrayInitialize(g_lastOhlc, 0);
    g_minStart = FetchMinStartDate();
    if (g_minStart <= 0)
        g_minStart = InpMinStartDate > 0 ? InpMinStartDate : TimeCurrent();
    Print("ForexPool ingest active for ", _Symbol, ", server ", g_server, ", min start ", TimeToString(g_minStart));
    SetPollInterval(InpPollMs < 100 ? 100 : InpPollMs);
    return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
    EventKillTimer();
}

void OnTimer()
{
    Heartbeat();
    bool ok = true;
    for (int t = 0; t < 9; t++)
    {
        if (!SyncTimeframe(t))
            ok = false;
    }
    if (ok)
    {
        if (g_failures > 0)
            Print(_Symbol, " sync recovered after ", g_failures, " failures");
        g_failures = 0;
        SetPollInterval(InpPollMs < 100 ? 100 : InpPollMs);
        return;
    }
    g_failures++;
    if (g_failures == 1 || (g_failures & (g_failures - 1)) == 0)
        Print(_Symbol, " sync failed (", g_lastError, "), failure #", g_failures);
    int shift = g_failures < 6 ? g_failures : 6;
    int backoff = InpPollMs * (1 << shift);
    if (backoff > 60000)
        backoff = 60000;
    SetPollInterval(backoff);
}

void SetPollInterval(int ms)
{
    if (g_timerMs == ms)
        return;
    EventKillTimer();
    EventSetMillisecondTimer(ms);
    g_timerMs = ms;
}

void Heartbeat()
{
    if (TimeCurrent() - g_heartbeat < 300)
        return;
    g_heartbeat = TimeCurrent();
    string stamp = g_lastPosted[0] > 0 ? TimeToString(g_lastPosted[0]) : "waiting";
    Print("status ", _Symbol, " m1 @ ", stamp);
}

bool HistoryReady(ENUM_TIMEFRAMES tf)
{
    if (SeriesInfoInteger(_Symbol, tf, SERIES_SYNCHRONIZED))
        return true;
    MqlRates probe[];
    CopyRates(_Symbol, tf, 0, 1, probe);
    return false;
}

bool SyncTimeframe(int t)
{
    if (!HistoryReady(TIMEFRAME_PERIODS[t]))
    {
        if (TimeCurrent() - g_lastHistoryLog > 60)
        {
            Print(_Symbol, " ", TIMEFRAME_KEYS[t], " still syncing history from broker");
            g_lastHistoryLog = TimeCurrent();
        }
        return true;
    }

    datetime start = g_lastPosted[t] > 0 ? g_lastPosted[t] : g_minStart;
    MqlRates rates[];
    int copied = CopyRates(_Symbol, TIMEFRAME_PERIODS[t], start, TimeCurrent(), rates);
    if (copied <= 0)
        return true;

    string candles[];
    datetime candleTimes[];
    double candleValues[];
    bool changed = false;

    for (int i = 0; i < copied; i++)
    {
        if (rates[i].time < g_minStart)
            continue;
        if (g_lastPosted[t] == rates[i].time && !OhlcChanged(t, rates[i]))
            continue;
        int size = ArraySize(candles);
        ArrayResize(candles, size + 1);
        ArrayResize(candleTimes, size + 1);
        ArrayResize(candleValues, (size + 1) * 4);
        candles[size] = CandleJson(TIMEFRAME_KEYS[t], rates[i]);
        candleTimes[size] = rates[i].time;
        candleValues[size * 4] = rates[i].open;
        candleValues[size * 4 + 1] = rates[i].high;
        candleValues[size * 4 + 2] = rates[i].low;
        candleValues[size * 4 + 3] = rates[i].close;
        changed = true;
    }

    if (!changed)
        return true;

    return SendBatches(t, candles, candleTimes, candleValues);
}

void ApplyProgress(int t, datetime candleTime, double &values[], int base)
{
    g_lastPosted[t] = candleTime;
    int obase = t * 4;
    g_lastOhlc[obase] = values[base];
    g_lastOhlc[obase + 1] = values[base + 1];
    g_lastOhlc[obase + 2] = values[base + 2];
    g_lastOhlc[obase + 3] = values[base + 3];
}

bool SendBatches(int t, string &candles[], datetime &times[], double &values[])
{
    string tf = TIMEFRAME_KEYS[t];
    int total = ArraySize(candles);
    int batchSize = InpBatchSize < 1 ? 1 : InpBatchSize;
    for (int start = 0; start < total; start += batchSize)
    {
        int end = start + batchSize;
        if (end > total)
            end = total;
        string body = "[";
        for (int i = start; i < end; i++)
        {
            if (i > start)
                body += ",";
            body += candles[i];
        }
        body += "]";
        uint mark = GetTickCount();
        string response;
        int status = HttpPost("/api/ohlc", body, response);
        uint elapsed = GetTickCount() - mark;
        if (status < 200 || status >= 300)
        {
            g_lastError = StringFormat("%s %s failed: status %d, error %d", _Symbol, tf, status, GetLastError());
            if (status == -1 || status >= 500)
                return false;
            ApplyProgress(t, times[end - 1], values, (end - 1) * 4);
            if (TimeCurrent() - g_lastRejectLog > 60)
            {
                Print("POST rejected (", status, ") ", _Symbol, " ", tf, ": ", g_lastError);
                g_lastRejectLog = TimeCurrent();
            }
            return true;
        }
        ApplyProgress(t, times[end - 1], values, (end - 1) * 4);
        if (InpLogPosts)
            Print("candle ", _Symbol, " ", tf, " sent (", end - start, ") ", elapsed, "ms");
    }
    return true;
}

bool OhlcChanged(int t, const MqlRates &rate)
{
    int base = t * 4;
    if (g_lastOhlc[base] != rate.open || g_lastOhlc[base + 1] != rate.high)
        return true;
    return g_lastOhlc[base + 2] != rate.low || g_lastOhlc[base + 3] != rate.close;
}

string CandleJson(string tf, const MqlRates &rate)
{
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
    return "{\"server\":\"" + JsonEscape(g_server) + "\",\"symbol\":\"" + JsonEscape(_Symbol) +
           "\",\"timeframe\":\"" + tf +
           "\",\"open\":" + DoubleToString(rate.open, digits) +
           ",\"high\":" + DoubleToString(rate.high, digits) +
           ",\"low\":" + DoubleToString(rate.low, digits) +
           ",\"close\":" + DoubleToString(rate.close, digits) +
           ",\"time\":" + IntegerToString((long)rate.time) + "}";
}

datetime FetchMinStartDate()
{
    string response;
    if (!HttpGet("/api/health", response))
        return InpMinStartDate;
    string value = JsonStringValue(response, "min_start_date");
    if (value == "")
        return InpMinStartDate;
    StringReplace(value, "-", ".");
    datetime parsed = StringToTime(value);
    return parsed > 0 ? parsed : InpMinStartDate;
}

bool HttpGet(string path, string &response)
{
    char data[];
    char result[];
    string headers;
    int status = WebRequest("GET", InpApiBase + path, "", InpTimeoutMs, data, result, headers);
    if (status < 200 || status >= 300)
    {
        Print("GET ", path, " failed: status ", status, ", error ", GetLastError());
        return false;
    }
    response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
    return true;
}

int HttpPost(string path, string body, string &response)
{
    char data[];
    int length = StringToCharArray(body, data, 0, WHOLE_ARRAY, CP_UTF8);
    if (length > 0)
        ArrayResize(data, length - 1);
    char result[];
    string headers;
    int status = WebRequest("POST", InpApiBase + path, "Content-Type: application/json", InpTimeoutMs, data, result, headers);
    if (status < 200 || status >= 300)
    {
        g_lastError = "status " + IntegerToString(status) + ", error " + IntegerToString(GetLastError());
        return status;
    }
    response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
    return status;
}

string JsonStringValue(string json, string key)
{
    string pattern = "\"" + key + "\"";
    int position = StringFind(json, pattern);
    if (position < 0)
        return "";
    position = StringFind(json, ":", position + StringLen(pattern));
    if (position < 0)
        return "";
    int start = StringFind(json, "\"", position);
    if (start < 0)
        return "";
    string between = StringSubstr(json, position + 1, start - position - 1);
    StringTrimLeft(between);
    StringTrimRight(between);
    if (between != "")
        return "";
    int end = StringFind(json, "\"", start + 1);
    if (end < 0)
        return "";
    return StringSubstr(json, start + 1, end - start - 1);
}

string JsonEscape(string value)
{
    StringReplace(value, "\\", "\\\\");
    StringReplace(value, "\"", "\\\"");
    return value;
}