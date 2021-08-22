# AWS IAM Database

This project creates a local sqlite database of AWS IAM actions using the AWS IAM documentation pages.

By default it creates a sqlite database in the current directory called `iam.db` and stores copies of the AWS documentation pages in the `/tmp` directory.

### Install

`git clone https://github.com/zscholl/aws-iam-db.git && cd aws-iam-db && python setup.py install`

### Usage
```
Usage: aws-iam-db [OPTIONS]

Options:
  --json-path TEXT                [default: /tmp/actions_data.json]
  --db-path TEXT                  [default: iam.db]
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.
```

```
Downloading aws docs  [####################################]  100%
Finished downloading docs
Converting docs to json  [####################################]  100%
Finished processing docs to JSON
Creating database  [####################################]  100%
Database created!
```
