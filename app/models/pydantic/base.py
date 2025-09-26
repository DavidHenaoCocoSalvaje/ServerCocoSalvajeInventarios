from pydantic import BaseModel, ConfigDict, model_validator


class Base(BaseModel):
    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)

    @model_validator(mode='before')
    @classmethod
    def remove_none_values(cls, data):
        return {k: v for k, v in data.items() if v is not None}
