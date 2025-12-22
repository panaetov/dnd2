#!/usr/bin/env bash

case "$1" in
    "help")
        echo "Please use of next parameters to start: "
        echo "  > webserver: Start webserver"
        echo "  > bash: Start bash shell"
        ;;
    "bash")
        echo "Starting bash ..."
        exec bash
        ;;

    "webserver")
        echo "Starting webserver ..."
        exec fastapi dev server.py --host 0.0.0.0
        ;;

    "payments_checker")
        echo "Starting payments checker ..."
        exec python payments_checker.py
        ;;

    *)
        echo "Unknown command '$1'. please use one of: [webserver, bash, help]"
        exit 1
        ;;
esac
