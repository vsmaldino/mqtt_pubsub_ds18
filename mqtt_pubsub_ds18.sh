#! /bin/sh

### BEGIN INIT INFO
# Provides:          mqtt_pubsub_ds18-1.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

NAME="mqtt_pubsub_ds18-1.py"
PGM="/usr/local/bin/mqtt_pubsub_ds18-1.py"

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting ${NAME}"
    sleep 120
    ${PGM} &
    ;;
  stop)
    echo "Stopping ${NAME}"
    pkill -f ${PGM}
    ;;
  *)
    echo "Usage: /etc/init.d/mqtt_pubsub_ds18.sh {start|stop}"
    exit 1
    ;;
esac

exit 0
