#!/usr/bin/env python3
"""
Typefully API Client

A Python client for interacting with the Typefully API to manage social media drafts,
scheduling, and analytics across multiple accounts.

Usage:
    python typefully_client.py create-draft --account "personal" --content "Your tweet content"
    python typefully_client.py get-published --account "company"
    python typefully_client.py get-analytics --account "main"
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional, Dict, List
import requests
from pathlib import Path

class TypefullyClient:
    """Client for interacting with Typefully API"""

    BASE_URL = "https://api.typefully.com/v1"

    def __init__(self, api_key: str):
        """
        Initialize Typefully client with API key

        Args:
            api_key: Typefully API key for a specific account
        """
        self.api_key = api_key
        self.headers = {
            "X-API-KEY": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def create_draft(
        self,
        content: str,
        threadify: bool = True,
        schedule_date: Optional[str] = None,
        share: bool = True,
        auto_retweet: bool = False,
        auto_plug: bool = False
    ) -> Dict:
        """
        Create a draft or scheduled post

        Args:
            content: Tweet text (use 4 newlines to split into multiple tweets)
            threadify: Auto-split content into tweets
            schedule_date: ISO format date or "next-free-slot" (None = draft only)
            share: Include shareable URL in response
            auto_retweet: Enable AutoRT per account settings
            auto_plug: Enable AutoPlug per account settings

        Returns:
            API response dict with draft details
        """
        endpoint = f"{self.BASE_URL}/drafts/"

        payload = {
            "content": content,
            "threadify": threadify,
            "share": share,
            "auto_retweet_enabled": auto_retweet,
            "auto_plug_enabled": auto_plug
        }

        if schedule_date:
            payload["schedule-date"] = schedule_date

        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_recently_scheduled(self, content_filter: Optional[str] = None) -> Dict:
        """
        Retrieve recently scheduled drafts

        Args:
            content_filter: Filter by "threads" or "tweets"

        Returns:
            API response dict with scheduled drafts
        """
        endpoint = f"{self.BASE_URL}/drafts/recently-scheduled/"
        params = {}
        if content_filter:
            params["content_filter"] = content_filter

        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_recently_published(self) -> Dict:
        """
        Retrieve recently published drafts

        Returns:
            API response dict with published drafts
        """
        endpoint = f"{self.BASE_URL}/drafts/recently-published/"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_notifications(self, kind: str = "activity") -> Dict:
        """
        Get latest notifications (useful for analytics)

        Args:
            kind: "inbox" (comments/replies) or "activity" (publishing events)

        Returns:
            API response dict with notifications
        """
        endpoint = f"{self.BASE_URL}/notifications/"
        params = {"kind": kind}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def mark_notifications_read(self, kind: Optional[str] = None, username: Optional[str] = None) -> Dict:
        """
        Mark notifications as read

        Args:
            kind: Filter by "inbox" or "activity"
            username: Mark read for specific account only

        Returns:
            API response dict
        """
        endpoint = f"{self.BASE_URL}/notifications/mark-all-read/"
        payload = {}
        if kind:
            payload["kind"] = kind
        if username:
            payload["username"] = username

        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()


class TypefullyManager:
    """Manager for handling multiple Typefully accounts"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize manager with configuration

        Args:
            config_path: Path to .env file or config directory
        """
        self.config_path = config_path or os.path.dirname(__file__)
        self.accounts = self._load_accounts()
        self.config = self._load_config()

    def _load_accounts(self) -> Dict[str, TypefullyClient]:
        """Load API keys from .env file and create clients"""
        env_path = Path(self.config_path) / ".env"
        accounts = {}

        if not env_path.exists():
            print(f"Warning: .env file not found at {env_path}")
            print("Create a .env file with: TYPEFULLY_API_KEY_<ACCOUNT>=your_key_here")
            return accounts

        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "TYPEFULLY_API_KEY_" in line:
                    key, value = line.split("=", 1)
                    account_name = key.replace("TYPEFULLY_API_KEY_", "").lower()
                    accounts[account_name] = TypefullyClient(value)

        return accounts

    def _load_config(self) -> Dict:
        """Load configuration settings"""
        config_path = Path(self.config_path) / "config.json"
        default_config = {
            "scheduling_enabled": False,  # Safety: draft-only by default
            "default_threadify": True,
            "default_share": True
        }

        if config_path.exists():
            with open(config_path) as f:
                return {**default_config, **json.load(f)}

        return default_config

    def get_client(self, account: str) -> TypefullyClient:
        """Get client for specific account"""
        if account not in self.accounts:
            available = ", ".join(self.accounts.keys())
            raise ValueError(f"Account '{account}' not found. Available: {available}")
        return self.accounts[account]

    def create_draft(
        self,
        account: str,
        content: str,
        schedule: bool = False,
        schedule_date: Optional[str] = None
    ) -> Dict:
        """
        Create draft for specific account (respects scheduling config)

        Args:
            account: Account name (e.g., "personal", "company")
            content: Tweet content
            schedule: Whether to schedule (only if globally enabled)
            schedule_date: When to schedule (ISO or "next-free-slot")

        Returns:
            API response dict
        """
        client = self.get_client(account)

        # Safety check: only schedule if globally enabled
        if schedule and not self.config["scheduling_enabled"]:
            print("⚠️  Scheduling is disabled. Creating draft only.")
            print("   To enable: Set 'scheduling_enabled': true in config.json")
            schedule_date = None
        elif schedule and schedule_date is None:
            schedule_date = "next-free-slot"

        return client.create_draft(
            content=content,
            schedule_date=schedule_date if schedule else None,
            threadify=self.config["default_threadify"],
            share=self.config["default_share"]
        )

    def cross_post(
        self,
        accounts: List[str],
        content_map: Dict[str, str],
        schedule: bool = False
    ) -> Dict[str, Dict]:
        """
        Create drafts across multiple accounts with unique content

        Args:
            accounts: List of account names
            content_map: Dict mapping account name to content
            schedule: Whether to schedule

        Returns:
            Dict mapping account to API response
        """
        results = {}
        for account in accounts:
            if account not in content_map:
                print(f"⚠️  No content provided for {account}, skipping")
                continue

            try:
                result = self.create_draft(
                    account=account,
                    content=content_map[account],
                    schedule=schedule
                )
                results[account] = result
                status = "scheduled" if schedule and self.config["scheduling_enabled"] else "drafted"
                print(f"✅ {account}: {status}")
            except Exception as e:
                print(f"❌ {account}: Error - {str(e)}")
                results[account] = {"error": str(e)}

        return results

    def get_analytics(self, account: str, days: int = 7) -> Dict:
        """
        Get analytics for account (recently published + notifications)

        Args:
            account: Account name
            days: Days to look back (not used by API, for display only)

        Returns:
            Combined analytics dict
        """
        client = self.get_client(account)

        try:
            published = client.get_recently_published()
            activity = client.get_notifications(kind="activity")

            return {
                "account": account,
                "recently_published": published,
                "activity_notifications": activity,
                "period": f"Last {days} days"
            }
        except Exception as e:
            return {"account": account, "error": str(e)}


def main():
    """CLI interface for Typefully client"""
    parser = argparse.ArgumentParser(description="Typefully API Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # create-draft command
    draft_parser = subparsers.add_parser("create-draft", help="Create a draft")
    draft_parser.add_argument("--account", required=True, help="Account name")
    draft_parser.add_argument("--content", required=True, help="Tweet content")
    draft_parser.add_argument("--schedule", action="store_true", help="Schedule post")
    draft_parser.add_argument("--schedule-date", help="Schedule date (ISO or next-free-slot)")

    # cross-post command
    cross_parser = subparsers.add_parser("cross-post", help="Cross-post to multiple accounts")
    cross_parser.add_argument("--accounts", required=True, nargs="+", help="Account names")
    cross_parser.add_argument("--content-json", required=True, help="JSON file with account:content mapping")
    cross_parser.add_argument("--schedule", action="store_true", help="Schedule posts")

    # get-published command
    pub_parser = subparsers.add_parser("get-published", help="Get recently published")
    pub_parser.add_argument("--account", required=True, help="Account name")

    # get-analytics command
    analytics_parser = subparsers.add_parser("get-analytics", help="Get analytics")
    analytics_parser.add_argument("--account", required=True, help="Account name")
    analytics_parser.add_argument("--days", type=int, default=7, help="Days to look back")

    # list-accounts command
    subparsers.add_parser("list-accounts", help="List configured accounts")

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
            schedule_date=args.schedule_date
        )
        print(json.dumps(result, indent=2))

    elif args.command == "cross-post":
        with open(args.content_json) as f:
            content_map = json.load(f)
        results = manager.cross_post(
            accounts=args.accounts,
            content_map=content_map,
            schedule=args.schedule
        )
        print(json.dumps(results, indent=2))

    elif args.command == "get-published":
        client = manager.get_client(args.account)
        result = client.get_recently_published()
        print(json.dumps(result, indent=2))

    elif args.command == "get-analytics":
        result = manager.get_analytics(args.account, days=args.days)
        print(json.dumps(result, indent=2))

    elif args.command == "list-accounts":
        print("Configured accounts:")
        for account in manager.accounts.keys():
            print(f"  - {account}")
        if not manager.accounts:
            print("  (none - check your .env file)")


if __name__ == "__main__":
    main()
