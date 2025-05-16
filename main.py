import sys
import subprocess

def help_menu():
    print("Usage: python main.py [command] [client_name]")
    print("Available commands:")
    print("  build <client_name>       Generate config.json from Google Sheet")
    print("  run <client_name>         Run lead scoring for the client")
    print("  test                      Validate all configs")
    print("  typeform                  Generate config suggestions from Typeform + OpenAI")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_menu()
        sys.exit(1)

    command = sys.argv[1]
    client_name = sys.argv[2] if len(sys.argv) > 2 else "KonnectInsights"

    if command == "build":
        from scripts.fetch_and_build import fetch_and_build
        fetch_and_build(client_name)

    elif command == "run":
        subprocess.run(["python3", "-m", "engine.runner", "--config", client_name])

    elif command == "test":
        import scripts.test_config_load

    elif command == "typeform":
        import scripts.typeform_to_config_ai

    else:
        help_menu()