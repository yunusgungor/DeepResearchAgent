#!/usr/bin/env python3
"""
WebSocket bağlantısını test etmek için basit bir script
"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        print("🔗 WebSocket bağlantısı test ediliyor...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket bağlantısı başarılı!")
            
            # Basit bir test mesajı gönder
            test_message = {
                "type": "test",
                "step": "Test Step",
                "details": "WebSocket test mesajı",
                "timestamp": "2025-06-21T19:54:00Z"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test mesajı gönderildi")
            
            # Kısa süre bekle
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"❌ WebSocket bağlantı hatası: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    sys.exit(0 if result else 1)
