#!/usr/bin/env python
"""The setup script."""
from setuptools import find_packages
from setuptools import setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click",
    "flask-logging",
    "flask-sqlalchemy",
    "celery",
]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest>=3", "pytest-cov"]

setup(
    author="Alex Rudy",
    author_email="opensource@alexrudy.net",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Boilerplate for Flask",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="beaker",
    name="beaker",
    packages=find_packages("src", include=["src/beaker", "src/beaker.*"]),
    package_dir={"": "src"},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/alexrudy/beaker",
    version="0.1.0",
    zip_safe=False,
)