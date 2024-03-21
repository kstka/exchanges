from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="exchanges",
    version="0.1",
    author="Konstantin",
    author_email="me@kstka.com",
    description="Cryptocurrency exchanges trading library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kstka/exchanges",
    packages=['exchanges'],
    license='MIT License',
    )
