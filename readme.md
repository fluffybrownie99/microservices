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
```

 docker build --pull --no-cache -t processor:latest .