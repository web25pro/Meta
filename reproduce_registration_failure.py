import asyncio
import httpx
import json

async def reproduce():
    url = "http://localhost:8000/api/v1/users"
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123", # Too short (min 12)
        "role": "User",
        "user_type": "User"
    }
    
    print(f"Attempting registration with too short password...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    payload["password"] = "SecurePassword123!" # Correct length
    print(f"\nAttempting registration with valid password...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
