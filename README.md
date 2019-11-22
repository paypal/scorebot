# SCORE Bot
An automated way to perform Secure COde REview

## Introduction
This bot helps identify potential security vulnerabilities during code review and provides feedback in the 
Pull Request (PR) on potential impacts and secure ways to fix the issues.

One of the performing states of this automated system is to feed domain code owners and security teams information 
on identified vulnerable code and the potential solutions to fix them.

In addition, various metadata collected in the process of identifying vulnerable code will provide insights to fine-tune 
security programs (including trainings for targeted audience) and help teach various aspects of specific categories of 
insecure coding and how to avoid them.

SCORE Bot kicks in when the PR is issued (after the webhook is set up for the repository) and performs the checks as 
configured. Commenting in the PR, sending an email to the coder/reviewer can be performed as well.

## Goals
1. Identify insecure code at the time of development, before the code is integrated.
2. Provide guidance to domain code owners to identify and fix potential security vulnerabilities during development
phase.
3. Keep security teams informed about the various security mistakes that are committed during development
4. Enable programs to identify insecure coding practices much earlier in the game
5. Provide guidance to Secure Product Lifecycle (SPLC) processes to target specific training for specific audience for 
specific categories of insecure coding practices.


## Modes
SCORE Bot use cases can be run in the following three modes:

### Silent Mode
In this mode, SCORE Bot will record metrics for any use case without sending any notifications. 
No PR comments, no emails sent. This mode is useful while integrating a new use case with SCORE Bot. 
Developers will be completely transparent to this.

### Notify Mode
In this mode, in addition to recording metrics, SCORE Bot will perform notification by commenting in the PR and sending
emails to developers.

### Enforce Mode
In this mode, SCORE Bot will record metrics on each commit and submit a status check, perform notification by commenting
in the PR and sending email to developers. If any vulnerabilities are found, the status check will fail and in order to
pass the check, developers will need to fix the issue or submit an exemption request. This mode is useful for higher
priority security use cases where enforcing use cases is necessary.

## Setup
### MySQL Database
```$ mysql -h localhost -u root -p```

```
CREATE DATABASE scorebot2;

CREATE USER 'scorebot'@'localhost' IDENTIFIED BY '<password>';
CREATE USER 'scorebot'@'%' IDENTIFIED BY '<password>';

GRANT ALL PRIVILEGES ON scorebot2 . * TO 'scorebot'@'localhost';
GRANT ALL PRIVILEGES ON scorebot2 . * TO 'scorebot'@'%';
FLUSH PRIVILEGES;

SELECT User, Host FROM mysql.user;
SHOW GRANTS FOR 'scorebot'@'localhost';
SHOW GRANTS FOR 'scorebot'@'%';

exit;
```

### Log Folder
```
$ mkdir -pv /var/log/scorebot2
$ chmod 755 /var/log/scorebot2
```

### Local Setup
Create project directory and clone repo
```
$ mkdir -pv /x/local/scorebot
$ cd /x/local/scorebot
$ git clone --recursive <repo_url>
```

Create and setup virtualenv
```
$ python3 -m venv scorebot2
$ source scorebot2/bin/activate

$ (scorebot2) python --version  # Python 3.7.2
$ (scorebot2) which python  # /x/local/scorebot/scorebot-service/scorebot2/bin/python

$ (scorebot2) pip install --upgrade pip setuptools
$ (scorebot2) pip install -r requirements.txt

$(scorebot2) deactivate
```

Create and setup project variables in project root
```
$ vi scorebot_vars.sh
```

`scorebot_vars.sh` template:
```
#!/bin/sh

export DOMAIN='<site_domain>'
export SECURE_FLAG='<secure_flag>'

export DJANGO_KEY='<django_secret>'
export DJANGO_SETTINGS_MODULE='scorebot.settings'
export PYTHONPATH='/x/local/scorebot/scorebot-service:/x/local/scorebot/scorebot-service/external_tools'
alias python='/x/local/scorebot/scorebot-service/scorebot2/bin/python'
export VIRTUALENVWRAPPER_VIRTUALENV_ARGS='--no-site-packages'

### Github
export GITHUB_DOMAIN='<github_domain>'
export GITHUB_API_USER='SCORE-Bot'
export STATUS_CONTEXT='scorebot'

### Database
export DB_NAME='scorebot2'
export DB_HOST='<db_host>'
export DB_PORT='3306'
export SB_SQL_USER='scorebot'
export SB_SQL_PASSWORD='<db_password>'

### Email
export SMTP_SERVER='<email_server>'
export SCOREBOT_CRITICAL_DL_GCP='<email_address>'
export SCOREBOT_DL_GCP='<email_address>'
export SCOREBOT_DL='<email_address>'
export SCOREBOT_CRITICAL_DL='<email_address>'
export DEFAULT_EMAIL='<email_address>'

### Host
export SSO_FLAG=''
export SSO_REDIRECT=''
export GCP_FLAG=''
export CURR_ENV=''
```

Start server and daemons
```
./runall.sh restart
```
