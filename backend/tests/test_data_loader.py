"""Tests for data_loader.py - verifies all acts and QA files load correctly."""


def test_load_all_acts_returns_nonempty(sample_acts):
    assert len(sample_acts) > 0


def test_load_all_acts_contains_expected_acts(sample_acts):
    act_names = {s.act for s in sample_acts}
    expected = {"IPC", "CRPC", "CPC", "IEA", "HMA", "IDA", "MVA", "NIA"}
    assert expected.issubset(act_names)


def test_load_all_acts_sections_have_required_fields(sample_acts):
    for sec in sample_acts[:50]:  # Check first 50
        assert sec.act is not None
        assert isinstance(sec.title, str)
        assert isinstance(sec.text, str)


def test_load_all_acts_ipc_has_sections(sample_acts):
    ipc_sections = [s for s in sample_acts if s.act == "IPC"]
    assert len(ipc_sections) > 0
    # IPC sections should have section numbers
    has_section = any(s.section is not None for s in ipc_sections)
    assert has_section


def test_load_all_acts_hma_parses(sample_acts):
    hma_sections = [s for s in sample_acts if s.act == "HMA"]
    # Should have at least some valid HMA records
    assert len(hma_sections) > 0


def test_load_all_qa_returns_nonempty(sample_qa):
    assert len(sample_qa) > 0


def test_load_all_qa_contains_expected_sources(sample_qa):
    sources = {qa.source for qa in sample_qa}
    expected = {"CONSTITUTION_QA", "CRPC_QA", "IPC_QA"}
    assert expected.issubset(sources)


def test_load_all_qa_pairs_have_content(sample_qa):
    for qa in sample_qa[:50]:
        assert len(qa.question) > 0
        assert len(qa.answer) > 0
