"""Unit tests for Synthetic Dataset Generator."""

from __future__ import annotations

from data.generator import AgencyDataGenerator


def test_generator_reproducibility() -> None:
    gen1 = AgencyDataGenerator(seed=123)
    data1 = gen1.generate(n_samples=25)

    gen2 = AgencyDataGenerator(seed=123)
    data2 = gen2.generate(n_samples=25)

    assert data1 == data2, "Generator produced divergent outputs with identical seed."


def test_generator_irregularities_injected() -> None:
    gen = AgencyDataGenerator(seed=999)
    data = gen.generate(n_samples=100, irregularity_rate=0.30)

    assert data["sample_count"] == 100
    assert data["irregular_sample_count"] > 0
    # Confirm some irregular samples contain None in their features
    has_none = any(
        any(v is None for v in org["features"].values())
        for org in data["organisations"]
        if org["is_irregular"]
    )
    assert has_none, "Expected irregular organisations to contain missing features."
