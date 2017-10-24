import	argparse
from	CheckSecurityAPI		import CheckSecurityAPI

logChoices = ['components get','events get']

options = {
	'logging'		:	logChoices
}

parser = argparse.ArgumentParser(prog='canvas')
subparser = parser.add_subparsers(dest='subparser',help='subcommand help')

### Logging Parser ###
parser_log = subparser.add_parser('logging',help='logging help')
parser_log.add_argument('command',choices=options['logging'],help='command help')
parser_log.add_argument('--userToken',help='userToken help')
parser_log.add_argument('--virtueId',help='virtueId help')
parser_log.add_argument('--logComponentId',help='logComponentId help')
parser_log.add_argument('--after',help='after help')
parser_log.add_argument('--aboveLogLevel',help='aboveLogLevel help')


args = vars(parser.parse_args())

check = CheckSecurityAPI()
print(check.calc(args))
#method_to_call = getattr(check, args['subparser'])
#print(method_to_call(args))
