#!/bin/bash

# Generate the docker-compose.yml file
python generate_docker_compose.py

# Deploy using Docker Compose
docker-compose up --build
