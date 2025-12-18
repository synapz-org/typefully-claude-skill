#!/usr/bin/env python3
"""
Typefully API Client (v2)

A Python client for interacting with the Typefully API v2 to manage social media drafts,
scheduling, and analytics across multiple platforms and social sets.

Supports: X (Twitter), LinkedIn, Mastodon, Threads, Bluesky

Usage:
    python typefully_client.py create-draft --account "covenant" --content "Your tweet content"
    python typefully_client.py list-social-sets --account "covenant"
    python typefully_client.py get-drafts --account "covenant" --status scheduled
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional, Dict, List, Any
import requests
from pathlib import Path


class TypefullyClient:
    """Client for interacting with Typefully API v2"""

    BASE_URL = "https://api.typefully.com/v2"

    # Supported platforms in v2
    PLATFORMS = ["x", "linkedin", "mastodon", "threads", "bluesky"]

    def __init__(self, api_key: str):
        """
        Initialize Typefully client with API key

        Args:
            api_key: Typefully API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._social_sets_cache: Optional[List[Dict]] = None

    def _handle_request_error(self, error: requests.HTTPError, context: str = "") -> None:
        """Convert HTTP errors to user-friendly messages"""
        status_code = error.response.status_code

        if status_code == 401:
            raise ValueError("Invalid API key. Check your configuration and regenerate if needed.")
        elif status_code == 403:
            raise ValueError("API key doesn't have permission for this operation.")
        elif status_code == 429:
            raise ValueError("Rate limit exceeded. Please wait before trying again.")
        elif status_code == 400:
            try:
                error_detail = error.response.json()
                raise ValueError(f"Bad request: {error_detail}")
            except json.JSONDecodeError:
                raise ValueError("Bad request. Check your input parameters.")
        else:
            raise ValueError(f"Typefully API error ({status_code}): {error.response.text}")

    def _paginated_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        limit: int = 50,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Handle paginated API requests

        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Results per page (max 50)
            max_results: Maximum total results to fetch

        Returns:
            List of all results
        """
        params = params or {}
        params["limit"] = min(limit, 50)
        params["offset"] = 0

        all_results = []

        while True:
            try:
                response = requests.get(endpoint, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                all_results.extend(results)

                # Check if we've reached max_results
                if max_results and len(all_results) >= max_results:
                    return all_results[:max_results]

                # Check if there are more pages
                if not data.get("next"):
                    break

                params["offset"] += params["limit"]

            except requests.HTTPError as e:
                self._handle_request_error(e, f"paginated request to {endpoint}")

        return all_results

    # === User Endpoints ===

    def get_me(self) -> Dict:
        """
        Get authenticated user details

        Returns:
            User info including email, name, signup date, profile image
        """
        endpoint = f"{self.BASE_URL}/me"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            self._handle_request_error(e, "getting user info")

    # === Social Sets Endpoints ===

    def get_social_sets(self, refresh: bool = False) -> List[Dict]:
        """
        List all accessible social sets (accounts)

        Args:
            refresh: Force refresh of cached social sets

        Returns:
            List of social sets with platform configurations
        """
        if self._social_sets_cache and not refresh:
            return self._social_sets_cache

        endpoint = f"{self.BASE_URL}/social-sets"
        self._social_sets_cache = self._paginated_request(endpoint)
        return self._social_sets_cache

    def get_social_set(self, social_set_id: str) -> Dict:
        """
        Get detailed info for a specific social set

        Args:
            social_set_id: Social set ID

        Returns:
            Detailed social set info including platform configurations
        """
        endpoint = f"{self.BASE_URL}/social-sets/{social_set_id}/"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            self._handle_request_error(e, f"getting social set {social_set_id}")

    def get_default_social_set_id(self) -> str:
        """
        Get the first available social set ID

        Returns:
            Social set ID

        Raises:
            ValueError if no social sets available
        """
        social_sets = self.get_social_sets()
        if not social_sets:
            raise ValueError("No social sets available. Configure accounts in Typefully first.")
        return social_sets[0]["id"]

    # === Draft Endpoints ===

    def get_drafts(
        self,
        social_set_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List drafts for a social set

        Args:
            social_set_id: Social set ID (uses default if not provided)
            status: Filter by status: "draft", "scheduled", "published", "publishing", "error"
            limit: Maximum drafts to return

        Returns:
            List of drafts with metadata
        """
        if not social_set_id:
            social_set_id = self.get_default_social_set_id()

        endpoint = f"{self.BASE_URL}/social-sets/{social_set_id}/drafts"
        params = {}
        if status:
            params["status"] = status

        return self._paginated_request(endpoint, params, max_results=limit)

    def get_draft(self, draft_id: str, social_set_id: Optional[str] = None) -> Dict:
        """
        Get a specific draft

        Args:
            draft_id: Draft ID
            social_set_id: Social set ID (uses default if not provided)

        Returns:
            Draft details including status, platforms, and content
        """
        if not social_set_id:
            social_set_id = self.get_default_social_set_id()

        endpoint = f"{self.BASE_URL}/social-sets/{social_set_id}/drafts/{draft_id}"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            self._handle_request_error(e, f"getting draft {draft_id}")

    def create_draft(
        self,
        content: str,
        social_set_id: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        publish_at: Optional[str] = None,
        share: bool = True,
        draft_title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new draft

        Args:
            content: Post content (use 4 newlines to split into thread)
            social_set_id: Social set ID (uses default if not provided)
            platforms: List of platforms to post to (default: ["x"])
            publish_at: "now", "next-free-slot", or ISO-8601 datetime (None = draft only)
            share: Include shareable URL
            draft_title: Optional title for the draft
            tags: Optional list of tag slugs

        Returns:
            Created draft with ID, status, URLs
        """
        if not social_set_id:
            social_set_id = self.get_default_social_set_id()

        if not platforms:
            platforms = ["x"]

        endpoint = f"{self.BASE_URL}/social-sets/{social_set_id}/drafts"

        # Build platform-specific posts
        # Split content into posts for threads (4 newlines separator)
        posts = self._content_to_posts(content)

        platform_config = {}
        for platform in platforms:
            if platform in self.PLATFORMS:
                platform_config[platform] = {
                    "enabled": True,
                    "posts": posts,
                    "settings": {}
                }

        payload = {
            "platforms": platform_config,
            "share": share
        }

        if publish_at:
            payload["publish_at"] = publish_at
        if draft_title:
            payload["draft_title"] = draft_title
        if tags:
            payload["tags"] = tags

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Add convenience URLs
            if "id" in result:
                result["edit_url"] = f"https://typefully.com/?d={result['id']}"

            return result
        except requests.HTTPError as e:
            self._handle_request_error(e, "creating draft")

    def update_draft(
        self,
        draft_id: str,
        social_set_id: Optional[str] = None,
        content: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        publish_at: Optional[str] = None,
        draft_title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Update an existing draft (partial update)

        Args:
            draft_id: Draft ID to update
            social_set_id: Social set ID (uses default if not provided)
            content: New content (optional)
            platforms: List of platforms (optional)
            publish_at: Schedule time (optional)
            draft_title: Draft title (optional)
            tags: Tag slugs (optional)

        Returns:
            Updated draft
        """
        if not social_set_id:
            social_set_id = self.get_default_social_set_id()

        endpoint = f"{self.BASE_URL}/social-sets/{social_set_id}/drafts/{draft_id}"

        payload = {}

        if content is not None:
            posts = self._content_to_posts(content)
            if platforms is None:
                platforms = ["x"]

            platform_config = {}
            for platform in platforms:
                if platform in self.PLATFORMS:
                    platform_config[platform] = {
                        "enabled": True,
                        "posts": posts,
                        "settings": {}
                    }
            payload["platforms"] = platform_config

        if publish_at is not None:
            payload["publish_at"] = publish_at
        if draft_title is not None:
            payload["draft_title"] = draft_title
        if tags is not None:
            payload["tags"] = tags

        try:
            response = requests.patch(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            self._handle_request_error(e, f"updating draft {draft_id}")

    def _content_to_posts(self, content: str) -> List[Dict]:
        """
        Convert content string to posts array for API

        Uses 4 newlines as thread separator (Typefully convention)

        Args:
            content: Raw content string

        Returns:
            List of post dictionaries with text field
        """
        # Split on 4 consecutive newlines for thread posts
        parts = content.split("\n\n\n\n")
        return [{"text": part.strip()} for part in parts if part.strip()]

    # === Analytics/Status Methods ===

    def get_scheduled_drafts(self, social_set_id: Optional[str] = None) -> List[Dict]:
        """Get all scheduled drafts"""
        return self.get_drafts(social_set_id, status="scheduled")

    def get_published_drafts(self, social_set_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get recently published drafts"""
        return self.get_drafts(social_set_id, status="published", limit=limit)


class TypefullyManager:
    """Manager for Typefully API v2 with social sets support"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize manager with configuration

        Args:
            config_path: Path to .env file or config directory
        """
        self.config_path = config_path or os.path.dirname(__file__)
        self.config = self._load_config()
        self.client: Optional[TypefullyClient] = None
        self._social_sets: Optional[List[Dict]] = None
        self._social_set_map: Optional[Dict[str, int]] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the API client from .env file"""
        env_path = Path(self.config_path) / ".env"

        if not env_path.exists():
            print(f"Warning: .env file not found at {env_path}")
            print("Create a .env file with: TYPEFULLY_API_KEY=your_key_here")
            return

        api_key = None
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if line.startswith("TYPEFULLY_API_KEY="):
                        api_key = line.split("=", 1)[1]
                        break

        if api_key:
            self.client = TypefullyClient(api_key)

    def _load_config(self) -> Dict:
        """Load configuration settings"""
        config_path = Path(self.config_path) / "config.json"
        default_config = {
            "scheduling_enabled": False,  # Safety: draft-only by default
            "default_platforms": ["x"],  # Default to X/Twitter
            "default_share": True,
            "brand_voice_validation": True
        }

        if config_path.exists():
            with open(config_path) as f:
                return {**default_config, **json.load(f)}

        return default_config

    def _ensure_social_sets(self) -> None:
        """Fetch and cache social sets if not already loaded"""
        if self._social_sets is None:
            if not self.client:
                raise ValueError("No API key configured. Add TYPEFULLY_API_KEY to .env")
            self._social_sets = self.client.get_social_sets()
            # Build name -> id mapping (lowercase names for easy lookup)
            self._social_set_map = {}
            for ss in self._social_sets:
                name = ss.get("name", "").lower()
                username = ss.get("username", "").lower()
                ss_id = ss.get("id")
                if name:
                    self._social_set_map[name] = ss_id
                if username:
                    self._social_set_map[username] = ss_id

    def get_social_set_id(self, account: str) -> int:
        """
        Get social set ID for an account name

        Args:
            account: Account name or username (case-insensitive)

        Returns:
            Social set ID
        """
        self._ensure_social_sets()
        account_lower = account.lower()

        if account_lower in self._social_set_map:
            return self._social_set_map[account_lower]

        # Try partial match
        for name, ss_id in self._social_set_map.items():
            if account_lower in name or name in account_lower:
                return ss_id

        available = ", ".join(self._social_set_map.keys())
        raise ValueError(f"Account '{account}' not found. Available: {available}")

    def get_client(self, account: str = None) -> TypefullyClient:
        """Get the API client (account parameter kept for compatibility)"""
        if not self.client:
            raise ValueError("No API key configured. Add TYPEFULLY_API_KEY to .env")
        return self.client

    def list_accounts(self) -> List[str]:
        """List all available social set names"""
        self._ensure_social_sets()
        return list(self._social_set_map.keys())

    def create_draft(
        self,
        account: str,
        content: str,
        schedule: bool = False,
        schedule_date: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Create draft for specific account (respects scheduling config)

        Args:
            account: Account name (e.g., "covenant", "basilica")
            content: Post content
            schedule: Whether to schedule (only if globally enabled)
            schedule_date: When to schedule (ISO, "now", or "next-free-slot")
            platforms: Platforms to post to (default from config)
            title: Optional draft title
            tags: Optional tag slugs

        Returns:
            API response with draft details
        """
        social_set_id = self.get_social_set_id(account)

        # Use default platforms if not specified
        if platforms is None:
            platforms = self.config.get("default_platforms", ["x"])

        # Safety check: only schedule if globally enabled
        publish_at = None
        if schedule:
            if not self.config["scheduling_enabled"]:
                print("Warning: Scheduling is disabled. Creating draft only.")
                print("   To enable: Set 'scheduling_enabled': true in config.json")
            else:
                publish_at = schedule_date or "next-free-slot"

        return self.client.create_draft(
            content=content,
            social_set_id=social_set_id,
            platforms=platforms,
            publish_at=publish_at,
            share=self.config["default_share"],
            draft_title=title,
            tags=tags
        )

    def cross_post(
        self,
        accounts: List[str],
        content_map: Dict[str, str],
        schedule: bool = False,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Create drafts across multiple accounts with unique content

        Args:
            accounts: List of account names
            content_map: Dict mapping account name to content
            schedule: Whether to schedule
            platforms: Platforms to post to

        Returns:
            Dict mapping account to API response
        """
        results = {}
        for account in accounts:
            if account not in content_map:
                print(f"Warning: No content provided for {account}, skipping")
                continue

            try:
                result = self.create_draft(
                    account=account,
                    content=content_map[account],
                    schedule=schedule,
                    platforms=platforms
                )
                results[account] = result
                status = "scheduled" if schedule and self.config["scheduling_enabled"] else "drafted"
                url = result.get("edit_url", result.get("share_url", ""))
                print(f"[OK] {account}: {status} - {url}")
            except Exception as e:
                print(f"[ERROR] {account}: {str(e)}")
                results[account] = {"error": str(e)}

        return results

    def get_analytics(self, account: str, limit: int = 20) -> Dict:
        """
        Get analytics for account

        Args:
            account: Account name
            limit: Number of recent drafts to retrieve

        Returns:
            Analytics summary with recent published and scheduled drafts
        """
        social_set_id = self.get_social_set_id(account)

        try:
            published = self.client.get_published_drafts(social_set_id=social_set_id, limit=limit)
            scheduled = self.client.get_scheduled_drafts(social_set_id=social_set_id)

            return {
                "account": account,
                "recently_published": published,
                "scheduled": scheduled,
                "stats": {
                    "published_count": len(published),
                    "scheduled_count": len(scheduled)
                }
            }
        except Exception as e:
            return {"account": account, "error": str(e)}

    def get_social_sets_info(self, account: str = None) -> List[Dict]:
        """
        Get all social sets (account parameter ignored in v2)

        Returns:
            List of social sets with platform info
        """
        self._ensure_social_sets()
        return self._social_sets


def main():
    """CLI interface for Typefully client"""
    parser = argparse.ArgumentParser(description="Typefully API Client (v2)")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # create-draft command
    draft_parser = subparsers.add_parser("create-draft", help="Create a draft")
    draft_parser.add_argument("--account", required=True, help="Account name")
    draft_parser.add_argument("--content", required=True, help="Post content")
    draft_parser.add_argument("--schedule", action="store_true", help="Schedule post")
    draft_parser.add_argument("--schedule-date", help="Schedule date (ISO, 'now', or 'next-free-slot')")
    draft_parser.add_argument("--platforms", nargs="+", default=["x"],
                              help="Platforms to post to (x, linkedin, mastodon, threads, bluesky)")
    draft_parser.add_argument("--title", help="Optional draft title")
    draft_parser.add_argument("--tags", nargs="+", help="Tag slugs")

    # cross-post command
    cross_parser = subparsers.add_parser("cross-post", help="Cross-post to multiple accounts")
    cross_parser.add_argument("--accounts", required=True, nargs="+", help="Account names")
    cross_parser.add_argument("--content-json", required=True, help="JSON file with account:content mapping")
    cross_parser.add_argument("--schedule", action="store_true", help="Schedule posts")
    cross_parser.add_argument("--platforms", nargs="+", default=["x"], help="Platforms to post to")

    # get-drafts command
    drafts_parser = subparsers.add_parser("get-drafts", help="List drafts")
    drafts_parser.add_argument("--account", required=True, help="Account name")
    drafts_parser.add_argument("--status", choices=["draft", "scheduled", "published", "publishing", "error"],
                               help="Filter by status")
    drafts_parser.add_argument("--limit", type=int, default=20, help="Max results")

    # get-analytics command
    analytics_parser = subparsers.add_parser("get-analytics", help="Get analytics")
    analytics_parser.add_argument("--account", required=True, help="Account name")
    analytics_parser.add_argument("--limit", type=int, default=20, help="Number of recent drafts")

    # list-social-sets command
    subparsers.add_parser("list-social-sets", help="List all available social sets")

    # list-accounts command
    subparsers.add_parser("list-accounts", help="List available accounts (social sets)")

    # get-me command
    subparsers.add_parser("get-me", help="Get user info")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize manager
    manager = TypefullyManager()

    # Execute commands
    if args.command == "create-draft":
        result = manager.create_draft(
            account=args.account,
            content=args.content,
            schedule=args.schedule,
            schedule_date=args.schedule_date,
            platforms=args.platforms,
            title=args.title,
            tags=args.tags
        )
        # Show URL prominently
        status = "scheduled" if args.schedule and manager.config["scheduling_enabled"] else "draft created"
        print(f"\n[OK] Draft {status}")
        if "edit_url" in result:
            print(f"Edit: {result['edit_url']}")
        if "share_url" in result:
            print(f"Preview: {result['share_url']}")
        print()
        print(json.dumps(result, indent=2))

    elif args.command == "cross-post":
        with open(args.content_json) as f:
            content_map = json.load(f)
        results = manager.cross_post(
            accounts=args.accounts,
            content_map=content_map,
            schedule=args.schedule,
            platforms=args.platforms
        )
        print(json.dumps(results, indent=2))

    elif args.command == "get-drafts":
        social_set_id = manager.get_social_set_id(args.account)
        drafts = manager.client.get_drafts(social_set_id=social_set_id, status=args.status, limit=args.limit)
        print(f"Found {len(drafts)} drafts for {args.account}")
        print(json.dumps(drafts, indent=2))

    elif args.command == "get-analytics":
        result = manager.get_analytics(args.account, limit=args.limit)
        print(json.dumps(result, indent=2))

    elif args.command == "list-social-sets":
        sets = manager.get_social_sets_info()
        print("Available social sets:")
        for s in sets:
            username = s.get('username', '')
            print(f"  - {s.get('id')}: {s.get('name', 'unnamed')} (@{username})")
        print(json.dumps(sets, indent=2))

    elif args.command == "list-accounts":
        print("Available accounts (social sets):")
        for account in manager.list_accounts():
            print(f"  - {account}")
        if not manager.list_accounts():
            print("  (none - check your API key)")

    elif args.command == "get-me":
        result = manager.client.get_me()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
