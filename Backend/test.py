import requests
import json

# Test the simple chat endpoint
def test_chat():
    url = "http://127.0.0.1:8000/api/chat"
    
    test_message = {
        "message": "Hello, AI!",
        "user_id": "test_user"
    }
    
    response = requests.post(url, json=test_message)
    
    if response.status_code == 200:
        print("✅ Chat endpoint working!")
        print("Response:", response.json())
    else:
        print("❌ Error:", response.status_code)

if __name__ == "__main__":
    test_chat()