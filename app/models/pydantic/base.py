from pydantic import BaseModel, ConfigDict, model_validator
from json import loads


class Base(BaseModel):
    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)

    @model_validator(mode='before')
    def remove_none_values(cls, data):
        return {k: v for k, v in data.items() if v is not None}

    def update(self, **data):
        model_properties = self.model_dump().keys()
        [setattr(self, key, value) for key, value in data.items() if key in model_properties]
        return self

    def update_from_json(self, json: str):
        dict = loads(json)
        self.update(**dict)
        return self
