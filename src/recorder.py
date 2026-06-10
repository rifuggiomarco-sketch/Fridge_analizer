import numpy as np


def record_audio(duration: int = 15, sample_rate: int = 22050) -> tuple[np.ndarray, int]:
    try:
        import sounddevice as sd
    except ImportError:
        raise ImportError(
            "sounddevice è richiesto per la registrazione. Installa con: pip install sounddevice"
        )
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return audio.flatten(), sample_rate


def load_audio(file_path: str, sample_rate: int = 22050) -> tuple[np.ndarray, int]:
    import librosa

    audio, sr = librosa.load(file_path, sr=sample_rate, mono=True)
    return audio, sr
