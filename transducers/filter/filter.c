#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include "cjson/cJSON.h"
#include "map/src/map.h"

/* Copyright (c) 2018 by Raytheon BBN Technologies Corp. */

/*
 * All of this should eventually be a thread in the syslog-ng module, not a 
 * separate process.
 * Also, the 'transducers' map should live in memory somewhere so that both 
 * the main part of the module and this thread can access it.
 */

int send_message(int sock, char* message, int len) {
    if (write(sock, message, len) < 0) {
        perror("writing on stream socket");
    }
}

int receive_int(int *num, int fd) {
    int32_t ret;
    char *data = (char*)&ret;
    int left = sizeof(ret);
    int rc;
    do {
        rc = read(fd, data, left);
        if (rc <= 0) {
            if ((errno == EAGAIN) || (errno == EWOULDBLOCK)) {
                // try again ???
            } else if (errno != EINTR) {
                return -1;
            }
        } else {
            data += rc;
            left -= rc;
        }
    } while (left > 0);
    *num = ntohl(ret);
    return 0;
}

void write_ruleset_to_json(cJSON* json, map_int_t* transducers) {
    const char* transducer_id;
    map_iter_t iter = map_iter(transducers);

    while ((transducer_id = map_next(transducers, &iter))) {
        int enabled = *map_get(transducers, transducer_id);
        cJSON* enabled_obj = enabled ? cJSON_CreateTrue() : cJSON_CreateFalse();

        cJSON_AddItemToObjectCS(json, transducer_id, enabled_obj);
    }
}

int read_command_from_json(cJSON* json, map_int_t* transducers) {
    if (!cJSON_IsObject(json)) {
        perror("parsed json command is not an object");
        return 1;
    }
    cJSON* item = json->child;
    while (item != NULL) {
        char* transducer_id = item->string;
        int enabled = 0;
        if (!cJSON_IsBool(item)) {
            perror("unexpected non-boolean type");
            return 1;
        }
        if (cJSON_IsTrue(item)) {
            enabled = 1;
        }
        map_set(transducers, transducer_id, enabled);
        printf("parsed command: %s %d\n", transducer_id, enabled);
        item = item->next;
    }

    return 0;
}

int thread(map_int_t* transducers) {
    // set up unix domain socket

    int sock, msgsock, rval;
    struct sockaddr_un server;
    char buf[1024];
    char s_filename[] = "./receiver_to_filter";
    int total_len;
    char* rcvd_msg;
    int offset;

    unlink(s_filename);
    sock = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("opening stream socket\n");
        return 1;
    }
    server.sun_family = AF_UNIX;
    strcpy(server.sun_path, s_filename);
    if (bind(sock, (struct sockaddr*)&server, sizeof(struct sockaddr_un))) {
        perror("binding stream socket\n");
        return 1;
    }

    printf("set up socket with name %s\n", server.sun_path);
    listen(sock, 5);
    for (;;) {
        msgsock = accept(sock, 0, 0);
        if (msgsock == -1) {
            perror("accept");
        } else {
            if (receive_int(&total_len, msgsock)) {
                perror("reading message length\n");
                return 1;
            }
            printf("message length: %d\n", total_len);
            rcvd_msg = (char *)malloc(total_len);
            offset = 0;
            do {
                bzero(buf, sizeof(buf));
                printf("waiting for read\n");
                if ((rval = read(msgsock, buf, 1024)) < 0) {
                    perror("reading stream message\n");
                } else if (rval == 0) {
                    printf("finished connection\n");
                } else {
                    printf(">>%s\n", buf);
                    if (total_len - rval < 0) {
                        perror("message too long");
                        rval = total_len;
                    }
                    total_len -= rval;
                    strncpy(rcvd_msg + offset, buf, rval);
                    offset += rval;
                }
            } while (total_len > 0);
            if (strncmp(rcvd_msg, "heartbeat", 9) == 0) {
                // heartbeat
                cJSON* json = cJSON_CreateObject();
                write_ruleset_to_json(json, transducers);
                char* str = cJSON_Print(json);
                printf(">>> json: %s\n", str);
                send_message(msgsock, str, strlen(str));
                cJSON_Delete(json);
            } else { //if (strncmp(rcvd_msg, "command", 8) == 0) {
                // command

                // parse command
                cJSON* json = cJSON_Parse(rcvd_msg);
                if (json == NULL) {
                    perror("failed to parse command");
                } else {
                    char* id;
                    int enabled;
                    if (read_command_from_json(json, transducers)) {
                        perror("unexpected format in command");
                    } else {

                        // free the json command
                        cJSON_Delete(json);

                        // change the ruleset - already done while reading

                        // send new/modified ruleset
                        cJSON* new_json = cJSON_CreateObject();
                        write_ruleset_to_json(new_json, transducers);
                        char* str = cJSON_Print(new_json);
                        send_message(msgsock, str, strlen(str));
                        cJSON_Delete(new_json);

                    }
                }
            //} else {
                //printf("unknown command: %s\n", rcvd_msg);
            }
            printf("closing msgsock\n");
            free(rcvd_msg);
            close(msgsock);
        }
    }
    close(sock);
    unlink(s_filename);
}

int main() {
    map_int_t transducers;
    map_init(&transducers);

    int ret = thread(&transducers);

    map_deinit(&transducers);
    return ret;
}
