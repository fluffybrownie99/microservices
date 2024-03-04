# Docker commands

```bash
cd ./kafkamysqldocker
docker-compose up -d
```

```bash
cd receiver
docker build -t receiver:latest .
docker run -d -p 8080:8080 receiver
```

```bash
cd ../storage
docker build -t storage:latest .
docker run -d -p 8090:8090 storage
```

```bash
cd ../processor
docker build -t processing:latest .
docker run -d -p 8100:8100 --network="host" processing
```

```bash
cd ../audit
docker build -t audit_log:latest .
docker run -d -p 8110:8110 audit_log
```

 docker build --pull --no-cache -t processor:latest .