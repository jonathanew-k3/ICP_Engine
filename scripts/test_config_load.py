from engine.utils import load_config
import sys

def test_load(client_name):
    try:
        config = load_config(client_name)
        print(f"✅ {client_name}: config loaded and validated successfully.")
    except Exception as e:
        print(f"❌ {client_name}: validation or load failed.")
        print(e)

if __name__ == "__main__":
    clients = ["konnect_insights", "KI_List", "kodex"]
    for client in clients:
        test_load(client)