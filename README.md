# Typefully Claude Skill

A Claude Code skill for managing social media content through the [Typefully](https://typefully.com) API. Create drafts, schedule posts, cross-post to multiple accounts, and retrieve analytics—all through conversational AI.

## Features

- **Draft Creation**: Create Twitter/X drafts with Claude's assistance
- **Thread Management**: Automatically format and split content into threads
- **Multi-Account Support**: Manage multiple social media accounts with separate API keys
- **Cross-Posting**: Publish unique content variations across different accounts
- **Safe by Default**: Draft-only mode prevents accidental publishing
- **Analytics**: Retrieve performance data and engagement metrics
- **Command-Line Interface**: Use directly via CLI or through Claude Code

## Prerequisites

- Python 3.7+
- [Typefully account](https://typefully.com) with API access
- [Claude Code](https://claude.ai/code) (for AI-assisted workflows)

## Installation

### Option 1: Install as Claude Code Skill

1. Download the skill:
   ```bash
   wget https://github.com/synapz-org/typefully-claude-skill/releases/latest/download/typefully.zip
   ```

2. Install in Claude Code:
   ```
   /skills install typefully.zip
   ```

3. Configure your API keys (see [Configuration](#configuration))

### Option 2: Standalone Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/synapz-org/typefully-claude-skill.git
   cd typefully-claude-skill
   ```

2. Install dependencies:
   ```bash
   pip install requests
   ```

3. Configure your API keys (see [Configuration](#configuration))

## Configuration

### 1. Get Typefully API Keys

1. Log into your [Typefully dashboard](https://typefully.com)
2. Navigate to **Settings > Integrations**
3. Generate an API key for each social media account you want to manage
4. **Important**: Each social media account requires its own API key

### 2. Create Configuration Files

Copy the example files:

```bash
cp .env.example .env
cp config.json.example config.json
```

Edit `.env` with your API keys:

```bash
TYPEFULLY_API_KEY_PERSONAL=your_personal_twitter_key
TYPEFULLY_API_KEY_COMPANY=your_company_twitter_key
```

Edit `config.json` for settings:

```json
{
  "scheduling_enabled": false,
  "default_threadify": true,
  "default_share": true
}
```

### Safety Settings

- **`scheduling_enabled: false`** (default): Creates drafts only, no auto-publishing
- **`scheduling_enabled: true`**: Enables automatic scheduling (use with caution)

We recommend keeping `scheduling_enabled: false` until you're confident in content quality.

## Usage

### With Claude Code

Once installed as a skill, simply ask Claude:

```
"Create a Twitter thread about AI ethics for my personal account"
"Cross-post this product announcement to company and project accounts"
"Show me last week's Twitter analytics for my personal account"
```

Claude will automatically use the Typefully skill to handle these requests.

### Command-Line Interface

The skill includes a Python client for direct CLI usage:

#### Create a Draft

```bash
python scripts/typefully_client.py create-draft \
  --account personal \
  --content "Your tweet content here"
```

#### Create a Thread

Use 4 newlines to separate tweets:

```bash
python scripts/typefully_client.py create-draft \
  --account personal \
  --content "First tweet

Second tweet

Third tweet"
```

#### Schedule a Post

```bash
python scripts/typefully_client.py create-draft \
  --account company \
  --content "Scheduled announcement" \
  --schedule \
  --schedule-date "2024-12-01T14:30:00Z"
```

#### Cross-Post to Multiple Accounts

Create `content.json`:
```json
{
  "personal": "Casual announcement for personal audience",
  "company": "Professional announcement for company account"
}
```

Execute cross-post:
```bash
python scripts/typefully_client.py cross-post \
  --accounts personal company \
  --content-json content.json
```

#### Get Analytics

```bash
python scripts/typefully_client.py get-analytics \
  --account personal \
  --days 7
```

#### List Configured Accounts

```bash
python scripts/typefully_client.py list-accounts
```

## Python API Usage

```python
from typefully_client import TypefullyManager

# Initialize (automatically loads .env configuration)
manager = TypefullyManager()

# Create a draft
result = manager.create_draft(
    account="personal",
    content="Your tweet content",
    schedule=False  # Draft only
)

# Cross-post with unique content
content_map = {
    "personal": "Personal voice content",
    "company": "Professional voice content"
}

results = manager.cross_post(
    accounts=["personal", "company"],
    content_map=content_map,
    schedule=False
)

# Get analytics
analytics = manager.get_analytics(account="personal", days=7)
```

## Thread Formatting

### Manual Thread Splitting

Use **4 consecutive newlines** to separate tweets:

```python
content = """First tweet

Second tweet

Third tweet"""
```

### Auto-Threadify

Enable `threadify: true` (default) to automatically split long content based on Twitter's character limits.

## Project Structure

```
typefully-claude-skill/
├── SKILL.md                    # Claude Code skill instructions
├── README.md                   # This file
├── .env.example                # API key template
├── config.json.example         # Configuration template
├── scripts/
│   └── typefully_client.py     # Python API client
└── references/
    └── typefully_api.md        # Detailed API documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for use with [Claude Code](https://claude.ai/code) by Anthropic
- Integrates with the [Typefully](https://typefully.com) social media management platform
- Created by [Synapz](https://github.com/synapz-org)

## Support

- **Documentation**: See [SKILL.md](SKILL.md) for detailed usage instructions
- **API Reference**: See [references/typefully_api.md](references/typefully_api.md)
- **Typefully API Docs**: https://support.typefully.com/en/articles/8718287-typefully-api
- **Issues**: https://github.com/synapz-org/typefully-claude-skill/issues

## Disclaimer

This skill is for personal automations and workflows. For public applications, use the X (Twitter) API directly. Always comply with X's automation and usage rules to avoid account suspension.
