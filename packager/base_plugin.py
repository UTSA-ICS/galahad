class PackagerPlugin():

    id = 'default'
    name = 'default'
    version_str = '1.0'
    version_int = 1
    description = 'The default plugin object'

    def __init__(self, file_interface):
        self.file_interface = file_interface

    # Called before export
    @staticmethod
    def get_required_app_configs(apps):
        for app in apps:
            if (app['name'].lower() == 'firefox'):
                return [app['id']]

    def export_virtue(self, virtue_id, apps):

        # For Firefox:
        # Copy entire firefox dir to package
        self.file_interface.copy_to_package('', '', 'firefox', recursive=True)

        return {}

    def interrogate_package(self, data):
        # Read available files and return a string summarizing the contents
        # Do not make any SSH calls
        print('This is a plugin')

    def import_virtue(self, virtue_id, data, apps):
        # Run commands and scp files over

        self.file_interface.copy_from_package('', '', 'firefox',
                                              recursive=True)
