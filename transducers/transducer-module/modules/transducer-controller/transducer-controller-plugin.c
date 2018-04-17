/*
 * Copyright (c) 2018 
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 2 as published
 * by the Free Software Foundation, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * As an additional exemption you are allowed to compile & link against the
 * OpenSSL libraries as published by the OpenSSL project. See the file
 * COPYING for details.
 *
 */

#include "cfg-parser.h"
#include "transducer-controller-parser.h"

#include "plugin.h"
#include "plugin-types.h"

extern CfgParser transducer_controller_parser;

static Plugin transducer_controller_plugins[] =
{
  {
    .type = LL_CONTEXT_PARSER,
    .name = "transducer-controller",
    .parser = &transducer_controller_parser,
  },
};

gboolean
transducer_controller_module_init(PluginContext *context, CfgArgs *args)
{
  plugin_register(context, transducer_controller_plugins, G_N_ELEMENTS(transducer_controller_plugins));
  return TRUE;
}

const ModuleInfo module_info =
{
  .canonical_name = "transducer_controller",
  .version = SYSLOG_NG_VERSION,
  .description = "Please fill this description",
  .core_revision = SYSLOG_NG_SOURCE_REVISION,
  .plugins = transducer_controller_plugins,
  .plugins_len = G_N_ELEMENTS(transducer_controller_plugins),
};
