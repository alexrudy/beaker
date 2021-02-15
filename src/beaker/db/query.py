"""A custom query class with a few extra methods"""
import logging
from typing import Any
from typing import Optional
from typing import TYPE_CHECKING

from flask_sqlalchemy import BaseQuery
from sqlalchemy.orm.exc import NoResultFound

if TYPE_CHECKING:
    # TODO: There might be a better way to typecheck this.
    Base = Any

log = logging.getLogger(__name__)


class Query(BaseQuery):
    def get_primary_model(self) -> Optional["Base"]:
        if not self._primary_entity:
            return None
        return self._primary_entity.type

    def get_or_create(self, **kwargs: Any) -> "Base":
        """Get or create a model object."""
        cls = self.get_primary_model()
        if cls is None:
            raise TypeError(f"Can't get or create for query {self}")

        query = self.filter_by(id=kwargs["id"])
        try:
            return query.one()
        except NoResultFound:
            item = cls(**kwargs)  # type: ignore
            log.info("Could not find %s, created new item %r", getattr(cls, "__name__", repr(cls)), item)
            self.session.add(item)
            return item

    def upsert(self, **kwargs: Any) -> "Base":
        """Insert or update a model object"""
        cls = self.get_primary_model()
        if cls is None:
            raise TypeError(f"Can't get or create for query {self}")

        query = self.filter_by(id=kwargs["id"])
        try:
            item = query.one()
        except NoResultFound:
            item = cls(**kwargs)  # type: ignore
            log.info("Could not find %s, created new item %r", getattr(cls, "__name__", repr(cls)), item)
            self.session.add(item)
        else:
            for key, value in kwargs.items():
                setattr(item, key, value)

        return item
