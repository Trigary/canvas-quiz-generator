import argparse
import logging
from pathlib import Path
import re
import shutil
import sys
import traceback

from canvas_exam_generator.config import GeneratorConfig
from canvas_exam_generator.logic import handle_variant, quiz_str_list_to_bank


_logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable more logging.")
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        action="append",
        type=Path,
        help="Path to the quiz description. (Supported formats: .md, .txt, .html)",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        action="append",
        type=Path,
        help="Path to the JSON configuration file containing placeholders, answers, etc.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Path to the empty directory where generated quizzes should be be placed.",
    )
    parser.add_argument(
        "--clear-output-dir",
        action="store_true",
        help="Deletes the contents of the output directory if it is not empty.",
    )
    parser.add_argument(
        "--bank-name", default="quiz_bank", help="Question bank name to use in Canvas and for the generated files."
    )
    args = parser.parse_args()
    if len(args.input) != len(args.config):
        parser.error("You must provide the same number of --input and --config arguments.")

    logging.basicConfig(
        force=True,
        level="DEBUG" if args.verbose else "INFO",
        format="%(levelname)s [%(name)s] %(message)s" if args.verbose else "%(message)s",
        stream=sys.stdout,
    )

    for input in args.input:
        if not input.exists() or not input.is_file():
            _logger.error("The specified input file does not exist: '%s'", input)
            exit(-1)

    configs = []  # Parsed configurations and the path they were loaded from
    for config in args.config:
        if not config.exists() or not config.is_file():
            _logger.error("The specified configuration file does not exist: '%s'", config)
            exit(-1)
        try:
            _logger.debug("Loading configuration file '%s'...", config)
            configs.append((GeneratorConfig.load_from_json(config), config))
        except Exception as e:
            _logger.debug("Exception caught when loading configuration", exc_info=True)
            _logger.error("Failed to load configuration file: %s", traceback.format_exception_only(e)[0].strip())
            exit(-1)

    if not re.match(r"^[a-zA-Z0-9\._-]+$", args.bank_name):
        _logger.error("The specified bank name (%s) is not valid. Please don't use special characters.")
        exit(-1)

    if args.clear_output_dir and args.output.exists() and args.output.is_dir():
        shutil.rmtree(args.output)

    if args.output.exists():
        if not args.output.is_dir():
            _logger.error("The specified output path is not a directory: '%s'", args.output)
            exit(-1)
        if any(args.output.iterdir()):
            _logger.error("The specified output directory is not empty: '%s'", args.output)
            exit(-1)
    else:
        args.output.mkdir(parents=True, exist_ok=True)

    try:
        _logger.debug("Generating quizzes...")
        execute_logic(list(zip(args.input, configs)), args.output, args.bank_name)
    except Exception as e:
        _logger.debug("Exception caught when generating quizzes", exc_info=True)
        _logger.error("Failed to generate quizzes: %s", traceback.format_exception_only(e)[0].strip())
        exit(-1)


def execute_logic(
    input_config_pairs: list[tuple[Path, tuple[GeneratorConfig, Path]]], output_dir: Path, bank_name: str
) -> None:
    quizzes = []
    for input, config in input_config_pairs:
        input_name, config_name = input.name, config[1].name

        _logger.debug("Processing input '%s' with configuration '%s'...", input_name, config_name)
        for variant_num, variant in enumerate(config[0].variants, start=1):
            _logger.debug("Processing variant #%d: %s", variant_num, variant)
            quizzes.append(handle_variant(variant, input, output_dir))

        _logger.info(
            "Processed %s - %s pair and generated %d quizzes.",
            input_name,
            config_name,
            len(config[0].variants),
        )

    quiz_str_list_to_bank(quizzes, output_dir, bank_name)
    _logger.info("A quiz bank containing %d quizzes has been created in the '%s' directory.", len(quizzes), output_dir)


if __name__ == "__main__":
    main()
