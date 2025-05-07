import pandas as pd
from .utils import normalize_company, match_company
from tqdm import tqdm
from rapidfuzz import process, fuzz
import json
import re

def determine_match_type(row, fuzzy_threshold):
    if row.get("is_reference") and row.get("title_score", 0) > 0:
        return "A - reference+title"
    elif row.get("fuzzy_score", 0) and float(row["fuzzy_score"]) >= fuzzy_threshold and row.get("title_score", 0) > 0:
        return "B - fuzzy+title"
    elif "priority sector matched" in row.get("match_reason", "").lower() and row.get("title_score", 0) > 0:
        return "C - priority industry+title"
    elif row.get("match_reason", "").lower().find("keyword") != -1 and row.get("title_score", 0) > 0:
        return "D - keyword+title"
    elif row.get("title_score", 0) > 0:
        return "E - title_only"
    else:
        return "F - weak"

def score_leads(df, reference_companies, company_map, settings):
    import os
    from datetime import datetime

    us_states = {
        "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
        "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
        "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
        "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey", "new mexico",
        "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
        "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
        "virginia", "washington", "west virginia", "wisconsin", "wyoming"
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client = settings.get("client_name", "default")
    output_dir = os.path.join("output_data", f"{client}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    priority_industries_path = os.path.join("configs", client, "priority_industries.json")
    if os.path.exists(priority_industries_path):
        with open(priority_industries_path, "r") as f:
            priority_industries = set(json.load(f))
    else:
        priority_industries = set()
    print("🧪 Sample industries from input data:", df['Industry'].dropna().unique()[:20])
    print("📌 Loaded priority industries:", list(priority_industries)[:20])

    def extract_country(hq, person_location=""):
        try:
            hq_lower = str(hq).strip().lower()

            if not hq_lower or hq_lower in ["nan", "none", ""]:
                person_loc_lower = str(person_location).strip().lower()
                if "united states" in person_loc_lower:
                    return "United States"
                parts = [p.strip() for p in person_loc_lower.split(",") if p.strip()]
                if len(parts) >= 2:
                    if parts[-1] in us_states or parts[-2] in us_states:
                        return "United States"
                    return parts[-1].title()
                return "unknown"

            if "united states" in hq_lower:
                return "United States"

            parts = [p.strip() for p in hq_lower.split(",") if p.strip()]
            if len(parts) >= 2:
                if parts[-1] in us_states or parts[-2] in us_states:
                    return "United States"
                return parts[-1].title()
            if any(state in hq_lower for state in us_states):
                return "United States"

            return parts[-1].title() if parts else "unknown"
        except Exception:
            return "unknown"

    reference_set = set(reference_companies['normalized_company'].tolist())

    df['normalized_company'] = df['Company Name'].str.lower().str.strip()
    df['matched_group'] = df['normalized_company'].apply(lambda x: company_map.get(x, x))
    df['is_reference'] = df['matched_group'].isin(reference_set)

    reference_sector_map = dict(zip(reference_companies['normalized_company'], reference_companies['Sector'].fillna("")))
    df['reference_sector'] = df['matched_group'].map(reference_sector_map).fillna("")

    scores = []
    explanations = []
    confidences = []
    review_flags = []
    matched_count = 0
    fuzzy_matched = 0
    title_matched = 0
    sector_matched = 0

    icp_sectors = []
    title_categories = []
    fuzzy_scores = []
    geo_scores = []
    resolved_countries = []
    scoring_breakdowns = []

    job_keywords = settings.get("job_title_categories", {})
    sector_keywords = settings.get("sector_keywords", {})
    weights = settings.get("weights", {})
    blacklist_terms = settings.get("blacklist_terms", [])
    sector_negatives = settings.get("sector_negatives", {})
    geo_prefs = settings.get("geo_scoring", {})
    preferred_countries = [c.lower() for c in geo_prefs.get("preferred", [])]
    penalized_countries = [c.lower() for c in geo_prefs.get("penalized", [])]

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Scoring leads"):

        score = 0
        explanation = []

        # Reference match
        if row['is_reference']:
            score += weights.get("reference_company", 10)
            matched_count += 1
            explanation.append("Exact reference match")
            fuzzy_scores.append("")

        # Fuzzy match (company name)
        else:
            result = process.extractOne(row['normalized_company'], reference_set, scorer=fuzz.token_sort_ratio)
            if result:
                candidate, similarity, _ = result
                if similarity >= settings.get("fuzzy_threshold", 95.5):
                    score += weights.get("fuzzy_match", 5)
                    fuzzy_matched += 1
                    explanation.append(f"Fuzzy match: {candidate} ({similarity}%)")
                    fuzzy_scores.append(similarity)
                else:
                    fuzzy_scores.append("")
            else:
                fuzzy_scores.append("")

        # Title categorization (always applied)
        title = str(row.get('Job Title', '')).lower()
        title_score = 0
        title_category = ""
        for category, keywords in job_keywords.items():
            if any(kw.lower() in title for kw in keywords):
                title_score = weights.get("title_match", 5)
                explanation.append(f"Title matched: {category}")
                title_category = category
                title_matched += 1
                break
        else:
            pass
        title_categories.append(title_category)
        score += title_score

        # Sector matching
        icp_sector = row.get('reference_sector', "")
        if icp_sector:
            score += weights.get("sector_match", 3)
            sector_matched += 1
            if icp_sector in priority_industries:
                explanation.append("Priority Sector Matched (Reference)")
            else:
                explanation.append(f"Sector from reference: {icp_sector}")
            icp_sectors.append(icp_sector)
        else:
            icp_sector = ""
            for category, keywords in sector_keywords.items():
                if any(kw in str(row.get('Industry', '')).lower() for kw in keywords):
                    # Check for negative keywords specific to this category
                    negatives = sector_negatives.get(category, [])
                    sector_value_lower = str(row.get('Industry', '')).lower()
                    if any(neg in sector_value_lower for neg in negatives):
                        explanation.append(f"Sector match blocked: negative keyword in {category}")
                        continue
                    if any(term in sector_value_lower for term in blacklist_terms):
                        explanation.append("Sector match skipped (blacklisted term)")
                        break
                    score += weights.get("sector_match", 3)
                    sector_matched += 1
                    if category in priority_industries:
                        explanation.append("Priority Sector Matched")
                    else:
                        explanation.append(f"Sector matched: {category}")
                    icp_sector = category
                    break
            icp_sectors.append(icp_sector)

        # HQ Country Extraction Logic with Fallback
        geo_score = 0
        raw_country = str(row.get('Company HQ', '')).strip()
        fallback_location = str(row.get("Person's Location", '')).strip()

        resolved_country = extract_country(raw_country, fallback_location)

        if resolved_country:
            resolved_countries.append(resolved_country)
            if resolved_country.lower() in penalized_countries:
                score -= 1
                geo_score -= 1
                explanation.append(f"Geo penalty: {resolved_country.title()}")
            elif resolved_country.lower() in preferred_countries:
                score += 1
                geo_score += 1
        else:
            resolved_countries.append("")

        geo_scores.append(geo_score)

        bands = settings.get("confidence_bands", {})
        high_cutoff = bands.get("high", 12)
        medium_cutoff = bands.get("medium", 7)

        if score >= high_cutoff:
            confidence = "High"
        elif score >= medium_cutoff:
            confidence = "Medium"
        else:
            confidence = "Low"

        scores.append(score)
        explanations.append("; ".join(explanation))
        confidences.append(confidence)
        review_flags.append(confidence == "Medium")

        scoring_breakdowns.append(f"Ref:{weights.get('reference_company', 10) if row['is_reference'] else 0}; "
                                  f"Fuzzy:{weights.get('fuzzy_match', 5) if explanation and 'Fuzzy match' in explanation[-1] else 0}; "
                                  f"Title:{weights.get('title_match', 5) if title_categories[-1] else 0}; "
                                  f"Sector:{weights.get('sector_match', 3) if icp_sectors[-1] else 0}; "
                                  f"Geo:{geo_score}")

    df['score'] = scores
    df['match_reason'] = explanations
    df['confidence'] = confidences
    df['review_flag'] = review_flags

    if len(df) != len(icp_sectors):
        raise ValueError(f"Length mismatch: df has {len(df)} rows but icp_sectors has {len(icp_sectors)} entries")

    df['icp_sector'] = icp_sectors
    df['title_category'] = title_categories
    df['fuzzy_score'] = fuzzy_scores
    df['geo_score'] = geo_scores
    df['scoring_breakdown'] = scoring_breakdowns
    df['resolved_country'] = resolved_countries

    df["title_score"] = [weights.get("title_match", 5) if cat else 0 for cat in title_categories]

    fuzzy_threshold = settings.get("fuzzy_threshold", 95.5)
    df["match_type"] = df.apply(lambda row: determine_match_type(row, fuzzy_threshold), axis=1)

    df.drop(columns=["reference_sector"], inplace=True)

    print(f"\n✅ Summary:")
    print(f" - Total leads scored: {len(df)}")
    print(f" - Matched reference companies: {matched_count}")
    print(f" - Fuzzy company matches: {fuzzy_matched}")
    print(f" - Title matches: {title_matched}")
    print(f" - Priority industry matches (sector): {sector_matched}")


    # Save run metadata
    run_metadata = {
        "total_scored": len(df),
        "matched_reference": matched_count,
        "fuzzy_matches": fuzzy_matched,
        "title_matches": title_matched,
        "sector_matches": sector_matched,
        "run_time": timestamp,
        "client": client
    }
    with open(f"{output_dir}/run_info.json", "w") as f:
        json.dump(run_metadata, f, indent=2)

    df.to_csv(os.path.join(output_dir, "Scored_Leads.csv"), index=False)
    return df
