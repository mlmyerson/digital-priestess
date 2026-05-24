from app.persona.prompts import build_system_prompt, list_modes


def test_modes_include_aelira_only() -> None:
    mode_ids = {mode.id for mode in list_modes()}

    assert mode_ids == {"aelira"}


def test_aelira_prompt_keeps_grounding_rules_and_file_references() -> None:
    prompt = build_system_prompt("aelira")

    assert "provided archive passages" in prompt
    assert "citation markers" in prompt
    assert "titles, paths, and line ranges" in prompt
    assert "Mode:" not in prompt