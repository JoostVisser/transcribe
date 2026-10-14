from pathlib import Path

import pytest
import typer

from transcribe.cli import load_bias_terms


def test_bias_terms_skip_blanks_and_comments(tmp_path: Path) -> None:
    glossary = tmp_path / "glossary.txt"
    glossary.write_text("# places\nBriançon\n\n  Cádiz  \n")

    assert load_bias_terms(glossary, limit=10) == ["Briançon", "Cádiz"]


def test_bias_terms_over_the_limit(tmp_path: Path) -> None:
    glossary = tmp_path / "glossary.txt"
    glossary.write_text("a\nb\nc\n")

    with pytest.raises(typer.Exit):
        load_bias_terms(glossary, limit=2)
