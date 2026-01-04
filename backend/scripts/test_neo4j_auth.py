import asyncio
from neo4j import AsyncGraphDatabase

async def test_auth(uri, user, password):
    print(f"Testing password: {password} ...", end=" ")
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        await driver.verify_connectivity()
        print("SUCCESS")
        await driver.close()
        return True
    except Exception as e:
        print(f"FAILED ({e})")
        return False

async def main():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    passwords = ["medkg2024", "neo4j", "password", "123456", "admin"]
    
    for pwd in passwords:
        if await test_auth(uri, user, pwd):
            print(f"\nFOUND CORRECT PASSWORD: {pwd}")
            return
            
    print("\nALL PASSWORDS FAILED")

if __name__ == "__main__":
    asyncio.run(main())
