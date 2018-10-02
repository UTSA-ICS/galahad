#!/usr/bin/env bash

# Copyright (c) 2018 by Raytheon BBN Technologies Corp.

if [ "$#" -ne 1 ]; then
    echo "Missing arguments: please specify which deb file to build (merlin, listener)"
    exit 1
fi

if [ $1 != "merlin" ] && [ $1 != "listener" ] && [ $1 != "processkiller" ]; then
    echo "Expected 'merlin', 'listener', 'processkiller' for deb file to build; got: $1"
    exit 1
fi


if [ $1 == "merlin" ]; then
    HANDLER_COPY_TO="$1/opt/$1/"
    cp ../elastic_log_handler/handlers.py $HANDLER_COPY_TO
fi

COPY_TO="$1/opt/$1/$1.py"
if [ $1 == "listener" ]; then
    COPY_TO="$1/opt/heartbeatlistener/$1.py"
fi

cp $1.py $COPY_TO

dpkg-deb --build $1