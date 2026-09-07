(function () {
    var client = null;
    var subscriptions = {};

    function setStatus(text, connected) {
        var el = document.getElementById('ws-status');
        if (!el) return;
        el.textContent = text;
        el.className = 'ws-badge ' + (connected ? 'ws-connected' : 'ws-disconnected');
    }

    function appendResult(channel, data) {
        var resultDiv = document.getElementById('ws-result');
        if (!resultDiv) return;
        var entry = document.createElement('div');
        entry.className = 'ws-entry';
        entry.innerHTML = '<span class="ws-channel">' + channel + '</span><pre>' + JSON.stringify(data, null, 2) + '</pre>';
        resultDiv.insertBefore(entry, resultDiv.firstChild);
        while (resultDiv.children.length > 50) {
            resultDiv.removeChild(resultDiv.lastChild);
        }
        resultDiv.className = 'api-result loaded';
    }

    function showPublish(ch, enabled) {
        var pubSection = document.getElementById('ws-publish-section');
        var pubChannel = document.getElementById('ws-pub-channel');
        var pubInput = document.getElementById('ws-pub-input');
        var pubBtn = document.getElementById('ws-pub-btn');
        if (!pubSection) return;
        pubSection.style.display = 'block';
        pubChannel.textContent = ch;
        pubBtn.disabled = !enabled;
        pubBtn.textContent = enabled ? 'Publish' : 'Subscribing...';
        if (enabled) {
            pubInput.value = '{\n  "symbol": "' + ch.replace('trade:', '') + '",\n  "open": 1.12345,\n  "high": 1.12400,\n  "low": 1.12300,\n  "close": 1.12380\n}';
            pubInput.focus();
        }

        pubBtn.onclick = function () {
            if (!subscriptions[ch]) return;
            var data;
            try {
                data = JSON.parse(pubInput.value);
            } catch (e) {
                pubInput.style.borderColor = '#f87171';
                setTimeout(function () { pubInput.style.borderColor = ''; }, 1500);
                return;
            }
            fetch('/api/centrifugo/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel: ch, data: data })
            }).then(function (r) { return r.json(); }).then(function (res) {
                if (res.error) {
                    appendResult(ch + ' [error]', res.error);
                } else {
                    appendResult(ch + ' [sent]', data);
                }
            }).catch(function (err) {
                appendResult(ch + ' [error]', err.message ? { error: err.message } : { error: String(err) });
            });
        };
    }

    function hidePublish() {
        var pubSection = document.getElementById('ws-publish-section');
        if (pubSection) pubSection.style.display = 'none';
    }

    function doSubscribe(ch) {
        if (!client) return;
        if (subscriptions[ch]) {
            showPublish(ch, true);
            return;
        }
        var existing = client.getSubscription(ch);
        if (existing) {
            subscriptions[ch] = existing;
            existing.subscribe();
            updateSubList();
            showPublish(ch, true);
            return;
        }
        var sub = client.newSubscription(ch);
        sub.on('publication', function (ctx) {
            appendResult(ch, ctx.pub.data);
        });
        sub.on('unsubscribe', function () {
            updateSubList();
            if (!Object.keys(subscriptions).length) hidePublish();
        });
        sub.subscribe();
        subscriptions[ch] = sub;
        updateSubList();
        showPublish(ch, true);
    }

    function doUnsubscribe(ch) {
        if (!subscriptions[ch]) return;
        subscriptions[ch].unsubscribe();
        client.removeSubscription(subscriptions[ch]);
        delete subscriptions[ch];
        updateSubList();
        if (!Object.keys(subscriptions).length) hidePublish();
    }

    function updateSubList() {
        var el = document.getElementById('active-subs');
        if (!el) return;
        var keys = Object.keys(subscriptions);
        el.textContent = keys.length === 0 ? 'None' : keys.join(', ');
    }

    function connectCentrifugo(token, wsUrl) {
        if (client) client.disconnect();
        client = new Centrifuge(wsUrl, { token: token });

        client.on('state', function (ctx) {
            if (ctx.newState === 'connected') setStatus('Connected', true);
            else if (ctx.newState === 'disconnected') setStatus('Disconnected', false);
            else if (ctx.newState === 'connecting') setStatus('Connecting...', false);
        });

        client.on('error', function (ctx) {
            console.error('Centrifugo error:', ctx);
        });

        client.connect();
    }

    function initCentrifugo() {
        var connectBtn = document.getElementById('ws-connect');
        var subBtn = document.getElementById('ws-sub-btn');
        var unsubBtn = document.getElementById('ws-unsub-btn');
        var channelInput = document.getElementById('ws-channel');
        if (!connectBtn) return;

        connectBtn.addEventListener('click', function () {
            if (client && client.state === 'connected') {
                client.disconnect();
                subscriptions = {};
                updateSubList();
                setStatus('Disconnected', false);
                return;
            }
            setStatus('Connecting...', false);
            fetch('/api/centrifugo/token').then(function (r) { return r.json(); }).then(function (res) {
                connectCentrifugo(res.token, res.ws_url);
            }).catch(function () {
                setStatus('Token error', false);
            });
        });

        if (subBtn && channelInput) {
            subBtn.addEventListener('click', function () {
                var ch = channelInput.value.trim();
                if (ch) doSubscribe(ch);
            });
        }

        if (unsubBtn && channelInput) {
            unsubBtn.addEventListener('click', function () {
                var ch = channelInput.value.trim();
                if (ch) doUnsubscribe(ch);
            });
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        initCentrifugo();
    });
})();
