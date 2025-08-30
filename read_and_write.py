import redis

# Connect to source-db (writes)
source_client = redis.Redis(
    host="redis-19361.re-cluster1.ps-redislabs.org",
    port=19361,
    decode_responses=True
)

# Connect to replica-db (reads)
replica_client = redis.Redis(
    host="redis-12035.re-cluster1.ps-redislabs.org",
    port=12035,
    decode_responses=True
)

# This piece will insert values 1-100 into source-db
for i in range(1, 101):
    source_client.set(f"num:{i}", i)

print("Inserted values 1–100 into source-db")

# Reads them in reverse order from replica-db
for i in range(100, 0, -1):
    val = replica_client.get(f"num:{i}")
    print(f"num:{i} -> {val}")
