module_LTLIBRARIES      += modules/transducer-controller/libtransducer-controller.la

modules_transducer_controller_libtransducer_controller_la_CFLAGS		= \
	$(INCUBATOR_CFLAGS)		  \
	-I$(top_srcdir)/modules/transducer-controller	  \
	-I$(top_builddir)/modules/transducer-controller

modules_transducer_controller_libtransducer_controller_la_LIBADD		= \
	$(INCUBATOR_LIBS)

modules_transducer_controller_libtransducer_controller_la_SOURCES = \
  modules/transducer-controller/transducer-controller-grammar.y       \
  modules/transducer-controller/transducer-controller-parser.c        \
  modules/transducer-controller/transducer-controller-parser.h        \
  modules/transducer-controller/transducer-controller.c               \
  modules/transducer-controller/transducer-controller.h               \
  modules/transducer-controller/transducer-controller-plugin.c        \
  modules/transducer-controller/map/src/map.h                         \
  modules/transducer-controller/map/src/map.c                         \
  modules/transducer-controller/cjson/cJSON.h                         \
  modules/transducer-controller/cjson/cJSON.c

BUILT_SOURCES       +=      \
  modules/transducer-controller/transducer-controller-grammar.y       \
  modules/transducer-controller/transducer-controller-grammar.c       \
  modules/transducer-controller/transducer-controller-grammar.h

EXTRA_DIST        +=      \
  modules/transducer-controller/transducer-controller-grammar.ym

modules_transducer_controller_libtransducer_controller_la_CPPFLAGS  =     \
  $(AM_CPPFLAGS)            \
  -I$(top_srcdir)/modules/transducer-controller        \
  -I$(top_builddir)/modules/transducer-controller
modules_transducer_controller_libtransducer_controller_la_LIBADD  = $(MODULE_DEPS_LIBS)
modules_transducer_controller_libtransducer_controller_la_LDFLAGS = $(MODULE_LDFLAGS)
modules_transducer_controller_libtransducer_controller_la_DEPENDENCIES= $(MODULE_DEPS_LIBS)

modules/transducer-controller modules/transducer-controller/ mod-transducer-controller: modules/transducer-controller/libtransducer-controller.la
.PHONY: modules/transducer-controller/ mod-transducer-controller

