# LSDP
Large scale data processing

![Architecture](assets/architecture.png)

The aim of the project is to create a distributed system for analyzing reddit posts.

Main assumption was to use Celery for management scheduled task, queues and 3 type of workers. Scheduled task split scrapping task for group of workers. These workers also publish basic metrics of scrapped post for example post length, tags, time. Metrics were inserted to InfluxDB and there was used Grafana for visualize this metrics.

In next step posts are going to text embedding workers and Database workers.
All information was saved in mongoDB. 

Embeddings were used to train ML models using Spark

## Quick start
- clone repo
- download GoogleNews-vectors-negative300-SLIM.bin to main folder
- ```docker-compose up```
