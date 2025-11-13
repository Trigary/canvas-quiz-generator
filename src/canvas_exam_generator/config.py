from pathlib import Path

from pydantic import BaseModel, model_validator


class VariantConfig(BaseModel):
    """Represents one quiz variant with placeholders and answer fields."""

    placeholders: dict[str, str]
    answer_fields: dict[str, str]


class GeneratorConfig(BaseModel):
    """Top-level config model holding all variants."""

    variants: list[VariantConfig]

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
        """Load and parse config JSON file."""
        json_string = path.read_text()
        return GeneratorConfig.model_validate_json(json_string)
