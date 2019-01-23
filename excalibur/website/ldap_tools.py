import copy

# A static file to make LDAP more usable while implementing the VirtUE API


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
        tmp = json.loads(data.pop(k)[0])

        if (k in parse_map.keys()):
            data[parse_map[k]] = tmp
        elif (k[0] == 'c' and k != 'credentials'):
            data[k[1:]] = tmp
        elif (type(data[k]) == list):
            data[k] = tmp


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
        modified_data[parse_map.get(k, k)] = json.dumps(data[k])

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
