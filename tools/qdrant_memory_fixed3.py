#!/usr/bin/env python3
import sys
import os
import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

print("Starting Qdrant memory sync (fixed IDs)...", file=sys.stderr)

client = QdrantClient("localhost", port=6333, timeout=30)
model = SentenceTransformer('all-MiniLM-L6-v2')
COLLECTION = "openclaw_memory"

def ensure_collection(dim=384):
    """Create collection if not exists, else delete and recreate."""
    print(f"Ensuring collection '{COLLECTION}'...", file=sys.stderr)
    # Recreate collection (deletes existing)
    try:
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print("Collection OK", file=sys.stderr)
    except Exception as e:
        print(f"Collection error: {e}", file=sys.stderr)
        sys.exit(1)

if sys.argv[1] == 'sync':
    ensure_collection()
    memories_dir = '/home/ubuntu/.openclaw/workspace/memory'
    total_chunks = 0
    for f in os.listdir(memories_dir):
        if not f.endswith('.md'):
            continue
        path = os.path.join(memories_dir, f)
        print(f"Processing {f}...", file=sys.stderr)
        try:
            with open(path, 'r', encoding='utf-8') as fd:
                content = fd.read()
        except Exception as e:
            print(f"  Failed to read {f}: {e}", file=sys.stderr)
            continue
        # Split into ~4000 char chunks
        chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
        points = []
        for i, chunk in enumerate(chunks):
            # Generate valid integer ID (positive 64-bit)
            point_id = hash(f"{f}:{i}") & 0x7FFFFFFFFFFFFFFF
            embedding = model.encode(chunk).tolist()
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={'file': f, 'snippet': chunk[:500]}
            )
            points.append(point)
        if points:
            try:
                client.upsert(collection_name=COLLECTION, points=points)
                total_chunks += len(points)
                print(f"  Upserted {len(points)} chunks for {f}", file=sys.stderr)
            except Exception as e:
                print(f"  Upsert failed for {f}: {e}", file=sys.stderr)
    print(json.dumps({'synced': total_chunks}))

elif sys.argv[1] == 'search':
    query = sys.argv[2]
    query_emb = model.encode(query).tolist()
    response = client.query_points(
        collection_name=COLLECTION,
        query=query_emb,
        limit=5
    )
    results = []
    for point in response.points:
        results.append({
            'file': point.payload.get('file', ''),
            'snippet': point.payload.get('snippet', ''),
            'score': point.score
        })
    print(json.dumps(results))

else:
    print(json.dumps({'error': 'usage: sync|search <query>'}), file=sys.stderr)