from string import Template
import os


# TODO (asmirnov): pass tmpl_path via argument
# tmpl_path = 'config/trafficdb.cfg.example'
tmpl_path = 'map-integration-testing/config/trafficdb.cfg.example_japan'

with open(tmpl_path) as fh:
    tmpl = Template(fh.read())

subst_dict = {
    'BRF': os.environ['BRF'],
    'OLP_KEY_ID': os.environ['OLP_KEY_ID'],
    'OLP_SECRET': os.environ['OLP_SECRET']
}

if 'japan' not in tmpl_path:
    subst_dict['TML_AUTHORIZATION'] = os.environ['TML_AUTHORIZATION']

config = tmpl.safe_substitute(subst_dict)

with open('/workspace/trafficdb.cfg', "w") as fh:
    fh.write(config)
