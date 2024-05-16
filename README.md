# Real-time Sentiment Analysis Pipeline for YouTube Comments

This project collects YouTube video comments, performs sentiment analysis, and shares "negative" results on a Telegram channel. The project consists of three main components:

## Components

1. **Comment Collection and Transfer to Kafka (producer.py)**: The first component collects YouTube video comments and transfers them to Kafka.
2. **Sentiment Analysis (sentiment-analyses.py)**: The second component performs sentiment analysis on the comments received from Kafka and sends the results to a new Kafka topic.
3. **Telegram Bot (telegram_bot.py)**: The third component retrieves the sentiment analysis results (negative ones) from Kafka and sends these results to a Telegram channel.

## Installation

There is a separate configuration file for each Python file. These files contain all the configuration information necessary for the project to run. You need to fill in your configuration files as follows:

- **producer_config.json**:
```json
{
    "youtube_api_key": "YOUR_YOUTUBE_API_KEY",
    "playlist_id": "YOUR_PLAYLIST_ID",
    "kafka_bootstrap_servers": "YOUR_KAFKA_BOOTSTRAP_SERVERS",
    "kafka_topic": "youtube_comments"
}
```

- **sentiment_analysis_config.json**:
```json
{
    "kafka_bootstrap_servers": "YOUR_KAFKA_BOOTSTRAP_SERVERS",
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "input_topic": "youtube_comments",
    "output_topic": "youtube_sentiments"
}
```

- **telegram_bot_config.json**:
```json
{
    "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "kafka_bootstrap_servers": "YOUR_KAFKA_BOOTSTRAP_SERVERS",
    "kafka_topic": "NEGATIVE_YOUTUBE_SENTIMENTS_STREAM",
    "telegram_channel_id": "YOUR_TELEGRAM_CHANNEL_ID"
}
```

## Usage

You need to run each Python file separately. Before running the files, make sure you have filled in the relevant configuration files.

```bash
python producer.py
python sentiment-analyses.py
```

After running the above two files, you need to run the following KSQL queries:

```sql
CREATE STREAM YOUTUBE_SENTIMENTS_STREAM (
    ID VARCHAR,
    TEXT VARCHAR,
    STATUS VARCHAR,
    AUTHOR VARCHAR,
    PUBLISHEDAT VARCHAR,
    UPDATEDAT VARCHAR,
    SENTIMENT VARCHAR
) WITH (
    KAFKA_TOPIC='youtube_sentiments', 
    VALUE_FORMAT='JSON'
);

CREATE STREAM NEGATIVE_YOUTUBE_SENTIMENTS_STREAM AS 
SELECT * 
FROM YOUTUBE_SENTIMENTS_STREAM 
WHERE SENTIMENT='negative';
```

Then, you can run the Telegram bot:

```bash
python3 telegram_bot.py
```

## License

This project is licensed under the MIT license.
```
This README file clearly explains what your project is, how to install it, and how to use it. It also describes what each component of your project does. If there is any other information I need to include, please let me know.
