#!/bin/bash

docker build -t d2-armor-analyzer .
docker run -p 8501:8501 d2-armor-analyzer