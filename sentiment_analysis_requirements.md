# Social Media Sentiment Analysis Dashboard - Project Brief

## Project Goal
Build a real-time dashboard that tracks public sentiment about specific topics across Twitter/X, Reddit, and YouTube. The system should show whether people are talking positively or negatively about chosen topics and display trends over time.

## Success Target
- Process 1,000+ social media posts per day
- Classify sentiment with 75%+ accuracy
- Display real-time results on interactive dashboard
- Update visualizations within 30 seconds of new data

## Required Technology Stack
- **Apache Spark Streaming**: Real-time data processing
- **MongoDB**: Data storage (Atlas free tier)
- **TensorFlow**: Machine learning for sentiment analysis
- **D3.js**: Interactive web visualizations  
- **Power BI**: Executive reporting
- **Python**: Primary programming language

## Data Sources & APIs
- **Twitter/X API**: Tweets, retweets, hashtags, mentions
- **Reddit API (PRAW)**: Posts, comments, upvotes/downvotes
- **YouTube Data API**: Video comments, titles, engagement metrics

## Core Features Required

### Data Collection
- Continuously collect posts about specified keywords/hashtags
- Handle API rate limits and connection failures
- Filter for English content and remove spam/duplicates
- Store raw data with timestamps and metadata

### Real-time Processing
- Use Spark Streaming for live data ingestion
- Clean and preprocess text data
- Apply TensorFlow sentiment models to classify posts
- Calculate sentiment scores (positive/negative/neutral percentages)

### Data Storage
- Store raw posts and processed sentiment scores in MongoDB
- Maintain historical data for trend analysis
- Organize data by topic, platform, and time periods

### Interactive Dashboard
- Real-time line charts showing sentiment trends over time
- Pie charts displaying overall sentiment distribution
- Top positive/negative posts display
- Filter controls for date ranges, platforms, keywords
- Auto-refresh every 30 seconds

### Reporting
- Power BI dashboards for executive summaries
- Export capabilities for further analysis
- Alert system for significant sentiment changes

## System Architecture Flow
```
Social Media APIs → Spark Streaming → Sentiment Analysis (TensorFlow) → MongoDB → Web Dashboard (D3.js)
                                                                        ↓
                                                                   Power BI Reports
```

## Key Implementation Steps
1. Set up API access and test data collection
2. Build basic data pipeline with Python scripts
3. Implement Spark Streaming for real-time processing
4. Train/implement TensorFlow sentiment analysis models
5. Create MongoDB data schemas and storage logic
6. Build interactive web dashboard with D3.js
7. Integrate Power BI for executive reporting
8. Add error handling, monitoring, and optimization

## Technical Constraints
- Use free/academic tiers of all cloud services
- Handle API rate limits gracefully
- Ensure system can scale to handle viral content spikes
- Maintain data privacy (only public posts, no personal info storage)

## Expected Deliverables
- Functioning real-time sentiment analysis system
- Interactive web dashboard accessible via browser
- Power BI report templates
- Complete source code with documentation
- Deployment and user guides

## Performance Requirements
- Process minimum 1,000 posts daily
- Dashboard load time under 5 seconds
- Real-time updates within 30 seconds
- Support 5-10 concurrent users
- 95% system uptime during demo periods

## Use Cases for Testing
- Track sentiment during product launches (e.g., "iPhone 16")
- Monitor brand mentions during crisis events
- Analyze public opinion on trending social topics
- Compare sentiment patterns across different platforms

This system demonstrates end-to-end data engineering skills, real-time processing capabilities, machine learning implementation, and modern data visualization techniques.