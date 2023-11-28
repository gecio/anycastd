from typing import Self, final

from pydantic import BaseModel


class SubConfiguration(BaseModel):
    """The base class from which all sub-configuration classes must inherit."""

    @final
    @classmethod
    def required_fields(cls) -> tuple[str, ...]:
        """Get the required fields of the sub-configuration.

        Returns:
            A tuple containing the names of required fields.
        """
        return tuple(cls.model_json_schema()["required"])

    @final
    @classmethod
    def from_configuration(cls, config: str | dict) -> Self:
        """Create an instance from the configuration format.

        The configuration can be provided in two formats, a simplified format
        containing the only required field as a string if the sub-configuration
        only has one required field, or a full format containing all required
        fields in form of a dictionary.

        Args:
            config: A dictionary containing all required fields or a string containing
                the only required field, if only a single field is required.

        Returns:
            A new SubConfiguration instance.

        Raises:
            ValidationError: Failed to validate the configuration.
            TypeError: The configuration has an invalid type.
        """
        multiple_fields_required = len(cls.required_fields()) > 1

        match config:
            case str() if not multiple_fields_required:
                return cls.model_validate({cls.required_fields()[0]: config})
            case dict():
                return cls.model_validate(config)

        msg = (
            f"Invalid configuration type {type(config)} for {cls.__name__}: "
            "Expecting a dictionary containing the {} {}".format(
                "fields" if multiple_fields_required else "field",
                ", ".join(cls.required_fields()),
            )
        )
        if not multiple_fields_required:
            msg += " or a string containing the {}".format(cls.required_fields()[0])
        raise TypeError(msg)
