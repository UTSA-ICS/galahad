import	argparse

from	__init__				import *
from	CheckUserAPI			import CheckUserAPI
from	ApplicationArguments	import ApplicationArguments
from	RoleArguments			import RoleArguments
from	VirtueArguments			import VirtueArguments
from	UserArguments			import UserArguments

appChoices = ['get']
roleChoices = ['get']
virtChoices = ['get','create','launch','stop','destroy','application launch','application stop',]
userChoices = ['login','logout','role list','virtue list']

options = {
	'application'	:	appChoices,
	'role'			:	roleChoices,
	'virtue'		:	virtChoices,
	'user'			:	userChoices,
}

parser = argparse.ArgumentParser(prog='canvas')
subparser = parser.add_subparsers(dest='subparser',help='subcommand help')

### Application Parser ###
parser_app = subparser.add_parser('application',help='application help')
parser_app.add_argument('command',choices=options['application'],help='command help')
parser_app.add_argument('--userToken',help='userToken help')
parser_app.add_argument('--applicationId',help='applicationId help')

### Role Parser ###
parser_role = subparser.add_parser('role',help='role help')
parser_role.add_argument('command',choices=options['role'],help='command help')
parser_role.add_argument('--userToken',help='userToken help')
parser_role.add_argument('--roleId',help='roleId help')

### Virtue Parser ###
parser_virt = subparser.add_parser('virtue',help='virtue help')
parser_virt.add_argument('command',choices=options['virtue'],help='command help')
parser_virt.add_argument('--userToken',help='userToken help')
parser_virt.add_argument('--virtueId',help='virtueId help')
parser_virt.add_argument('--roleId',help='roleId help')
parser_virt.add_argument('--applicationId',help='applicationId help')

### User Parser ###
parser_user = subparser.add_parser('user',help='user help')
parser_user.add_argument('command',choices=options['user'],help='command help')
parser_user.add_argument('--userToken',help='userToken help')
parser_user.add_argument('--credentials',help='credentials help')
parser_user.add_argument('--forceLogoutOfOtherSessions',help='force help')
parser_user.add_argument('--username',help='username help')

args = vars(parser.parse_args())

check = CheckUserAPI()
print(check.calc(args))

cd = {
	'application'		:	ApplicationArguments(),
	'role'				:	RoleArguments(),
	'virtue'			:	VirtueArguments(),
	'user'				:	UserArguments(),
}

inst = cd[args['subparser']]
method_to_call = getattr(inst, args['subparser'])
print(method_to_call(args))

