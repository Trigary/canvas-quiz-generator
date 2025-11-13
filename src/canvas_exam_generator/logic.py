import logging
from pathlib import Path
import subprocess

from canvas_exam_generator import qtiConverterApp
from canvas_exam_generator.config import VariantConfig


_logger = logging.getLogger(__name__)


def quiz_str_list_to_bank(quizzes: list[str], output_dir: Path) -> None:
    _logger.debug("Generated %d quiz variants, creating quiz bank...", len(quizzes))
    quiz_bank_txt = output_dir / "quiz_bank.txt"
    _to_canvas_quiz_bank_txt(quizzes, quiz_bank_txt)

    _logger.debug("Quiz bank created at '%s', converting to QTI ZIP...", quiz_bank_txt)
    quiz_bank_zip = _to_canvas_quiz_bank_zip(quiz_bank_txt)
    _logger.debug("Quiz bank ZIP created at '%s'", quiz_bank_zip)


def handle_variant(config: VariantConfig, input: Path, output_dir: Path) -> str:
    if input.suffix == ".md":
        intermediate_file = output_dir / f"{input.name}.html"
        _convert_format_if_necessary(input, intermediate_file)
    else:
        intermediate_file = input

    quiz_description = intermediate_file.read_text()
    quiz_description = _replace_placeholders(config, quiz_description)
    return _to_canvas_quiz_str(config, quiz_description)


def _convert_format_if_necessary(input: Path, output: Path) -> None:
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


def _replace_placeholders(config: VariantConfig, quiz_description: str) -> str:
    for placeholder, value in config.placeholders.items():
        if placeholder not in quiz_description:
            _logger.warning("Placeholder '%s' not found in quiz description.", placeholder)
        quiz_description = quiz_description.replace(placeholder, value)
    return quiz_description


def _to_canvas_quiz_str(config: VariantConfig, quiz_description: str) -> str:
    quiz_str = "MB\n"
    quiz_str += "1. " + quiz_description.replace("\r", "").replace("\n", "<br>")
    quiz_str += "\r"
    for answer_field, answer_value in config.answer_fields.items():
        if f"[{answer_field}]" not in quiz_description:
            _logger.error(
                "Answer field '[%s]' not found in quiz description. The student will have no way to enter the answer.",
                answer_field,
            )
        quiz_str += f"{answer_field}: {answer_value}\r"
    quiz_str += "\r"
    return quiz_str


def _to_canvas_quiz_bank_txt(quizzes: list[str], output: Path) -> None:
    with output.open("w", encoding="utf-8") as f:
        for quiz in quizzes:
            f.write(quiz)


def _to_canvas_quiz_bank_zip(quiz_bank_txt: Path) -> Path:
    qti_maker = qtiConverterApp.makeQti(str(quiz_bank_txt), ".")
    qti_maker.run()
    return qti_maker.newDirPath.with_suffix(".zip")
