#!/usr/bin/env bash

port=8025

ip=0.0.0.0
pidfile=scorebot.pid
logfile=/var/log/scorebot2/scorebot_server.log
database=default

FILE=/x/local/scorebot/scorebot-service/scorebot_vars.sh

if [ -f ${FILE} ];
then
   source ${FILE}
else
   echo "Missing source server vars file: $FILE"
fi

# virtual environment, don't run if docker is not in use
# source $(dirname $0)/virtual_env.config

usage() {
    cat <<EOF

usage:
    $(basename $0) start [ ip:port ]
    $(basename $0) restart [ ip:port ]
    $(basename $0) stop
    $(basename $0) status

EOF
    exit 1
}

cd $(dirname $0)

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
            echo $(basename $0 .sh) is running on $(echo "$command" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}(:[0-9]{1,5})?\b" | head -1)
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
            --chdir $(dirname $0) \
            --module scorebot.wsgi:application  \
            --http-socket=${ip}:${port} \
            --env DJANGO_SETTINGS_MODULE=scorebot.settings \
            --static-map /static=$(dirname $0)/static \
            --pidfile=${pidfile} \
            --daemonize=${logfile} \
            --stats $(dirname $0)/uwsgistats.socket \
            --buffer-size 16383 \
            --max-requests 1000 \
            --master \
            --workers 10 \
            --logformat '%(addr) - %(user) [%(ltime)] "%(method) %(uri) %(proto)" %(status) %(size) "%(referer)" "%(uagent)"'
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
            else
                echo FAILED to stop $(basename $0 .sh)
                exit 1
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
