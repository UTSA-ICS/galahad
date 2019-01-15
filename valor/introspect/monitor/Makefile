
introspection-monitor: introspection-monitor.c
	gcc -Wall -Werror \
        introspection-monitor.c \
        -lssl \
        -lcrypto \
        -lvmi \
        -o $@

clean:
	rm -f xenaccess-starlab-daemon
