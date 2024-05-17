import os
import json
import time
import logging
from confluent_kafka import Consumer, Producer
import google.generativeai as genai
import backoff

def read_config(file_path):
  """Reads the configuration file."""
  with open(file_path) as f:
    return json.load(f)

def setup_logging(log_file):
  """Sets up logging."""
  logging.basicConfig(filename=log_file, level=logging.INFO, 
                      format='%(asctime)s - %(levelname)s - %(message)s')

def configure_gemini(api_key):
  """Configures the Gemini API."""
  genai.configure(api_key=api_key)
  return genai.GenerativeModel('gemini-pro')

def create_consumer(servers, group_id, offset_reset, topic):
  """Creates a Kafka consumer."""
  consumer = Consumer({
      'bootstrap.servers': servers,
      'group.id': group_id,
      'auto.offset.reset': offset_reset
  })
  consumer.subscribe([topic])
  return consumer

def create_producer(servers):
  """Creates a Kafka producer."""
  return Producer({
      'bootstrap.servers': servers,
      'enable.idempotence': 'true',
      'acks': 'all'
  })

def delivery_report(err, msg):
  """Callback function to handle Kafka message delivery reports."""
  if err is not None:
    logging.error(f'Message delivery failed: {err}')
  else:
    logging.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def analyze_sentiment(comment, model):
  """Performs sentiment analysis on a comment."""
  try:
    prompt = "This is a sentiment analysis task. Please respond with a single word: 'positive', 'negative', or 'neutral'. Do not provide any additional information or explanation. Here is the comment: '{}'".format(comment)
    response = model.generate_content(prompt)
    return response.text.strip()
  except Exception as e:
    logging.error(f'Error during sentiment analysis: {e}')
    raise e # Re-raise exception for backoff

def process_messages(consumer, producer, model, output_topic):
  """Processes messages from the consumer."""
  processed_messages = set()
  while True:
    message = consumer.poll(1.0)
    if message is None:
      continue
    if message.error():
      logging.error(f"Consumer error: {message.error()}")
      continue

    try:
      message_data = json.loads(message.value().decode('utf-8'))
      message_id = message_data['id']

      # If the message has already been processed, skip it
      if message_id in processed_messages:
        continue

      comment = message_data['text']

      # Perform sentiment analysis using Gemini API
      sentiment = analyze_sentiment(comment, model)

      # Create a new message containing the sentiment analysis result and original comment
      new_message = message_data.copy()
      new_message['sentiment'] = sentiment

      # Send the new message to another Kafka topic
      producer.produce(output_topic, key=message_id, value=json.dumps(new_message).encode('utf-8'), callback=delivery_report)

      # Add the message ID to the set to mark it as processed
      processed_messages.add(message_id)

      # Commit the offset
      consumer.commit()

      logging.info(f"Comment {message_id} processed, sentiment: {sentiment}")

    except Exception as e:
      logging.error(f"Error processing message: {e}")

    # Wait for a certain amount of time after each call
    time.sleep(3) # Wait for 2 seconds


def main():
  """Main function to initiate the process."""
  config = read_config('sentiment_analysis_config.json')
  setup_logging('sentiment-analysis.log')
  model = configure_gemini(config['gemini_api_key'])
  consumer = create_consumer(config['kafka_bootstrap_servers'], 'youtube_comments_group', 'earliest', 'youtube_comments')
  producer = create_producer(config['kafka_bootstrap_servers'])
  process_messages(consumer, producer, model, 'youtube_sentiments')
  consumer.close()
  producer.flush()

if __name__ == "__main__":
  main()