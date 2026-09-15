import json,sys
r=json.load(open(sys.argv[1]))
assert r=={"answer":"ASTRA_CONTROLLER_OK","code":""}
