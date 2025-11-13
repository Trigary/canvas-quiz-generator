from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator


class VariantConfig(BaseModel):
    """Represents one quiz variant with placeholders and answer fields."""

    placeholders: dict[str, str]
    """Maps the strings that should be replaced to the values they should be replaced with."""

    answer_fields: dict[str, str]
    """Maps the question identifiers to the correct answers."""

    @field_validator("answer_fields")
    def validate_answer_fields(cls, v):
        """Ensures that neither the keys nor the values contain unsupported characters such as newlines."""
        for key, value in v.items():
            if any(c in key for c in ("\r", "\n", ":")):
                raise ValueError(f"Key '{key!r}' in 'answer_fields' contains invalid character(s).")
            if any(c in value for c in ("\r", "\n")):
                raise ValueError(f"Value '{value!r}' in 'answer_fields' contains invalid character(s).")
        return v


class GeneratorConfig(BaseModel):
    """Top-level config model holding all variants."""

    variants: list[VariantConfig]
    """The different variants that should be generated."""

    @model_validator(mode="after")
    def _validate_consistency(self) -> "GeneratorConfig":
        """Ensure every variant has the same placeholders and answer fields."""
        if len(self.variants) <= 1:
            return self

        for field in ["placeholders", "answer_fields"]:
            first_value = getattr(self.variants[0], field).keys()
            for variant in self.variants[1:]:
                current_value = getattr(variant, field).keys()
                if first_value != current_value:
                    raise ValueError(
                        f"All variants must have the same '{field}' values, "
                        f"but found different values: {first_value} != {current_value}"
                    )
        return self

    @staticmethod
    def load_from_json(path: Path) -> "GeneratorConfig":
        """Load and parse config JSON file found at the specified path."""
        json_string = path.read_text()
        return GeneratorConfig.model_validate_json(json_string)
