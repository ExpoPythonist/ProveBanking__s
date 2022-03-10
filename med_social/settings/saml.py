from os import path
import saml2
from saml2.saml import NAMEID_FORMAT_PERSISTENT
BASEDIR = path.dirname(path.abspath(__file__))
import logging
logging.basicConfig()


SAML_CONFIG = {
    # full path to the xmlsec1 binary programm

    'xmlsec_binary': '/usr/bin/xmlsec1',

    # your entity id, usually your subdomain plus the url to the metadata view
    'entityid': 'http://intuit.proven.cc/saml2/metadata/',

    # directory with attribute mapping
    'attribute_map_dir': path.join(BASEDIR, 'attribute_maps'),
    # this block states what services we provide
    'service': {
        # we are just a lonely SP
        'sp': {
            'name': 'Proven SP',
            'name_id_format': NAMEID_FORMAT_PERSISTENT,
            "allow_unsolicited": True,
            'endpoints': {
                # url and binding to the assetion consumer service view
                # do not change the binding or service name
                'assertion_consumer_service': [
                    ('http://intuit.proven.cc/saml2/acs/',
                     saml2.BINDING_HTTP_POST),
                ],
                # url and binding to the single logout service view
                # do not change the binding or service name
                'single_logout_service': [
                    ('http://intuit.proven.cc/saml2/ls/',
                     saml2.BINDING_HTTP_REDIRECT),
                    ('http://intuit.proven.cc/saml2/ls/post',
                     saml2.BINDING_HTTP_POST),
                ],
            },

            # attributes that this project need to identify a user
            'required_attributes': ['email',],

            # attributes that may be useful to have but not required
            'optional_attributes': ['eduPersonAffiliation'],

            # 'idp_url': 'https://app.onelogin.com/saml/metadata/494800',

            # # in this section the list of IdPs we talk to are defined
            # 'idp': {
            #     # we do not need a WAYF service since there is
            #     # only an IdP defined here. This IdP should be
            #     # present in our metadata

            #     # the keys of this dictionary are entity ids
            #     'https://app.onelogin.com/saml/metadata/494800': {
            #         'single_sign_on_service': {
            #             saml2.BINDING_HTTP_REDIRECT: 'https://gagan.onelogin.com/trust/saml2/http-post/sso/494800',
            #         },
            #         'single_logout_service': {
            #             saml2.BINDING_HTTP_REDIRECT: 'https://gagan.onelogin.com/trust/saml2/http-redirect/slo/494800',
            #         },
            #     },
            # },
        },
    },

    # set to 1 to output debugging information
    'debug': 1,

    # certificate
    'key_file': path.join(BASEDIR, 'key.pem'),  # private part
    'cert_file': path.join(BASEDIR, 'cert.pem'),  # public part

    "metadata": {
        "local": [path.join(BASEDIR, 'metadata/onelogin_metadata.xml'),
                  path.join(BASEDIR, 'metadata/intuit_metadata.xml')]
    },

    # own metadata settings
    'contact_person': [
        {'given_name': 'Kevin',
         'sur_name': 'Marcelo',
         'company': 'Proven.cc',
         'email_address': 'kevin@proven.cc',
         'contact_type': 'technical'},
        {'given_name': 'Suzanne',
         'sur_name': 'Jordan',
         'company': 'Proven.cc',
         'email_address': 'suzanne@proven.cc',
         'contact_type': 'administrative'},
    ],
    # you can set multilanguage information here
    'organization': {
        'name': [('Proven', 'en'),],
        'display_name': [('Proven', 'en'),],
        'url': [('http://proven.cc', 'en')],
    },
    'valid_for': 24,  # how long is our metadata valid
}
