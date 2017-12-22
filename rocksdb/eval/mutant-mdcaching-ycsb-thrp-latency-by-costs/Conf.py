import os
import sys
import yaml

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons


_yaml_root = None

def Get(k):
  global _yaml_root

  if _yaml_root is not None:
    return _yaml_root[k]

  # Load region name to coordinate
  fn = "%s/config.yaml" % os.path.dirname(__file__)
  with open(fn) as fo:
    _yaml_root = yaml.load(fo)
  #Cons.P(pprint.pformat(_yaml_root))

  return _yaml_root[k]


def GetDir(k):
  return Get(k).replace("~", os.path.expanduser("~"))


def GetOutDir():
  return "%s/.output" % os.path.dirname(__file__)
