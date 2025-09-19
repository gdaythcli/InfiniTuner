import json
from copy import deepcopy
from typing import Optional, Type, Any, Tuple, List, Union
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


def make_field_optional(model: Type[BaseModel]):
    '''
    Function to make all the fields in the model optional. Works with nested models.
    Source: https://stackoverflow.com/questions/67699451/make-every-field-as-optional-with-pydantic/

    Parameters:
    - model (Type[BaseModel]): The model to make optional

    Returns:
    - model (Type[BaseModel]): The model with all fields optional
    '''
    def convert_to_optional(field: FieldInfo, default: Any = None) -> Tuple[Any, FieldInfo]:
        '''
        Function to convert a field to optional

        Parameters:
        - field (FieldInfo): The field to convert
        - default (Any): The default value

        Returns:
        - Tuple[Any, FieldInfo]: The converted field
        '''
        new = deepcopy(field)
        new.default = default

        # If the field annotation is a subclass of BaseModel, recursively make its fields optional.
        field_type = field.annotation
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            field_type = make_field_optional(field_type)

        # Update the annotation to be optional
        new.annotation = Union[field_type, type(None)]  # type: ignore
        return new.annotation, new
    
    return create_model(
        f'Optional{model.__name__}',
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: convert_to_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        }
    )
