import asyncio
import os
import sys
from neo4j import AsyncGraphDatabase

async def verify():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "medkg2024")
    
    print(f"Connecting to {uri} as {user}...")
    
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    try:
        await driver.verify_connectivity()
        async with driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            count = record["count"]
            print(f"Total Nodes in DB: {count}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(verify())
