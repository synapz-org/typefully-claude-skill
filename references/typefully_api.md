# Typefully API Reference

This document provides detailed reference for the Typefully API endpoints and usage patterns.

## Authentication

**Method:** API Key in Header
**Header Name:** `X-API-KEY`
**Format:** `Bearer YOUR_API_KEY`

### Obtaining API Keys

1. Log into your Typefully account
2. Navigate to Settings > Integrations
3. Generate an API key for each social media account you want to manage
4. **Important:** Each social media account in Typefully requires its own API key

## Base URL

```
https://api.typefully.com/v1
```

## Endpoints

### 1. Create Draft

**Endpoint:** `POST /v1/drafts/`

Creates a new draft or scheduled post in Typefully.

**Request Headers:**
```
X-API-KEY: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | Yes | Tweet text. Use 4 consecutive newlines (`\n\n\n\n`) to split into multiple tweets |
| `threadify` | boolean | No | Auto-split content into tweets based on character limits |
| `share` | boolean | No | Include a shareable URL in the response |
| `schedule-date` | string | No | ISO 8601 date string or `"next-free-slot"`. If omitted, creates draft without scheduling |
| `auto_retweet_enabled` | boolean | No | Enable AutoRT feature per account settings |
| `auto_plug_enabled` | boolean | No | Enable AutoPlug feature per account settings |

**Example Request:**
```json
{
  "content": "First tweet of the thread\n\n\n\nSecond tweet of the thread\n\n\n\nThird tweet",
  "threadify": true,
  "share": true,
  "schedule-date": "2024-11-15T14:30:00Z"
}
```

**Example Response:**
```json
{
  "id": "draft_abc123",
  "share_url": "https://typefully.com/share/abc123",
  "scheduled_at": "2024-11-15T14:30:00Z",
  "status": "scheduled"
}
```

### 2. Retrieve Recently Scheduled Drafts

**Endpoint:** `GET /v1/drafts/recently-scheduled/`

Fetches drafts that have been scheduled for future publication.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_filter` | string | No | Filter by content type: `"threads"` or `"tweets"` |

**Example Request:**
```
GET /v1/drafts/recently-scheduled/?content_filter=threads
```

**Example Response:**
```json
{
  "drafts": [
    {
      "id": "draft_abc123",
      "content": "Thread content...",
      "scheduled_at": "2024-11-15T14:30:00Z",
      "type": "thread"
    }
  ]
}
```

### 3. Retrieve Recently Published Drafts

**Endpoint:** `GET /v1/drafts/recently-published/`

Fetches drafts that have been published.

**Example Request:**
```
GET /v1/drafts/recently-published/
```

**Example Response:**
```json
{
  "drafts": [
    {
      "id": "draft_xyz789",
      "content": "Published tweet...",
      "published_at": "2024-11-10T09:00:00Z",
      "engagement": {
        "likes": 42,
        "retweets": 7,
        "replies": 3
      }
    }
  ]
}
```

### 4. Get Latest Notifications

**Endpoint:** `GET /v1/notifications/`

Retrieves notifications for the account. Useful for tracking engagement and publishing activity.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `kind` | string | No | Filter type: `"inbox"` (comments/replies) or `"activity"` (publishing events) |

**Example Request:**
```
GET /v1/notifications/?kind=activity
```

**Example Response:**
```json
{
  "notifications": [
    {
      "id": "notif_123",
      "kind": "activity",
      "payload": {
        "action": "published",
        "draft_id": "draft_xyz789",
        "timestamp": "2024-11-10T09:00:00Z"
      }
    }
  ]
}
```

### 5. Mark Notifications as Read

**Endpoint:** `POST /v1/notifications/mark-all-read/`

Marks notifications as read, optionally filtering by type or username.

**Request Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `kind` | string | No | Filter by `"inbox"` or `"activity"` |
| `username` | string | No | Mark read for specific account only |

**Example Request:**
```json
{
  "kind": "activity"
}
```

## Content Formatting

### Thread Splitting

To create a multi-tweet thread, use **4 consecutive newlines** to separate tweets:

```
First tweet content

Second tweet content

Third tweet content
```

In JSON, this is represented as: `"First tweet\n\n\n\nSecond tweet\n\n\n\nThird tweet"`

### Auto-Threadify

Setting `threadify: true` allows Typefully to automatically split content based on character limits. This is useful for long-form content.

## Scheduling

### Schedule Date Formats

1. **ISO 8601 format:** `"2024-11-15T14:30:00Z"`
2. **Next available slot:** `"next-free-slot"` (uses Typefully's scheduling algorithm)

### Draft-Only Mode

Omit the `schedule-date` parameter to create a draft without scheduling. The draft will appear in your Typefully dashboard for manual review and scheduling.

## Rate Limits and Constraints

**Important:** The Typefully API is designed for **personal automations and workflows**, not public applications. For building public apps, use the X (Twitter) API instead.

- Always respect X's automation and general usage rules
- Excessive automation may result in account suspension
- No official rate limits documented, but use responsibly

## Error Handling

Common HTTP status codes:

- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Invalid or missing API key
- `403 Forbidden` - API key doesn't have permission for this account
- `429 Too Many Requests` - Rate limit exceeded (use exponential backoff)
- `500 Internal Server Error` - Server-side issue

## Best Practices

1. **Multiple Accounts:** Create separate API keys for each social media account
2. **Draft First:** Start with draft-only mode until confident in automation quality
3. **Content Validation:** Always validate content before scheduling
4. **Error Handling:** Implement robust error handling for API calls
5. **Testing:** Test with drafts before enabling auto-scheduling

## Python Client Usage

The included `typefully_client.py` script provides a high-level interface:

```python
from typefully_client import TypefullyManager

# Initialize manager (loads accounts from .env)
manager = TypefullyManager()

# Create a draft
manager.create_draft(
    account="personal",
    content="Your tweet content",
    schedule=False  # Draft only
)

# Cross-post to multiple accounts
manager.cross_post(
    accounts=["personal", "company"],
    content_map={
        "personal": "Casual tweet...",
        "company": "Professional announcement..."
    },
    schedule=False
)

# Get analytics
analytics = manager.get_analytics(account="personal", days=7)
```

## Additional Resources

- Official Documentation: https://support.typefully.com/en/articles/8718287-typefully-api
- Typefully Dashboard: https://typefully.com
- Support: Contact Typefully support through their help center
