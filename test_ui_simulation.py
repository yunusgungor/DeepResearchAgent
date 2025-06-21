#!/usr/bin/env python3
"""
Streamlit session state simulation test
"""

import requests
import json
import time

class MockAgentManager:
    def __init__(self):
        self.detailed_steps = []
        self.current_step_status = "idle"
        self.is_initialized = False

def simulate_ui_refresh():
    """UI refresh mantığını simüle et"""
    
    print("🔄 UI Refresh simülasyonu başlıyor...")
    
    # Mock session state
    agent_manager = MockAgentManager()
    should_refresh = False
    
    print(f"📊 Başlangıç: detailed_steps sayısı = {len(agent_manager.detailed_steps)}")
    
    # API çağrısını simüle et
    try:
        response = requests.get("http://localhost:8000/status", timeout=2)
        if response.status_code == 200:
            status_data = response.json()
            agent_status = status_data.get("agent_status", "idle")
            print(f"✅ API Status: {agent_status}")
            
            # Steps endpoint test
            try:
                steps_response = requests.get("http://localhost:8000/agent/steps", timeout=2)
                if steps_response.status_code == 200:
                    steps_data = steps_response.json()
                    if "steps" in steps_data:
                        new_steps = steps_data["steps"]
                        print(f"📋 API'den {len(new_steps)} step alındı")
                        
                        # UI format'ına çevir
                        converted_steps = []
                        for step in new_steps:
                            converted_step = {
                                "step_type": "api_step",
                                "title": step.get("title", ""),
                                "description": step.get("description", ""),
                                "timestamp": step.get("timestamp", ""),
                                "details": {
                                    "status": step.get("status", ""),
                                },
                                "agent_name": "api"
                            }
                            converted_steps.append(converted_step)
                        
                        print(f"🔄 {len(converted_steps)} step UI format'ına çevrildi")
                        
                        # Mock session state güncelle
                        if len(converted_steps) != len(agent_manager.detailed_steps):
                            agent_manager.detailed_steps = converted_steps
                            should_refresh = True
                            print(f"✅ Session state güncellendi! Yeni step sayısı: {len(agent_manager.detailed_steps)}")
                            
                            # İlk birkaç step'i göster
                            for i, step in enumerate(agent_manager.detailed_steps[:3]):
                                print(f"   Step {i+1}: {step['title']} - {step['details']['status']}")
                        else:
                            print(f"ℹ️ Step sayısı değişmemiş ({len(converted_steps)}), güncelleme yapılmadı")
            
            except Exception as e:
                print(f"❌ Steps endpoint hatası: {e}")
            
            # Fallback test
            if not should_refresh and "current_task_steps" in status_data:
                fallback_steps = status_data["current_task_steps"]
                print(f"🔄 Fallback: Status'da {len(fallback_steps)} step var")
                if len(fallback_steps) != len(agent_manager.detailed_steps):
                    agent_manager.detailed_steps = fallback_steps
                    should_refresh = True
                    print(f"✅ Fallback ile güncellenld! Yeni step sayısı: {len(agent_manager.detailed_steps)}")
    
    except Exception as e:
        print(f"❌ API bağlantı hatası: {e}")
    
    print(f"\n📊 Sonuç:")
    print(f"   - should_refresh: {should_refresh}")
    print(f"   - detailed_steps sayısı: {len(agent_manager.detailed_steps)}")
    print(f"   - current_step_status: {agent_manager.current_step_status}")

if __name__ == "__main__":
    simulate_ui_refresh()
