#!/usr/bin/python3
import json

import base

class SecurityCLI(base.BaseCLI):

    def __init__(self, ip, interactive=True):
        super().__init__(ip, interactive)

        self.base_url = 'https://{0}:5002/virtue/security'.format(ip)

        self.commands['security api config'] = self.sec_api_config
        self.commands['transducer list'] = self.trans_list
        self.commands['transducer get'] = self.trans_get
        self.commands['transducer enable'] = self.trans_enable
        self.commands['transducer disable'] = self.trans_disable
        self.commands['transducer get enabled'] = self.trans_get_enabled
        self.commands['transducer get configuration'] = self.trans_get_config
        self.commands['transducer list enabled'] = self.trans_list_enabled

    def sec_api_config(self):

        config_path = input('Configuration file (json): ')

        try:
            with open(config_path, 'r') as json_file:
                config = json.load(json_file)
        except FileNotFoundError:
            return '{0} does not exist.'.format(config_path)
        except IsADirectoryError:
            return '{0} is a directory.'.format(config_path)
        except json.decoder.JSONDecodeError:
            return 'Json file has invalid format.'

        result = self.session.get(self.base_url + '/api_config',
                                  params=config)
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_list(self):

        result = self.session.get(self.base_url + '/transducer/list')
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_get(self):

        trans_id = input('Transducer ID: ').strip()

        result = self.session.get(self.base_url + '/transducer/get',
                                  params={'transducerId': trans_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_enable(self):

        trans_id = input('Transducer ID: ').strip()
        virtue_id = input('Virtue ID: ').strip()
        config_path = input('Configuration file (json): ')

        try:
            with open(config_path, 'r') as json_file:
                config = json.load(json_file)
        except FileNotFoundError:
            return '{0} does not exist.'.format(config_path)
        except IsADirectoryError:
            return '{0} is a directory.'.format(config_path)
        except json.decoder.JSONDecodeError:
            return 'Json file has invalid format.'

        result = self.session.get(self.base_url + '/transducer/enable',
                                  params={
                                      'transducerId': trans_id,
                                      'virtueId': virtue_id,
                                      'configuration': json.dumps(config)
                                  })
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_disable(self):

        trans_id = input('Transducer ID: ').strip()
        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/transducer/disable',
                                  params={'transducerId': trans_id,
                                          'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_get_enabled(self):

        trans_id = input('Transducer ID: ').strip()
        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/transducer/get_enabled',
                                  params={'transducerId': trans_id,
                                          'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_get_config(self):

        trans_id = input('Transducer ID: ').strip()
        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url +'/transducer/get_configuration',
                                  params={'transducerId': trans_id,
                                          'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)

    def trans_list_enabled(self):

        virtue_id = input('Virtue ID: ').strip()

        result = self.session.get(self.base_url + '/transducer/list_enabled',
                                  params={'virtueId': virtue_id})
        data = result.json()
        
        return json.dumps(data, indent=4, sort_keys=True)
        

if (__name__ == '__main__'):

    cli = SecurityCLI(input('Excalibur address: ').strip())

    command = ''
    
    while (command != 'exit'):
        command = input('------- ')
        cli.handle_command(command)
