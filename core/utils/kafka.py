from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json



class KafkaConsumer:
    def __init__(self, broker: str, topic: str, group_id: str):
        self.broker = broker
        self.topic = topic
        self.group_id = group_id
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.broker,
            group_id=self.group_id,
        )
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        try:

            if self.consumer:
                async for message in self.consumer:
                    # Handle message (deserialize)
                    message_value = json.loads(message.value.decode())
                    print(f"Received message: {message_value}")
                    if message['action'] == "create":
                        data = message_value.get("product")
                        if data:
                            # Index into Elasticsearch
                            await message_value.get("es").index(
                                index="products",
                                id=data.get("id"),
                                document=data,
                            )
                            print(f"Indexed product {data.get('id')} into ES")
        except Exception as e:
            print(f"[KAFKA-CONSUMER] Error: {e}")

# Usage example:
# kafka_consumer = KafkaConsumer(broker=settings.KAFKA_BOOTSTRAP_SERVERS, topic="your_topic", group_id="your_group")
# await kafka_consumer.start()
# await kafka_consumer.consume()


class KafkaProducer:
    def __init__(self, broker: str, topic: str):
        self.broker = broker
        self.topic = topic
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.broker)
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send(self, message: dict):
        if self.producer:
            await self.producer.send_and_wait(self.topic, json.dumps(message).encode())

# Usage example:
# kafka_producer = KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS, topic="your_topic")
# await kafka_producer.start()
# await kafka_producer.send({"key": "value"})
# await kafka_producer.stop()
async def send_kafka_message(kafka_producer, message: dict):
    await kafka_producer.send(message)
