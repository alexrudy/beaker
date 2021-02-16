import os.path
from pathlib import Path
from typing import Iterator
from typing import List
from typing import Optional
from typing import Protocol
from typing import Set
from typing import Union

import pkg_resources
from flask import Flask
from flask_logging import configure_logging
from flask_logging import setup_null_handler
from werkzeug.utils import find_modules
from werkzeug.utils import import_string

__all__ = ["create_app"]


class Plugin(Protocol):
    def init_app(self, app: Flask) -> None:
        ...


def init_logging() -> None:
    # Must do this twice to really fool flask-alembic
    setup_null_handler("alembic")
    setup_null_handler("alembic")
    setup_null_handler("sqlalchemy")


init_logging()


def initalize_logging(app: Flask) -> None:
    """Setup logging using implied configuration"""
    default_logging_path = pkg_resources.resource_filename(
        app.import_name, os.path.join("data", "logging", "defaults.yml")
    )
    if os.path.exists(default_logging_path):
        configure_logging(Path(default_logging_path))

    env_logging_path = os.path.join(app.instance_path, "config", "logging", f"{app.env!s}.yml")
    if os.path.exists(env_logging_path):
        configure_logging(Path(env_logging_path))

    if "LOGGING" in app.config:
        configure_logging(app.config["LOGGING"])


def initalize_plugins(app: Flask, plugins: List[Plugin]) -> None:
    """Initialize registered plugins"""
    logger = app.logger.getChild("init")
    for plugin in plugins:
        if hasattr(plugin, "init_app"):
            logger.debug(f"Initializing plugin {plugin!r}")
            plugin.init_app(app)


DEFAULT_EXCLUDE_MODULES = {"wsgi", "celery", "schema"}
DEFAULT_PRIORITY_MODULES = {"models"}


def _iterate_modules(
    root: str, excludes: Set[str] = DEFAULT_EXCLUDE_MODULES, priority: Set[str] = DEFAULT_PRIORITY_MODULES
) -> Iterator[str]:

    modules = []

    for module in find_modules(root, include_packages=True, recursive=True):
        if any(exclude in module.split(".") for exclude in excludes):
            continue

        elif any(pri in module.split(".") for pri in priority):
            yield module
        else:
            modules.append(module)

    yield from modules


def initalize_modules(app: Flask, root: Optional[str] = None) -> None:
    """
    Initialize `root` modules via iteration.

    Iterates through all modules and finds `init_app` functions to initialize applications.
    Iteration is recrusive, and starts from the `root` module, defaulting to "pynab"
    """
    logger = app.logger.getChild("init")

    root = root or app.import_name

    for name in _iterate_modules(root=root):
        mod = import_string(name)
        if hasattr(mod, "init_app"):
            logger.debug(f"Initializing {name}")
            mod.init_app(app)


def get_instance_root(filename) -> str:
    # <root>/src|lib?/package/module.py
    parts = os.path.normpath(os.path.dirname(filename)).split(os.path.sep)
    if parts[-2] in ("src", "lib"):
        instance_parts = parts[:-2]
    else:
        instance_parts = parts[:-1]
    return os.path.sep + os.path.join(*instance_parts)


def create_app(
    name: str,
    plugins: Optional[List[Plugin]] = None,
    instance_path: Optional[Union[os.PathLike, str]] = "instance",
    filename: Optional[str] = None,
) -> Flask:
    """Set up a flask app"""

    # Ensure that pynab has a logger during configuration, to prevent FLASK from adding its own.
    setup_null_handler(name)

    instance_root = get_instance_root(filename or __file__)
    if instance_path is None:
        instance_path = instance_root
    else:
        instance_path = os.path.join(instance_root, instance_path)
    instance_path = os.path.abspath(instance_path)
    app = Flask(name, instance_relative_config=True, instance_path=instance_path)

    defaults = os.path.abspath(pkg_resources.resource_filename(name, "data/config/defaults.cfg"))
    app.config.from_pyfile(defaults)

    env_defaults = os.path.abspath(pkg_resources.resource_filename(name, f"data/config/{app.env!s}.cfg"))
    try:
        app.config.from_pyfile(env_defaults)
    except FileNotFoundError:
        pass

    try:
        filename = os.path.join(app.instance_path, "config", f"{app.env!s}.cfg")
        app.config.from_pyfile(filename)
    except FileNotFoundError as e:
        msg = f"Can't load configuration file: {e!s}"
        print(msg)
        app.logger.exception(msg)

    for key in os.environ:
        if key in app.config:
            app.logger.debug(f"Environmnet variable is overriding {key}")
            app.config[key] = os.environ[key]

    initalize_logging(app)

    initalize_plugins(app, plugins)
    initalize_modules(app)

    return app
