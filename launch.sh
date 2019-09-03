set -e

# Launch the machines, set up disks, etc
ansible-playbook ./launch_nodes.yml -i inventory

# Some time for everything to come up
echo "Waiting 15 seconds for the VMs to come up"
sleep 15

# Provision, configure and initialize everything
ansible-playbook ./launch_cluster.yml -i inventory

