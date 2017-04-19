# What's it?
Console tool which helps to migrate tasks and worklogs between SK Jira and PUB Jira.

*Can be used for other JIRAs but need small changes in this case.*

# Requirements
* [Python 3.5+](https://www.python.org/downloads/)
* [Pip](https://pip.pypa.io/en/stable/installing/#installation)

# Usage
```sh
jirapub config        # Change configuration

jirapub time 10       # Start to migrate worklogs for last 10 days

jirapub issue TASK-3  # Start to migrate issue `TASK-3` from SK to PUB

jirapub issues 18     # Finds and migartes all non-synchronized tickets for last 18 days
