import logging
import os
from pathlib import Path
import subprocess

from canvas_quiz_generator import qtiConverterApp
from canvas_quiz_generator.config import VariantConfig


_logger = logging.getLogger(__name__)


def quiz_str_list_to_bank(quizzes: list[str], output_dir: Path, bank_name: str) -> None:
    """Aggregates a list of text-format quizzes into a shared quiz bank."""
    _logger.debug("Generated %d quiz variants, creating quiz bank...", len(quizzes))
    quiz_bank_txt = output_dir / f"{bank_name}.txt"
    with quiz_bank_txt.open("w", encoding="utf-8") as f:
        for quiz in quizzes:
            f.write(quiz)

    _logger.debug("Quiz bank created at '%s', converting to QTI ZIP...", quiz_bank_txt)
    qti_maker = qtiConverterApp.makeQti(str(quiz_bank_txt), ".")
    qti_maker.run()
    _logger.debug("Quiz bank ZIP created at '%s'", qti_maker.newDirPath.with_suffix(".zip"))


def generate_variant(config: VariantConfig, input: Path, output_dir: Path) -> str:
    """
    Generates a single quiz variant based on the provided config and input file.
    The output directory might be used as a working directory for intermediate files.
    """
    intermediate_file = output_dir / f"{input.name}.html"
    if input.suffix == ".md":
        _execute_format_conversion_pandoc(input, intermediate_file)
    elif input.suffix != ".html":
        _execute_format_conversion_newline(input, intermediate_file)
    else:
        intermediate_file = input

    quiz_description = intermediate_file.read_text()
    quiz_description = _replace_placeholders(config, quiz_description)
    return _to_canvas_quiz_str(config, quiz_description)


def _execute_format_conversion_pandoc(input: Path, output: Path) -> None:
    """
    Executes the format conversion using the 'pandoc' command.
    The input and output file formats are determined by the file extensions.
    """
    try:
        cmd = ["pandoc", "-o", str(output), str(input)]
        _logger.debug("Executing format conversion: %s", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        raise RuntimeError("The 'pandoc' command couldn't be found, markdown format cannot be converted.") from e

    _logger.debug("Pandoc output:")
    _logger.debug("  Exit code: %d", proc.returncode)
    _logger.debug("  stdout: %s", proc.stdout.strip())
    _logger.debug("  stderr: %s", proc.stderr.strip())

    if proc.returncode != 0:
        raise RuntimeError(
            f"The 'pandoc' command returned with exit code {proc.returncode} and the following stderr: {proc.stderr.strip()}"
        )


def _execute_format_conversion_newline(input: Path, output: Path) -> None:
    """
    Handles newline conversion for text files: the text-format quizzes can't contain line breaks,
    therefore they are replaced with HTML line break tags.
    """
    with input.open("r", encoding="utf-8") as fin, output.open("w", encoding="utf-8") as fout:
        for line in fin:
            fout.write(line.rstrip("\r\n") + "<br>")


def _replace_placeholders(config: VariantConfig, quiz_description: str) -> str:
    """
    Executes the placeholder replacement in the quiz description.
    A warning is logged if a placeholder is not found in the description.
    """
    for placeholder, value in config.placeholders.items():
        if placeholder not in quiz_description:
            _logger.warning("Placeholder '%s' not found in quiz description.", placeholder)
        quiz_description = quiz_description.replace(placeholder, value)
    return quiz_description


def _to_canvas_quiz_str(config: VariantConfig, quiz_description: str) -> str:
    """
    Converts the specified values into a text-format quiz string.
    Ane rror is logged if an answer field is not found in the quiz description.
    """
    quiz_str = "MB"
    quiz_str += os.linesep
    quiz_str += "1. " + quiz_description.replace("\r", "").replace("\n", "")
    quiz_str += os.linesep
    for answer_field, answer_value in config.answer_fields.items():
        if f"[{answer_field}]" not in quiz_description:
            _logger.error(
                "Answer field '[%s]' not found in quiz description. The student will have no way to enter the answer.",
                answer_field,
            )
        quiz_str += f"{answer_field}: {answer_value}"
        quiz_str += os.linesep
    quiz_str += os.linesep
    return quiz_str
