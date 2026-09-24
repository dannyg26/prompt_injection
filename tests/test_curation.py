import pytest

from injection_lab.curation import collapse, components, cross_split_edges, split_rows
from injection_lab.data import assert_disjoint


def example(i, text, label):
    return {"id": str(i), "text": text, "label": label, "source": "fixture", "split": "train"}


def test_transitive_components():
    assert components(4, {(0, 1), (1, 2)}) == [[0, 1, 2], [3]]


def test_conflicting_component_is_quarantined_not_relabelled():
    rows = [
        example(0, "same content", 0),
        example(1, "same content", 1),
        example(2, "unrelated record", 0),
    ]
    retained, ledger, quarantine = collapse(rows, {(0, 1)})
    assert [r["id"] for r in retained] == ["2"]
    assert {r["label"] for r in quarantine} == {0, 1}
    assert ledger[0]["label_conflict"]
    assert ledger[0]["representative_id"] is None


def test_representative_independent_of_previous_split():
    rows = [
        example(0, "The meeting begins at noon.", 0),
        example(1, "The meeting begins at noon!", 0),
    ]
    chosen, _, _ = collapse(rows, {(0, 1)})
    swapped = [dict(r, split="test") for r in rows]
    second, _, _ = collapse(swapped, {(0, 1)})
    assert chosen[0]["id"] == second[0]["id"]


def test_cosine_cross_split_detects_duplicate():
    rows = [
        example(0, "The library opens at noon", 0),
        dict(example(1, "THE LIBRARY OPENS AT NOON", 0), split="validation"),
        dict(example(2, "A completely unrelated sentence", 1), split="test"),
    ]
    assert any({a, b} == {"0", "1"} for a, b, _ in cross_split_edges(rows))


def test_split_disjoint_and_reproducible():
    rows = [dict(example(i, f"unique record {i}", i % 2), group_id=f"group-{i}") for i in range(40)]
    first = split_rows(rows, 42)
    assert first == split_rows(rows, 42)
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        assert_disjoint(
            [r for r in first if r["split"] == a], [r for r in first if r["split"] == b], f"{a}/{b}"
        )
    assert {r["id"] for r in first} == {r["id"] for r in rows}


def test_group_validation_rejects_cross_split_template():
    with pytest.raises(ValueError, match="Group leakage"):
        assert_disjoint(
            [dict(example(0, "one template version", 0), group_id="shared")],
            [dict(example(1, "another version", 0), group_id="shared")],
            "a/b",
        )
