#!/usr/bin/env bash

homedir=/x/local/scorebot/scorebot-service
pidfile=$(basename $0 .sh).pid
logfile=/var/log/scorebot2/$(basename $0 .sh)_server.log
database=default

#Environment variable files
varfile=scorebot_vars.sh

if [ -f ${varfile} ];
then
  source ${varfile}
else
  echo "Missing source server vars file: $varfile"
fi

source ${homedir}/virtual_env.config

usage() {
   cat <<EOF

usage:
   $(basename $0) start
   $(basename $0) restart
   $(basename $0) stop
   $(basename $0) status

EOF
   exit 1
}

cd ${homedir}

descendent_pids() {
   for ppid in $* ; do
       echo ${ppid}
       descendent_pids $(ps ax -o ppid,pid | awk "\$1 == $ppid { print \$2 }")
   done
}

status() {
   for pid in $(cat ${pidfile}) ; do
       command="$(ps -o command ${pid} | tail -1)"
       if [[ "$command" == *uwsgi\ * ]]; then
           echo $(basename $0 .sh) is running through uwsgi.sock for nginx integration
       else
           echo ProcessID ${pid} invalid. Run stop for clean up
       fi
   done
}

case "$1" in
   start)
       if [ -s ${pidfile} ]; then
           echo $(basename $0 .sh) CANNOT be started
           status
           exit 1
       fi
       echo Starting up $(basename $0 .sh)
       ./manage.py migrate --database=${database} --noinput || exit 1
       ./manage.py collectstatic --noinput || exit 1
       uwsgi \
           ${VIRTENV} \
           --chdir=${homedir} \
           --module=scorebot.wsgi:application  \
           --env DJANGO_SETTINGS_MODULE=scorebot.settings \
           --env HTTPS=on \
           --env wsgi.url_scheme=https \
           --static-map /static=${homedir}/static \
           --pidfile=${pidfile} \
           --daemonize=${logfile} \
           --stats=${homedir}/uwsgistats.socket \
           --buffer-size=16383 \
           --max-requests=1000 \
           --master \
           --workers=10 \
           --uwsgi-socket=${homedir}/uwsgi.sock \
           --chmod-socket=666 \
           --vacuum \
           --logformat='%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"'
       sleep 2
       ./$(basename $0) status
       ;;

       stop)
       if [ -s ${pidfile} ]; then
           echo Shutting down $(basename $0 .sh)
           uwsgi --stop ${pidfile}
           sleep 5

           if ./$(basename $0) status > /dev/null ; then
               rm -f ${pidfile}
               exit 0
           fi
       else
           echo $(basename $0 .sh) does NOT appear to be running
           exit 1
       fi
       ;;

   restart)
       if ./$(basename $0) status > /dev/null ; then
           ./$(basename $0) stop
       fi
       ./$(basename $0) start ${2:-$ip:$port}
       ;;
status)
       if [ -s ${pidfile} ]; then
           status
           exit 0
       fi

       echo $(basename $0 .sh) is NOT running
       exit 1
       ;;

   *)
       usage
       ;;
esac
