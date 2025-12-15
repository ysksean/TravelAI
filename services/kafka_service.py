import json
from kafka import KafkaProducer, KafkaConsumer
from flask_socketio import SocketIO

# [중요] docker-compose 설정에 따라 외부 접속 포트인 19092 사용
BOOTSTRAP_SERVERS = ['localhost:19092']
TOPIC_NAME = 'chat_messages'

# 1. Producer 초기화
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def send_to_kafka(data):
    """Kafka로 메시지 전송"""
    try:
        producer.send(TOPIC_NAME, data)
        producer.flush()
        # print(f">>> [Kafka Produce] {data['sender_type']} -> {data['room_id']}")
    except Exception as e:
        print(f"⚠️ [Kafka Error] 전송 실패: {e}")


# 2. Consumer 로직
def kafka_consumer_worker(socketio: SocketIO):
    """백그라운드에서 실행될 Consumer 함수"""
    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='chat_server_group'
        )
        print(f">>> [Kafka] Consumer 시작됨 (Port: 19092)")

        for message in consumer:
            data = message.value
            room_id = data.get('room_id')
            # SocketIO로 해당 방에만 메시지 전송
            socketio.emit('new_message', data, room=room_id)

    except Exception as e:
        print(f"⚠️ [Kafka Consumer Error] 연결 실패: {e}")