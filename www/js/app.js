const RECORD_SECONDS = 15;
const NUM_BARS = 32;

const analyzer = new FridgeAnalyzer();

/* ── Waveform bars ── */
const waveformEl = document.getElementById('waveform');
for (let i = 0; i < NUM_BARS; i++) {
  const b = document.createElement('div');
  b.className = 'bar';
  waveformEl.appendChild(b);
}
const bars = waveformEl.querySelectorAll('.bar');

let waveTimer = null;
function startWave() {
  waveTimer = setInterval(() => {
    const rms = analyzer.instantRms();
    bars.forEach(b => {
      const h = 4 + (rms * 280 + Math.random() * 18) * 0.55;
      b.style.height = Math.min(h, 60) + 'px';
    });
  }, 50);
}
function stopWave() {
  clearInterval(waveTimer);
  bars.forEach(b => b.style.height = '4px');
}

/* ── Screen transitions ── */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

/* ── Main recording flow ── */
document.getElementById('btn-start').addEventListener('click', async () => {
  showScreen('screen-recording');

  const countdownEl    = document.getElementById('countdown');
  const recIndicator   = document.getElementById('rec-indicator');
  const progressWrap   = document.getElementById('progress-wrap');
  const progressBar    = document.getElementById('progress-bar');
  const recStatus      = document.getElementById('rec-status');

  // Countdown 3-2-1
  for (let i = 3; i >= 1; i--) {
    countdownEl.textContent = i;
    countdownEl.classList.add('pop');
    await sleep(1000);
    countdownEl.classList.remove('pop');
  }

  countdownEl.classList.add('hidden');
  recIndicator.classList.remove('hidden');
  progressWrap.classList.remove('hidden');

  try {
    await analyzer.start();
  } catch (e) {
    recStatus.textContent = 'Errore microfono: ' + e.message;
    return;
  }

  startWave();

  const t0 = Date.now();
  const tick = setInterval(() => {
    const elapsed = (Date.now() - t0) / 1000;
    progressBar.style.width = Math.min(elapsed / RECORD_SECONDS * 100, 100) + '%';
    recStatus.textContent   = 'Registrazione… ' + Math.max(0, RECORD_SECONDS - Math.floor(elapsed)) + 's';
  }, 100);

  await sleep(RECORD_SECONDS * 1000);

  clearInterval(tick);
  stopWave();
  recStatus.textContent = 'Analisi in corso…';

  const features = analyzer.stop();
  await sleep(400);

  const result = classifyHealth(features);
  renderResults(result);
  showScreen('screen-results');
});

document.getElementById('btn-retry').addEventListener('click', () => showScreen('screen-home'));

/* ── Render results ── */
function renderResults({ status, confidence, details }) {
  const info = STATUS_INFO[status] || STATUS_INFO.UNKNOWN;

  document.getElementById('res-icon').textContent   = info.icon;
  document.getElementById('res-status').textContent = info.label;
  document.getElementById('res-status').style.color = info.color;
  document.getElementById('res-desc').textContent   = info.desc;

  const pct = Math.round(confidence * 100);
  const fill = document.getElementById('conf-fill');
  fill.style.backgroundColor = info.color;
  setTimeout(() => { fill.style.width = pct + '%'; }, 50);
  document.getElementById('conf-text').textContent = 'Confidenza: ' + pct + '%';

  const indBox = document.getElementById('indicators');
  indBox.innerHTML = '';
  details.forEach(d => {
    const div = document.createElement('div');
    div.className = 'indicator ' + d.sev;
    div.innerHTML =
      '<span class="ind-name">'  + d.name  + '</span>' +
      '<span class="ind-value">' + d.value + '</span>' +
      '<span class="ind-text">'  + d.text  + '</span>';
    indBox.appendChild(div);
  });

  const recBox = document.getElementById('recommendations');
  recBox.innerHTML = '';
  (RECOMMENDATIONS[status] || []).forEach(r => {
    const li = document.createElement('li');
    li.textContent = r;
    recBox.appendChild(li);
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
