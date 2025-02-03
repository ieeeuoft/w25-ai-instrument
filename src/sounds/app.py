from flask import Flask, request, jsonify
from dotenv import load_dotenv
import csv
import json
import requests
import os
import pinecone
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

model = SentenceTransformer('all-MiniLM-L6-v2')

app = Flask(__name__)
# Load environment variables
load_dotenv()
# API keys for Freesound and OpenAI
FREESOUND_API_KEY = os.getenv('FREESOUND_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

# Initialize Pinecone
pc = Pinecone(
    api_key=os.environ.get("PINECONE_API_KEY")
)

index_name = "freesound-sounds"  # Index name

index = pc.Index(index_name)
print(index)


# Blank route
@app.route('/')
def home():
    return "Welcome to my Flask backend!"

# Route to search Freesound for sounds
@app.route('/search_sound', methods=['GET'])
def search_sounds():
    query = request.args.get('query', 'nature')  # Default to 'nature' if no query
    try:
        # Make a request to Freesound's API
        url = f"https://freesound.org/apiv2/search/text/"
        params = {
            "query": query,
            "fields": "id,name,previews,description",  # Specify fields to include in the response
            "token": FREESOUND_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error if the request fails

        # Parse and return the response JSON
        results = response.json()
        sounds = []
        for sound in results.get('results', []):
            sounds.append({
                "id": sound["id"],
                "name": sound["name"],
                "description": sound["description"],
                "preview": sound["previews"]["preview-lq-mp3"]  # Low-quality preview URL
            })

        return jsonify(sounds)

    except requests.exceptions.RequestException as e:  # Corrected this line
        return jsonify({"error": str(e)}), 500


# Fetch and process random sounds, embed descriptions, and save locally
@app.route('/random_search', methods=['GET'])
def random_search_sounds():
    query = request.args.get('query', 'sound')  # Default to 'sound'
    try:
        # Fetch sounds from Freesound API
        url = f"https://freesound.org/apiv2/search/text/"
        params = {
            "query": query,
            "fields": "id,name,previews,description",
            "token": FREESOUND_API_KEY,
            "page_size": 50
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get('results', [])

        # Prepare metadata and descriptions for embedding
        sound_metadata = []
        descriptions = []
        for sound in results:
            sound_metadata.append({
                "id": sound["id"],
                "name": sound["name"],
                "description": sound["description"],
                "preview": sound["previews"]["preview-lq-mp3"]
            })
            descriptions.append(sound["description"])

        # Generate embeddings for descriptions
        embeddings = model.encode(descriptions, show_progress_bar=True)

        # Save to CSV
        save_to_csv(sound_metadata, embeddings)

        # Push to Pinecone
        push_to_pinecone(sound_metadata, embeddings)

        return jsonify(sound_metadata)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/search', methods=['GET', 'POST'])
def search_embeddings():
    try:
        if request.method == 'POST':
            query_text = request.json.get('query', '')
        else:  # GET request
            query_text = request.args.get('query', '')

        if not query_text:
            return jsonify({"error": "Query text is required"}), 400

        query_embedding = model.encode([query_text])[0].tolist()

        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )

        # Correctly handle the results from Pinecone
        matches = results.get('matches', [])
        response_data = []
        for match in matches:
            response_data.append({
                "id": match['id'],
                "score": match['score'],
                "metadata": match.get('metadata', {})
            })

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/test', methods=['POST'])
def test():
    return jsonify({"message": "POST request received"})

# Save metadata and embeddings to a CSV
def save_to_csv(metadata, embeddings, filename='sounds.csv'):
    data = {
        "id": [item["id"] for item in metadata],
        "name": [item["name"] for item in metadata],
        "description": [item["description"] for item in metadata],
        "preview": [item["preview"] for item in metadata],
        "embedding": [list(embedding) for embedding in embeddings]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)


# Push metadata and embeddings to Pinecone
def push_to_pinecone(metadata, embeddings):
    for item, embedding in zip(metadata, embeddings):
        index.upsert([(str(item["id"]), embedding, {"name": item["name"], "description": item["description"]})])


# Run the app
if __name__ == '__main__':
    app.run(debug=True)