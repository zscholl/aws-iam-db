import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="iam_policy_db",
    version="0.0.1",
    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="author",
    package_dir={"": "iam_policy_db"},
    packages=setuptools.find_packages(where="iam_policy_db"),
    install_requires=[
        "aws-cdk.core==1.116.0",
        "aws-cdk.aws_dynamodb",
        "aws-cdk.aws_lambda",
        "aws-cdk.aws_events",
        "aws-cdk.aws_events_targets",
        "aws-cdk.aws_iam",
        "aws-cdk.aws_cognito",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
