/* Records audio via Web Audio API and computes acoustic features. */
class FridgeAnalyzer {
  constructor() {
    this._ctx      = null;
    this._analyser = null;
    this._source   = null;
    this._stream   = null;
    this._timeFrames = [];
    this._freqFrames = [];
    this._timer    = null;
    this._active   = false;
  }

  async start() {
    this._stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
    });
    this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    this._analyser = this._ctx.createAnalyser();
    this._analyser.fftSize = 2048;
    this._analyser.smoothingTimeConstant = 0;
    this._source = this._ctx.createMediaStreamSource(this._stream);
    this._source.connect(this._analyser);

    this._timeFrames = [];
    this._freqFrames = [];
    this._active = true;

    const tBuf = new Float32Array(this._analyser.fftSize);
    const fBuf = new Float32Array(this._analyser.frequencyBinCount);

    this._timer = setInterval(() => {
      if (!this._active) return;
      this._analyser.getFloatTimeDomainData(tBuf);
      this._analyser.getFloatFrequencyData(fBuf);
      this._timeFrames.push(new Float32Array(tBuf));
      this._freqFrames.push(new Float32Array(fBuf));
    }, 50);
  }

  stop() {
    this._active = false;
    clearInterval(this._timer);
    if (this._source) this._source.disconnect();
    if (this._stream) this._stream.getTracks().forEach(t => t.stop());
    return this._features();
  }

  instantRms() {
    if (!this._analyser) return 0;
    const buf = new Float32Array(this._analyser.fftSize);
    this._analyser.getFloatTimeDomainData(buf);
    return Math.sqrt(buf.reduce((s, x) => s + x * x, 0) / buf.length);
  }

  _features() {
    const sr       = this._ctx.sampleRate;
    const fftSize  = this._analyser.fftSize;
    const binCount = this._analyser.frequencyBinCount;
    const binHz    = sr / fftSize;

    // RMS per frame
    const rmsFrames = this._timeFrames.map(f => {
      return Math.sqrt(f.reduce((s, x) => s + x * x, 0) / f.length);
    });
    const rmsMean = rmsFrames.reduce((a, b) => a + b, 0) / (rmsFrames.length || 1);
    const rmsVar  = rmsFrames.reduce((s, r) => s + (r - rmsMean) ** 2, 0) / (rmsFrames.length || 1);
    const rmsStd  = Math.sqrt(rmsVar);
    const rmsMax  = Math.max(...rmsFrames, 0);

    // Average linear spectrum (frames are in dB)
    const avgFreq = new Float32Array(binCount).fill(0);
    this._freqFrames.forEach(f => {
      f.forEach((db, i) => { avgFreq[i] += Math.pow(10, db / 20); });
    });
    if (this._freqFrames.length) avgFreq.forEach((_, i) => { avgFreq[i] /= this._freqFrames.length; });

    // Dominant frequency (skip DC bin 0)
    let maxMag = -Infinity, domBin = 1;
    for (let i = 1; i < binCount; i++) {
      if (avgFreq[i] > maxMag) { maxMag = avgFreq[i]; domBin = i; }
    }
    const dominantFreq = domBin * binHz;

    // Energy band ratios
    let totalE = 0, lowE = 0, highE = 0;
    for (let i = 0; i < binCount; i++) {
      const e = avgFreq[i] * avgFreq[i];
      const hz = i * binHz;
      totalE += e;
      if (hz < 300)  lowE  += e;
      if (hz > 2000) highE += e;
    }
    totalE += 1e-10;
    const lowFreqRatio  = lowE  / totalE;
    const highFreqRatio = highE / totalE;

    // Spectral centroid
    let wSum = 0, mSum = 0;
    for (let i = 0; i < binCount; i++) { wSum += i * binHz * avgFreq[i]; mSum += avgFreq[i]; }
    const spectralCentroid = mSum > 0 ? wSum / mSum : 0;

    // ZCR
    let zcrSum = 0;
    this._timeFrames.forEach(f => {
      let z = 0;
      for (let i = 1; i < f.length; i++) if ((f[i] >= 0) !== (f[i-1] >= 0)) z++;
      zcrSum += z / f.length;
    });
    const zcrMean = this._timeFrames.length ? zcrSum / this._timeFrames.length : 0;

    // Click count: frames where RMS is >3× mean and above noise floor
    const clickCount = rmsFrames.filter(r => r > rmsMean * 3 && r > 0.01).length;

    const duration = (this._timeFrames.length * fftSize) / sr;

    return { rmsMean, rmsStd, rmsMax, dominantFreq, spectralCentroid, lowFreqRatio, highFreqRatio, zcrMean, clickCount, duration };
  }
}
