import os
import json
import time
from confluent_kafka import Consumer, Producer
import google.generativeai as genai

# İşlenmiş mesajların ID'lerini saklamak için bir set oluşturun
processed_messages = set()

# Yapılandırma dosyasını oku
with open('config.json') as f:
    config = json.load(f)

# API anahtarını ayarla
gemini_api_key = config['gemini_api_key']

# Gemini API ayarları
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

# Kafka ayarları
kafka_bootstrap_servers = config['kafka_bootstrap_servers']
input_topic = 'youtube_comments'
output_topic = 'youtube_sentiments'

# Kafka tüketicisini başlat
consumer = Consumer({
    'bootstrap.servers': kafka_bootstrap_servers,
    'group.id': 'youtube_comments_group',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe([input_topic])

# Kafka üreticisini başlat
producer = Producer({
    'bootstrap.servers': kafka_bootstrap_servers,
    'enable.idempotence': 'true',
    'acks': 'all'
})

# Yorumları tüket ve duygu analizi yap
while True:
    message = consumer.poll(1.0)
    if message is None:
        continue
    if message.error():
        print("Consumer error: {}".format(message.error()))
        continue

    message_id = json.loads(message.value().decode('utf-8'))['id']
    
    # Eğer mesaj daha önce işlendi ise, tekrar işlenmez
    if message_id in processed_messages:
        continue

    comment = json.loads(message.value().decode('utf-8'))['text']
    
    # Gemini API ile duygu analizi yap
    prompt = "This is a sentiment analysis task. Please respond with a single word: 'positive', 'negative', or 'neutral'. Do not provide any additional information or explanation. Here is the comment: '{}'".format(comment)

    response = model.generate_content(prompt)
    
    # Duygu analizi sonucunu ve orijinal yorumu içeren yeni bir mesaj oluştur
    new_message = json.loads(message.value().decode('utf-8'))
    try:
        new_message['sentiment'] = response.text
    except ValueError:
        new_message['sentiment'] = 'neutral'  # Varsayılan değer

    # Yeni mesajı başka bir Kafka topicine gönder
    producer.produce(output_topic, key=message_id, value=json.dumps(new_message).encode('utf-8'))

    # Mesajın işlendiğini belirtmek için ID'yi set'e ekleyin
    processed_messages.add(message_id)

    # Offset'i commit et
    consumer.commit()

    # Her çağrıdan sonra belirli bir süre bekleyin
    time.sleep(2)  # 2 saniye bekleyin

consumer.close()
# Kafka üreticisini durdur
producer.flush()
