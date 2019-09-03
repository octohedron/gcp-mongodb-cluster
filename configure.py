from os.path import dirname, realpath
import sys
# from pprint import pprint
from ruamel import yaml

import argparse

# New args parser
parser = argparse.ArgumentParser(description='Configure the deployment')

# The amount of shards
parser.add_argument('--shards', metavar='N', type=int,
                    help='The amount of shards')

# The cluster identifier
parser.add_argument('--id', type=str, help='The cluster identifier')


args = parser.parse_args()

if len(args.id) > 3:
    print(
        "ERROR: Cluster identifier should be at most 3 characters, i.e. 'clx'")
    sys.exit()

vars_p = dirname(realpath(__file__))
vars_base = vars_p + "/inventory/inventory.base.yml"
gcp_inv = vars_p + "/inventory/inventory.gcp.yml"
vars_file = vars_p + "/inventory/inventory.yml"

# Make project and rmem top-level variables for using in the gcp inventory
project = ""
replicas = []

# Parse and configure vars
with open(vars_base, 'r+') as f:
    hvars = yaml.load(f, Loader=yaml.Loader)
    # shards list
    shards = []
    shardrs = {}
    # Also set shardrs
    for s in range(0, args.shards):
        srd = "shrs"+str(s)
        shards.append(srd)
        shardrs[srd] = "rs" + str(s)
    hvars["all"]["vars"]["shardrs"] = shardrs
    # Set replicas
    for x in range(0, 2*args.shards):
        replicas.append(args.id + "-"+str(x)+"-n")
    hvars["all"]["vars"]["replicas"] = replicas
    # Set arbiters
    arbiters = []
    for x in range(0, args.shards):
        arbiters.append(args.id+"-"+str(x)+"-ab")
    hvars["all"]["vars"]["arbiters"] = arbiters
    # Set mongos
    mongos = [args.id + "-mg"]
    hvars["all"]["vars"]["mongos"] = mongos
    # Set config
    config = [args.id + "-cf"]
    hvars["all"]["vars"]["config"] = config
    # Set Replica sets
    rs = {}
    rmem = {}
    for i, r in enumerate(replicas):
        rs[r] = shards[i % len(shards)]
        rmem["rs" + str(i % len(shards))] = []
    # Set arbiters in replica sets
    for i in range(0, len(arbiters)):
        rs[arbiters[i]] = shards[i]
    hvars["all"]["vars"]["rs"] = rs
    # Set rmem
    project = hvars["all"]["vars"]["gcp_project"]
    idns = ".c."+project+".internal"
    for i, r in enumerate(replicas):
        rmem["rs" + str(i % len(shards))].append(r + idns)
    for i in range(0, len(arbiters)):
        rmem["rs" + str(i)].append(arbiters[i] + idns)
    hvars["all"]["vars"]["rmem"] = rmem
    hvars["all"]["vars"]["config_server"] =  \
        hvars["all"]["vars"]["config"][0]+idns
    hvars["all"]["vars"]["mongos_server"] = \
        hvars["all"]["vars"]["mongos"][0]+idns
    # Set shards
    srds = []
    for k, v in shardrs.items():
        srd = k + "/"
        for i, s in enumerate(rmem[v]):
            srd += s + ":27017"
            if i != 2:
                srd += ","
        srds.append(srd)
    hvars["all"]["vars"]["shards"] = srds

    # Write new config
    with open(vars_file, 'w') as f:
        yaml.dump(hvars, f, Dumper=yaml.RoundTripDumper)


# Parse and configure Inventory
with open(gcp_inv, 'r+') as f:
    inv = yaml.load(f, Loader=yaml.Loader)
    # Set projects list to this project
    inv["projects"] = [project]
    # Set filters to cluster identifier
    inv["filters"] = ["name = " + args.id + "*"]
    # pprint(inv)
    rsprimaries = ""
    for i in range(0, args.shards):
        rsprimaries += "'-{0}-n' in name".format(i)
        if i != args.shards - 1:
            rsprimaries += " or "
    inv["groups"]["rsprimaries"] = rsprimaries

    # Write new config
    with open(gcp_inv, 'w') as f:
        yaml.dump(inv, f, Dumper=yaml.RoundTripDumper)
