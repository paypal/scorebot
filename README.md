# SCORE Bot
SCORE Bot stands for Secure Code Review Bot. To learn more about the philosophy, guiding principles and lessons learned from our own deployment at PayPal, watch this AppSec USA talk: https://www.youtube.com/watch?v=4rjmtdvrGrg
 
## Introduction
This bot is designed to help identify potential security vulnerabilities during code review and surface that to developers via Pull Request (PR) comments.
 
The comments can be customized to include details about the vulnerability, its impact and also remediation guidance. The bot is language agnostic and the best use-case is to identify vulnerabilities in your own organization-specific custom frameworks, libraries, etc. We have provided a simple generic rule as an example with which you can model your own rules.
  
In addition, metadata/metrics collected in the process of identifying vulnerable code can provide insights which can then be actioned by the AppSec team (targeted training for example).
  
## Goals
1. Identify insecure code at the time of development, before the code is integrated
2. Provide guidance to code contributors & owners to identify and fix potential security vulnerabilities during development
3. Keep security teams abreast with actionable insights into vulnerabilities that are committed during development
 
## Modes
SCORE Bot checks can be run in the following three modes:
 
### Silent Mode
In this mode, SCORE Bot will record metrics for any vulnerability it detects without sending any notifications.
No PR comments or emails will be sent. This mode is useful while integrating a new check with SCORE Bot to figure out false positives, tune the rules, etc.
 
### Notify Mode
In this mode, SCORE Bot will notify about the vulnerabilities (in addition to recoding the metrics) it detects in the PR and it can also be configured to send emails to code contributors.
 
### Enforce Mode
In this mode, SCORE Bot will record metrics on each commit, notify in the PR and/or send email to code contributors and also submit a status check. If any vulnerabilities are found, the status check will fail. This mode is useful for critical security vulnerabilities where enforcing the fix might be necessary before allowing the code to propagate in the pipeline.


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
