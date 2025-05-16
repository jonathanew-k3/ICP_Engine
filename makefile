TEMPLATE_ID=1GeJSHa0lY8tM2GmO3N_QPu5Y4rP9O555ab5p1A3OtvE

build-konnect:
	python3 scripts/fetch_and_build.py KonnectInsights

run-konnect:
	python3 -m engine.runner --config KonnectInsights

test-configs:
	python3 scripts/test_config_load.py

generate-typeform-config:
	python3 scripts/typeform_to_config_ai.py

bootstrap-client:
	@echo "🧠 Generating OpenAI suggestions..."
	python3 scripts/typeform_to_config_ai.py

	@echo "📄 Creating Google Sheet for client $(CLIENT)..."
	python3 scripts/create_client_sheet.py $(CLIENT) $(TEMPLATE_ID)

	@echo "📤 Pushing config into the sheet..."
	python3 scripts/push_openai_config_to_sheet.py $(CLIENT)

	@echo "🔧 Building config.json from the sheet..."
	python3 -m scripts.fetch_and_build $(CLIENT)

	@echo "✅ Done. Final config is at configs/$(CLIENT)/config.json"
