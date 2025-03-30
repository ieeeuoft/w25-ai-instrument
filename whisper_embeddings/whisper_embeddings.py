import os
import ast
import pandas as pd
import numpy as np
import requests
import subprocess
from sentence_transformers import SentenceTransformer

CSV_FILENAME = "sounds.csv"             # Path to CSV file with sound metadata and embeddings
QUERY_FILENAME = "transcript.txt"       # Text file with sample query
TEMP_MP3_FILENAME = "temp_sound.mp3"    # Temporary filename to save the downloaded preview

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def load_dataset(csv_filename):
    """
    Load the sounds dataset from a CSV.
    The CSV is expected to have a column 'embedding' where each entry is a string representation of a list.
    """
    df = pd.read_csv(csv_filename)
    # Convert the embedding column from string to actual list of floats using ast.literal_eval
    df['embedding'] = df['embedding'].apply(ast.literal_eval)
    return df

def get_query_text(filename):
    """Read and return query text from a given text file."""
    with open(filename, 'r') as f:
        return f.read().strip()

def compute_query_embedding(query, model):
    """Compute the embedding vector for the given query text using the provided model."""
    return model.encode(query)

def find_best_match(query_embedding, df):
    """
    Compare the query embedding against all embeddings in the DataFrame,
    and return the row with the highest cosine similarity.
    """
    similarities = []
    for _, row in df.iterrows():
        sound_embedding = np.array(row['embedding'])
        sim = cosine_similarity(query_embedding, sound_embedding)
        similarities.append(sim)
    df['similarity'] = similarities
    df_sorted = df.sort_values(by='similarity', ascending=False)
    return df_sorted.iloc[0]

def download_sound(url, filename):
    """
    Download the sound file from the provided URL and save it locally.
    """
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as f:
        f.write(response.content)

def play_sound(filename):
    """
    Play the sound file using omxplayer.
    This method uses subprocess to call omxplayer; adjust if you prefer a different player.
    """
    try:
        subprocess.run(["mpv", filename], check=True)
    except subprocess.CalledProcessError as e:
        print("Error playing sound:", e)

# ----- MAIN SCRIPT -----
def main():
    print("Loading sentence transformer model...")
    model_path = '/home/athavan/Downloads/all-MiniLM-L6-v2'
    model = SentenceTransformer(model_path)
    print("Model loaded successfully from local path")
    
    print(f"Reading query from {QUERY_FILENAME} ...")
    query_text = get_query_text(QUERY_FILENAME)
    if not query_text:
        print("Query text file is empty. Exiting.")
        return

    print("Computing embedding for the query...")
    query_embedding = compute_query_embedding(query_text, model)

    print(f"Loading dataset from {CSV_FILENAME} ...")
    df = load_dataset(CSV_FILENAME)
    
    print("Searching for the best matching sound...")
    best_match = find_best_match(query_embedding, df)
    
    print("\nBest Matching Sound:")
    print("ID:", best_match['id'])
    print("Name:", best_match['name'])
    print("Description:", best_match['description'])
    print("Preview URL:", best_match['preview'])
    print("Similarity Score:", best_match['similarity'])
    
    preview_url = best_match['preview']
    print(f"\nDownloading preview from {preview_url} ...")
    try:
        download_sound(preview_url, TEMP_MP3_FILENAME)
    except requests.exceptions.RequestException as e:
        print("Error downloading sound:", e)
        return

    # Play the downloaded sound using omxplayer on Raspberry Pi
    print("Playing the sound...")
    play_sound(TEMP_MP3_FILENAME)
    if os.path.exists(TEMP_MP3_FILENAME):
        os.remove(TEMP_MP3_FILENAME)
    print("Done.")

if __name__ == '__main__':
    main()
