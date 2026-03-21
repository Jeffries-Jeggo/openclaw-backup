#!/bin/bash
set -e
docker pull qdrant/qdrant:latest
docker run -d --name qdrant \\
  -p 6333:6333 \\
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \\
  qdrant/qdrant:latest
echo "Qdrant started: http://localhost:6333/dashboard"
echo "Stop: docker stop qdrant"
echo "Logs: docker logs qdrant"
echo "Storage: $(pwd)/qdrant_storage"