from dataclasses import dataclass
from typing import List

from src.analyzer import AudioFeatures


@dataclass
class ClassificationDetail:
    indicator: str
    value: str
    assessment: str
    severity: str  # "ok" | "warning" | "critical"


HEALTH_STATUSES = {
    "NORMAL": "Frigo in buono stato — funzionamento regolare",
    "OVERWORKING": "Frigo sotto stress — compressore in sovraccarico",
    "CLICKING": "Problema rilevato — rumori anomali (clic/scatti)",
    "RATTLING": "Problema rilevato — vibrazioni anomale",
    "SILENT": "Compressore spento — potrebbe essere normale o guasto",
    "UNKNOWN": "Stato indeterminato — segnale insufficiente",
}


def classify_health(
    features: AudioFeatures,
) -> tuple[str, float, List[ClassificationDetail]]:
    details: List[ClassificationDetail] = []
    scores = {
        "NORMAL": 0.0,
        "OVERWORKING": 0.0,
        "CLICKING": 0.0,
        "RATTLING": 0.0,
        "SILENT": 0.0,
    }

    # Silence check — early exit so trivially-true checks don't pollute scores
    if features.rms_mean < 0.001:
        details.append(ClassificationDetail(
            indicator="Energia RMS",
            value=f"{features.rms_mean:.6f}",
            assessment="Nessun suono rilevato",
            severity="warning",
        ))
        return "SILENT", 1.0, details

    details.append(ClassificationDetail(
        indicator="Energia RMS",
        value=f"{features.rms_mean:.5f}",
        assessment="Livello sonoro presente",
        severity="ok",
    ))

    # Dominant frequency: healthy compressor hum is 40–150 Hz
    if 40 <= features.dominant_freq <= 150:
        details.append(ClassificationDetail(
            indicator="Frequenza dominante",
            value=f"{features.dominant_freq:.1f} Hz",
            assessment="Ronzio compressore nella norma",
            severity="ok",
        ))
        scores["NORMAL"] += 2.0
    elif features.dominant_freq > 150:
        details.append(ClassificationDetail(
            indicator="Frequenza dominante",
            value=f"{features.dominant_freq:.1f} Hz",
            assessment="Frequenza elevata — possibile vibrazione anomala",
            severity="warning",
        ))
        scores["RATTLING"] += 1.5

    # Energy stability (coefficient of variation)
    cv = features.rms_std / (features.rms_mean + 1e-10)
    if cv < 0.3:
        details.append(ClassificationDetail(
            indicator="Stabilità energetica",
            value=f"CV={cv:.2f}",
            assessment="Suono stabile e uniforme",
            severity="ok",
        ))
        scores["NORMAL"] += 1.5
    elif cv < 0.7:
        details.append(ClassificationDetail(
            indicator="Stabilità energetica",
            value=f"CV={cv:.2f}",
            assessment="Leggera irregolarità energetica",
            severity="warning",
        ))
        scores["OVERWORKING"] += 1.0
    else:
        details.append(ClassificationDetail(
            indicator="Stabilità energetica",
            value=f"CV={cv:.2f}",
            assessment="Forte irregolarità — compressore sotto stress",
            severity="critical",
        ))
        scores["OVERWORKING"] += 2.0

    # Click / transient rate
    clicks_per_sec = features.click_count / (features.duration + 1e-10)
    if clicks_per_sec < 0.5:
        details.append(ClassificationDetail(
            indicator="Transitori/Clic",
            value=f"{features.click_count} ({clicks_per_sec:.1f}/s)",
            assessment="Nessun clic anomalo",
            severity="ok",
        ))
        scores["NORMAL"] += 1.0
    elif clicks_per_sec < 2.0:
        details.append(ClassificationDetail(
            indicator="Transitori/Clic",
            value=f"{features.click_count} ({clicks_per_sec:.1f}/s)",
            assessment="Possibili clic periodici — monitorare",
            severity="warning",
        ))
        scores["CLICKING"] += 1.5
    else:
        details.append(ClassificationDetail(
            indicator="Transitori/Clic",
            value=f"{features.click_count} ({clicks_per_sec:.1f}/s)",
            assessment="Clic frequenti — possibile guasto al compressore",
            severity="critical",
        ))
        scores["CLICKING"] += 3.0

    # High-frequency energy (rattling / vibrations)
    if features.high_freq_energy_ratio > 0.3:
        details.append(ClassificationDetail(
            indicator="Energia alte frequenze",
            value=f"{features.high_freq_energy_ratio:.1%}",
            assessment="Elevata energia >2 kHz — possibile vibrazione",
            severity="warning",
        ))
        scores["RATTLING"] += 2.0
    else:
        details.append(ClassificationDetail(
            indicator="Energia alte frequenze",
            value=f"{features.high_freq_energy_ratio:.1%}",
            assessment="Profilo frequenze nella norma",
            severity="ok",
        ))
        scores["NORMAL"] += 0.5

    # Low-frequency dominance (healthy hum has strong low-freq content)
    if features.low_freq_energy_ratio > 0.5:
        details.append(ClassificationDetail(
            indicator="Energia basse frequenze",
            value=f"{features.low_freq_energy_ratio:.1%}",
            assessment="Buona dominanza basse frequenze — tipico del compressore sano",
            severity="ok",
        ))
        scores["NORMAL"] += 1.0

    # ZCR — high values indicate noise or clicking
    if features.zcr_mean > 0.15:
        details.append(ClassificationDetail(
            indicator="Zero-Crossing Rate",
            value=f"{features.zcr_mean:.3f}",
            assessment="ZCR elevato — possibile rumore ad alta frequenza",
            severity="warning",
        ))
        scores["RATTLING"] += 1.0

    best = max(scores, key=scores.get)
    total = sum(scores.values()) + 1e-10

    if scores[best] < 0.5:
        return "UNKNOWN", 0.3, details

    return best, float(scores[best] / total), details
