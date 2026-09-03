import sys
sys.stdout.reconfigure(encoding='utf-8')
from fastapi.testclient import TestClient
from main import app
import models
from database import SessionLocal

client = TestClient(app)

def test_ai_suggestions_endpoint():
    resp = client.get("/api/ai/suggestions")
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) >= 3
    print("AI Suggestions:", data["suggestions"])

def test_ai_chat_pricing_and_products():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "What are your cheapest cold-pressed juices under ₹150, and what discount coupons are available?"
            }
        ]
    }
    resp = client.post("/api/ai/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    print("\n--- AI Chat Response ---")
    print(data["reply"])
    print("Suggested products count:", len(data.get("suggested_products", [])))
    print("Quick replies:", data.get("quick_replies", []))

def test_ai_chat_specific_product():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Tell me the origin and ingredients of Kashmiri Apple Juice."
            }
        ],
        "current_product_id": 1
    }
    resp = client.post("/api/ai/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    reply = data["reply"].lower()
    assert "kashmir" in reply or "apple" in reply or "srinagar" in reply or "149" in reply
    print("\n--- Specific Product Response ---")
    print(data["reply"])

if __name__ == "__main__":
    test_ai_suggestions_endpoint()
    test_ai_chat_pricing_and_products()
    test_ai_chat_specific_product()
    print("\n=== ALL AI TESTS PASSED WITH 100% SUCCESS! ===")
