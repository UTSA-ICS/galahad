#!/bin/bash

for arg in $(cat /proc/cmdline); do
  case "${arg}" in
    unity-net=*)
      eval $(echo "${arg#unity-net=*}" | base64 --decode)
      ;;
    nameserver=*)
      echo "nameserver ${arg#nameserver=*}" >> /etc/resolv.conf
      ;;
  esac
done
