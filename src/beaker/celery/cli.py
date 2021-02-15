import dataclasses as dc
import os
import socket
import subprocess
from pathlib import Path
from typing import Optional

import click
from click import Context
from flask import current_app
from flask import Flask
from flask.cli import AppGroup

__all__ = ["celery", "add_celery_commands", "CeleryRC"]

celery = AppGroup("celery", help="Celery wrappers")


@dc.dataclass
class CeleryRC:
    root: Path
    hostname: str

    @classmethod
    def build(cls, hostname: Optional[str] = None, app: Optional[Flask] = None) -> "CeleryRC":
        hostname = hostname or socket.gethostname()
        app = app or current_app

        root = Path(os.path.join(app.instance_path, "data"))
        for directory in ("run", "log", "var"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        return cls(root=root, hostname=hostname)

    def directory(self, name: str) -> Path:
        path = self.root / name / self.hostname
        path.mkdir(parents=True, exist_ok=True)
        return path

    def argument(self, name: str, directory: str, filename: str) -> str:
        return f"--{name}={self.directory(directory) / filename}"


def _prepare_host_directories(hostname: str) -> str:
    root = os.path.join(current_app.instance_path, "data")

    os.makedirs(os.path.join(root, "run", hostname), exist_ok=True)
    os.makedirs(os.path.join(root, "log", hostname), exist_ok=True)
    os.makedirs(os.path.join(root, "var", hostname), exist_ok=True)

    return root


@celery.command()
@click.option("--loglevel", type=str, help="Log Level")
@click.pass_context
def worker(ctx: Context, loglevel: str) -> None:
    """Start a celery worker"""
    rc = CeleryRC.build()
    args = ["celery", "-A", "pynab.celery:celery", "worker", f"--loglevel={loglevel}"]
    args.append(rc.argument("pidfile", "run", "%n-%i.pid"))
    args.append(rc.argument("logfile", "log", "%n-%i.log"))

    r = subprocess.run(args)
    ctx.exit(r.returncode)


@celery.command()
@click.option("--loglevel", type=str, help="Log Level")
@click.pass_context
def flower(ctx: Context, loglevel: str) -> None:
    rc = CeleryRC.build()  # noqa: F841
    # TODO: What arguments do we need to pass to flower for logs etc.

    r = subprocess.run(["celery", "-A", "pynab.celery:celery", "flower", f"--loglevel={loglevel}", "--address=0.0.0.0"])
    ctx.exit(r.returncode)


@celery.command()
@click.option("--loglevel", type=str, help="Log Level")
@click.pass_context
def beat(ctx: Context, loglevel: str) -> None:
    rc = CeleryRC.build()

    args = ["celery", "-A", "pynab.celery:celery", "beat", f"--loglevel={loglevel}"]
    args.append(rc.argument("schedule", "var", "celery-beat-schedule"))
    args.append(rc.argument("pidfile", "run", "celery-beat.pid"))
    args.append(rc.argument("logfile", "log", "celery-beat.log"))
    r = subprocess.run(args)
    ctx.exit(r.returncode)


def add_celery_commands(app: Flask) -> None:
    app.cli.add_command(celery)
