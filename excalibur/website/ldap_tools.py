import copy
import json

# A static file to make LDAP more usable while implementing the VirtUE API


# Due to LDAP constraints (dn cannot contain quotes), these values will not
# be run through the json formatter:
always_string_values = ['username', 'id']

def parse_ldap(data):

    parse_map = {
        'cappIds': 'applicationIds',
        'cstartResIds': 'startingResourceIds',
        'cstartTransIds': 'startingTransducerIds',
        'cstartConfig': 'startingConfiguration',
        'creqAccess': 'requiredAccess',
        'cauthRoleIds': 'authorizedRoleIds',
        'cresIds': 'resourceIds',
        'ctransIds': 'transducerIds',
        'cAmiId': 'amiId',
        'cawsInstId': 'awsInstanceId'
    }

    if ('ou' in data.keys()):
        del data['ou']
    if ('objectClass' in data.keys()):
        del data['objectClass']

    for k in data.keys():
        tmp = data.pop(k)

        if (type(tmp) == list):
            tmp = tmp[0]

        new_key = None
        if (k in parse_map.keys()):
            new_key = parse_map[k]
        elif (k[0] == 'c' and k != 'credentials'):
            new_key = k[1:]
        else:
            new_key = k

        if (new_key not in always_string_values):
            tmp = json.loads(tmp)

        data[new_key] = tmp


def to_ldap(data, objectClass):

    if (type(data) != dict):
        return None

    parse_map = {
        'id': 'cid',
        'version': 'cversion',
        'os': 'cos',
        'port': 'cport',
        'type': 'ctype',
        'unc': 'cunc',
        'credentials': 'ccredentials',
        'applicationIds': 'cappIds',
        'startingResourceIds': 'cstartResIds',
        'startingTransducerIds': 'cstartTransIds',
        'startEnabled': 'cstartEnabled',
        'startingConfiguration': 'cstartConfig',
        'requiredAccess': 'creqAccess',
        'username': 'cusername',
        'authorizedRoleIds': 'cauthRoleIds',
        'token': 'ctoken',
        'expiration': 'cexpiration',
        'roleId': 'croleId',
        'resourceIds': 'cresIds',
        'transducerIds': 'ctransIds',
        'state': 'cstate',
        'ipAddress': 'cipAddress',
        'amiId': 'cAmiId',
        'awsInstanceId': 'cawsInstId'
    }

    modified_data = {'objectClass': objectClass, 'ou': 'virtue'}

    for k in data.keys():
        tmp = data[k]
        if (k in always_string_values):
            tmp = str(tmp)
        else:
            tmp = json.dumps(tmp)
        modified_data[parse_map.get(k, k)] = tmp

    return modified_data


def parse_ldap_list(ls):

    ret = []

    try:
        for (dn, obj) in ls:
            obj2 = copy.copy(obj)
            parse_ldap(obj2)
            ret.append(obj2)
    except:
        return None

    return ret
