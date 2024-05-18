# Real-Time Sentiment Analysis Pipeline for YouTube Comments


https://github.com/bunyaminonum/youtube-comments-sentiment-analyses/assets/59376910/0aabda01-a71f-483e-9b31-2ca820727d78

![youtube_comments_realtime_processing_diagram](https://github.com/bunyaminonum/youtube-comments-sentiment-analyses/assets/59376910/0daaeb0b-2e7e-4e44-a977-8cfb157f67ed)


This project is a real-time sentiment analysis pipeline for YouTube comments. It collects comments from YouTube videos, performs sentiment analysis using the Gemini API, and shares negative results on a Telegram channel.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Project](#running-the-project)
- [Project Structure](#project-structure)
- [License](#license)

## Introduction
This project aims to create a real-time pipeline that collects comments from YouTube videos, performs sentiment analysis on these comments using the Gemini API, and shares the negative results on a Telegram channel. The pipeline consists of three main components:
1. Comment collection and transfer to Kafka.
2. Sentiment analysis using the Gemini API.
3. Telegram bot for sharing negative comments.

## Features
- Real-time collection of YouTube comments.
- Sentiment analysis using the Gemini API to classify comments as positive, negative, or neutral.
- Automatic sharing of negative comments on a specified Telegram channel.

## Getting Started

### Prerequisites
- Python 3.6 or higher
- Kafka
- KSQL
- YouTube Data API key
- Gemini API key
- Telegram Bot API key

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/bunyaminonum/youtube-comments-sentiment-analyses.git
   cd youtube-comments-sentiment-analyses
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
1. Fill in the configuration files with your credentials and settings:
   - `producer_config.json`
   - `sentiment_analysis_config.json`
   - `telegram_bot_config.json`

   Example `producer_config.json`:
   ```json
   {
     "youtube_api_key": "YOUR_YOUTUBE_API_KEY",
     "playlist_id": "YOUR_PLAYLIST_ID",
     "kafka_bootstrap_servers": "YOUR_KAFKA_BOOTSTRAP_SERVERS",
     "kafka_topic": "youtube_comments"
   }
   ```

   Example `sentiment_analysis_config.json`:
   ```json
   {
     "kafka_bootstrap_servers": "YOUR_KAFKA_BOOTSTRAP_SERVERS",
     "gemini_api_key": "YOUR_GEMINI_API_KEY",
     "input_topic": "youtube_comments",
     "output_topic": "youtube_sentiments"
   }
   ```

   Example `telegram_bot_config.json`:
   ```json
   {
     "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
     "kafka_bootstrap_servers": "YOUR_KAFKA_BOOTSTRAP_SERVERS",
     "kafka_topic": "negative_youtube_sentiments",
     "telegram_channel_id": "YOUR_TELEGRAM_CHANNEL_ID"
   }
   ```

### Running the Project
1. Start the Kafka server and create the necessary topics.
2. Run the following KSQL queries to create streams:
   ```sql
   CREATE STREAM YOUTUBE_SENTIMENTS_STREAM (
       ID VARCHAR,
       TEXT VARCHAR,
       STATUS VARCHAR,
       AUTHOR VARCHAR,
       PUBLISHEDAT VARCHAR,
       UPDATEDAT VARCHAR,
       VIDEOTITLE VARCHAR,
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

3. Run each Python file separately:
   ```bash
   python producer.py
   python sentiment-analyses.py
   python telegram_bot.py
   ```

## Project Structure
The project consists of the following files:

- `LICENSE`: Contains the project's license information.
- `README.md`: Provides an overview of the project, its purpose, and usage instructions.
- `producer.py`: Script for collecting YouTube comments and sending them to Kafka.
- `producer_config.json`: Configuration file for `producer.py`.
- `sentiment-analyses.py`: Script for performing sentiment analysis on YouTube comments using the Gemini API.
- `sentiment_analysis_config.json`: Configuration file for `sentiment-analyses.py`.
- `telegram_bot.py`: Script for sending negative comments to a Telegram channel.
- `telegram_bot_config.json`: Configuration file for `telegram_bot.py`.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
