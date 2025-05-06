import pandas as pd
from .utils import normalize_company, match_company
from tqdm import tqdm
from rapidfuzz import process, fuzz
import json
import re

def score_leads(df, reference_companies, company_map, settings):
    import os

    reference_set = set(reference_companies['normalized_company'].tolist())

    df['normalized_company'] = df['Company Name'].str.lower().str.strip()
    df['matched_group'] = df['normalized_company'].apply(lambda x: company_map.get(x, x))
    df['is_reference'] = df['matched_group'].isin(reference_set)

    scores = []
    explanations = []
    confidences = []
    review_flags = []
    matched_count = 0
    fuzzy_matched = 0
    title_matched = 0
    sector_matched = 0

    job_keywords = settings.get("job_title_categories", {})
    sector_keywords = settings.get("sector_keywords", {})
    weights = settings.get("weights", {})
    blacklist_terms = settings.get("blacklist_terms", [])
    sector_negatives = settings.get("sector_negatives", {})

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Scoring leads"):

        score = 0
        explanation = []

        # Reference match
        if row['is_reference']:
            score += weights.get("reference_company", 10)
            matched_count += 1
            explanation.append("Exact reference match")

        # Fuzzy match (company name)
        else:
            result = process.extractOne(row['normalized_company'], reference_set, scorer=fuzz.token_sort_ratio)
            if result:
                candidate, similarity, _ = result
                if similarity >= settings.get("fuzzy_threshold", 95.5):
                    score += weights.get("fuzzy_match", 5)
                    fuzzy_matched += 1
                    explanation.append(f"Fuzzy match: {candidate} ({similarity}%)")

        # Title matching
        title = str(row.get('title', '')).lower()
        for category, keywords in job_keywords.items():
            if any(kw in title for kw in keywords):
                score += weights.get("title_match", 5)
                title_matched += 1
                explanation.append(f"Title matched: {category}")
                break

        # Domain-based sector inference
        domain = str(row.get('domain', '')).lower()
        domain_match_applied = False
        if domain.endswith(".bank"):
            score += weights.get("sector_match", 3)
            sector_matched += 1
            explanation.append("Sector matched via domain: Banking (.bank)")
            domain_match_applied = True
        elif domain.endswith(".games"):
            score += weights.get("sector_match", 3)
            sector_matched += 1
            explanation.append("Sector matched via domain: Gaming (.games)")
            domain_match_applied = True
        elif domain.endswith(".org"):
            explanation.append("Possible NGO (.org) — flagged")

        # Sector matching
        sector = str(row.get('sector', '')).lower()
        if not domain_match_applied:
            for category, keywords in sector_keywords.items():
                if any(kw in sector for kw in keywords):
                    # Check for negative keywords specific to this category
                    negatives = sector_negatives.get(category, [])
                    if any(neg in sector for neg in negatives):
                        explanation.append(f"Sector match blocked: negative keyword in {category}")
                        continue
                    if any(term in sector for term in blacklist_terms):
                        explanation.append("Sector match skipped (blacklisted term)")
                        break
                    score += weights.get("sector_match", 3)
                    sector_matched += 1
                    explanation.append(f"Sector matched: {category}")
                    break

        # HQ Country Extraction Logic with Fallback
        country = str(row.get('Company HQ', '')).strip().lower()
        if not country:
            country = str(row.get("Person's Location", '')).strip().lower()

        if country:
            if country in ['united states', 'canada', 'mexico', 'brazil']:
                score -= 1
                explanation.append(f"Geo penalty: {country.title()}")
            elif country in ['united kingdom', 'germany', 'france', 'netherlands', 'italy', 'spain', 'sweden', 'norway', 'finland']:
                score += 1
                explanation.append(f"Geo boost: {country.title()}")

        if score >= 12:
            confidence = "High"
        elif score >= 7:
            confidence = "Medium"
        else:
            confidence = "Low"

        scores.append(score)
        explanations.append("; ".join(explanation))
        confidences.append(confidence)
        review_flags.append(confidence == "Medium")

    df['score'] = scores
    df['match_reason'] = explanations
    df['confidence'] = confidences
    df['review_flag'] = review_flags

    print(f"\n✅ Summary:")
    print(f" - Total leads scored: {len(df)}")
    print(f" - Matched reference companies: {matched_count}")
    print(f" - Fuzzy company matches: {fuzzy_matched}")
    print(f" - Title matches: {title_matched}")
    print(f" - Sector matches: {sector_matched}")

    # Save excluded leads (low confidence or low score)
    excluded_df = df[df['confidence'] == "Low"]
    if not excluded_df.empty:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excluded_df.to_csv(f"data/{settings.get('client_name', 'default')}/Excluded_Leads_{timestamp}.csv", index=False)
    else:
        # If no excluded leads, still need a timestamp for metadata log consistency
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save run metadata
    run_metadata = {
        "total_scored": len(df),
        "matched_reference": matched_count,
        "fuzzy_matches": fuzzy_matched,
        "title_matches": title_matched,
        "sector_matches": sector_matched,
        "run_time": timestamp,
        "client": settings.get("client_name", "default")
    }
    import os
    os.makedirs(f"data/{settings.get('client_name', 'default')}", exist_ok=True)
    with open(f"data/{settings.get('client_name', 'default')}/run_info_{timestamp}.json", "w") as f:
        json.dump(run_metadata, f, indent=2)

    return df
