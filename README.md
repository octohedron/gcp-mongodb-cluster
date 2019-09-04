# GCP configurable MongoDB cluster

With this project you can launch your own MongoDB cluster with up to thousands of shards in Google Compute Cloud with just a few commands.

---

## Features

+ Easy to configure, with `ansible` YAML
+ Set any amount of shards
+ Latest `MongoDB version 4.0.12`
+ `XFS` file system for the replication nodes storage
+ Authentication enabled with `KeyFile` in all nodes 
+ Password protected with root user
+ Configured for simple vertical scaling
+ 2 Replication nodes and 1 arbiter per shard
+ 1 Config server
+ 1 Mongos

## What do you need?

+ `Ansible`, `Python` and `google-auth` python libraries
+ A google compute cloud account with billing enabled for the API's
+ A JSON service account file with the required permissions
+ A compute engine project

## Steps

+ Edit the `inventory/inventory.base.yml` file, changing
  + `PROJECT` with your google compute engine project
  + Change the `username` and `password`
  + Set your desired zone, it's configured for frankfurt's `europe-west3-b`.
  + Change the ansible ssh user, which should be your configured user in Google Compute Engine so the ssh keys are copied automatically when creating the instances.

NOTE: *You don't have to edit the rest of the configuration in the `inventory.base.yml` but it's contents are used for the inventory file that will be used, i.e. `inventory.yml`*

+ Configure the project with the `configure.py` script

```
$ python3 configure.py --shards 2 --id cl7
```

+ Place your service account JSON file downloaded from the google compute engine website in `~/gcp_sa.json`, you can change the path if you want editing the `inventory.gcp.yml` file

That will configure everything, first parameter of the script is the amount of shards, the second one is the cluster identifier which can't be more than 3 characters long, i.e. `cl8` or any combination of 3 characters.

+ Run the launch script

```
$ ./launch.sh
```

## How does it work?

+ The `configure.py` python script configures the `inventory` variables and the google compute inventory.
+ The launch script Launches the nodes, with the ansible command `ansible-playbook ./launch_nodes.yml -i inventory` which
  + Launches the instances based on the ubuntu 18.04 image
  + Creates the disks, etc.
  
You can edit this file `launch_nodes.yml` if you would like a different image, type of disk, instance type, etc.
For production you'd need a better instance type, i.e. not `f1-micro` and larger ssd disks, i.e. `"pd-ssd"` instead of `"pd-standard"`, etc.
+ Sets up the whole MongoDB cluster with `ansible-playbook ./launch_cluster.yml -i inventory`. This playbook imports all the set-up tasks in the right order, which are
  - `gcp_common.yml`  - *common provision to all nodes*
  - `gcp_xfs.yml`  - *set up XFS disks*
  - `t_gcp_node_p.yml`  - *provision replica set nodes*
  - `t_gcp_arbiter.yml`  - *provision shard arbiters*
  - `t_gcp_cluster.yml`  - *create replica sets in shards*
  - `t_gcp_node_auth.yml`  - *enable auth in nodes*
  - `t_gcp_arb_auth.yml`  - *enable auth in arbiters*
  - `t_gcp_config.yml`  - *provision config server*
  - `t_gcp_mongos.yml`  - *provision mongos server*

After all of this runs, you can go to your google compute engine page, find the mongos instance external IP address, connect and check the sharding status.

For example

```
$ mongo --host IP_ADDRESS:27017 \
        -u 'mongouser' -p '123456' --authenticationDatabase 'admin'
MongoDB shell version v4.0.11
MongoDB server version: 4.0.12
mongos> sh.status()
  shards:
    {  "_id" : "shrs0",  "host" : "shrs0/cl8-0-ab.c.PROJECT.internal:27017,cl8-0-n.c.PROJECT.internal:27017,cl8-2-n.c.PROJECT.internal:27017",  "state" : 1 }
    {  "_id" : "shrs1",  "host" : "shrs1/cl8-1-ab.c.PROJECT.internal:27017,cl8-1-n.c.PROJECT.internal:27017,cl8-3-n.c.PROJECT.internal:27017",  "state" : 1 }
  active mongoses:
    "4.0.12" : 1
  autosplit:
    Currently enabled: yes
  balancer:
    Currently enabled:  yes
    Currently running:  no
    Failed balancer rounds in last 5 attempts:  0
    Migration Results for the last 24 hours:
      No recent migrations
  databases:
    {  "_id" : "config",  "primary" : "config",  "partitioned" : true }
      config.system.sessions
        shard key: { "_id" : 1 }
```
*trimmed for clarirty, replace IP_ADDRESS with your mongos external IP.*

## Additional notes

The cluster is configured in a way in which you can reboot the nodes, after stopping all transactions of course and re-scale the instances, i.e. from `f1-micro` to `n1-highmem-2`, reboot it and enjoy the new computing power, or the other way around.

---

Something doesn't work? Open an issue.


Contributing? YES

LICENSE: MIT
