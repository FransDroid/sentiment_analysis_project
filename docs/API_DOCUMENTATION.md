# API Documentation

This document describes the REST API endpoints available in the Sentiment Analysis Dashboard.

## Base URL

```
http://localhost:5000
```

## Authentication

No authentication is currently required for the API endpoints. This is suitable for development and educational use.

## Response Format

All API responses follow this format:

```json
{
  "success": true|false,
  "data": {...},
  "timestamp": "2024-01-01T12:00:00.000Z",
  "error": "error message if success=false"
}
```

## Endpoints

### 1. Sentiment Summary

Get current sentiment statistics.

**Endpoint:** `GET /api/sentiment/summary`

**Parameters:**
- `platform` (optional): Filter by platform (`twitter`, `reddit`, `youtube`)
- `hours` (optional): Time range in hours (default: 24)

**Example Request:**
```bash
curl "http://localhost:5000/api/sentiment/summary?platform=twitter&hours=12"
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "positive": 45.2,
    "neutral": 32.1,
    "negative": 22.7,
    "total": 1247
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 2. Sentiment Trends

Get historical sentiment trend data.

**Endpoint:** `GET /api/sentiment/trends`

**Parameters:**
- `platform` (optional): Filter by platform (`twitter`, `reddit`, `youtube`)
- `days` (optional): Number of days to look back (default: 7)

**Example Request:**
```bash
curl "http://localhost:5000/api/sentiment/trends?days=3"
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-01",
      "hour": 14,
      "sentiment": "positive",
      "count": 23
    },
    {
      "date": "2024-01-01",
      "hour": 14,
      "sentiment": "negative",
      "count": 12
    }
  ],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 3. Top Posts

Get top posts by sentiment confidence.

**Endpoint:** `GET /api/posts/top`

**Parameters:**
- `sentiment` (optional): Filter by sentiment (`positive`, `neutral`, `negative`, default: `positive`)
- `platform` (optional): Filter by platform (`twitter`, `reddit`, `youtube`)
- `limit` (optional): Number of posts to return (default: 10, max: 50)

**Example Request:**
```bash
curl "http://localhost:5000/api/posts/top?sentiment=negative&limit=5"
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "64f8a1b2c3d4e5f6a7b8c9d0",
      "text": "This is a sample post text...",
      "platform": "twitter",
      "sentiment": {
        "label": "negative",
        "confidence": 0.87,
        "probabilities": {
          "positive": 0.05,
          "neutral": 0.08,
          "negative": 0.87
        }
      },
      "created_at": "2024-01-01T11:30:00.000Z",
      "metadata": {
        "author_id": "user123",
        "likes": 5,
        "retweets": 2
      }
    }
  ],
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 4. Recent Posts

Get recently collected posts.

**Endpoint:** `GET /api/posts/recent`

**Parameters:**
- `platform` (optional): Filter by platform (`twitter`, `reddit`, `youtube`)
- `hours` (optional): Time range in hours (default: 1)
- `limit` (optional): Number of posts to return (default: 50, max: 200)

**Example Request:**
```bash
curl "http://localhost:5000/api/posts/recent?hours=2&limit=20"
```

**Example Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "64f8a1b2c3d4e5f6a7b8c9d0",
      "text": "Sample post content here",
      "platform": "reddit",
      "created_at": "2024-01-01T11:45:00.000Z",
      "author": "user456",
      "metrics": {
        "likes": 15,
        "retweets": 0,
        "score": 8
      }
    }
  ],
  "count": 20,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### 5. Overview Statistics

Get comprehensive system overview.

**Endpoint:** `GET /api/stats/overview`

**Parameters:** None

**Example Request:**
```bash
curl "http://localhost:5000/api/stats/overview"
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "overall": {
      "positive": 42.5,
      "neutral": 35.0,
      "negative": 22.5,
      "total": 1500
    },
    "platforms": {
      "twitter": {
        "positive": 45.0,
        "neutral": 30.0,
        "negative": 25.0,
        "total": 800
      },
      "reddit": {
        "positive": 40.0,
        "neutral": 40.0,
        "negative": 20.0,
        "total": 500
      },
      "youtube": {
        "positive": 38.0,
        "neutral": 42.0,
        "negative": 20.0,
        "total": 200
      }
    },
    "last_updated": "2024-01-01T12:00:00.000Z"
  }
}
```

## Error Responses

When an error occurs, the API returns an error response:

```json
{
  "success": false,
  "error": "Detailed error message"
}
```

### Common Error Codes

- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Endpoint not found
- **500 Internal Server Error**: Server error

### Example Error Response

```json
{
  "success": false,
  "error": "Invalid platform parameter. Must be one of: twitter, reddit, youtube"
}
```

## Data Models

### Sentiment Object

```json
{
  "label": "positive|neutral|negative",
  "confidence": 0.85,
  "probabilities": {
    "positive": 0.85,
    "neutral": 0.10,
    "negative": 0.05
  }
}
```

### Post Object

```json
{
  "id": "unique_post_id",
  "text": "post content",
  "platform": "twitter|reddit|youtube",
  "created_at": "ISO 8601 timestamp",
  "author": "author_identifier",
  "sentiment": {}, // Sentiment object (if analyzed)
  "metadata": {
    "likes": 0,
    "retweets": 0,
    "score": 0,
    "author_id": "author_id"
  }
}
```

## Rate Limiting

Currently, there are no rate limits implemented. For production use, consider implementing:
- Rate limiting per IP address
- API key authentication
- Request throttling

## Usage Examples

### Python Example

```python
import requests

# Get sentiment summary
response = requests.get('http://localhost:5000/api/sentiment/summary')
data = response.json()

if data['success']:
    print(f"Positive: {data['data']['positive']}%")
    print(f"Negative: {data['data']['negative']}%")
    print(f"Total posts: {data['data']['total']}")
else:
    print(f"Error: {data['error']}")
```

### JavaScript Example

```javascript
// Get recent posts
fetch('http://localhost:5000/api/posts/recent?limit=10')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log(`Found ${data.count} recent posts`);
      data.data.forEach(post => {
        console.log(`${post.platform}: ${post.text.substring(0, 50)}...`);
      });
    } else {
      console.error('Error:', data.error);
    }
  });
```

### curl Examples

```bash
# Get Twitter sentiment for last 6 hours
curl "http://localhost:5000/api/sentiment/summary?platform=twitter&hours=6"

# Get trend data for last 3 days
curl "http://localhost:5000/api/sentiment/trends?days=3"

# Get top 5 positive posts from Reddit
curl "http://localhost:5000/api/posts/top?sentiment=positive&platform=reddit&limit=5"

# Get overview stats
curl "http://localhost:5000/api/stats/overview"
```

## Data Freshness

- **Sentiment Summary**: Updated every 30 seconds
- **Trends**: Calculated from stored data, updated as new data arrives
- **Recent Posts**: Shows posts collected in the specified time range
- **Top Posts**: Based on sentiment confidence scores, updated as new analysis completes

## Performance Considerations

- **Caching**: Results are not currently cached. Consider implementing caching for better performance.
- **Database Indexes**: Ensure proper indexing on frequently queried fields.
- **Pagination**: For large result sets, consider implementing pagination.
- **Filtering**: Use platform and time filters to reduce response sizes.

## Integration Notes

### Dashboard Integration

The dashboard uses these APIs with JavaScript to:
- Update charts every 30 seconds
- Respond to user filter changes
- Display real-time statistics

### External Integration

For external applications:
- Use appropriate time ranges to balance freshness with performance
- Implement retry logic for transient errors
- Consider polling frequency to avoid overloading the system
- Cache results when appropriate

## Future Enhancements

Planned API improvements:
- Authentication and API keys
- Rate limiting
- Webhook support for real-time updates
- Additional aggregation endpoints
- Bulk data export endpoints
- Historical data analysis endpoints

## Support

For API-related questions or issues:
1. Check the error response message
2. Verify parameter format and values
3. Review the system logs
4. Ensure the backend services are running
5. Contact the development team