import pytest
import math
from app.services.uncertainty_service import uncertainty_service

def test_calculate_metrics():
    # Mock logprobs (list of dicts)
    # log(0.9) approx -0.105
    # log(0.8) approx -0.223
    logprobs = [
        {"logprob": math.log(0.9)},
        {"logprob": math.log(0.8)}
    ]
    
    metrics = uncertainty_service.calculate_metrics(logprobs)
    
    expected_confidence = (0.9 + 0.8) / 2
    assert metrics["confidence_score"] == pytest.approx(expected_confidence)
    
    # Entropy = -log_prob (NLL approximation here)
    expected_entropy = (-math.log(0.9) - math.log(0.8)) / 2
    assert metrics["entropy"] == pytest.approx(expected_entropy)

def test_is_hallucination():
    assert uncertainty_service.is_hallucination(0.6, threshold=0.7) is True
    assert uncertainty_service.is_hallucination(0.8, threshold=0.7) is False
