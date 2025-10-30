---
name: typefully
description: This skill should be used when managing social media content through Typefully, including creating drafts, scheduling posts, cross-posting to multiple accounts with unique content, and retrieving analytics. Use it for Twitter/X thread creation, multi-account management, and social media workflow automation via the Typefully API.
---

# Typefully Social Media Management Skill

## Overview

This skill enables Claude to interact with the Typefully API for professional social media management. Typefully is a platform for drafting, scheduling, and analyzing social media content across multiple accounts.

**Key Capabilities:**
- Create drafts and scheduled posts
- Cross-post content to multiple accounts with unique adaptations
- Retrieve analytics and engagement data
- Manage multiple social media accounts through a unified interface
- Safety-first approach with draft-only mode by default

## When to Use This Skill

Use this skill when:
- Creating Twitter/X threads or single tweets
- Scheduling social media content for future publication
- Cross-posting announcements to multiple branded accounts
- Adapting content for different audiences across accounts
- Retrieving social media analytics and performance data
- Managing social media workflows programmatically

**Example triggers:**
- "Create a Twitter thread about [topic] for my personal account"
- "Schedule this announcement to post tomorrow at 2pm"
- "Cross-post this to my company and personal accounts with appropriate adaptations"
- "Show me last week's Twitter analytics"

## Setup and Configuration

### Initial Setup

1. **Obtain Typefully API Keys:**
   - Log into Typefully dashboard (https://typefully.com)
   - Navigate to Settings > Integrations
   - Generate an API key for each social media account
   - **Important:** Each account requires its own API key

2. **Configure the Skill:**
   - Create a `.env` file in the skill directory
   - Add API keys using the format: `TYPEFULLY_API_KEY_<ACCOUNT_NAME>=your_key_here`
   - Create a `config.json` file for global settings

3. **Example Configuration:**

`.env`:
```
TYPEFULLY_API_KEY_PERSONAL=your_personal_account_key
TYPEFULLY_API_KEY_COMPANY=your_company_account_key
TYPEFULLY_API_KEY_PROJECT=your_project_account_key
```

`config.json`:
```json
{
  "scheduling_enabled": false,
  "default_threadify": true,
  "default_share": true
}
```

### Safety Settings

**Draft-Only Mode (Default):**
- `scheduling_enabled: false` creates drafts without auto-scheduling
- Allows human review before publication
- Recommended until confidence in content quality is established

**Enable Scheduling:**
- Set `scheduling_enabled: true` in `config.json`
- Only enable after validating draft quality
- Consider integrating with brand voice validation before enabling

## Core Workflows

### Workflow 1: Create Draft for Single Account

**Use Case:** Draft a tweet or thread for review before publishing

**Process:**
1. Use `scripts/typefully_client.py` to interact with the API
2. Load account configuration from `.env`
3. Create draft using TypefullyManager
4. Review draft in Typefully dashboard
5. Manually schedule or publish from dashboard

**Example:**
```python
from typefully_client import TypefullyManager

manager = TypefullyManager()

# Create draft for review
result = manager.create_draft(
    account="personal",
    content="Your tweet content here.\n\n\n\nSecond tweet in thread.",
    schedule=False  # Draft only
)
```

**Command-line usage:**
```bash
python scripts/typefully_client.py create-draft \
    --account personal \
    --content "Your tweet content"
```

### Workflow 2: Schedule Post (When Enabled)

**Use Case:** Schedule content for future publication

**Prerequisites:**
- `scheduling_enabled: true` in `config.json`
- Content has passed quality validation

**Process:**
```python
manager = TypefullyManager()

result = manager.create_draft(
    account="company",
    content="Scheduled announcement content",
    schedule=True,
    schedule_date="2024-11-15T14:30:00Z"  # ISO format or "next-free-slot"
)
```

**Notes:**
- If `scheduling_enabled` is false, the skill will create a draft only (safety mechanism)
- Use "next-free-slot" to let Typefully choose optimal timing
- Always verify the schedule_date format

### Workflow 3: Cross-Post to Multiple Accounts

**Use Case:** Publish the same announcement across multiple branded accounts with unique content for each

**Process:**
1. Prepare content variations for each account
2. Create a JSON file mapping accounts to content
3. Use the cross-post functionality

**Example content map (content.json):**
```json
{
  "personal": "Excited to share: we just launched our new feature! Check it out:",
  "company": "Introducing our latest product update with enhanced capabilities:"
}
```

**Execute cross-post:**
```python
manager = TypefullyManager()

content_map = {
    "personal": "Casual, personal tone announcement",
    "company": "Professional, formal announcement"
}

results = manager.cross_post(
    accounts=["personal", "company"],
    content_map=content_map,
    schedule=False  # Respect global config
)

# Results show success/failure for each account
for account, result in results.items():
    print(f"{account}: {result}")
```

**Command-line usage:**
```bash
python scripts/typefully_client.py cross-post \
    --accounts personal company \
    --content-json content.json
```

### Workflow 4: Retrieve Analytics

**Use Case:** Get performance data for recently published content

**Process:**
```python
manager = TypefullyManager()

analytics = manager.get_analytics(account="personal", days=7)

# Analytics includes:
# - Recently published posts
# - Engagement notifications
# - Publishing activity
```

**Command-line usage:**
```bash
python scripts/typefully_client.py get-analytics \
    --account personal \
    --days 7
```

### Workflow 5: List Configured Accounts

**Use Case:** Verify which accounts are configured

**Command-line:**
```bash
python scripts/typefully_client.py list-accounts
```

## Thread Formatting

### Creating Multi-Tweet Threads

Use **4 consecutive newlines** (`\n\n\n\n`) to separate tweets in a thread:

```python
content = """First tweet in the thread

Second tweet with more details

Third tweet wrapping up"""

manager.create_draft(account="personal", content=content)
```

### Auto-Threadify

Enable `threadify: true` (default) to automatically split long content based on Twitter's character limits:

```python
# Long content automatically split into tweets
content = "Very long form content that exceeds Twitter's character limit will be automatically split into a thread by Typefully's threadify feature..."
```

## Integration with Other Skills

This skill can be integrated with other content creation and brand management workflows:

**Content Creation Pipeline:**
1. Generate content using content creation agents
2. Validate with brand voice guidelines
3. Create Typefully draft for review
4. Manually approve and schedule (or auto-schedule if enabled)

**Multi-Brand Management:**
1. Adapt content for different brand voices
2. Use cross-post with unique content per account
3. Maintain consistent messaging with appropriate tone

**Analytics and Reporting:**
1. Retrieve performance data via analytics
2. Generate reports on engagement
3. Inform future content strategy

## API Reference

For detailed API documentation, load `references/typefully_api.md` which includes:
- Complete endpoint specifications
- Request/response formats
- Error handling guidance
- Rate limits and best practices

Load reference when:
- Debugging API issues
- Implementing custom functionality
- Understanding response structures
- Troubleshooting authentication

## Error Handling

Common issues and solutions:

**Account Not Found:**
- Verify `.env` file contains `TYPEFULLY_API_KEY_<ACCOUNT>=key`
- Check account name matches exactly (case-sensitive)
- Run `list-accounts` to see configured accounts

**Scheduling Disabled Warning:**
- Expected when `scheduling_enabled: false`
- Draft created for manual review
- Enable in `config.json` only when ready

**API Authentication Errors:**
- Verify API key is correct
- Check API key has permissions for the account
- Ensure `X-API-KEY` header format is correct

**Content Formatting Issues:**
- Use 4 newlines to split threads
- Enable `threadify` for auto-splitting
- Verify content doesn't exceed platform limits

## Best Practices

1. **Start with Draft Mode:**
   - Keep `scheduling_enabled: false` initially
   - Review drafts in Typefully dashboard
   - Enable scheduling only after validating quality

2. **Multiple Accounts:**
   - Use descriptive account names in `.env`
   - Maintain separate API keys per account
   - Organize content_map clearly for cross-posting

3. **Content Quality:**
   - Validate content before creating drafts
   - Use brand voice guidelines for multi-account scenarios
   - Test with personal accounts before company accounts

4. **Error Resilience:**
   - Handle API errors gracefully
   - Provide clear error messages
   - Fall back to draft mode on scheduling failures

5. **Analytics Usage:**
   - Retrieve analytics regularly
   - Use data to inform content strategy
   - Track engagement trends over time

## Extending the Skill

The `typefully_client.py` script provides a foundation that can be extended:

- Add custom content transformation logic
- Integrate with brand voice validation systems
- Build automated scheduling based on optimal timing
- Create custom analytics dashboards
- Implement A/B testing workflows

Modify the script as needed while maintaining the core API interaction patterns.

## Troubleshooting

**Problem:** "Account 'xyz' not found"
- **Solution:** Check `.env` file, verify account name matches configuration

**Problem:** Scheduling doesn't work despite `schedule=True`
- **Solution:** Verify `scheduling_enabled: true` in `config.json`

**Problem:** API returns 401 Unauthorized
- **Solution:** Regenerate API key in Typefully dashboard, update `.env`

**Problem:** Cross-post fails for some accounts
- **Solution:** Check each account's API key separately, ensure all are valid

For additional support, consult the official Typefully API documentation: https://support.typefully.com/en/articles/8718287-typefully-api
