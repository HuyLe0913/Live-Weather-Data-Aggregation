# Kafka Configuration

Apache Kafka configured to run in **KRaft mode** (no Zookeeper needed).
KRaft (Kafka Raft) mode replaces ZooKeeper with Kafka’s internal consensus protocol. 
In this setup, Kafka acts as both broker and controller, suitable for single-node development and testing.

## Configuration File

`server.properties` contains:
- **KRaft mode** settings (process.roles=broker,controller)
  This enables Kafka to:
  - Manage metadata internally
  - Act as both controller and broker in one process
- **Listeners** for both Docker network and localhost access.
  Multiple listeners allow:
  - Local development from the host machine
  - Inter-container communication inside Docker
- **Auto-create topics** enabled.
  Topics are created automatically when a producer or consumer first references them.
- **Single node** replication settings.
  Replication factor is set to 1 because there is only one broker. No redundancy is provided.

## Access Points

- **From host**: `localhost:9092`
- **From Docker network**: `kafka:29092`
- **Internal broker**: `kafka:9092` (inter-broker communication)

## Creating Topics

### Using Kafka CLI

```bash
# Create topic:
# Creates a topic named weather-data with 1 partition (single-threaded consumption) and replication factor 1 (for single broker)
docker exec -it kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create \
  --topic weather-data \
  --partitions 1 \
  --replication-factor 1

# List topics:
# Lists all topics registered in the Kafka metadata log.
docker exec -it kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list

# Describe topic:
# Shows partition count, leader broker, replication assignments.
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:29092 \
  --describe \
  --topic weather-data
```

### Consuming Messages

```bash
# Consume messages:
# Consumes messages from the earliest offset via the host-accessible listener
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic weather-data \
  --from-beginning
```

```bash
# Try consuming from a specific partition
# Consumes only partition 0 using the internal broker address
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic weather-data \
  --partition 0 \
  --from-beginning
```

### Producing Messages

```bash
# Produce test message
docker exec -it kafka kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic weather-data
```

## Configuration Details

- **Node ID**: 1
- **Controller Port**: 9093
- **Broker Port**: 9092
- **Internal Port**: 29092
- **Storage**: `/var/lib/kafka/data` (persisted volume)
  Stores topic logs, Kafka metadata, KRaft quorum state.

## Troubleshooting

### Topic auto-creation not working
- Check `auto.create.topics.enable=true` in server.properties
- Restart Kafka: `docker-compose restart kafka`

### Connection refused
- Verify Kafka is running: `docker-compose ps kafka`
- Check logs: `docker-compose logs kafka`
- Ensure correct listener and port are being used
- Ensure ports are not blocked

### Formatting issues
- Kafka automatically formats storage on first run.
- If needed, remove volume: `docker-compose down -v kafka`
- Remove volume if metadata is corrupted or incompatible. This removes the persisted data and forces re-initialization.

