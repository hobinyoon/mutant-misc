#!/bin/bash

set -e
set -u
set -x

# Make changes in effect
#
# Seems like it won't change the limit while a process under the cgroup is running
#   audrey@vostro200:~$ sudo cgconfigparser -l /etc/cgconfig.conf
#     cgconfigparser; error loading /etc/cgconfig.conf: This kernel does not support this feature
sudo cgconfigparser -l ./cgconfig.conf

cgexec -g memory:small_mem ./cgroup-test.py

# Memory statistics
#   /sys/fs/cgroup/memory/small_mem/memory.stat
