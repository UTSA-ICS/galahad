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

#include "transducer-controller-parser.h"
#include "driver.h"
#include "cfg-parser.h"
#include "transducer-controller-grammar.h"

extern int transducer_controller_debug;

int transducer_controller_parse(CfgLexer *lexer, LogDriver **instance, gpointer arg);

static CfgLexerKeyword transducer_controller_keywords[] =
{
        { "transducer_controller", KW_TRANSDUCER_CONTROLLER },
  { NULL }
};

CfgParser transducer_controller_parser =
{
#if ENABLE_DEBUG
  .debug_flag = &transducer_controller_debug,
#endif
  .name = "transducer-controller",
  .keywords = transducer_controller_keywords,
  .parse = (gint (*)(CfgLexer *, gpointer *, gpointer)) transducer_controller_parse,
  .cleanup = (void (*)(gpointer)) log_pipe_unref,
};

CFG_PARSER_IMPLEMENT_LEXER_BINDING(transducer_controller_, LogDriver **)

