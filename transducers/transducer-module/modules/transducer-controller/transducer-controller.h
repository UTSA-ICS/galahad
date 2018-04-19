//
// Created by jprice on 3/23/2018.
//

#ifndef SYSLOG_NG_INCUBATOR_TRANSDUCER_CONTROLLER_H
#define SYSLOG_NG_INCUBATOR_TRANSDUCER_CONTROLLER_H


#include <pthread.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <pwd.h>
#include <grp.h>

#include "parser/parser-expr.h"
#include "map/src/map.h"
#include "cjson/cJSON.h"


typedef struct {
    LogParser super;
    gchar *prefix;
    int prefix_len;
    gboolean debug;
    map_int_t* transducers;
} TransducerController;

void transducer_controller_set_prefix(LogParser *p, const gchar *prefix);


gboolean transducer_controller_init_method(LogPipe *s);
gboolean transducer_controller_deinit_method(LogPipe *s);
LogPipe *transducer_controller_clone_method(TransducerController *dst, TransducerController *src);
void transducer_controller_init_instance(TransducerController *self, GlobalConfig *cfg);
LogParser *transducer_controller_new(GlobalConfig *cfg);


#endif //SYSLOG_NG_INCUBATOR_TRANSDUCER_CONTROLLER_H
