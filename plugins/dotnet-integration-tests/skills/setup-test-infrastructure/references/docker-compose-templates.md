# Docker Compose Templates

Use these snippets to assemble a `docker-compose.yml` for integration test dependencies.
Start with the **header**, then append one **service snippet** per detected dependency.

Run with `docker compose up -d` before executing your integration tests.
Run `docker compose down` to clean up.

> **Note:** All snippets use 2-space indentation. YAML is whitespace-sensitive — preserve indentation exactly when copying service blocks.

---

## Header / Structure Template

```yaml
services:
  # --- paste service snippets below ---
```

No `version:` key is needed for Compose Specification (Docker Desktop 4.x+ / Docker Engine 23+).

---

## PostgreSQL

```yaml
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpassword
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testdb"]
      interval: 5s
      timeout: 5s
      retries: 5
```

Connection string: `Host=localhost;Port=5432;Database=testdb;Username=testuser;Password=testpassword`

---

## SQL Server

```yaml
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    ports:
      - "1433:1433"
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "TestPassword123!"
    healthcheck:
      test: ["CMD-SHELL", "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'TestPassword123!' -Q 'SELECT 1' -No"]
      interval: 10s
      timeout: 5s
      retries: 10
```

Connection string: `Server=localhost,1433;Database=testdb;User Id=sa;Password=TestPassword123!;TrustServerCertificate=True`

---

## RabbitMQ

```yaml
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: testuser
      RABBITMQ_DEFAULT_PASS: testpassword
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Connection string: `amqp://testuser:testpassword@localhost:5672`
Management UI: `http://localhost:15672` (login: testuser / testpassword)

---

## Redis

```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

Connection string: `localhost:6379`

---

## MongoDB

```yaml
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: testuser
      MONGO_INITDB_ROOT_PASSWORD: testpassword
      MONGO_INITDB_DATABASE: testdb
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Connection string: `mongodb://testuser:testpassword@localhost:27017/testdb?authSource=admin`

> `authSource=admin` is required because `MONGO_INITDB_ROOT_USERNAME` creates the user in the `admin` database.

---

## Kafka (with Zookeeper)

Kafka requires a Zookeeper sidecar. Both snippets must be included together.

```yaml
  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.1
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  # From host use localhost:29092. From other containers use kafka:9092.
  kafka:
    image: confluentinc/cp-kafka:7.6.1
    ports:
      - "29092:29092"
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_HOST://0.0.0.0:29092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics --bootstrap-server localhost:9092 --list"]
      interval: 15s
      timeout: 10s
      retries: 5
```

Bootstrap address (from host): `localhost:29092`  
Bootstrap address (container-to-container): `kafka:9092`

---

## Elasticsearch

```yaml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    ports:
      - "9200:9200"
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms512m -Xmx512m"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -v '\"status\":\"red\"'"]
      interval: 15s
      timeout: 10s
      retries: 10
```

Connection string: `http://localhost:9200`

---

## Complete Example (PostgreSQL + Redis)

```yaml
services:

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpassword
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testdb"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

---

Run with `docker compose up -d` before executing your integration tests. Run `docker compose down` to clean up.
