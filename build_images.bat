docker buildx build -f .\Dockerfile.Frontend    -t vch_frontend:latest . 
docker buildx build -f .\Dockerfile.Backend     -t vch_backend:latest . 
docker buildx build -f .\Dockerfile.Scheduler   -t vch_scheduler:latest . 