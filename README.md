# Canvas Exam Generator

A tool that creates multiple variants from a Canvas quiz description using a JSON file containing placeholders and the correct answers.

## Usage, example

The tool can handle quiz descriptions in `.md` and `.html`, `.txt` formats.
See the [example](./example/) folder for a ready-to-execute example and more information.

```bash
$ canvas-exam-generator -i task.md -c config.json -o output_dir
A quiz bank containing 2 variants of 'task.md' has been created in the 'output_dir' directory.
```

The generated quiz variants can be found in `quiz_bank.txt`.
The `quiz_bank_export.zip` can be directly [imported into Canvas](#importing-a-quiz-bank-into-canvas).
An optional quiz bank name may be specified via the `--bank-name` argument.

The `-i` (`--input`) and `-c` (`--config`) parameters may be repeated to include multiple quiz descriptions into the same bank.
For example: `canvas-exam-generator -i task_1A.md -c config_1A.json -i task_1B.md -c config_1B.json -o output_dir`

Example quiz description (`task.md`):

```md
This is a fruit: [[FRUIT]]  
Run the provided application via: `python3 example.py --student-key [[STUDENT_KEY]]`

Paste the answers returned by the program below:  
Test 1: [SUBTASK1]  
Test 2: [SUBTASK2]
```

Example configuration file (`config.json`):

```json
{
    "variants": [
        {
            "placeholders": {
                "[[STUDENT_KEY]]": "KEY_STUDENT_SHOULD_COPY_PASTE",
                "[[FRUIT]]": "apple"
            },
            "answer_fields": {
                "SUBTASK1": "ANSWER_1",
                "SUBTASK2": "ANSWER_2"
            }
        },
        ...
    ]
}
```

Please note that placeholder keys are replaced in the quiz description as-is,
therefore it's advised to surround them with special characters (like the double brackets in the example above).
On the other hand, square brackets must be placed around the answer field names in the quiz description,
but not in the config JSON.

## Installation

Navigate to the directory containing this README file and execute the following command:

```bash
python3 -m pip install -e .
```

After installation, the tool can be invoked via `canvas-exam-generator` or `python3 -m canvas_exam_generator`.

If you do not wish to install this tool, you can try running it the following way:

```bash
PYTHONPATH=path/to/this/folder/./src python3 -m canvas_exam_generator
```

Please note that the dependencies of this tool (`pydantic`) still need to be installed.

## Importing a quiz bank into Canvas

- Open the course
- Append `content_migrations` to the URL: `https://canvas.your.domain/courses/<ID>/content_migrations`
- Select the `QTI .zip file` option, the generated `.zip` file and the creation of a new question bank
  - The name doesn't matter: it will get overwritten.
- Click import and wait for it to finish
- Navigate to the `question_banks` page: `https://canvas.your.domain/courses/<ID>/question_banks`
- Find and open the newly created question bank.
  - Rename if necessary.
  - Double-check whether everything is correct.
- Importing a quiz bank also automatically creates a new quiz. You may want to delete that.
