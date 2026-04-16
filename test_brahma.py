#!/usr/bin/env python3
"""Quick test for Brahma endpoint"""
import requests
import sys

try:
    data = {"message": "What is typical delivery time from Shanghai to Rotterdam?"}
    print(f"Testing /chat endpoint with message: {data['message'][:50]}...")
    
    resp = requests.post('http://localhost:8000/chat', json=data, timeout=30)
    print(f"Status code: {resp.status_code}")
    
    if resp.status_code == 200:
        result = resp.json()
        print("✓✓✓ BRAHMA WORKS!")
        print(f"Response: {result.get('response', 'N/A')[:100]}...")
        sys.exit(0)
    else:
        print(f"✗ Error response: {resp.text}")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Exception: {e}")
    sys.exit(1)
