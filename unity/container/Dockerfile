FROM ubuntu:17.10
MAINTAINER Jonathan Creekmore <jonathan.creekmore@starlab.io>

ENV DEBIAN_FRONTEND=noninteractive
ENV USER root

# build depends
RUN apt-get update && \
    apt-get --quiet --yes install \
        build-essential ca-certificates curl wget git libssl-dev \
        software-properties-common gcc-multilib python2.7-dev bc \
        python-pip python-virtualenv check linux-headers-generic && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists* /tmp/* /var/tmp/*

# Get the specific pre-requisites for building debs
RUN apt-get --quiet --yes update && \
	apt-get --quiet --yes install debhelper dh-strip-nondeterminism autotools-dev gawk man-db bsdmainutils \
    groff-base po-debconf intltool-debian libfile-stripnondeterminism-perl libarchive-zip-perl cpio && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists

RUN apt-get --quiet --yes update && \
	apt-get --quiet --yes install rsync && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists

RUN apt-get --quiet --yes update && \
	apt-get --quiet --yes install libudev-dev libpci-dev libelf-dev flex bison && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists


# where we build
RUN mkdir /source
VOLUME ["/source"]
WORKDIR /source
CMD ["/bin/bash"]
