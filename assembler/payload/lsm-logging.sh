#!/usr/bin/env bash

if [ $1 == "inode" ];
then
  if [ $2 == "on" ];
  then
    echo "1" > /sys/fs/virtuefs/loginode
  elif [ $2 == "off" ];
  then
    echo "0" > /sys/fs/virtuefs/loginode
  fi
elif [ $1 == "mkdir" ];
then
  if [ $2 == "on" ];
  then
    echo "1" > /sys/fs/virtuefs/logmkdir
  elif [ $2 == "off" ];
  then
    echo "0" > /sys/fs/virtuefs/logmkdir
  fi
else
  echo "ERROR: Invalid argument provided"
fi