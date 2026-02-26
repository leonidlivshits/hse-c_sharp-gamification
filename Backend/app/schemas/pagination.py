# app/schemas/pagination.py
from typing import Generic, TypeVar, List
from pydantic.generics import GenericModel
from pydantic import ConfigDict

T = TypeVar("T")

class Paginated(GenericModel, Generic[T]):
    total: int
    items: List[T]
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)
