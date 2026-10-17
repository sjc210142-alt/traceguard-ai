from falkordb import FalkorDB

# Connect to our local FalkorDB server
db = FalkorDB(
    host="localhost",
    port=6379
)

# Select our existing graph
graph = db.select_graph("traceguard")

# Find accounts sharing a device
query = """
MATCH
    (a:Account)-[:USES_DEVICE]->(d:Device)
    <-[:USES_DEVICE]-(b:Account)
WHERE a.id = $account_id
  AND a.id <> b.id
RETURN
    a.id AS investigated_account,
    d.id AS shared_device,
    b.id AS connected_account
"""
# Execute the query
result = graph.query(
    query,
    params={"account_id": "ACC001"}
)

# Display the results
print("Connected accounts:")

for record in result.result_set:
    print(record)
