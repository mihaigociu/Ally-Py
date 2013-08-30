#!/bin/sh

#PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-api"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-core"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-core-http"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-core-sqlalchemy"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-http"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/service-cdm"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-http-asyncore-server"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-http-mongrel2-server"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-plugin"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/ally-indexing"

PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/support-sqlalchemy"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/security"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/gui-core"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/support-cdm"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/gateway"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/indexing"

PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/service-assemblage"
PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/components/service-gateway"

PYTHONPATH=$PYTHONPATH:"/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/plugins/gateway-acl"

export PYTHONPATH
echo $PYTHONPATH

idle3 -r "/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/distribution/application.py" &
#python3 "/home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/distribution/application.py"
#python3 /home/mihai/allypy-workspace/apy-8-implement-x-filter/Ally-Py/distribution/application.py -dump
#python3
