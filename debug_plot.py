#!/usr/bin/env python3
import requests
import json

# Test the plot generation endpoint
url = "http://localhost:5000/generate-plot"
data = {
    "indicator_filter": "NTP",
    "time_range": "all"
}

print("Testing plot generation endpoint...")
print(f"URL: {url}")
print(f"Data: {data}")

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")

    if response.status_code == 200:
        try:
            json_data = response.json()
            if 'plot_html' in json_data:
                html_length = len(json_data['plot_html'])
                print(f"Success! Plot HTML length: {html_length} characters")
                print(f"First 200 chars: {json_data['plot_html'][:200]}")
                print("Last 200 chars: ..." + json_data['plot_html'][-200:])
            else:
                print("Error: No plot_html in response")
                print(f"Response: {json_data}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response (first 500 chars): {response.text[:500]}")
    else:
        print(f"Error: HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"Request failed: {e}")