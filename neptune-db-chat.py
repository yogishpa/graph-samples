import streamlit as st
import boto3
import requests
from llama_index.llms.bedrock import Bedrock
from llama_index.core import PromptTemplate
import json

# Initialize Bedrock LLM
@st.cache_resource
def init_llm():
    return Bedrock(
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        region_name="us-east-1"
    )

# Neptune connection
@st.cache_resource
def init_neptune():
    # For OpenCypher, we use the base URL
    return 'https://YOUR-NEPTUNE-CLUSTER.us-east-1.neptune.amazonaws.com:8182'

# Query generation prompt
CYPHER_PROMPT = PromptTemplate(
    "Given this natural language question: {question}\n"
    "Generate a valid OpenCypher query for Neptune database with airroutes dataset.\n"
    "Schema: Nodes have label 'airport'. Relationships are 'route' between airports.\n"
    "There are NO separate country nodes - country is a property of airport nodes.\n"
    "Airport properties include: code, icao, desc, region, runways, country, city, lat, lon, continent, elev\n"
    "Route properties include: dist (distance)\n"
    "Examples:\n"
    "- MATCH (n:airport) RETURN n.code, n.city LIMIT 5\n"
    "- MATCH (a1:airport)-[r:route]->(a2:airport) RETURN a1.code, a2.code, r.dist LIMIT 5\n"
    "- MATCH (a:airport) WHERE a.country = 'US' RETURN a.code, a.city LIMIT 5\n"
    "- MATCH (a:airport) WHERE a.country = 'DE' RETURN a.code, a.city LIMIT 5\n"
    "- MATCH (a1:airport)-[r:route]->(a2:airport) WHERE a1.country = 'US' AND a2.country = 'CA' RETURN a1.code, a2.code, r.dist LIMIT 5\n"
    "Return ONLY the OpenCypher query, no explanations or markdown:\n"
)

def generate_cypher_query(llm, question):
    prompt = CYPHER_PROMPT.format(question=question)
    response = llm.complete(prompt)
    query = response.text.strip()
    # Clean the query
    if query.startswith('```'):
        query = query.split('\n')[1:-1]
        query = '\n'.join(query)
    return query.strip()

def execute_neptune_query(neptune_endpoint, query):
    try:
        # For OpenCypher, we use the HTTP endpoint
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Prepare the request
        endpoint = f"{neptune_endpoint}/openCypher"
        payload = {'query': query}
        
        # Execute the query
        response = requests.post(endpoint, headers=headers, data=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()['results']
        else:
            return {"error": f"HTTP Error {response.status_code}: {response.text}"}
    except Exception as e:
        # Return error as dict to avoid JSON parsing issues
        return {"error": str(e)}

def format_results(llm, results, original_question):
    # Check if results is an error
    if isinstance(results, dict) and "error" in results:
        return f"Error executing query: {results['error']}"
    
    prompt = f"Convert these database results into natural language answer for: {original_question}\nResults: {results}"
    response = llm.complete(prompt)
    return response.text

# Debug functions to explore the database
def test_neptune_connection():
    try:
        endpoint = init_neptune()
        # Simple test query
        test_query = "MATCH (n:airport) RETURN n.code LIMIT 1"
        result = execute_neptune_query(endpoint, test_query)
        return "Connection successful", result
    except Exception as e:
        return f"Connection failed: {str(e)}", None

def explore_schema():
    endpoint = init_neptune()
    # Get node labels
    labels_query = "MATCH (n) RETURN DISTINCT labels(n) LIMIT 10"
    labels_result = execute_neptune_query(endpoint, labels_query)
    
    # Get relationship types
    rel_query = "MATCH ()-[r]->() RETURN DISTINCT type(r) LIMIT 10"
    rel_result = execute_neptune_query(endpoint, rel_query)
    
    # Get airport properties
    airport_query = "MATCH (a:airport) RETURN a LIMIT 1"
    airport_result = execute_neptune_query(endpoint, airport_query)
    
    # Get countries
    countries_query = "MATCH (a:airport) RETURN DISTINCT a.country LIMIT 10"
    countries_result = execute_neptune_query(endpoint, countries_query)
    
    # Get German airports
    german_airports_query = "MATCH (a:airport) WHERE a.country = 'DE' RETURN a.code, a.city LIMIT 5"
    german_airports_result = execute_neptune_query(endpoint, german_airports_query)
    
    return {
        "labels": labels_result,
        "relationships": rel_result,
        "airport_sample": airport_result,
        "countries": countries_result,
        "german_airports": german_airports_result
    }

# Streamlit UI
st.title("Neptune Database Chat")

# Add debug buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Test Connection"):
        status, result = test_neptune_connection()
        st.write(status)
        if result and not isinstance(result, str):
            st.json(result)

with col2:
    if st.button("Explore Schema"):
        with st.spinner("Exploring database schema..."):
            schema_info = explore_schema()
            st.subheader("Node Labels")
            st.json(schema_info["labels"])
            
            st.subheader("Relationship Types")
            st.json(schema_info["relationships"])
            
            st.subheader("Airport Sample")
            st.json(schema_info["airport_sample"])
            
            st.subheader("Countries (from airport.country property)")
            st.json(schema_info["countries"])
            
            st.subheader("German Airports (if any)")
            st.json(schema_info["german_airports"])

# Direct query execution
st.subheader("Test Direct Query")
test_query = st.text_area("Enter OpenCypher query to test:", 
                         "MATCH (a:airport) RETURN a.code, a.city LIMIT 5")
if st.button("Run Test Query"):
    with st.spinner("Executing query..."):
        endpoint = init_neptune()
        result = execute_neptune_query(endpoint, test_query)
        if isinstance(result, dict) and "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.json(result)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your graph data"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Generating query..."):
            llm = init_llm()
            neptune_endpoint = init_neptune()
            
            # Generate OpenCypher query
            cypher_query = generate_cypher_query(llm, prompt)
            st.code(cypher_query, language="cypher")
            
            # Execute query
            results = execute_neptune_query(neptune_endpoint, cypher_query)
            
            # Format response
            if isinstance(results, dict) and "error" in results:
                response = f"Error executing query: {results['error']}"
            else:
                response = format_results(llm, results, prompt)
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
