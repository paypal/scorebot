# SCORE Bot
An automated way to perform Secure COde REview

## Introduction
This bot is designed to help identify potential security vulnerabilities during code review and provide feedback in the 
Pull Request (PR) on potential impact and secure ways to fix the them.

One of the performing states of this automated system is to feed code contributers, owners & security teams information 
on identified vulnerable code.

In addition, various metadata collected in the process of identifying vulnerable code will provide insight to fine tune 
security programs (including trainings for targeted audience) and help learn various aspects of specific categories of 
vaulnerabilities.

SCORE Bot kicks in when the PR is issued (after the webhook is set up for the repository or integrated with CI/CD pipeline) and performs checks as configured. Commenting in the PR, sending an email to the contributer & reviewer can be performed as well.

## Goals
1. Identify insecure code at the time of development, before the code is integrated
2. Provide guidance to code contributers & owners to identify and fix potential security vulnerabilities during development
3. Keep security teams informed about the various potential vulnerabilities that are committed during development
4. Enable organizational security programs to identify insecure code much earlier in SDLC
5. Provife data to enable targeted & effective training for code communities for specific categories of insecure coding practices.


## Modes
SCORE Bot use cases can be run in the following three modes:

### Silent Mode
In this mode, SCORE Bot will record metrics for any use case without sending any notifications. 
No PR comments, no emails sent. This mode is useful while integrating a new use case with SCORE Bot. 
Developers will be completely transparent to this.

### Notify Mode
In this mode, in addition to recording metrics, SCORE Bot will notify in the PR and can be configured to send emails to code contributers.

### Enforce Mode
In this mode, SCORE Bot will record metrics on each commit and submit a status check, notigy in the PR and send email to code contributers. If any vulnerabilities are found, the status check will fail. This mode is useful for priority security use cases where enforcing is necessary.

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
