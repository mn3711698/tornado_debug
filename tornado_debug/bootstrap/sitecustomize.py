# coding: utf8
import os
import sys
import imp
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# We need to import the original sitecustomize.py file if it exists. We
# can't just try and import the existing one as we will pick up
# ourselves again. Even if we remove ourselves from sys.modules and
# remove the bootstrap directory from sys.path, still not sure that the
# import system will not have cached something and return a reference to
# ourselves rather than searching again. What we therefore do is use the
# imp module to find the module, excluding the bootstrap directory from
# the search, and then load what was found.

boot_directory = os.path.dirname(__file__)
#root_directory = os.path.dirname(os.path.dirname(boot_directory))
path = list(sys.path)

if boot_directory in path:
    del path[path.index(boot_directory)]

try:
    (file, pathname, description) = imp.find_module('sitecustomize', path)
except ImportError:
    pass
else:
    imp.load_module('sitecustomize', file, pathname, description)


from tornado_debug import agent

#if root_directory in sys.path:
#    del sys.path[sys.path.index(root_directory)]

# Finally initialize the agent.

agent.initialize()
