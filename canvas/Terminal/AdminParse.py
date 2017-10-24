import	argparse
from	CheckAdminAPI		import CheckAdminAPI

appChoices = ['list']
roleChoices = ['create','list']
resChoices = ['get','list','attach','detach']
userChoices = ['list','get','virtue list','logout','role authorize','role unauthorize']
sysChoices = ['export','import']
testChoices = ['import user','import application','import role']
utChoices = ['list']

options = {
	'application'	:	appChoices,
	'role'			:	roleChoices,
	'resource'		:	resChoices,
	'user'			:	userChoices,
	'system'		:	sysChoices,
	'test'			:	testChoices,
	'userToken'		:	utChoices,
}

parser = argparse.ArgumentParser(prog='canvas')
subparser = parser.add_subparsers(dest='subparser',help='subcommand help')

### Application Parser ###
parser_app = subparser.add_parser('application',help='application help')
parser_app.add_argument('command',choices=options['application'],help='command help')
parser_app.add_argument('--userToken',help='userToken help')

### Role Parser ###
parser_role = subparser.add_parser('role',usage='role [-h] command [--userToken USERTOKEN] [--roleId ROLEID] [--role ROLE]',help='role help')
parser_role.add_argument('command',choices=options['role'],help='command help')
parser_role.add_argument('--userToken',help='userToken help')
parser_role.add_argument('--role',help='role help')

### Resource Parser ###
parser_res = subparser.add_parser('resource',help='resource help')
parser_res.add_argument('command',choices=options['resource'],help='command help')
parser_res.add_argument('--userToken',help='userToken help')
parser_res.add_argument('--resourceId',help='resourceId help')
parser_res.add_argument('--virtueId',help='virtueId help')

### User Parser ###
parser_user = subparser.add_parser('user',help='user help')
parser_user.add_argument('command',choices=options['user'],help='command help')
parser_user.add_argument('--userToken',help='userToken help')
parser_user.add_argument('--username',help='username help')
parser_user.add_argument('--roleId',help='roleId help')

### System Parser ###
parser_sys = subparser.add_parser('system',help='system help')
parser_sys.add_argument('command',choices=options['system'],help='command help')
parser_sys.add_argument('--userToken',help='userToken help')
parser_sys.add_argument('--data',help='which help')

### Test Parser ###
parser_test = subparser.add_parser('test',help='test help')
parser_test.add_argument('command',choices=options['test'],help='command help')
parser_test.add_argument('--userToken',help='userToken help')
parser_test.add_argument('--which', help='which help')

### UserToken Parser ###
parser_ut = subparser.add_parser('usertoken',help='usertoken help')
parser_ut.add_argument('command',choices=options['userToken'],help='command help')
parser_ut.add_argument('--userToken',help='userToken help')


args = vars(parser.parse_args())

check = CheckAdminAPI()
print(check.calc(args))
