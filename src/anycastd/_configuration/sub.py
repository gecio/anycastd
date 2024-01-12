from typing import Self, final

from pydantic import BaseModel, ValidationError

from anycastd._configuration.exceptions import ConfigurationSyntaxError


class SubConfiguration(BaseModel, extra="forbid"):
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
            ConfigurationSyntaxError: The configuration data has an invalid syntax.
        """
        required_fields = cls.required_fields()

        match config:
            case str() if len(required_fields) <= 1:
                config = {required_fields[0]: config}
            case str():
                raise ConfigurationSyntaxError.from_invalid_simple_format(
                    cls.__name__, required_fields
                )

        try:
            return cls.model_validate(config)
        except ValidationError as exc:
            raise ConfigurationSyntaxError.from_validation_error(exc) from exc
