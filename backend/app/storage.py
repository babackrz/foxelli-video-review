import os
import shutil
from pathlib import Path


def path(key):
    return Path(os.environ["VIDEO_DIR"]) / Path(key).name


def save(source, key):
    destination = path(key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def delete(key):
    path(key).unlink(missing_ok=True)
