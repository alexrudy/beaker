import os.path
from typing import Any

from celery import Celery
from flask import Flask

from .cli import add_celery_commands


def initialize_celery(app: Flask, celery: Celery) -> None:
    """Initialize the celery application and task setup"""

    class ContextTask(celery.Task):  # type: ignore
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    celery_config_overrides = app.config.get_namespace("CELERY_")

    for key, value in os.environ.items():
        if key.startswith("CELERY_"):
            cname = key[len("CELERY_") :].lower()
            celery_config_overrides[cname] = value

    celery.conf.update(**celery_config_overrides)
    app.celery = celery

    add_celery_commands(app)


class CeleryPlugin(Celery):
    def init_app(self, app: Flask) -> None:
        initialize_celery(app, self)
