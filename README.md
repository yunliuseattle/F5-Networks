# F5-Networks

from f5.bigip import ManagementRoot

# Connect to the BIG-IP
mgmt = ManagementRoot("bigip.example.com", "admin", "somepassword")

# Get a list of all pools on the BigIP and print their name and their
# members' name
pools = mgmt.tm.ltm.pools.get_collection()
for pool in pools:
    print pool.name
    for member in pool.members_s.get_collection():
        print member.name

# Create a new pool on the BigIP
mypool = mgmt.tm.ltm.pools.pool.create(name='mypool', partition='Common')

# Load an existing pool and update its description
pool_a = mgmt.tm.ltm.pools.pool.load(name='mypool', partition='Common')
pool_a.description = "New description"
pool_a.update()

# Delete a pool if it exists
if mgmt.tm.ltm.pools.pool.exists(name='mypool', partition='Common'):
    pool_b = mgmt.tm.ltm.pools.pool.load(name='mypool', partition='Common')
    pool_b.delete()
