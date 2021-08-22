import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


setup(
    name="aws_iam_db",
    version="0.0.1",
    description="Creates a sqlite database of AWS IAM actions",
    long_description=README,
    long_description_content_type="text/markdown",
    author="zscholl",
    packages=find_packages(exclude=("tests",)),
    install_requires=["typer", "beautifulsoup4", "sqlalchemy", "requests"],
    entry_points={
        "console_scripts": ["aws-iam-db=aws_iam_db.__main__:main"],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
