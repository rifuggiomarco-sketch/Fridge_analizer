from datetime import datetime
from typing import List

from src.analyzer import AudioFeatures
from src.classifier import ClassificationDetail, HEALTH_STATUSES

_SEV_ICON = {"ok": "[OK]", "warning": "[!!]", "critical": "[XX]"}
_STATUS_ICON = {
    "NORMAL": "[OK]",
    "OVERWORKING": "[!!]",
    "CLICKING": "[XX]",
    "RATTLING": "[XX]",
    "SILENT": "[??]",
    "UNKNOWN": "[??]",
}
_RECOMMENDATIONS = {
    "NORMAL": [
        "Il frigo funziona normalmente.",
        "Pulisci le bobine del condensatore ogni 6–12 mesi.",
        "Continua il monitoraggio periodico.",
    ],
    "OVERWORKING": [
        "Controlla le guarnizioni delle porte — potrebbero essere deteriorate.",
        "Lascia almeno 10 cm di spazio sui lati per la ventilazione.",
        "Verifica che le bobine del condensatore non siano sporche.",
        "Il frigo potrebbe essere troppo pieno di alimenti.",
    ],
    "CLICKING": [
        "ATTENZIONE: clic ripetuti indicano un possibile problema al compressore.",
        "Potrebbe essere il relè di avviamento del compressore — contatta un tecnico.",
        "Documenta la frequenza dei clic prima di chiamare l'assistenza.",
    ],
    "RATTLING": [
        "Controlla che non ci siano oggetti sul frigo che vibrano.",
        "Verifica che il frigo sia livellato — regola i piedini se necessario.",
        "Controlla il vassoio raccogli-acqua sotto il frigo.",
        "Potrebbe essere il ventilatore del condensatore.",
    ],
    "SILENT": [
        "Verifica che il frigo sia collegato e acceso.",
        "Se gli alimenti non sono freddi, contatta subito un tecnico.",
        "Un ciclo di sbrinamento automatico in corso è normale (20–40 min).",
    ],
    "UNKNOWN": [
        "Segnale insufficiente per una diagnosi affidabile.",
        "Riprova in un ambiente più silenzioso.",
        "Posiziona il microfono a 20–30 cm dal frigo.",
    ],
}


def generate_report(
    status: str,
    confidence: float,
    details: List[ClassificationDetail],
    features: AudioFeatures,
    show_plot: bool = False,
) -> str:
    sep = "=" * 52
    thin = "-" * 52
    lines = [
        sep,
        "    RAPPORTO ANALISI SALUTE FRIGO",
        f"    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        sep,
        "",
        f"STATO:      {_STATUS_ICON.get(status, '[?]')}  {status}",
        f"            {HEALTH_STATUSES.get(status, status)}",
        f"CONFIDENZA: {confidence:.0%}",
        "",
        "INDICATORI ANALIZZATI:",
        thin,
    ]

    for d in details:
        icon = _SEV_ICON.get(d.severity, "   ")
        lines += [
            f"  {icon}  {d.indicator}",
            f"         Valore:  {d.value}",
            f"         Analisi: {d.assessment}",
        ]

    lines += [
        "",
        "DATI TECNICI:",
        thin,
        f"  Durata registrazione : {features.duration:.1f} s",
        f"  Sample rate          : {features.sample_rate} Hz",
        f"  Energia RMS media    : {features.rms_mean:.5f}",
        f"  Frequenza dominante  : {features.dominant_freq:.1f} Hz",
        f"  Centroide spettrale  : {features.spectral_centroid_mean:.1f} Hz",
        f"  Zero-crossing rate   : {features.zcr_mean:.4f}",
        f"  Energia basse freq   : {features.low_freq_energy_ratio:.1%}",
        f"  Energia alte freq    : {features.high_freq_energy_ratio:.1%}",
        f"  Transitori rilevati  : {features.click_count}",
        "",
        "RACCOMANDAZIONI:",
        thin,
    ]
    for rec in _RECOMMENDATIONS.get(status, []):
        lines.append(f"  • {rec}")

    lines += ["", sep]

    report = "\n".join(lines)

    if show_plot:
        _show_plot(features)

    return report


def _show_plot(features: AudioFeatures) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("(matplotlib non disponibile — grafico non mostrato)")
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("Analisi Spettrale Frigo", fontsize=14)

    mid_ratio = max(
        0.0,
        1.0 - features.low_freq_energy_ratio - features.high_freq_energy_ratio,
    )
    axes[0].bar(
        ["Basse\n(<300 Hz)", "Medie\n(300–2k Hz)", "Alte\n(>2k Hz)"],
        [features.low_freq_energy_ratio, mid_ratio, features.high_freq_energy_ratio],
        color=["green", "orange", "red"],
    )
    axes[0].set_title("Distribuzione Energia per Banda di Frequenza")
    axes[0].set_ylabel("Frazione Energia")
    axes[0].set_ylim(0, 1)

    axes[1].bar(range(len(features.mfcc_mean)), features.mfcc_mean, color="steelblue")
    axes[1].set_title("Coefficienti MFCC (profilo timbrico)")
    axes[1].set_xlabel("Coefficiente MFCC")
    axes[1].set_ylabel("Valore medio")

    plt.tight_layout()
    plt.show()
