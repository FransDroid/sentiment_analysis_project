# Social Media Sentiment Analysis Dashboard

A real-time sentiment analysis system that tracks public opinion across Twitter, Reddit, and YouTube, displaying interactive visualizations and trends.

## 🎯 Project Overview

This system processes 1,000+ social media posts per day, classifies sentiment with machine learning, and displays real-time results on an interactive dashboard. Built with Apache Spark Streaming, TensorFlow, MongoDB, and D3.js.

## ✨ Key Features

- **Real-time Data Collection**: Continuous monitoring of Twitter, Reddit, and YouTube
- **Sentiment Analysis**: Machine learning-powered sentiment classification
- **Interactive Dashboard**: Live visualizations with D3.js
- **Scalable Architecture**: Apache Spark for big data processing
- **Multiple Deployment Modes**: Dashboard-only, pipeline-only, or full system

## 🏗️ System Architecture

```
Social Media APIs → Spark Streaming → Sentiment Analysis (TensorFlow) → MongoDB → Web Dashboard (D3.js)
                                                                        ↓
                                                                   Power BI Reports
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (free tier)
- Social Media API keys (Twitter, Reddit, YouTube)

### Installation

1. **Clone and setup environment**:
   ```bash
   git clone <repository>
   cd sentiment_analysis_project
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the system**:
   ```bash
   # Full system (pipeline + dashboard)
   python main.py --mode full

   # Dashboard only
   python main.py --mode dashboard

   # Data pipeline only
   python main.py --mode pipeline
   ```

4. **Access dashboard**:
   Open http://localhost:5000 in your browser

## 📋 Configuration

### Environment Variables

Edit `.env` file with your credentials:

```env
# Twitter API
TWITTER_BEARER_TOKEN=your_token_here
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here

# Reddit API
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here

# YouTube API
YOUTUBE_API_KEY=your_key_here

# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sentiment_analysis
```

### Keywords Configuration

Modify `config/settings.py` to change tracked keywords:

```python
DEFAULT_KEYWORDS = ['python', 'AI', 'machine learning']
```

## 🔧 API Setup Guide

### Twitter API Setup
1. Create a Twitter Developer account
2. Create a new App
3. Generate Bearer Token and API keys
4. Add to `.env` file

### Reddit API Setup
1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (script type)
3. Note the client ID and secret
4. Add to `.env` file

### YouTube API Setup
1. Go to Google Cloud Console
2. Enable YouTube Data API v3
3. Create API key
4. Add to `.env` file

### MongoDB Setup
1. Create MongoDB Atlas account
2. Create a cluster (free tier)
3. Create database user
4. Get connection string
5. Add to `.env` file

## 📊 Dashboard Features

The web dashboard provides:

- **Real-time sentiment overview**: Positive, neutral, negative percentages
- **Trend charts**: Sentiment changes over time
- **Platform breakdown**: Twitter, Reddit, YouTube statistics
- **Top posts**: Highest confidence posts by sentiment
- **Auto-refresh**: Updates every 30 seconds

### Dashboard Controls

- **Refresh Button**: Manual data refresh
- **Time Period Selector**: Choose trend analysis period
- **Platform Filters**: View specific platform data

## 🛠️ Development

### Project Structure

```
sentiment_analysis_project/
├── src/
│   ├── data_collection/     # Social media API clients
│   ├── sentiment_analysis/  # ML models and text processing
│   ├── database/           # MongoDB connection and schemas
│   ├── streaming/          # Spark streaming pipeline
│   ├── dashboard/          # Flask web app and frontend
│   └── utils/             # Logging, monitoring, error handling
├── config/                # Configuration settings
├── tests/                 # Unit tests
├── docs/                  # Additional documentation
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

### Adding New Data Sources

1. Create collector class in `src/data_collection/`
2. Implement data collection methods
3. Add to pipeline in `src/streaming/real_time_pipeline.py`
4. Update dashboard API if needed

### Customizing Sentiment Analysis

1. Train new model in `src/sentiment_analysis/sentiment_analyzer.py`
2. Replace TextBlob with custom TensorFlow model
3. Adjust confidence thresholds
4. Add new sentiment categories

## 📈 Monitoring & Maintenance

### System Status

Check system health:
```bash
python main.py --mode status
```

### Log Files

- `logs/sentiment_analysis.log`: General application logs
- `logs/errors.log`: Error-specific logs

### Performance Monitoring

The system tracks:
- CPU and memory usage
- Processing times
- Error rates
- API response times

### Database Maintenance

Clean old data:
```python
from src.database.mongodb_client import MongoDBClient
db = MongoDBClient()
db.cleanup_old_data(days=30)  # Remove data older than 30 days
```

## 🧪 Testing

Run tests:
```bash
python -m pytest tests/
```

Create test data:
```bash
python tests/create_test_data.py
```

## 📚 API Documentation

### REST Endpoints

- `GET /api/sentiment/summary`: Current sentiment statistics
- `GET /api/sentiment/trends`: Historical trend data
- `GET /api/posts/top`: Top posts by sentiment
- `GET /api/posts/recent`: Recent posts
- `GET /api/stats/overview`: System overview

### Query Parameters

- `platform`: Filter by platform (twitter, reddit, youtube)
- `hours`: Time range in hours (default: 24)
- `limit`: Number of results (default: 10)

## 🚨 Troubleshooting

### Common Issues

**API Rate Limits**:
- Twitter: 300 requests/15 minutes
- Reddit: 60 requests/minute
- YouTube: 10,000 units/day

**Database Connection**:
- Check MongoDB URI format
- Verify network access (whitelist IP)
- Confirm credentials

**Dashboard Not Loading**:
- Check Flask is running on port 5000
- Verify no firewall blocking
- Check browser console for errors

**No Data Collection**:
- Verify API keys are correct
- Check internet connectivity
- Review error logs

### Debug Mode

Run with debug logging:
```bash
python main.py --mode full --log-level DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is for educational purposes. Ensure compliance with social media platform terms of service.

## 📞 Support

For issues and questions:
1. Check troubleshooting section
2. Review log files
3. Create GitHub issue
4. Contact development team

---

**Note**: This system is designed for academic and learning purposes. Always respect social media platform rate limits and terms of service.