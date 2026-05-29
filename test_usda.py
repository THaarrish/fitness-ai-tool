import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import uuid


def test_rag_with_api(query):
    api_key = os.getenv("USDA_API_KEY")

    # 1. Fetch from API
    response = requests.get(
        "https://api.nal.usda.gov/fdc/v1/foods/search",
        params={
        "query": query,
        "api_key": api_key,
        "pageSize": 9,
        "dataType": "Foundation,SR Legacy",  # filters out branded food products
    }
    )
    foods = response.json().get("foods", [])

    # 2. Convert to text chunks
    chunks = []
    for food in foods:
        nutrients = food.get("foodNutrients", [])
        nutrient_text = ", ".join([
            f"{n['nutrientName']}: {n.get('value', 'N/A')} {n.get('unitName', '')}"
            for n in nutrients[:8]
        ])
        chunks.append(f"{food['description']}: {nutrient_text}")

    print(f"\n Chunks created: {len(chunks)}")
    for c in chunks:
        print(f" - {c[:100]}...")  # print first 100 chars of each

    # 3. Embed into ChromaDB
    documents = [Document(page_content=c) for c in chunks]
    collection_name = f"test_{uuid.uuid4().hex[:8]}"
    db = Chroma.from_documents(
        documents,
        OpenAIEmbeddings(),
        collection_name=collection_name
    )

    # 4. Run similarity search
    results = db.similarity_search(query, k=2)
    print(f"\n Retrieved chunks:")
    for r in results:
        print(f" - {r.page_content[:150]}...")

    # 5. Cleanup
    db.delete_collection()
    print("\n ChromaDB cleaned up ✅")


test_rag_with_api("creatine")

def test_usda_search(query):
    api_key = os.getenv("USDA_API_KEY")

    response = requests.get(
        "https://api.nal.usda.gov/fdc/v1/foods/search",
        params={
            "query": query,
            "api_key": api_key,
            "pageSize": 5
        }
    )

    print(f"Status code: {response.status_code}")
    data = response.json()

    for food in data.get("foods", []):
        print(f"\n Name: {food.get('description')}")
        print(f" Category: {food.get('foodCategory')}")
        print(f" FDC ID: {food.get('fdcId')}")


# Test it
test_usda_search("vitamin D")