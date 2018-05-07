//
// Created by jprice on 3/23/2018.
//

#include "transducer-controller.h"

const gchar *TRANSDUCER_KEY = "Event";

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

void transducer_rules_connection_thread(void *vargp) {
    TransducerController* self = (TransducerController *) vargp;
    map_int_t* transducers = self->transducers;
//    map_int_t* transducers = (map_int_t *) vargp;
//    // set up unix domain socket
    int sock, msgsock, rval;
    struct sockaddr_un server;
    char buf[1024];
    char* s_filename = self->socket_path;
    int total_len;
    char* rcvd_msg;
    int offset;
    struct group *grp;
    gid_t gid;

    grp = getgrnam("virtue");
    gid =  grp->gr_gid;
    unlink(s_filename);
    printf("socket path pointer in startup method: %s\n", self->socket_path);

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


    if (chmod(s_filename, 0770) == -1) {
        int errsv = errno;
        printf("Chmod fail %d\n", errsv);
        return 1;
    }


    if (chown(s_filename, -1, gid) == -1) {
        int errsv = errno;
        printf("Chown fail %d\n", errsv);
        return 1;
    }

    printf("set up socket with name %s\n", server.sun_path);
    listen(sock, 5);

    for (;;) {
        msgsock = accept(sock, 0, 0);
        printf("Accepted connection\n");
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
                if ((rval = read(msgsock, buf, 1024)) < 0) {
                    perror("reading stream message\n");
                } else if (rval == 0) {
                    printf("finished connection\n");
                } else {
                    if (total_len - rval < 0) {
                        perror("message too long\n");
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
}

void transducer_set_socket(LogParser *p, char* socket_path) {
    TransducerController *self = (TransducerController *)p;
    printf("Adding socket path of %s to module\n", socket_path);
    g_free(self->prefix);
//    self->socket_path = socket_path;
    self->socket_path = (char*) malloc(strlen(socket_path) + 1);
    strncpy(self->socket_path, socket_path, strlen(socket_path) + 1);
    printf("Adding socket path of %s to module\n", self->socket_path);
    printf("socket path pointer: %p\n", self->socket_path);
    pthread_t tid;
    pthread_create(&tid, NULL, transducer_rules_connection_thread, (void *) self);
}


void
transducer_controller_set_prefix(LogParser *p, const gchar *prefix)
{
    TransducerController *self = (TransducerController *)p;

    g_free(self->prefix);
    if (prefix)
    {
        self->prefix = g_strdup(prefix);
        self->prefix_len = strlen(prefix);
    }
    else
    {
        self->prefix = NULL;
        self->prefix_len = 0;
    }
}

static gboolean _process(LogParser *s, LogMessage **pmsg, const LogPathOptions *path_options, const gchar *input,
         gsize input_len)
{
    TransducerController *self = (TransducerController *) s;

    gchar *event_key = log_msg_get_value_by_name(*pmsg, TRANSDUCER_KEY, NULL);
    if (event_key != NULL) {
        int *val = map_get(self->transducers, event_key);
        if (val == NULL) {
            return TRUE;
        }
        if (*val == 0) {
            return FALSE;
        } else {
            return TRUE;
        }
    }

    // Should we be fail-open, fail-close, or configurable?
    return TRUE;


//    log_msg_make_writable(pmsg, path_options);
//    /* FIXME: input length */
//    while (kv_scanner_scan_next(&kv_scanner))
//    {
//
//        /* FIXME: value length */
//        log_msg_set_value_by_name(*pmsg,
//                                  _get_formatted_key(self, kv_scanner_get_current_key(&kv_scanner), formatted_key),
//                                  kv_scanner_get_current_value(&kv_scanner), -1);
//    }
//    if (self->stray_words_value_name)
//        log_msg_set_value_by_name(*pmsg,
//                                  self->stray_words_value_name,
//                                  kv_scanner_get_stray_words(&kv_scanner), -1);
//
//    kv_scanner_deinit(&kv_scanner);
}

LogPipe *transducer_controller_clone_method(TransducerController *dst, TransducerController *src) {
    transducer_controller_set_prefix(&dst->super, src->prefix);
    transducer_set_socket(&dst->super, src->socket_path);
    printf("socket path value in clone method: %s : %s\n", src->socket_path, &dst->socket_path);
    log_parser_set_template(&dst->super, log_template_ref(src->super.template));
    return &dst->super.super;
}

static LogPipe *_clone(LogPipe *s)
{
    TransducerController *self = (TransducerController *) s;
    TransducerController *cloned = (TransducerController *) transducer_controller_new(s->cfg);

    return transducer_controller_clone_method(cloned, self);
}

static void
_free(LogPipe *s)
{
    TransducerController *self = (TransducerController *)s;

    g_free(self->prefix);
    g_free(self->socket_path);
    g_free(self);
    log_parser_free_method(s);
}
void transducer_controller_init_instance(TransducerController *self, GlobalConfig *cfg) {
    log_parser_init_instance(&self->super, cfg);
    self->super.process = _process;
}

void mock_map(map_int_t *map) {
    map_set(map, "task_create", 0);
}

LogParser *transducer_controller_new(GlobalConfig *cfg)  {
    TransducerController *self = g_new0(TransducerController, 1);
    //map_int_t transducers;
    map_int_t* transducers = (map_int_t*)malloc(sizeof(map_int_t));
    map_init(transducers);
//    mock_map(&transducers);
//    pthread_t tid;
//    pthread_create(&tid, NULL, transducer_rules_connection_thread, (void *) self);

    transducer_controller_init_instance(self, cfg);
    self->super.super.clone = _clone;
    self->transducers = transducers;

    return &self->super;
}
