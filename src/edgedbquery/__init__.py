from enum import Enum
from functools import cached_property
from typing import Type, TypeVar
from uuid import UUID
from ujson import loads  # pylint: disable=no-name-in-module
from pydantic import BaseModel, parse_raw_as
from edgedb.blocking_client import Client
from edgedb.errors import ClientConnectionFailedError

T = TypeVar("T")  # pylint: disable=invalid-name


class QueryMethod(Enum):
    MULTIPLE = 1
    SINGLE = 2
    SINGLE_REQUIRED = 3
    EXECUTE = 4


class Query:
    def __init__(self, client: Client, method: QueryMethod = QueryMethod.MULTIPLE):

        if isinstance(client, Client) is False:
            raise ValueError("Client is incorrect.")
        if isinstance(method, QueryMethod) is False:
            raise ValueError("Method is incorrect.")

        self._client = client
        self._method = method
        self._result: str | None = None

    def make(self, query: str, *args, **kwargs):
        try:
            return self._make(query, *args, **kwargs)
        except ClientConnectionFailedError:
            # Retry once if connection failed
            return self._make(query, *args, **kwargs)

    def _make(self, query: str, *args, **kwargs):
        if self._method == QueryMethod.MULTIPLE:
            self._result = self._client.query_json(query, *args, **kwargs)
        elif self._method == QueryMethod.SINGLE:
            self._result = self._client.query_single_json(query, *args, **kwargs)
        elif self._method == QueryMethod.SINGLE_REQUIRED:
            self._result = self._client.query_required_single_json(
                query, *args, **kwargs
            )
        elif self._method == QueryMethod.EXECUTE:
            self._result = self._client.execute(query)
        return self

    def parse(self, type_: Type[T]) -> T:
        if self._result is None:
            raise ValueError("Query result is emtpy.")

        if self._result == "null":
            self._result = None

        return parse_raw_as(type_, self._result, json_loads=loads)


class Model(BaseModel):
    class EdgeDB:
        query_required_fields: str | None = None


class LazyModel(BaseModel):

    id: UUID

    class Config:
        keep_untouched = (cached_property,)

    @cached_property
    def lazy(self):
        raise NotImplementedError
