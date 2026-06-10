import argparse
import sys
import time

from src.recorder import load_audio, record_audio
from src.analyzer import extract_features
from src.classifier import classify_health
from src.report import generate_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fridge Health Analyzer — diagnosi stato frigo via analisi audio"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Percorso file audio (WAV/MP3). Se omesso, registra dal microfono.",
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=15,
        help="Durata registrazione in secondi (default: 15)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Salva il rapporto su file di testo",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Mostra grafico spettrale",
    )
    args = parser.parse_args()

    print("=== Fridge Health Analyzer ===\n")

    if args.file:
        print(f"Caricamento audio da: {args.file}")
        audio, sr = load_audio(args.file)
    else:
        print(f"Registrazione {args.duration}s dal microfono...")
        print("Posiziona il microfono vicino al frigo. Avvio in:")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        print("  Registrazione!\n")
        audio, sr = record_audio(duration=args.duration)
        print("  Fine registrazione.\n")

    print("Analisi audio in corso...")
    features = extract_features(audio, sr)

    print("Classificazione stato di salute...\n")
    status, confidence, details = classify_health(features)

    report = generate_report(status, confidence, details, features, args.plot)
    print(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"\nRapporto salvato in: {args.output}")

    return 0 if status in {"NORMAL", "SILENT"} else 1


if __name__ == "__main__":
    sys.exit(main())
