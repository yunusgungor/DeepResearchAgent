#!/usr/bin/env python3
"""
UI Step handling test
"""

import requests
import json

def test_ui_step_handling():
    """UI'daki step handling'i test et"""
    
    print("🔍 UI Step Handling Test başlıyor...")
    
    # 1. Status endpoint'i test et
    print("\n1. Status endpoint test:")
    try:
        response = requests.get("http://localhost:8000/status", timeout=2)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Status başarılı, agent_status: {status_data.get('agent_status')}")
            print(f"   📊 current_task_steps sayısı: {len(status_data.get('current_task_steps', []))}")
        else:
            print(f"   ❌ Status hata: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status exception: {e}")
    
    # 2. Steps endpoint test
    print("\n2. Steps endpoint test:")
    try:
        response = requests.get("http://localhost:8000/agent/steps", timeout=2)
        if response.status_code == 200:
            steps_data = response.json()
            steps = steps_data.get('steps', [])
            print(f"   ✅ Steps başarılı, step sayısı: {len(steps)}")
            
            if steps:
                print(f"   📋 İlk step örneği:")
                first_step = steps[0]
                print(f"      Title: {first_step.get('title')}")
                print(f"      Description: {first_step.get('description')}")
                print(f"      Status: {first_step.get('status')}")
                print(f"      Timestamp: {first_step.get('timestamp')}")
                
                # UI format'ına çevirmeyi test et
                converted_step = {
                    "step_type": "api_step",
                    "title": first_step.get("title", ""),
                    "description": first_step.get("description", ""),
                    "timestamp": first_step.get("timestamp", ""),
                    "details": {
                        "status": first_step.get("status", ""),
                    },
                    "agent_name": "api"
                }
                print(f"   🔄 UI format'a çevrildi:")
                print(f"      step_type: {converted_step['step_type']}")
                print(f"      details.status: {converted_step['details']['status']}")
        else:
            print(f"   ❌ Steps hata: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Steps exception: {e}")
    
    print("\n✅ Test tamamlandı!")

if __name__ == "__main__":
    test_ui_step_handling()
