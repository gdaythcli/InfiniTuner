#!/bin/bash
ACTION=$1
CGROUP_PATH=$2
VALUE=$3

case $ACTION in
    "create")
        sudo sh -c "mkdir '$CGROUP_PATH'"
        ;;
    "write")
        sudo sh -c "echo '$VALUE' > '$CGROUP_PATH'"
        ;;
    "delete")
        sudo sh -c "rmdir '$CGROUP_PATH'"
        ;;
    *)
        exit 1
        ;;
esac