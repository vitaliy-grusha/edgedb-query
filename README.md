# edgedb-query

Simple wrapper for edgedb python client with pydantic and anntotations.

## Installation

`pip install -e git+https://github.com/vitaliy-grusha/edgedb-query.git@main#egg=edgedbquery`

## Usage example

### Models definitions

```python
from __future__ import annotations

from functools import cached_property
from datetime import datetime
from typing import Optional, List
from uuid import UUID

import edgedb
from edgedbquery import Query, QueryMethod, Model, LazyModel

client = edgedb.blocking_client.create_client(...)


class User(Model):

    id: UUID
    email: str
    update_datetime: datetime
    create_datetime: datetime

    class EdgeDB:
        query_required_fields = """
            id,
            email,
            update_datetime,
            create_datetime
        """

    @classmethod
    def get_by_id(cls, _id: UUID):

        return (
            Query(client, QueryMethod.SINGLE_REQUIRED)
            .make(
                f"""
                SELECT User {{
                    {cls.EdgeDB.query_required_fields}
                }}
                FILTER .id = <uuid>$id
                """,
                id=_id,
            )
            .parse(User)
        )

    @classmethod
    def create(cls, email: str):
        return (
            Query(client, QueryMethod.SINGLE_REQUIRED)
            .make(
                f"""
                SELECT (
                    INSERT User {{
                        email := <str>$email,
                        update_datetime := std::datetime_current(),
                        create_datetime := std::datetime_current()
                    }}
                ) {{
                    {cls.EdgeDB.query_required_fields}
                }}
                """,
                email=email,
            )
            .parse(User)
        )

class EntityLazy(LazyModel):
    @cached_property
    def lazy(self):
        return Entity.get_by_id(self.id)


class Entity(Model):

    id: UUID
    user: User
    parent: Optional[EntityLazy] = None
    title: str
    update_datetime: datetime
    create_datetime: datetime

    class EdgeDB:
        query_required_fields = f"""
            id,
            title,
            user: {{
                {User.EdgeDB.query_required_fields}
            }},
            parent: {{
                id
            }},
            update_datetime,
            create_datetime
        """

    @classmethod
    def get_by_id(cls, _id: UUID):

        return (
            Query(client, QueryMethod.SINGLE_REQUIRED)
            .make(
                f"""
                SELECT Entity {{
                     {cls.EdgeDB.query_required_fields}
                }}
                FILTER .id = <uuid>$id
                """,
                id=_id,
            )
            .parse(Entity)
        )

    @classmethod
    def create(cls, title: str, user_id: UUID, parent_id: UUID = None):
        return (
            Query(client, QueryMethod.SINGLE_REQUIRED)
            .make(
                f"""
                WITH
                    user := (SELECT User filter .id = <uuid>$user_id),
                    parent := (SELECT Entity filter .id = <optional uuid>$parent_id)
                SELECT (
                    INSERT Entity {{
                        title := <str>$title,
                        user := user,
                        parent := parent,
                        update_datetime := std::datetime_current(),
                        create_datetime := std::datetime_current()
                    }}
                ) {{
                    {cls.EdgeDB.query_required_fields}
                }}
                """,
                title=title,
                user_id=user_id,
                parent_id=parent_id,
            )
            .parse(Entity)
        )

    @classmethod
    def get_all(cls):
        return (
            Query(client, QueryMethod.MULTIPLE).make(f"""
                SELECT Entity {{
                    {cls.EdgeDB.query_required_fields}
                }}
            """).parse(List[Entity])
        )
```

### Models usage

```python
user = User.create('email@email.com') # Returns User model
entity = Entity.create('Title', user.id) # Returns Entity model
print(entity.user)

entity_child = Entity.create('Title child', user.id, entity.id)
print(entity_child.parent.lazy) # Runs a new query to return parent entity and caches it

entities = Entity.get_all() # Returns List[Entity]
print(entities) 
```
