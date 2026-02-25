/* ── Config ───────────────────────────────────────────────────────────────── */
const API = '';  // Same-origin — FastAPI serves both API and static files

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function now() {
    return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function logToFeed(source, msg, type = 'log') {
    const feed = document.getElementById('feedList');
    const placeholder = feed.querySelector('.log-placeholder');
    if (placeholder) placeholder.remove();
    const item = document.createElement('div');
    item.className = 'feed-item';
    item.innerHTML = `
    <span class="feed-time">${now()}</span>
    <span class="feed-source">${source}</span>
    <span class="feed-msg">${escHtml(msg)}</span>`;
    feed.prepend(item);
    const items = feed.querySelectorAll('.feed-item'); // Keep feed trimmed
    if (items.length > 200) items[items.length - 1].remove();
}

function escHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function setBadge(id, label, cls) {
    const el = document.getElementById(id);
    el.textContent = label;
    el.className = `panel-badge ${cls}`;
}

function appendLog(boxId, msg, type = 'log') {
    const box = document.getElementById(boxId);
    const placeholder = box.querySelector('.log-placeholder');
    if (placeholder) placeholder.remove();
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = msg;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
}

function scoreClass(score) {
    const n = parseFloat(score);
    if (isNaN(n)) return '';
    if (n >= 80) return 'high';
    if (n >= 60) return 'medium';
    return 'low';
}

/* ── Status on load ───────────────────────────────────────────────────────── */
async function loadStatus() {
    try {
        const res = await fetch(`${API}/api/status`);
        const data = await res.json();
        const dot = document.getElementById('statusDot');
        const label = document.getElementById('statusLabel');
        const pills = document.getElementById('statusPills');
        if (data.api_key_present) {
            dot.className = 'status-dot ok';
            label.textContent = 'Services available';
        } else {
            dot.className = 'status-dot warn';
            label.textContent = 'No API key — mock mode';
        }
        pills.innerHTML = `
      <span class="pill ${data.api_key_present ? 'ok' : 'warn'}">
        ${data.api_key_present ? '🔑 Key OK' : '⚠ No Key'}
      </span>
      <span class="pill">vault: ${data.vault_path}</span>
      <span class="pill">chroma: ${data.chroma_path}</span>`;
        document.getElementById('vaultPath').value = data.vault_path;
        document.getElementById('chromaPath').value = data.chroma_path;
        logToFeed('SYS', `Status loaded — API key: ${data.api_key_present ? 'present' : 'missing'}`);
    } catch (e) {
        document.getElementById('statusDot').className = 'status-dot error';
        document.getElementById('statusLabel').textContent = 'Cannot reach server';
        logToFeed('SYS', `Error loading status: ${e.message}`, 'error');
    }
}

/* ── Vault Ingest ─────────────────────────────────────────────────────────── */
async function triggerIngest() {
    const btn = document.getElementById('ingestBtn');
    const vaultPath = document.getElementById('vaultPath').value.trim();
    const chromaPath = document.getElementById('chromaPath').value.trim();
    const logBox = document.getElementById('ingestLog');
    logBox.innerHTML = ''; // Reset log
    btn.disabled = true;
    btn.classList.add('pulsing');
    setBadge('ingestBadge', 'Running…', 'running');
    logToFeed('INGEST', 'Started vault ingest');
    try {
        const response = await fetch(`${API}/api/vault/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vault_path: vaultPath, chroma_path: chromaPath }),
        });
        if (!response.ok) { throw new Error(`HTTP ${response.status}`); }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop(); // last possibly incomplete chunk
            for (const part of parts) {
                const eventMatch = part.match(/^event:\s*(.+)$/m);
                const dataMatch = part.match(/^data:\s*(.+)$/m);
                if (!dataMatch) continue;
                const eventType = eventMatch ? eventMatch[1].trim() : 'log';
                let payload;
                try { payload = JSON.parse(dataMatch[1]); } catch { continue; }
                if (eventType === 'done') break;
                const msg = payload.message || '';
                appendLog('ingestLog', msg, eventType);
                logToFeed('INGEST', msg, eventType);
                if (eventType === 'success') {
                    setBadge('ingestBadge', 'Success', 'success');
                } else if (eventType === 'error') { setBadge('ingestBadge', 'Error', 'error'); }
            }
        }
        const badge = document.getElementById('ingestBadge');
        if (badge.textContent === 'Running…') { setBadge('ingestBadge', 'Done', 'success'); } // If badge still says "Running", settle to success
    } catch (e) {
        appendLog('ingestLog', `❌ ${e.message}`, 'error');
        setBadge('ingestBadge', 'Error', 'error');
        logToFeed('INGEST', `Error: ${e.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.classList.remove('pulsing');
    }
}

/* ── Trend Scout ──────────────────────────────────────────────────────────── */
async function triggerScout() {
    const btn = document.getElementById('scoutBtn');
    const theme = document.getElementById('scoutTheme').value.trim();
    const raw = document.getElementById('scoutConstraints').value.trim();
    const constraints = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : [];
    const grid = document.getElementById('trendsGrid');
    grid.innerHTML = ''; // Reset
    btn.disabled = true;
    btn.classList.add('pulsing');
    setBadge('scoutBadge', 'Running…', 'running');
    logToFeed('SCOUT', `Started scout — theme: "${theme || 'none'}"`);
    let trendCount = 0;
    try {
        const response = await fetch(`${API}/api/scout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme, constraints }),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();
            for (const part of parts) {
                const eventMatch = part.match(/^event:\s*(.+)$/m);
                const dataMatch = part.match(/^data:\s*(.+)$/m);
                if (!dataMatch) continue;
                const eventType = eventMatch ? eventMatch[1].trim() : 'log';
                let payload;
                try { payload = JSON.parse(dataMatch[1]); } catch { continue; }
                if (eventType === 'done') break;
                if (eventType === 'trend') {
                    const t = payload.trend || payload;
                    renderTrendCard(t);
                    trendCount++;
                    logToFeed('SCOUT', `Trend: ${t.topic} (score: ${t.score ?? t.relevance ?? 'N/A'})`);
                } else {
                    const msg = payload.message || '';
                    logToFeed('SCOUT', msg, eventType);
                    if (eventType === 'error') setBadge('scoutBadge', 'Error', 'error');
                }
            }
        }
        setBadge('scoutBadge', trendCount ? `${trendCount} Trends` : 'Done', 'success');
    } catch (e) {
        setBadge('scoutBadge', 'Error', 'error');
        logToFeed('SCOUT', `Error: ${e.message}`, 'error');
        grid.innerHTML = `<div class="log-line error">❌ ${escHtml(e.message)}</div>`; // Show error in grid
    } finally {
        btn.disabled = false;
        btn.classList.remove('pulsing');
    }
}

function renderTrendCard(t) {
    const grid = document.getElementById('trendsGrid');
    const score = t.score ?? t.relevance ?? '?';
    const cls = scoreClass(score);
    const card = document.createElement('div');
    card.className = 'trend-card';
    card.innerHTML = `
    <div class="trend-score-ring ${cls}">${score}</div>
    <div class="trend-body">
      <div class="trend-topic">${escHtml(t.topic || 'Unknown')}</div>
      <div class="trend-rationale">${escHtml(t.rationale || '')}</div>
    </div>`;
    grid.appendChild(card);
}

/* ── Activity Feed clear ─────────────────────────────────────────────────── */
function clearFeed() {
    const feed = document.getElementById('feedList');
    feed.innerHTML = '<div class="log-placeholder">No activity yet…</div>';
}

/* ── Init ─────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', loadStatus);
