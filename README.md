# AWS IAM Database

This project creates a local sqlite database of AWS IAM actions using the AWS IAM documentation pages.

By default it creates a sqlite database in the current directory called `iam.db` and stores copies of the AWS documentation pages in the `/tmp` directory.

### Install

`git clone https://github.com/zscholl/aws-iam-db.git && cd aws-iam-db && python setup.py install`

### Usage

`aws-iam-db`

```
Downloading aws docs  [####################################]  100%
Finished downloading docs
Converting docs to json  [####################################]  100%
Finished processing docs to JSON
Creating database  [####################################]  100%
Database created!
```
