import os
import asyncio
from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

load_dotenv()  # Load the .env file

GRAPHQL_API_KEY = os.environ.get("GRAPHQL_API_KEY")
GRAPHQL_ENDPOINT = os.environ.get("GRAPHQL_ENDPOINT")

async def test_connection():
    transport = AIOHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        headers={
            "x-api-key": GRAPHQL_API_KEY,
            'Content-Type': 'application/json',
        },
        timeout=30,  # 30 seconds timeout
    )
    
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    try:
        async with client as session:
            query = gql("""
            query {
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """)
            result = await session.execute(query)
            print("Connection successful!")
            print(result)
            return True
    except Exception as e:
        print(f"Error connecting: {str(e)}")
        return False

# Run the test
if __name__ == "__main__":
    print(f"Testing connection to: {GRAPHQL_ENDPOINT}")
    print(f"Using API key: {GRAPHQL_API_KEY[:5]}...")
    success = asyncio.run(test_connection())
    print(f"Connection test {'successful' if success else 'failed'}")