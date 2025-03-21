from fastmcp import FastMCP
from typing import Optional, Dict, Any

# GraphQL Server
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from graphql import print_schema

import json
import os
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Create a named server
mcp = FastMCP("GQL")

from dotenv import load_dotenv

load_dotenv()  # Load the .env file

GRAPHQL_API_KEY = os.environ.get("GRAPHQL_API_KEY")
GRAPHQL_ENDPOINT = os.environ.get("GRAPHQL_ENDPOINT")

class GraphQLClient:
    def __init__(self, endpoint: str):
        self.transport = AIOHTTPTransport(
            url=endpoint,
            headers={
                "x-api-key": GRAPHQL_API_KEY,
                'Content-Type': 'application/json',
            },
            timeout=60,  # 60 seconds timeout
        )
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)
        self.schema = None  # Cache for schema
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_schema(self) -> str:
        """Fetch and return the GraphQL schema as a string"""
        if self.schema is not None:
            return self.schema
            
        async with self.client as session:
            schema = session.client.schema
            self.schema = print_schema(schema)
            return self.schema
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query and return the results"""
        async with self.client as session:
            result = await session.execute(gql(query), variable_values=variables)
            return result

client = GraphQLClient(GRAPHQL_ENDPOINT)

@mcp.tool()
async def connect_graphql() -> str:
    """Connect to the GraphQL endpoint and fetch its schema"""
    try:
        # Use a simple test query first to verify connectivity
        async with client.client as session:
            test_query = gql("""
            query {
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """)
            await session.execute(test_query)
        
        # If we get here, the connection is working, now get the schema
        schema = await client.get_schema()
        return f"Successfully connected to {GRAPHQL_ENDPOINT}. Schema loaded."
    except Exception as e:
        return f"Error connecting to GraphQL endpoint: {str(e)}"

@mcp.tool()
async def generate_query(description: str) -> str:
    """Generate a GraphQL query based on the schema and user description"""
    try:
        schema = await client.get_schema()
        
        # Provide context about the schema and request to help generate the query
        prompt = f"""Given this GraphQL schema:

{schema}

Generate a GraphQL query that: {description}.

Please note that the GraphQL API is designed to answer policy questions for a specific organization.
The quesions of the users related to a speicific country where they are located or want to go. 
When you generate a GraphQL query, the query should be focused on the country, and therefore use the state query, with the short code of the country as the id (for example: "id": "FR", for France).
When you ask for policies, don't filter by their names, as you don't know them yet. Once you get the policies, you can filter by their names.
Please note that you should also request the policy holder of the policies, and then check for their type. The policies are organized in an hierarchy, where lower levels override higher levels (for example: a policy of a country can override a policy of a region).
For example, here is a query to get all the policies of a state:
```graphql
query sampleCountryQuery {{
  country(id: "KR") {{
    country_name
    policies {{
      policy_type
      policy_document
      policy_holder {{
        __typename
      }}
    }}
  }}
}}
```

Return only the GraphQL query without any explanation."""
        
        return prompt
    except Exception as e:
        return f"Error generating query: {str(e)}"

@mcp.tool()
async def execute_graphql(query: str, variables: Optional[str] = None) -> str:
    """Execute a GraphQL query against the connected endpoint"""
    try:
        vars_dict = json.loads(variables) if variables else None
        result = await client.execute_query(query, vars_dict)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing query: {str(e)}"


@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m ** 2)
