import numpy as np
import pytest

from src.analyzer import extract_features
from src.classifier import classify_health


def _sine(freq: float, duration: float = 5.0, sr: int = 22050, amp: float = 0.1) -> np.ndarray:
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_extract_features_basic():
    features = extract_features(_sine(60.0), sr=22050)
    assert features.rms_mean > 0
    assert features.dominant_freq > 0
    assert len(features.mfcc_mean) == 13
    assert 0.0 <= features.low_freq_energy_ratio <= 1.0
    assert 0.0 <= features.high_freq_energy_ratio <= 1.0


def test_duration_is_correct():
    sr = 22050
    features = extract_features(_sine(60.0, duration=10.0, sr=sr), sr=sr)
    assert abs(features.duration - 10.0) < 0.1


def test_classify_normal_60hz():
    features = extract_features(_sine(60.0, amp=0.05), sr=22050)
    status, confidence, _ = classify_health(features)
    assert status == "NORMAL"
    assert confidence > 0.3


def test_classify_silent():
    audio = np.zeros(22050 * 5, dtype=np.float32)
    features = extract_features(audio, sr=22050)
    status, _, _ = classify_health(features)
    assert status == "SILENT"


def test_high_freq_detected_as_rattling_candidate():
    features = extract_features(_sine(3500.0, amp=0.1), sr=22050)
    assert features.high_freq_energy_ratio > 0.3


def test_energy_ratios_sum_to_at_most_one():
    features = extract_features(_sine(100.0), sr=22050)
    assert features.low_freq_energy_ratio + features.high_freq_energy_ratio <= 1.0 + 1e-6
