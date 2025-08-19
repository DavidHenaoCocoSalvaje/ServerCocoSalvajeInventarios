from pydantic import BaseModel, ConfigDict
from json import loads


class Base(BaseModel):
    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)

    def update(self, **data):
        model_properties = self.model_dump().keys()
        [
            setattr(self, key, value)
            for key, value in data.items()
            if key in model_properties
        ]

    def update_from_json(self, json: str):
        dict = loads(json)
        self.update(**dict)
