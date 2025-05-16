# ICP Engine – Lead Scoring Framework

The ICP Engine is a modular Python system for scoring and prioritizing leads based on configurable criteria such as reference company match, industry alignment, title relevance, and geographic focus.

## 🔧 Features

- A–E match type banding for clean prioritization
- Modular, client-specific config system
- Clean scored outputs with consistent fields
- Integration-ready design for Clay, Zapier, HubSpot, etc.
- Pre-release tagging and changelog versioning
- Easy-to-rebuild virtual environments

## 📁 Project Structure

```
configs/               # Per-client settings and reference files
data/                  # Raw lead input files (e.g. Source_Data.csv)
engine/                # Core scoring logic
shared/                # Shared resources (e.g. company_map.json)
output_data/           # Timestamped scored outputs
docs/                  # Optional: stream planning and roadmap
```

## ▶️ Getting Started

### 1. Set up the environment

```bash
./setup_env.sh
```

This creates a clean Python virtual environment and installs the required packages.

### 2. Score leads

```bash
python3 -m engine.runner --config konnect_insights
```

Optional flags:
- `--input`: Specify an input CSV path
- `--limit`: Limit the number of rows for testing

### 3. Output

- Clean scored file will be saved to:
  ```
  output_data/{client}_{timestamp}/scored_output_clean.csv
  ```

## 🧪 Match Types (A–E)

| Type | Description                     |
|------|---------------------------------|
| A    | Reference match (fuzzy or exact) + title match |
| B    | Industry match (from priority list) + title match |
| C    | Keyword-inferred sector + title match |
| D    | Title match only                |
| E    | Weak/unmatched leads            |

## 📝 Versioning

- Pre-releases follow this format: `vYYYY.MM.DD-v0.X`
- See [`CHANGELOG.md`](./CHANGELOG.md) for details

## 🚧 Future Improvements

- GUI for config editing and output review
- Integrations with CRMs and automation tools
- AI-assisted ICP targeting and list generation

---

## 🤝 Contributing

Coming soon: contributor guidelines, CI scripts, and documentation on how to add new clients or sectors.
