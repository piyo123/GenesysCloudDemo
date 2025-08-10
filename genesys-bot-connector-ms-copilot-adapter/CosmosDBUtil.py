import os
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from azure.cosmos.partition_key import PartitionKey

"""
 Cosmos DB 設定
"""
# Replace these values with your Cosmos DB connection information
endpoint = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_id = "databasename goes here"
container_id = "contaeiner name goes here"
partition_key = "partition key name goes here"

# Set the total throughput (RU/s) for the database and container
database_throughput = 1000

# Singleton CosmosClient instance
client = CosmosClient(endpoint, credential=key)

# Helper function to get or create database and container
async def get_or_create_container(client, database_id, container_id, partition_key):
    database = await client.create_database_if_not_exists(id=database_id)
    print(f'Database "{database_id}" created or retrieved successfully.')

    container = await database.create_container_if_not_exists(id=container_id, partition_key=PartitionKey(path=partition_key))
    print(f'Container with id "{container_id}" created or retrieved successfully.')
 
    return container
 
async def upsert_conversation_data(genesysConversationId, msCopilotConversationId, msCopilotWatermark):
    container = await get_or_create_container(client, database_id, container_id, partition_key)
    
    await container.upsert_item({
        'id': f'{genesysConversationId}',
        'fixedkey': "genesys_bot_connector_ms_copilot_session", # 同じPartitionにするために固定
        'genesysConversationId': f'{genesysConversationId}',
        'msCopilotConversationId': f'{msCopilotConversationId}',
        'msCopilotWatermark': f'{msCopilotWatermark}'
    })
 
async def get_all_conversations_data():
    items = []
    container = await get_or_create_container(client, database_id, container_id, partition_key)
    async for item in container.read_all_items():
        items.append(item)
    return items

async def get_conversation_data2(genesysConversationId):
    container = await get_or_create_container(client, database_id, container_id, partition_key)
    query = f"SELECT * FROM c WHERE c.genesysConversationId = '{genesysConversationId}'"
    items = []
    async for item in container.query_items(query=query, enable_cross_partition_query=False):
        items.append(item)
    return items

async def get_conversation_data(genesysConversationId):
    container = await get_or_create_container(client, database_id, container_id, partition_key)
    
    try:
        document = await container.read_item(item=genesysConversationId, partition_key="genesys_bot_connector_ms_copilot_session")
        print(document)
        return document
    except exceptions.CosmosResourceNotFoundError as e:
        return None
