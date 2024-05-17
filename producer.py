import json
import logging
from googleapiclient.discovery import build
from confluent_kafka import Producer
import time
import backoff

def read_config(file_path):
  """Reads the configuration file."""
  with open(file_path) as f:
    return json.load(f)

def setup_logging(log_file):
  """Sets up logging."""
  logging.basicConfig(filename=log_file, level=logging.INFO, 
                      format='%(asctime)s - %(levelname)s - %(message)s')

def build_youtube(api_key):
  """Builds the YouTube API client."""
  return build('youtube', 'v3', developerKey=api_key)

def create_producer(servers):
  """Creates a Kafka producer."""
  return Producer({'bootstrap.servers': servers,
                   'enable.idempotence': 'true',
                   'acks': 'all'
                  })

def delivery_report(err, msg):
  """Callback function to handle Kafka message delivery reports."""
  if err is not None:
    logging.error(f'Message delivery failed: {err}')
  else:
    logging.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def get_comments(video_id, youtube, producer, kafka_topic):
  """Fetches comments for a given video."""
  comments = {}
  try:
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
      author = comment["snippet"]["authorDisplayName"]
      published_at = comment["snippet"]["publishedAt"]
      updated_at = comment["snippet"]["updatedAt"]

      # Get the video title
      video_title_request = youtube.videos().list(
          part="snippet",
          id=video_id
      )
      video_title_response = video_title_request.execute()
      video_title = video_title_response["items"][0]["snippet"]["title"]

      # If the comment already exists, check its status
      if comment_id in comments:
        old_text = comments[comment_id]['text']
        if text != old_text:
          # Comment has been edited
          logging.info(f'Comment {comment_id} edited')
          comments[comment_id]['status'] = 'edited'
          comments[comment_id]['text'] = text
          comments[comment_id]['updatedAt'] = updated_at  # Add the updated time
      else:
        # New comment
        logging.info(f'New comment {comment_id} found')
        comments[comment_id] = {'id': comment_id, 'text': text, 'status': 'new', 'author': author, 'publishedAt': published_at, 'updatedAt': updated_at, 'videoTitle': video_title}  # Add the ID, author, published time, and video title

      # Send the comment's status to Kafka
      producer.produce(kafka_topic, key=comment_id, value=json.dumps(comments[comment_id]).encode('utf-8'), callback=delivery_report)

  except Exception as e:
    logging.error(f'Error fetching comments: {e}')
    raise e # Re-raise exception for backoff

def get_playlist_videos(playlist_id, youtube, producer, kafka_topic):
  """Fetches video IDs from a specific playlist."""
  next_page_token = None
  while True:
    try:
      request = youtube.playlistItems().list(
          part="snippet",
          maxResults=25,
          playlistId=playlist_id,
          pageToken=next_page_token
      )
      response = request.execute()

      for item in response["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        get_comments(video_id, youtube, producer, kafka_topic)
        time.sleep(1) # To comply with API rate limits

      next_page_token = response.get('nextPageToken')
      if next_page_token is None:
        break # Break after processing all pages

    except Exception as e:
      logging.error(f'Error fetching playlist videos: {e}')
      break

  producer.flush()


def main():
  """Main function to initiate the process."""
  config = read_config('producer_config.json')
  setup_logging('producer.log')
  youtube = build_youtube(config['youtube_api_key'])
  producer = create_producer(config['kafka_bootstrap_servers'])
  kafka_topic = config['kafka_topic']  # Get the Kafka topic from the config
  while True:
    get_playlist_videos(config['playlist_id'], youtube, producer, kafka_topic)  # Pass the Kafka topic to the function
    logging.info('Comments checked, waiting for 1 hour...')
    time.sleep(60*60)  # Check every hour

if __name__ == "__main__":
  main()
