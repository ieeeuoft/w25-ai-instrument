from sentence_transformers import SentenceTransformer
import os
import csv
import numpy as np
from pathlib import Path
import json

# Use the existing model path
SENTENCE_MODEL_PATH = 'whisper_embeddings/all-MiniLM-L6-v2'

# Define allowed audio file extensions
AUDIO_FILE_EXTENSIONS = {'.wav', '.mp3'}

# Initialize the model using the existing path
print(f"Loading model from {SENTENCE_MODEL_PATH}...")
model = SentenceTransformer(SENTENCE_MODEL_PATH)
print("Model loaded successfully!")

def compute_query_embedding(query, model):
    """Compute the embedding vector for the query text."""
    return model.encode(query)

def get_existing_files(samples_csv):
    """Get a set of filenames that are already in the samples.csv file."""
    existing_files = set()
    if os.path.exists(samples_csv):
        with open(samples_csv, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row:  # Check if row is not empty
                    existing_files.add(row[0])
    return existing_files

def is_audio_file(file_path):
    """Check if the file is an audio file based on its extension."""
    return file_path.suffix.lower() in AUDIO_FILE_EXTENSIONS

def main():
    samples_dir = Path('samples')
    samples_csv = 'samples.csv'
    
    # Create CSV file with headers if it doesn't exist
    if not os.path.exists(samples_csv):
        with open(samples_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'description', 'file_path', 'embedding'])

    # Get list of files already in the database
    existing_files = get_existing_files(samples_csv)
    
    # Process each file in samples directory
    for file_path in samples_dir.glob('*'):
        if file_path.is_file():
            if not is_audio_file(file_path):
                print(f"\nSkipping {file_path.name} - not an audio file")
                continue
                
            if file_path.name in existing_files:
                print(f"\nSkipping {file_path.name} - already in database")
                continue
            
            # Get user input for description
            print(f"\nFile: {file_path.name}")
            description = input("Please enter a description for this sample: ")
            
            try:
                # Generate embedding for the description
                embedding = compute_query_embedding(description, model)
                
                # Save to CSV
                with open(samples_csv, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        file_path.name,
                        description,
                        str(file_path),
                        json.dumps(embedding.tolist())  # Convert to JSON string to keep it as one field
                    ])
                
                print(f"Added {file_path.name} to samples database")
            except Exception as e:
                print(f"\nError processing {file_path.name}: {str(e)}")

if __name__ == "__main__":
    main()
