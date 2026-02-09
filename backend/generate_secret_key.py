#!/usr/bin/env python3
"""Generate a secure SECRET_KEY for .env file."""

import secrets

if __name__ == "__main__":
    secret_key = secrets.token_urlsafe(32)
    print("=" * 60)
    print("Generated SECRET_KEY:")
    print("=" * 60)
    print(secret_key)
    print("=" * 60)
    print("\nCopy this key and paste it into your .env file as SECRET_KEY value")
