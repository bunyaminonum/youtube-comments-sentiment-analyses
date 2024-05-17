import asyncio
import json
from time import sleep
from telegram import Bot
from confluent_kafka import Consumer
from datetime import datetime, timezone
import logging

# Configuration
with open('telegram_bot_config.json') as f:
    config = json.load(f)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='telegram_bot.log',
    filemode='w'
)

# Kafka consumer setup
consumer = Consumer({
    'bootstrap.servers': config['kafka_bootstrap_servers'],
    'group.id': 'mygroup',
    'auto.offset.reset': 'earliest',
})
consumer.subscribe([config['kafka_topic']])

# Telegram bot setup
bot = Bot(token=config['telegram_bot_token'])
channel_id = config['telegram_channel_id']

# Helper function to format datetime
def format_datetime(timestamp_str):
    """Formats a timestamp string to a user-friendly format."""
    timestamp = datetime.fromisoformat(timestamp_str)
    return timestamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

async def send_message(message):
    """Sends a formatted message to the Telegram channel."""
    formatted_message = (
        f"ID: {message['ID']}\n\n"
        f"Text: {message['TEXT']}\n\n"
        f"Status: {message['STATUS']}\n\n"
        f"Author: {message['AUTHOR']}\n\n"
        f"Published At: {format_datetime(message['PUBLISHEDAT'])}\n\n"
        f"Updated At: {format_datetime(message['UPDATEDAT'])}\n\n"
        f"Video Title: {message['VIDEOTITLE']}\n\n"  # Add the video title
        f"Sentiment: {message['SENTIMENT']}\n\n"
    )
    try:
        await bot.send_message(chat_id=channel_id, text=formatted_message)
        logging.info(f"Message sent to Telegram channel: {channel_id}")
    except Exception as e:
        logging.error(f"Error sending message to Telegram channel: {e}")


async def main():
    """Main function to handle message consumption and sending."""
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            logging.error(f"Consumer error: {msg.error()}")
            continue

        message = json.loads(msg.value().decode('utf-8'))
        logging.info(f"Received message from Kafka: {message}")
        await send_message(message)
        sleep(3)  # Adjust the sleep duration as needed

if __name__ == '__main__':
    asyncio.run(main())