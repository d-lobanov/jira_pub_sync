# What's it?
Console tool which helps to migrate tasks and worklogs between SK Jira and PUB Jira.

*Can be used for other JIRAs but need small changes in this case.*

# Requirements
* [Python 3.5+](https://www.python.org/downloads/)
* [Pip](https://pip.pypa.io/en/stable/installing/#installation)

# Installation
```sh
pip install git+https://github.com/d-lobanov/jira_pub_sync
```
If python3 is not default in your system
```sh
python3 -m pip install git+https://github.com/d-lobanov/jira_pub_sync
```

For updating just add `--upgrade` in your installation pip command.

# Usage
```sh
jirapub config        # Change configuration

jirapub time 10       # Start to migrate worklogs for last 10 days

jirapub issue TASK-3  # Start to migrate issue `TASK-3` from SK to PUB

jirapub issues 18     # Finds and migartes all non-synchronized tickets for last 18 days
```

Or if you used `python3` for installing
```sh
python3 -m jirapub config        # Change configuration

python3 -m jirapub time 10       # Start to migrate worklogs for last 10 days

python3 -m jirapub issue TASK-3  # Start to migrate issue `TASK-3` from SK to PUB

python3 -m jirapub issues 18     # Finds and migartes all non-synchronized tickets for last 18 days
```
