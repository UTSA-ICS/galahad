from saml2 import config, s_utils
from saml2.server import Server
from saml2.client import Saml2Client

__author__ = 'rolandh'

server = Server("idp_conf")

conf = config.SPConfig()
conf.load_file("server_conf")
client = Saml2Client(conf)

id, authn_request = client.create_authn_request(id = "id1",
                                    destination = "http://localhost:8088/sso")

print(authn_request)
intermed = s_utils.deflate_and_base64_encode("%s" % authn_request)

response = server.parse_authn_request(intermed)
