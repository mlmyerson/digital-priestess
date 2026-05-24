from app.persona.prompts import build_system_prompt, list_modes


def test_modes_include_archivist_and_priestess() -> None:
    mode_ids = {mode.id for mode in list_modes()}

    assert mode_ids == {"archivist", "priestess"}


def test_priestess_prompt_keeps_grounding_rules() -> None:
    prompt = build_system_prompt("priestess")

    assert "provided archive passages" in prompt
    assert "symbolic" in prompt.lower()