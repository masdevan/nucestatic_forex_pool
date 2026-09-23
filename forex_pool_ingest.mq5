#property service
#property version "1.00"
#property description "ForexPool OHLC ingest service"

string SYMBOL = "XAUUSDm,USDJPYm,GBPUSDm,USOILm,BTCUSDm,EURUSDm";

input group "Connection"
input string InpApiBase = "https://sourcewave.devan.my.id";
input string InpServer = "";
input int InpTimeoutMs = 5000;

input group "Sync"
input datetime InpMinStartDate = D'2026.09.20 00:00';
input int InpPollMs = 2000;
input int InpBatchSize = 500;

string TIMEFRAME_KEYS[9] = {"m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1"};
ENUM_TIMEFRAMES TIMEFRAME_PERIODS[9] = {PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, PERIOD_D1, PERIOD_W1, PERIOD_MN1};

string g_wanted[];
int g_wantedCount = 0;
bool g_wantedReported[];
string g_symbols[];
int g_symbolCount = 0;
string g_server = "";
datetime g_minStart = 0;
datetime g_lastPosted[];
double g_lastOhlc[];
int g_failures = 0;
string g_lastError = "";
datetime g_lastRejectLog = 0;

int OnStart()
{
    Initialize();
    int base = InpPollMs < 100 ? 100 : InpPollMs;
    while (!IsStopped())
    {
        RefreshSymbols();
        if (SyncAll())
        {
            if (g_failures > 0)
                Print("API recovered after ", g_failures, " failure(s)");
            g_failures = 0;
            Sleep(base);
            continue;
        }
        g_failures++;
        if (g_failures == 1 || (g_failures & (g_failures - 1)) == 0)
            Print("Sync failed (", g_lastError, "), failures ", g_failures);
        int shift = g_failures < 6 ? g_failures : 6;
        int pause = base * (1 << shift);
        if (pause > 60000)
            pause = 60000;
        Sleep(pause);
    }
    return 0;
}

void Initialize()
{
    g_server = InpServer == "" ? AccountInfoString(ACCOUNT_SERVER) : InpServer;
    ParseSymbols(SYMBOL);
    ArrayResize(g_symbols, 0);
    g_symbolCount = 0;
    ArrayResize(g_lastPosted, 0);
    ArrayResize(g_lastOhlc, 0);
    RefreshSymbols();
    g_minStart = FetchMinStartDate();
    if (g_minStart <= 0)
    {
        Print("MIN_START_DATE unavailable, using current time");
        g_minStart = TimeCurrent();
    }
    if (g_wantedCount == 0)
        Print("SYMBOL is empty, service idle");
    else
        Print("ForexPool ingest: ", g_symbolCount, "/", g_wantedCount, " symbol(s) active, server ", g_server, ", min start ", TimeToString(g_minStart));
}

void ParseSymbols(string raw)
{
    ArrayResize(g_wanted, 0);
    g_wantedCount = 0;
    string parts[];
    int count = StringSplit(raw, ',', parts);
    for (int i = 0; i < count; i++)
    {
        string name = parts[i];
        StringTrimLeft(name);
        StringTrimRight(name);
        if (name == "")
            continue;
        bool duplicate = false;
        for (int j = 0; j < g_wantedCount; j++)
        {
            if (g_wanted[j] == name)
            {
                duplicate = true;
                break;
            }
        }
        if (duplicate)
            continue;
        ArrayResize(g_wanted, g_wantedCount + 1);
        g_wanted[g_wantedCount] = name;
        g_wantedCount++;
    }
    ArrayResize(g_wantedReported, g_wantedCount);
}

void RefreshSymbols()
{
    for (int w = 0; w < g_wantedCount; w++)
    {
        if (IsSymbolActive(g_wanted[w]))
            continue;
        if (SymbolSelect(g_wanted[w], true))
        {
            AddSymbol(g_wanted[w]);
            Print("Symbol added: ", g_wanted[w]);
            continue;
        }
        if (!g_wantedReported[w])
        {
            Print("Symbol unavailable: ", g_wanted[w]);
            g_wantedReported[w] = true;
        }
    }
}

bool IsSymbolActive(string name)
{
    for (int i = 0; i < g_symbolCount; i++)
    {
        if (g_symbols[i] == name)
            return true;
    }
    return false;
}

void AddSymbol(string name)
{
    ArrayResize(g_symbols, g_symbolCount + 1);
    g_symbols[g_symbolCount] = name;
    g_symbolCount++;
    ArrayResize(g_lastPosted, g_symbolCount * 9);
    ArrayResize(g_lastOhlc, g_symbolCount * 36);
}

bool SyncAll()
{
    for (int s = 0; s < g_symbolCount; s++)
    {
        for (int t = 0; t < 9; t++)
        {
            if (!SyncTimeframe(s, t))
                return false;
        }
    }
    return true;
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

bool SyncTimeframe(int symbolIndex, int timeframeIndex)
{
    int slot = symbolIndex * 9 + timeframeIndex;
    datetime start = g_lastPosted[slot] > 0 ? g_lastPosted[slot] : g_minStart;
    MqlRates rates[];
    int copied = CopyRates(g_symbols[symbolIndex], TIMEFRAME_PERIODS[timeframeIndex], start, TimeCurrent(), rates);
    if (copied <= 0)
        return true;

    string candles[];
    datetime lastTime = 0;
    double lastValues[4];
    bool changed = false;

    for (int i = 0; i < copied; i++)
    {
        if (rates[i].time < g_minStart)
            continue;
        if (g_lastPosted[slot] == rates[i].time && !OhlcChanged(slot, rates[i]))
            continue;
        int size = ArraySize(candles);
        ArrayResize(candles, size + 1);
        candles[size] = CandleJson(g_symbols[symbolIndex], timeframeIndex, rates[i]);
        lastTime = rates[i].time;
        lastValues[0] = rates[i].open;
        lastValues[1] = rates[i].high;
        lastValues[2] = rates[i].low;
        lastValues[3] = rates[i].close;
        changed = true;
    }

    if (!changed)
        return true;

    int status = PostCandles(candles);
    if (status != 0)
    {
        if (status == -1 || status >= 500)
            return false;
        if (TimeCurrent() - g_lastRejectLog > 60)
        {
            Print("POST rejected (", status, "): ", g_lastError);
            g_lastRejectLog = TimeCurrent();
        }
        return true;
    }

    g_lastPosted[slot] = lastTime;
    int base = slot * 4;
    g_lastOhlc[base] = lastValues[0];
    g_lastOhlc[base + 1] = lastValues[1];
    g_lastOhlc[base + 2] = lastValues[2];
    g_lastOhlc[base + 3] = lastValues[3];
    return true;
}

bool OhlcChanged(int slot, const MqlRates &rate)
{
    int base = slot * 4;
    if (g_lastOhlc[base] != rate.open || g_lastOhlc[base + 1] != rate.high)
        return true;
    return g_lastOhlc[base + 2] != rate.low || g_lastOhlc[base + 3] != rate.close;
}

string CandleJson(string symbol, int timeframeIndex, const MqlRates &rate)
{
    int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    return "{\"server\":\"" + JsonEscape(g_server) + "\",\"symbol\":\"" + JsonEscape(symbol) +
           "\",\"timeframe\":\"" + TIMEFRAME_KEYS[timeframeIndex] +
           "\",\"open\":" + DoubleToString(rate.open, digits) +
           ",\"high\":" + DoubleToString(rate.high, digits) +
           ",\"low\":" + DoubleToString(rate.low, digits) +
           ",\"close\":" + DoubleToString(rate.close, digits) +
           ",\"time\":" + IntegerToString((long)rate.time) + "}";
}

string JsonEscape(string value)
{
    StringReplace(value, "\\", "\\\\");
    StringReplace(value, "\"", "\\\"");
    return value;
}

int PostCandles(string &candles[])
{
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
        string response;
        int status = HttpPost("/api/ohlc", body, response);
        if (status < 200 || status >= 300)
            return status;
    }
    return 0;
}
