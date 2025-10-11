# Complete Setup Guide

This guide walks you through setting up the Social Media Sentiment Analysis Dashboard from scratch.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Python Environment Setup](#python-environment-setup)
3. [API Credentials Setup](#api-credentials-setup)
4. [Database Setup](#database-setup)
5. [Application Configuration](#application-configuration)
6. [First Run](#first-run)
7. [Verification](#verification)

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Stable internet connection

### Software Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)

### Optional Requirements
- **Java 8+** (for Spark local mode)
- **Git** (for version control)

## Python Environment Setup

### Step 1: Check Python Version
```bash
python --version
# Should show 3.8 or higher
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv sentiment_env

# Activate virtual environment
# On Windows:
sentiment_env\Scripts\activate
# On macOS/Linux:
source sentiment_env/bin/activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import tweepy, praw, pymongo, tensorflow, flask; print('All packages installed successfully')"
```

## API Credentials Setup

### Twitter API Setup

1. **Create Developer Account**
   - Go to https://developer.twitter.com/
   - Sign up for a developer account
   - Verify your email and phone number

2. **Create a New App**
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Click "Create App"
   - Fill in app details:
     - App name: "Sentiment Analysis Dashboard"
     - Description: "Educational sentiment analysis project"
     - Website: "https://example.com" (can be placeholder)

3. **Generate API Keys**
   - Go to your app's "Keys and tokens" tab
   - Generate the following:
     - API Key and Secret
     - Bearer Token
     - Access Token and Secret
   - Save these values securely

### Reddit API Setup

1. **Create Reddit Account**
   - Go to https://www.reddit.com/register
   - Create an account if you don't have one

2. **Create Reddit App**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Fill in details:
     - Name: "Sentiment Analysis"
     - Type: "script"
     - Description: "Educational sentiment analysis"
     - Redirect URI: "http://localhost:8080"

3. **Save Credentials**
   - Client ID: Found under the app name
   - Client Secret: The secret key shown
   - User Agent: "SentimentAnalysis/1.0"

### YouTube API Setup

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Name: "Sentiment Analysis Dashboard"

2. **Enable YouTube Data API**
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"

3. **Create API Key**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the generated API key
   - Optionally restrict the key to YouTube Data API

## Database Setup

### MongoDB Atlas Setup (Recommended)

1. **Create MongoDB Atlas Account**
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for a free account

2. **Create Cluster**
   - Choose "Build a Database"
   - Select "FREE" tier (M0 Sandbox)
   - Choose a cloud provider and region (closest to you)
   - Name your cluster: "sentiment-analysis"

3. **Configure Database Access**
   - Go to "Database Access"
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: "sentimentuser"
   - Generate secure password
   - Set role to "Read and write to any database"

4. **Configure Network Access**
   - Go to "Network Access"
   - Click "Add IP Address"
   - Choose "Allow Access from Anywhere" (0.0.0.0/0) for development
   - Or add your specific IP address for better security

5. **Get Connection String**
   - Go to "Database" > "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

### Local MongoDB Setup (Alternative)

If you prefer local MongoDB:

1. **Install MongoDB Community Edition**
   - Follow instructions at https://docs.mongodb.com/manual/installation/

2. **Start MongoDB Service**
   ```bash
   # On Windows (as service)
   net start MongoDB

   # On macOS
   brew services start mongodb-community

   # On Linux
   sudo systemctl start mongod
   ```

3. **Connection String**
   ```
   mongodb://localhost:27017/sentiment_analysis
   ```

## Application Configuration

### Step 1: Create Environment File
```bash
# Copy the example environment file
cp .env.example .env
```

### Step 2: Edit Environment Variables
Open `.env` file in a text editor and fill in your credentials:

```env
# Twitter API Keys
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=SentimentAnalysis/1.0

# YouTube API
YOUTUBE_API_KEY=your_youtube_api_key_here

# MongoDB (use your connection string)
MONGODB_URI=mongodb+srv://sentimentuser:your_password@sentiment-analysis.xxxxx.mongodb.net/sentiment_analysis?retryWrites=true&w=majority

# Flask Settings
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here_make_it_long_and_random
```

### Step 3: Verify Configuration
```bash
python -c "
from config.settings import Config
print('Twitter API Key:', 'SET' if Config.TWITTER_API_KEY else 'MISSING')
print('Reddit Client ID:', 'SET' if Config.REDDIT_CLIENT_ID else 'MISSING')
print('YouTube API Key:', 'SET' if Config.YOUTUBE_API_KEY else 'MISSING')
print('MongoDB URI:', 'SET' if Config.MONGODB_URI else 'MISSING')
"
```

## First Run

### Step 1: Test Database Connection
```bash
python -c "
from src.database.mongodb_client import MongoDBClient
try:
    db = MongoDBClient()
    print('Database connection successful!')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### Step 2: Test API Connections
```bash
python -c "
from src.data_collection.twitter_collector import TwitterCollector
from src.data_collection.reddit_collector import RedditCollector
from src.data_collection.youtube_collector import YouTubeCollector

# Test Twitter
try:
    twitter = TwitterCollector()
    print('Twitter API: Connected')
except Exception as e:
    print(f'Twitter API: Failed - {e}')

# Test Reddit
try:
    reddit = RedditCollector()
    print('Reddit API: Connected')
except Exception as e:
    print(f'Reddit API: Failed - {e}')

# Test YouTube
try:
    youtube = YouTubeCollector()
    print('YouTube API: Connected')
except Exception as e:
    print(f'YouTube API: Failed - {e}')
"
```

### Step 3: Start the Application
```bash
# Start with dashboard only first
python main.py --mode dashboard
```

Open http://localhost:5000 in your browser. You should see the dashboard interface.

### Step 4: Test Data Collection
In a new terminal (keep dashboard running):
```bash
# Test data collection
python main.py --mode pipeline
```

Let it run for a few minutes, then check the dashboard for data.

### Step 5: Run Full System
Stop both processes and run the full system:
```bash
python main.py --mode full
```

## Verification

### Check Dashboard Features
1. **Open Dashboard**: http://localhost:5000
2. **Verify Sections**:
   - Overview statistics (should show percentages)
   - Trend chart (may be empty initially)
   - Platform breakdowns
   - Top posts sections

### Check Data Collection
1. **Monitor Logs**: Watch the console output for data collection messages
2. **Check Database**:
   ```bash
   python -c "
   from src.database.mongodb_client import MongoDBClient
   db = MongoDBClient()
   recent_posts = db.get_recent_posts(hours=1)
   print(f'Collected {len(recent_posts)} posts in the last hour')
   "
   ```

### Check System Status
```bash
python main.py --mode status
```

This should show:
- System health status
- Uptime information
- Processing statistics
- Any recent errors

## Troubleshooting

### Common Issues and Solutions

**1. "Module not found" errors**
```bash
# Make sure virtual environment is activated
source sentiment_env/bin/activate  # macOS/Linux
# or
sentiment_env\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

**2. API authentication errors**
- Double-check all API keys in `.env` file
- Ensure no extra spaces or quotes around values
- Verify API keys are active and not expired

**3. Database connection errors**
- Check MongoDB Atlas cluster is running
- Verify IP address is whitelisted
- Test connection string format
- Confirm database user has correct permissions

**4. Dashboard shows no data**
- Let data collection run for 5-10 minutes first
- Check pipeline logs for collection errors
- Verify API rate limits aren't exceeded
- Check if keywords are finding relevant posts

**5. Port 5000 already in use**
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or use different port
# Edit src/dashboard/app.py to change port
```

### Getting Help

If you encounter issues:

1. **Check logs** in the `logs/` directory
2. **Review error messages** carefully
3. **Verify all prerequisites** are met
4. **Test each component** individually
5. **Check API status pages** for service outages

### Next Steps

Once setup is complete:
- Customize keywords in `config/settings.py`
- Explore the dashboard features
- Monitor system performance
- Consider scheduling regular data cleanup
- Set up monitoring alerts for production use

## Security Notes

For production deployment:
- Use strong, unique passwords
- Restrict MongoDB network access
- Use environment-specific API keys
- Enable HTTPS for the dashboard
- Regularly rotate API credentials
- Monitor for unusual activity

Congratulations! Your sentiment analysis dashboard is now ready to use.