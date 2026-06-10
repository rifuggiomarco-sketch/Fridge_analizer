const STATUS_INFO = {
  NORMAL:     { icon: "✅", label: "NORMALE",     desc: "Frigo in buono stato — funzionamento regolare", color: "#00c853" },
  OVERWORKING:{ icon: "⚠️", label: "SOTTO STRESS", desc: "Compressore in sovraccarico",                   color: "#ffd600" },
  CLICKING:   { icon: "🔴", label: "CLIC ANOMALI", desc: "Rumori di scatto — possibile guasto",            color: "#d50000" },
  RATTLING:   { icon: "🔴", label: "VIBRAZIONI",   desc: "Vibrazioni anomale rilevate",                    color: "#d50000" },
  SILENT:     { icon: "❓", label: "SILENZIOSO",   desc: "Compressore spento o audio assente",             color: "#9e9e9e" },
  UNKNOWN:    { icon: "❓", label: "SCONOSCIUTO",  desc: "Segnale insufficiente per la diagnosi",          color: "#9e9e9e" },
};

const RECOMMENDATIONS = {
  NORMAL:      ["Il frigo funziona normalmente.", "Pulisci le bobine del condensatore ogni 6–12 mesi.", "Continua il monitoraggio periodico."],
  OVERWORKING: ["Controlla le guarnizioni delle porte.", "Lascia almeno 10 cm di spazio sui lati per la ventilazione.", "Verifica che le bobine del condensatore non siano sporche.", "Il frigo potrebbe essere troppo pieno."],
  CLICKING:    ["ATTENZIONE: clic ripetuti indicano un possibile guasto al compressore.", "Potrebbe essere il relè di avviamento — contatta un tecnico.", "Documenta la frequenza dei clic prima di chiamare l'assistenza."],
  RATTLING:    ["Controlla che non ci siano oggetti sul frigo che vibrano.", "Verifica che il frigo sia livellato (regola i piedini).", "Controlla il vassoio raccogli-acqua sotto il frigo."],
  SILENT:      ["Verifica che il frigo sia collegato e acceso.", "Potrebbe essere in ciclo di sbrinamento automatico (normale, 20–40 min).", "Se gli alimenti non sono freddi, chiama un tecnico."],
  UNKNOWN:     ["Segnale insufficiente — riprova in un ambiente più silenzioso.", "Posiziona il telefono a 20–30 cm dal frigo.", "Assicurati che il microfono non sia coperto."],
};

function classifyHealth(f) {
  const details = [];
  const scores  = { NORMAL: 0, OVERWORKING: 0, CLICKING: 0, RATTLING: 0, SILENT: 0 };

  if (f.rmsMean < 0.001) {
    details.push({ name: "Energia RMS", value: f.rmsMean.toFixed(6), text: "Nessun suono rilevato", sev: "warning" });
    return { status: "SILENT", confidence: 1.0, details };
  }
  details.push({ name: "Energia RMS", value: f.rmsMean.toFixed(5), text: "Livello sonoro presente", sev: "ok" });

  if (f.dominantFreq >= 40 && f.dominantFreq <= 150) {
    details.push({ name: "Frequenza dominante", value: f.dominantFreq.toFixed(1) + " Hz", text: "Ronzio compressore nella norma", sev: "ok" });
    scores.NORMAL += 2;
  } else if (f.dominantFreq > 150) {
    details.push({ name: "Frequenza dominante", value: f.dominantFreq.toFixed(1) + " Hz", text: "Frequenza elevata — possibile vibrazione", sev: "warning" });
    scores.RATTLING += 1.5;
  }

  const cv = f.rmsStd / (f.rmsMean + 1e-10);
  if (cv < 0.3) {
    details.push({ name: "Stabilità energetica", value: "CV=" + cv.toFixed(2), text: "Suono stabile e uniforme", sev: "ok" });
    scores.NORMAL += 1.5;
  } else if (cv < 0.7) {
    details.push({ name: "Stabilità energetica", value: "CV=" + cv.toFixed(2), text: "Leggera irregolarità energetica", sev: "warning" });
    scores.OVERWORKING += 1;
  } else {
    details.push({ name: "Stabilità energetica", value: "CV=" + cv.toFixed(2), text: "Forte irregolarità — compressore sotto stress", sev: "critical" });
    scores.OVERWORKING += 2;
  }

  const cps = f.clickCount / (f.duration + 1e-10);
  if (cps < 0.5) {
    details.push({ name: "Transitori/Clic", value: f.clickCount + " (" + cps.toFixed(1) + "/s)", text: "Nessun clic anomalo", sev: "ok" });
    scores.NORMAL += 1;
  } else if (cps < 2) {
    details.push({ name: "Transitori/Clic", value: f.clickCount + " (" + cps.toFixed(1) + "/s)", text: "Clic periodici — monitorare", sev: "warning" });
    scores.CLICKING += 1.5;
  } else {
    details.push({ name: "Transitori/Clic", value: f.clickCount + " (" + cps.toFixed(1) + "/s)", text: "Clic frequenti — possibile guasto", sev: "critical" });
    scores.CLICKING += 3;
  }

  if (f.highFreqRatio > 0.3) {
    details.push({ name: "Energia alte freq.", value: (f.highFreqRatio * 100).toFixed(1) + "%", text: "Alta energia >2 kHz — possibile vibrazione", sev: "warning" });
    scores.RATTLING += 2;
  } else {
    details.push({ name: "Energia alte freq.", value: (f.highFreqRatio * 100).toFixed(1) + "%", text: "Profilo frequenze normale", sev: "ok" });
    scores.NORMAL += 0.5;
  }

  if (f.lowFreqRatio > 0.5) {
    details.push({ name: "Energia basse freq.", value: (f.lowFreqRatio * 100).toFixed(1) + "%", text: "Buona dominanza basse frequenze", sev: "ok" });
    scores.NORMAL += 1;
  }

  if (f.zcrMean > 0.15) {
    details.push({ name: "Zero-Crossing Rate", value: f.zcrMean.toFixed(3), text: "ZCR elevato — possibile rumore", sev: "warning" });
    scores.RATTLING += 1;
  }

  const best  = Object.entries(scores).reduce((a, b) => b[1] > a[1] ? b : a)[0];
  const total = Object.values(scores).reduce((a, b) => a + b, 0) + 1e-10;
  if (scores[best] < 0.5) return { status: "UNKNOWN", confidence: 0.3, details };

  return { status: best, confidence: scores[best] / total, details };
}
