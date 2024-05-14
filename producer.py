import json
from googleapiclient.discovery import build
from confluent_kafka import Producer
import time

# Yapılandırma dosyasını oku
with open('config.json') as f:
    config = json.load(f)

# YouTube API ayarları
api_key = config['youtube_api_key']
youtube = build('youtube', 'v3', developerKey=api_key)

# Kafka ayarları
producer = Producer({'bootstrap.servers': config['kafka_bootstrap_servers'],
                     'enable.idempotence': 'true',
                     'acks': 'all'
                     })

# Yorumları saklamak için bir sözlük
comments = {}

def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

def get_comments(video_id):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText"
    )
    response = request.execute()

    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]
        text = comment["snippet"]["textDisplay"]
        comment_id = comment["id"]

        # Yorum zaten varsa, durumunu kontrol et
        if comment_id in comments:
            old_text = comments[comment_id]['text']
            if text != old_text:
                # Yorum düzenlendi
                comments[comment_id]['status'] = 'edited'
                comments[comment_id]['text'] = text
                comments[comment_id]['id'] = comment_id  # ID'yi ekle
                # Yorumun durumunu Kafka'ya gönder
                producer.produce('youtube_comments', key=comment_id, value=json.dumps(comments[comment_id]).encode('utf-8'), callback=delivery_report)
            # else: yorum değişmedi, hiçbir şey yapma
        else:
            # Yeni yorum
            comments[comment_id] = {'text': text, 'status': 'new', 'id': comment_id}  # ID'yi ekle
            # Yorumun durumunu Kafka'ya gönder
            producer.produce('youtube_comments', key=comment_id, value=json.dumps(comments[comment_id]).encode('utf-8'), callback=delivery_report)

def get_playlist_videos(playlist_id):
    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            maxResults=25,
            playlistId=playlist_id,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            get_comments(video_id)
            time.sleep(1)  # API sınırlamalarına uygun olmak için

        next_page_token = response.get('nextPageToken')
        if next_page_token is None:
            break  # Break after processing all pages

    producer.flush()

# İşlemi başlat
while True:
    get_playlist_videos(config['playlist_id'])
    time.sleep(60*3)  # Her saat başı kontrol et


