# Lead Scoring Engine

A modular and configurable lead scoring engine designed to help identify high-potential leads using multiple signals like company match, job title, and sector fit.

---

## 🚀 Features

✅ Job title scoring and multi-source sector classification (reference → industry map → keyword fallback)  
✅ Sector relevance prioritized via client-defined priority sectors

## 🛠 Configuration Layers (per client)

Each client has their own config directory under `configs/clients/<client_name>`, supporting:

- `settings.json`: scoring weights, keyword lists, job title categories, geo preferences, etc.
- `priority_sectors.json`: maps which sectors are prioritized in scoring.
- `reference_companies.csv`: a curated list of matched companies and sectors.

Shared resources across clients:

- `industry_sector_map.csv`: maps raw industry labels to normalized sectors.
- `industry_synonyms.json`: optional synonym support for mapping industry variants.

---

## 🗂 Folder Structure