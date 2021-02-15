import os.path
from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from packaging.version import parse as parse_version
from sqlalchemy.engine.url import make_url


def _get_fsqla_version() -> Optional[str]:
    """Safely grab the Flask-SQLAlchemy version identifier"""
    try:
        from flask_sqlalchemy import __version__

        return __version__
    except (ImportError, NameError):
        return None


def _fsqla_requires_sqlite_fix() -> bool:
    """Detect if we should fix the SQLite path to be relative to the app.instance_path

    Flask-SQLAlchemy < 3 uses sqlite relative to app.root_dir, but it should
    be app.instance_path. See https://github.com/pallets/flask-sqlalchemy/pull/537"""

    fsqla_version = _get_fsqla_version()
    if fsqla_version is None:
        return True
    return parse_version(fsqla_version) < parse_version("3.0")


def initialize_sqlalchemy_uri(app: Flask) -> None:
    """Set up a custom scheme for the SQLALCHEMY database URI components"""

    uri = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    for name in ("database", "drivername", "host", "password", "port", "query", "username"):
        config_name = f"SQLALCHEMY_DATABASE_{name.upper()}"
        if config_name in app.config:
            setattr(uri, name, app.config[config_name])

    if "SQLALCHEMY_DATABASE_NAME" in app.config:
        uri.database = app.config["SQLALCHEMY_DATABASE_NAME"]

    if (
        uri.drivername == "sqlite"
        and uri.database not in (":memory:", "", None)
        and not os.path.isabs(uri.database)
        and _fsqla_requires_sqlite_fix()
    ):
        uri.database = os.path.abspath(os.path.join(app.instance_path, uri.database))

    app.config["SQLALCHEMY_DATABASE_URI"] = str(uri)
    uri = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    app.logger.getChild("db").debug(f"Connection to {uri!r}")


class SQLAlchemyPlugin(SQLAlchemy):
    def init_app(self, app: Flask) -> None:
        initialize_sqlalchemy_uri(app)
        return super().init_app(app)
