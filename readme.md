# Microservices Project for a Home Server setup

The goal of this project is to be a myriad of containerized microservices to run on a local media server using RESTful APIs for media uploads and media retrieval (or playbacks)
- **Audit**: Provides two endpoints for retrieving media upload and media playback information through our Kafka Client
- **Kafka/Mysql**: Provides a single container for Kafka, Zookeeper. and our MySQL database.
- **Receiver**: The primary endpoints that we will interact with, which will communicate with our other endpoints privately.
- **Storage**: Provides a container that handles storing and retrieving data regarding server media to the MySQL database using messages.
- **Processor**: Retrieves data from the Storage Service and processes basic statistics.

about media uplaods and media retrieval (or playbacks).   


# Docker commands

```bash
cd ./kafkamysqldocker
docker-compose up -d
```

```bash
cd ../receiver
docker build -t receiver:latest .
docker run -d -p 8080:8080 receiver:latest
```

```bash
cd ../storage
docker build -t storage:latest .
docker run -d -p 8090:8090 storage
```

```bash
cd ../processor
docker build -t processing:latest .
docker run -d -p 8100:8100 --network="host" processing:latest
```

```bash
cd ../audit
docker build -t audit_log:latest .
docker run -d -p 8110:8110 audit_log:latest
```

 docker build --pull --no-cache -t processor:latest .


 ```bash
 
cd ./kafkamysqldocker
docker-compose up -d

cd ../receiver
docker build -t receiver:latest .
docker run -d -p 8080:8080 receiver:latest

cd ../storage
docker build -t storage:latest .
docker run -d -p 8090:8090 storage

cd ../processor
docker build -t processing:latest .
docker run -d -p 8100:8100 --network="host" processing:latest

cd ../audit
docker build -t audit_log:latest .
docker run -d -p 8110:8110 audit_log:latest

 ```


 # Prep for compose

 ```bash
cd ./kafkamysqldocker
docker-compose up -d

cd ../receiver
docker build -t receiver:latest .

cd ../storage
docker build -t storage:latest .

cd ../processor
docker build -t processing:latest .

cd ../audit
docker build -t audit_log:latest .


 
 ```
