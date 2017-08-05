import os
import yaml

def Get(k = None):
  # Load region name to coordinate
  fn = "%s/config.yaml" % os.path.dirname(__file__)
  with open(fn) as fo:
    root = yaml.load(fo)
  #Cons.P(pprint.pformat(root))

  return root[k]
