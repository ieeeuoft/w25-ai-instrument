import pandas as pd
import numpy as np
import ast
from sentence_transformers import SentenceTransformer


def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def load_dataset(csv_filename):
    """
    Load the sounds dataset from a CSV.
    The CSV must have an 'embedding' column with string representations of a list.
    """
    df = pd.read_csv(csv_filename)
    df['embedding'] = df['embedding'].apply(ast.literal_eval)
    return df

def compute_query_embedding(query, model):
    """Compute the embedding vector for the query text."""
    return model.encode(query)

def find_best_match(query_embedding, csv_filename):
    """
    Compare the query embedding against all embeddings in the DataFrame,
    and return the row with the highest cosine similarity.
    """
    df = load_dataset(csv_filename)
    similarities = []
    for _, row in df.iterrows():
        sound_embedding = np.array(row['embedding'])
        sim = cosine_similarity(query_embedding, sound_embedding)
        similarities.append(sim)
    df['similarity'] = similarities
    df_sorted = df.sort_values(by='similarity', ascending=False)
    return df_sorted.iloc[0]

def text_to_filename(text, csv_filename):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = compute_query_embedding(text, model)
    best_match = find_best_match(query_embedding, csv_filename)
    return best_match['filename']


if __name__ == "__main__":
    text = "hard kick sound for hip hop or trap"
    csv_filename = "samples.csv"
    filename = text_to_filename(text, csv_filename)
    print(filename)
