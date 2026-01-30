import requests
import os
from datetime import datetime
from pathlib import Path

def main():
    """Generate a weekly briefing using the CEO briefing system."""
    try:
        # Get the API base URL
        api_port = os.getenv("API_PORT", "8000")
        base_url = f"http://localhost:{api_port}"

        print("Generating CEO briefing via API...")

        # Call the CEO briefing generation endpoint
        response = requests.post(f"{base_url}/api/ceo-briefing/generate")

        if response.status_code == 200:
            result = response.json()
            report_path = result.get("report_path")

            print(f"CEO briefing generated successfully: {report_path}")

            # Get the latest briefing content
            content_response = requests.get(f"{base_url}/api/ceo-briefing/latest")
            if content_response.status_code == 200:
                content_result = content_response.json()
                content = content_result.get("content", "")

                print("\nWeekly CEO Briefing Generated Successfully!")
                print("="*50)
                print(content[:1000] + "..." if len(content) > 1000 else content)
                print("="*50)

                return report_path
            else:
                print(f"Could not retrieve briefing content: {content_response.status_code}")
                return report_path
        else:
            print(f"Failed to generate briefing: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error generating weekly briefing: {e}")
        return None

if __name__ == "__main__":
    main()