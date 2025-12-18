# Typefully API Reference (v2)

This document provides detailed reference for the Typefully API v2 endpoints and usage patterns.

## Authentication

**Method:** Bearer Token in Authorization Header
**Header Name:** `Authorization`
**Format:** `Bearer YOUR_API_KEY`

```
Authorization: Bearer YOUR_API_KEY
```

### API Key Permissions

API keys inherit permissions from the user who created them:
- **WRITE**: Can create drafts
- **PUBLISH**: Can schedule and publish drafts

Generate API keys from Typefully Settings > Integrations.

## Base URL

```
https://api.typefully.com/v2
```

## Rate Limiting & Pagination

### Rate Limits
- Rate-limited per user and social set basis
- HTTP 429 responses indicate exceeded limits
- Implement exponential backoff when rate limited

### Pagination
List endpoints use limit-offset pagination:
- **Default limit**: 10 items
- **Maximum limit**: 50 items

**Response format:**
```json
{
  "results": [...],
  "count": 100,
  "limit": 10,
  "offset": 0,
  "next": "https://api.typefully.com/v2/...",
  "previous": null
}
```

## Supported Platforms

API v2 supports multi-platform publishing:
- **x** - X (Twitter)
- **linkedin** - LinkedIn
- **mastodon** - Mastodon
- **threads** - Threads
- **bluesky** - Bluesky

## Endpoints

### 1. Get User Info

**Endpoint:** `GET /v2/me`

Retrieve authenticated user details.

**Response:**
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "signup_date": "2024-01-15T10:30:00Z",
  "profile_image": "https://..."
}
```

### 2. List Social Sets

**Endpoint:** `GET /v2/social-sets`

List all accessible social sets (account groups).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Results per page (max 50) |
| `offset` | integer | Pagination offset |

**Response:**
```json
{
  "results": [
    {
      "id": "social_set_abc123",
      "name": "My Brand",
      "x": {"username": "mybrand", "connected": true},
      "linkedin": {"connected": false},
      "mastodon": {"connected": false},
      "threads": {"connected": false},
      "bluesky": {"connected": false}
    }
  ],
  "count": 1,
  "limit": 10,
  "offset": 0
}
```

### 3. Get Social Set Details

**Endpoint:** `GET /v2/social-sets/{social_set_id}/`

Get detailed platform configuration for a social set.

**Response:**
```json
{
  "id": "social_set_abc123",
  "name": "My Brand",
  "x": {
    "username": "mybrand",
    "connected": true,
    "followers_count": 5000
  },
  "linkedin": {
    "connected": true,
    "profile_url": "https://linkedin.com/in/mybrand"
  }
}
```

### 4. List Drafts

**Endpoint:** `GET /v2/social-sets/{social_set_id}/drafts`

List drafts for a social set, ordered by last edited.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `draft`, `scheduled`, `published`, `publishing`, `error` |
| `limit` | integer | Results per page (max 50) |
| `offset` | integer | Pagination offset |

**Response:**
```json
{
  "results": [
    {
      "id": "draft_xyz789",
      "status": "scheduled",
      "created_at": "2024-11-15T10:00:00Z",
      "updated_at": "2024-11-15T12:30:00Z",
      "scheduled_date": "2024-11-16T14:30:00Z",
      "preview": "First 180 characters of content...",
      "share_url": "https://typefully.com/share/abc123",
      "private_url": "https://typefully.com/private/xyz789"
    }
  ],
  "count": 5,
  "limit": 10,
  "offset": 0
}
```

### 5. Create Draft

**Endpoint:** `POST /v2/social-sets/{social_set_id}/drafts`

Create a new draft with platform-specific content.

**Request Body:**

```json
{
  "platforms": {
    "x": {
      "enabled": true,
      "posts": [
        {"text": "First tweet of the thread"},
        {"text": "Second tweet with more details"},
        {"text": "Final tweet wrapping up"}
      ],
      "settings": {}
    },
    "linkedin": {
      "enabled": true,
      "posts": [
        {"text": "LinkedIn version of the content"}
      ],
      "settings": {}
    }
  },
  "draft_title": "My Thread Title",
  "publish_at": "next-free-slot",
  "share": true,
  "tags": ["product-launch", "announcement"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `platforms` | object | Yes | Platform-specific content and settings |
| `draft_title` | string | No | Internal title for the draft |
| `publish_at` | string | No | `"now"`, `"next-free-slot"`, or ISO-8601 datetime. Omit for draft-only. |
| `share` | boolean | No | Include shareable URL in response |
| `tags` | array | No | List of tag slugs (not names) |

**Platform Object:**

Each platform in `platforms` has:
- `enabled`: boolean - Whether to post to this platform
- `posts`: array - List of post objects with `text` field
- `settings`: object - Platform-specific settings

**Response:**
```json
{
  "id": "draft_abc123",
  "status": "scheduled",
  "created_at": "2024-11-15T10:00:00Z",
  "updated_at": "2024-11-15T10:00:00Z",
  "scheduled_date": "2024-11-15T14:30:00Z",
  "preview": "First tweet of the thread",
  "share_url": "https://typefully.com/share/abc123",
  "private_url": "https://typefully.com/private/abc123"
}
```

### 6. Get Draft

**Endpoint:** `GET /v2/social-sets/{social_set_id}/drafts/{draft_id}`

Retrieve a specific draft with full details.

**Response:**
```json
{
  "id": "draft_abc123",
  "status": "scheduled",
  "created_at": "2024-11-15T10:00:00Z",
  "updated_at": "2024-11-15T12:30:00Z",
  "scheduled_date": "2024-11-16T14:30:00Z",
  "published_at": null,
  "preview": "First 180 characters...",
  "share_url": "https://typefully.com/share/abc123",
  "private_url": "https://typefully.com/private/abc123",
  "x_published_url": null,
  "linkedin_published_url": null,
  "platforms": {
    "x": {
      "enabled": true,
      "posts": [{"text": "Tweet content"}],
      "settings": {}
    }
  },
  "tags": ["product-launch"]
}
```

### 7. Update Draft

**Endpoint:** `PATCH /v2/social-sets/{social_set_id}/drafts/{draft_id}`

Partial update of an existing draft.

**Request Body:** (all fields optional)
```json
{
  "platforms": {
    "x": {
      "enabled": true,
      "posts": [{"text": "Updated content"}],
      "settings": {}
    }
  },
  "draft_title": "Updated Title",
  "publish_at": "2024-11-20T10:00:00Z",
  "tags": ["updated-tag"]
}
```

**Response:** Updated draft object

## Draft Status Values

| Status | Description |
|--------|-------------|
| `draft` | Saved but not scheduled |
| `scheduled` | Scheduled for future publication |
| `publishing` | Currently being published |
| `published` | Successfully published |
| `error` | Publication failed |

## Published URLs

After publication, drafts include platform-specific URLs:
- `x_published_url`: Link to X/Twitter post
- `linkedin_published_url`: Link to LinkedIn post
- `mastodon_published_url`: Link to Mastodon post
- `threads_published_url`: Link to Threads post
- `bluesky_published_url`: Link to Bluesky post

## Webhooks

### Supported Events

| Event | Description |
|-------|-------------|
| `draft.created` | New draft created |
| `draft.scheduled` | Draft scheduled for publication |
| `draft.published` | Draft successfully published |
| `draft.status_changed` | Draft status changed |
| `draft.tags_changed` | Draft tags modified |
| `draft.deleted` | Draft deleted |

### Webhook Headers

| Header | Description |
|--------|-------------|
| `X-Typefully-Event` | Event type |
| `X-Typefully-Timestamp` | Unix timestamp |
| `X-Typefully-Signature` | HMAC-SHA256 signature |

### Signature Verification

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret, timestamp):
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{payload}".encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Retry Policy
- Failed deliveries retry 5 times over 1 hour
- Auto-disables after 100 consecutive failures

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Invalid/missing API key |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource doesn't exist |
| `429` | Rate Limit Exceeded |
| `500` | Internal Server Error |

### Error Response Format

```json
{
  "error": "invalid_request",
  "message": "The 'platforms' field is required",
  "details": {
    "field": "platforms",
    "code": "required"
  }
}
```

## Content Formatting

### Thread/Multi-Post Content

The v2 API uses an explicit posts array instead of newline separation:

```json
{
  "platforms": {
    "x": {
      "enabled": true,
      "posts": [
        {"text": "First tweet"},
        {"text": "Second tweet"},
        {"text": "Third tweet"}
      ]
    }
  }
}
```

For backward compatibility with content using 4 newlines, the Python client automatically converts:
```
"First tweet\n\n\n\nSecond tweet\n\n\n\nThird tweet"
```
into the posts array format.

### Platform-Specific Content

You can provide different content for each platform:

```json
{
  "platforms": {
    "x": {
      "enabled": true,
      "posts": [{"text": "Short tweet version"}]
    },
    "linkedin": {
      "enabled": true,
      "posts": [{"text": "Longer, more professional LinkedIn version with additional context..."}]
    }
  }
}
```

## Tags

Tags use slugs (URL-friendly identifiers), not display names:
- Display name: "Product Launch"
- Slug: `product-launch`

Retrieve available tags through the Typefully dashboard to get correct slugs.

## Account-Level Settings

These settings apply automatically based on Typefully account configuration:
- **Auto-Retweet**: Automatically retweets your posts
- **Auto-Plug**: Adds promotional content to high-performing posts
- **Natural Posting Time**: Varies exact publish time for natural appearance

## Best Practices

1. **Start with Drafts**: Omit `publish_at` to create drafts for review
2. **Use Social Set Caching**: Cache social set IDs to reduce API calls
3. **Handle Rate Limits**: Implement exponential backoff on 429 errors
4. **Verify Webhooks**: Always validate webhook signatures
5. **Platform Permissions**: Ensure API key has PUBLISH permission for scheduling

## Python Client Usage

The included `typefully_client.py` provides a high-level interface:

```python
from typefully_client import TypefullyManager

# Initialize manager (loads accounts from .env)
manager = TypefullyManager()

# Create a draft for X
result = manager.create_draft(
    account="covenant",
    content="Your post content",
    platforms=["x"],
    schedule=False
)

# Create multi-platform draft
result = manager.create_draft(
    account="covenant",
    content="Multi-platform announcement",
    platforms=["x", "linkedin"],
    schedule=True,
    schedule_date="next-free-slot"
)

# Cross-post to multiple accounts
manager.cross_post(
    accounts=["covenant", "basilica", "templar"],
    content_map={
        "covenant": "Ecosystem announcement...",
        "basilica": "Infrastructure update...",
        "templar": "Miner-focused content..."
    },
    platforms=["x"]
)

# Get analytics
analytics = manager.get_analytics(account="covenant", limit=20)

# List social sets
sets = manager.get_social_sets_info(account="covenant")
```

## Migration from v1

Key changes from API v1:
1. **Authentication**: `X-API-KEY: Bearer token` -> `Authorization: Bearer token`
2. **Social Sets**: Drafts now require `social_set_id` in path
3. **Content Structure**: Use `platforms` object with `posts` array instead of `content` string
4. **Endpoints**: New path structure `/v2/social-sets/{id}/drafts`
5. **Pagination**: Proper limit-offset pagination on list endpoints
6. **Status Values**: New statuses including `publishing` and `error`

## Additional Resources

- Official Documentation: https://typefully.com/docs/api
- Typefully Dashboard: https://typefully.com
- X Automation Rules: Review before building X automation
