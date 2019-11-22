#!/usr/bin/env bash

FILE=scorebot_vars.sh
SCOREBOT_DAEMON=/x/local/scorebot/scorebot-service/sb_service/daemons
if [ -f ${FILE} ];
then
   source ${FILE}
else
   echo "Missing source server vars file: $FILE"
fi

if [ "$CURR_ENV" != "docker" ];
then
    # virtual environment
    source $(dirname $0)/virtual_env.config
fi

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

COMMAND=""
case "$1" in
    start)
        COMMAND=start
        ;;

    stop)
        COMMAND=stop
        ;;

    restart)
        COMMAND=restart
        ;;

    status)
        COMMAND=status
        ;;

    *)
        usage
        ;;
esac
if [ ${COMMAND} != "" ];
then
    echo "Running command: $COMMAND"
    cd ${SCOREBOT_DAEMON}
    echo "ScorebotDaemon"
    python ScorebotDaemonCpp.py ${COMMAND}
fi
