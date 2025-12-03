# Kafka Configuration

Apache Kafka configured to run in **KRaft mode** (no Zookeeper needed).

## Configuration File

`server.properties` contains:
- **KRaft mode** settings (process.roles=broker,controller)
- **Listeners** for both Docker network and localhost access
- **Auto-create topics** enabled
- **Single node** replication settings

## Access Points

- **From host**: `localhost:9092`
- **From Docker network**: `kafka:29092`
- **Internal broker**: `kafka:9092` (inter-broker communication)

## Creating Topics

### Using Kafka CLI

```bash
# Create topic
docker exec -it kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create \
  --topic weather-data \
  --partitions 1 \
  --replication-factor 1

# List topics
docker exec -it kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list

# Describe topic
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:29092 \
  --describe \
  --topic weather-data
```

### Consuming Messages

```bash
# Consume messages
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic weather-data \
  --from-beginning
```

```bash
# Try consuming from a specific partition
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

## Troubleshooting

### Topic auto-creation not working
- Check `auto.create.topics.enable=true` in server.properties
- Restart Kafka: `docker-compose restart kafka`

### Connection refused
- Verify Kafka is running: `docker-compose ps kafka`
- Check logs: `docker-compose logs kafka`
- Ensure ports are not blocked

### Formatting issues
- Kafka automatically formats on first run
- If needed, remove volume: `docker-compose down -v kafka`

