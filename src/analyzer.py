import numpy as np
import librosa
from dataclasses import dataclass


@dataclass
class AudioFeatures:
    rms_mean: float
    rms_std: float
    rms_max: float
    spectral_centroid_mean: float
    spectral_rolloff_mean: float
    zcr_mean: float
    zcr_std: float
    dominant_freq: float
    low_freq_energy_ratio: float   # fraction of energy below 300 Hz
    high_freq_energy_ratio: float  # fraction of energy above 2000 Hz
    mfcc_mean: np.ndarray
    click_count: int
    duration: float
    sample_rate: int


def extract_features(audio: np.ndarray, sr: int) -> AudioFeatures:
    rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
    zcr = librosa.feature.zero_crossing_rate(y=audio)[0]

    fft = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1.0 / sr)

    dominant_freq = float(freqs[np.argmax(fft)]) if len(fft) > 0 else 0.0

    total_energy = np.sum(fft**2) + 1e-10
    low_freq_energy_ratio = float(np.sum(fft[freqs < 300] ** 2) / total_energy)
    high_freq_energy_ratio = float(np.sum(fft[freqs > 2000] ** 2) / total_energy)

    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    mfcc_mean = np.mean(mfcc, axis=1)

    onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units="frames")
    click_count = int(len(onset_frames))

    return AudioFeatures(
        rms_mean=float(np.mean(rms)),
        rms_std=float(np.std(rms)),
        rms_max=float(np.max(rms)),
        spectral_centroid_mean=float(np.mean(spectral_centroid)),
        spectral_rolloff_mean=float(np.mean(spectral_rolloff)),
        zcr_mean=float(np.mean(zcr)),
        zcr_std=float(np.std(zcr)),
        dominant_freq=dominant_freq,
        low_freq_energy_ratio=low_freq_energy_ratio,
        high_freq_energy_ratio=high_freq_energy_ratio,
        mfcc_mean=mfcc_mean,
        click_count=click_count,
        duration=float(len(audio) / sr),
        sample_rate=sr,
    )
