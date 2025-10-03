from setuptools import find_packages, setup

__version__ = "0.0.0"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="metadata_server",
    version=__version__,
    description="Short description of your package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sidkos/metadata_server",
    author="Your Name",
    author_email="sidkosergeyv@gmail.com",
    license="GNU GENERAL PUBLIC LICENSE",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE",
        "Programming Language :: Python :: 3.13",
    ],
    packages=find_packages(exclude=["docs", "tests*", ".venv*"]),
    python_requires="==3.13",
)
