# This is a temporary file. To run, call the command
#     python ~/galahad/excalibur/test_role_create.py
# from the assembler directory.

from website.apiendpoint_admin import EndPoint_Admin

role = {
    'name': 'TestAssembler',
    'version': '1.0',
    'applicationIds': ['firefox'],
    'startingResourceIds': [],
    'startingTransducerIds': []
}

epa = EndPoint_Admin('jmitchell', 'Test123!')

print(epa.role_create(role))
