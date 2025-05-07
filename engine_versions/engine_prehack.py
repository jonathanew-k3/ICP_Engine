import pandas as pd
from tqdm import tqdm
from rapidfuzz import process, fuzz
import json

def determine_match_type(row, fuzzy_threshold, priority_industries):
    if row.get("is_reference") and row.get("title_score", 0) > 0:
        return "A - reference+title"
    elif row.get("fuzzy_score", 0) and float(row["fuzzy_score"]) >= fuzzy_threshold and row.get("title_score", 0) > 0:
        return "B - fuzzy+title"
    elif row.get("match_source") == "priority_industry" and row.get("title_score", 0) > 0:
        return "C - priority industry+title"
    elif row.get("match_source") == "keyword_sector" and row.get("title_score", 0) > 0:
        return "D - keyword+title"
    elif row.get("title_score", 0) > 0:
        return "E - title_only"
    else:
        return "F - weak"

def score_leads(df, reference_companies, company_map, settings):
    import os
    from datetime import datetime

    if 'Company Name' not in reference_companies.columns and 'Company' not in reference_companies.columns:
        raise KeyError("The reference companies file must contain a 'Company Name' or 'Company' column.")

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

    reference_companies['normalized_company'] = reference_companies.get('Company Name', reference_companies.get('Company')).str.lower().str.strip()
    reference_companies['matched_group'] = reference_companies['normalized_company'].apply(lambda x: company_map.get(x, x))
    reference_sector_map = dict(zip(reference_companies['matched_group'], reference_companies['Sector'].fillna("")))
    reference_industry_map = dict(zip(reference_companies['matched_group'], reference_companies.get('Industry', "").fillna("")))

    df['reference_sector'] = df['matched_group'].map(reference_sector_map).fillna("")

    scores = []
    explanations = []
    explanation_labels = []
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
    mapped_industries = []

    job_keywords = settings.get("job_title_categories", {})
    sector_keywords = settings.get("sector_keywords", {})
    blacklist_terms = settings.get("blacklist_terms", [])
    sector_negatives = settings.get("sector_negatives", {})
    geo_prefs = settings.get("geo_scoring", {})
    preferred_countries = [c.lower() for c in geo_prefs.get("preferred", [])]
    penalized_countries = [c.lower() for c in geo_prefs.get("penalized", [])]

    explanation_map = {
        1: "Geo Match only",
        2: "Job Title only",
        3: "Geo Match and Job Title",
        4: "Keyword Sector Match only",
        5: "Keyword Sector and Geo Match",
        6: "Keyword Sector and Job Title",
        7: "Keyword Sector, Job Title, and Geo Match",
        8: "Reference Sector Match only",
        9: "Reference Sector and Geo Match",
        10: "Reference Sector and Job Title",
        11: "Reference Sector, Job Title, and Geo Match",
        16: "Reference Match only",
        17: "Reference and Geo Match",
        18: "Reference and Job Title",
        19: "Reference, Job Title, and Geo Match",
        20: "Reference and Keyword Sector Match",
        21: "Reference, Keyword Sector, and Geo Match",
        22: "Reference, Keyword Sector, and Job Title",
        23: "Reference, Keyword Sector, Job Title, and Geo Match",
        24: "Reference and Reference Sector Match",
        25: "Reference, Reference Sector, and Geo Match",
        26: "Reference, Reference Sector, and Job Title",
        27: "Reference, Reference Sector, Job Title, and Geo Match"
    }

    match_sources = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Scoring leads"):

        score = 0
        explanation = []

        # Reference or Fuzzy match (binary flag scoring)
        reference_or_fuzzy_matched = False
        if row['is_reference']:
            score += 16
            matched_count += 1
            explanation.append("Exact reference match")
            fuzzy_scores.append("")
            reference_or_fuzzy_matched = True
        else:
            result = process.extractOne(row['normalized_company'], reference_set, scorer=fuzz.token_sort_ratio)
            if result:
                candidate, similarity, _ = result
                if similarity >= settings.get("fuzzy_threshold", 95.5):
                    score += 16
                    fuzzy_matched += 1
                    explanation.append(f"Fuzzy match: {candidate} ({similarity}%)")
                    fuzzy_scores.append(similarity)
                    reference_or_fuzzy_matched = True
                else:
                    fuzzy_scores.append("")
            else:
                fuzzy_scores.append("")

        # Title categorization (binary flag scoring)
        title = str(row.get('Job Title', '')).lower()
        title_category = ""
        title_matched_flag = False
        for category, keywords in job_keywords.items():
            if any(kw.lower() in title for kw in keywords):
                score += 2
                explanation.append(f"Title matched: {category}")
                title_category = category
                title_matched += 1
                title_matched_flag = True
                break
        else:
            pass
        title_categories.append(title_category)

        # Sector matching (binary flag scoring)
        icp_sector = ""
        mapped_industry_label = ""

        # First: try to assign industry and sector from reference match
        if row['matched_group'] in reference_sector_map:
            icp_sector = reference_sector_map.get(row['matched_group'], "")
            industry_from_ref = reference_industry_map.get(row['matched_group'], "")
            if icp_sector:
                score += 8
                sector_matched += 1
                if icp_sector in priority_industries:
                    explanation.append("Priority Sector Matched (Reference)")
                else:
                    explanation.append(f"Sector from reference: {icp_sector}")
            mapped_industry_label = industry_from_ref or icp_sector

        # Otherwise: keyword-based mapping
        if not icp_sector:
            for category, keywords in sector_keywords.items():
                if any(kw in str(row.get('Industry', '')).lower() for kw in keywords):
                    negatives = sector_negatives.get(category, [])
                    sector_value_lower = str(row.get('Industry', '')).lower()
                    if any(neg in sector_value_lower for neg in negatives):
                        explanation.append(f"Sector match blocked: negative keyword in {category}")
                        continue
                    if any(term in sector_value_lower for term in blacklist_terms):
                        explanation.append("Sector match skipped (blacklisted term)")
                        break
                    score += 4
                    row['is_keyword_sector'] = True
                    sector_matched += 1
                    if category in priority_industries:
                        explanation.append("Priority Sector Matched")
                        explanation.append("keyword sector match")
                    else:
                        explanation.append(f"Sector matched: {category}")
                    icp_sector = category
                    mapped_industry_label = category
                    break

        icp_sectors.append(icp_sector)
        mapped_industries.append(mapped_industry_label)

        # HQ Country Extraction Logic with Fallback
        geo_score = 0
        raw_country = str(row.get('Company HQ', '')).strip()
        fallback_location = str(row.get("Person's Location", '')).strip()

        resolved_country = extract_country(raw_country, fallback_location)

        if resolved_country:
            resolved_countries.append(resolved_country)
            if resolved_country.lower() in penalized_countries:
                # No score addition for penalized countries in binary scoring
                pass
            elif resolved_country.lower() in preferred_countries:
                score += 1
                geo_score += 1
        else:
            resolved_countries.append("")

        geo_scores.append(geo_score)

        explanation_label = explanation_map.get(score, "Unclassified")
        explanation_labels.append(explanation_label)

        scores.append(score)
        explanations.append("; ".join(explanation))
        scoring_breakdowns.append(f"Binary:{score:04b}")

        normalized_industry = str(row.get("Industry", "")).strip().lower()
        priority_normalized = [x.strip().lower() for x in priority_industries]
        matched_priority_by_industry = normalized_industry in priority_normalized

        if reference_or_fuzzy_matched:
            match_source = "reference"
        elif matched_priority_by_industry and not reference_or_fuzzy_matched:
            match_source = "priority_industry"
        elif row.get('is_keyword_sector', False) and not matched_priority_by_industry and not reference_or_fuzzy_matched:
            match_source = "keyword_sector"
        else:
            match_source = "none"

        # Debug print for financial services industry
        if "financial services" in normalized_industry:
            print(f"[DEBUG] industry={normalized_industry}, matched_priority_by_industry={matched_priority_by_industry}, match_source={match_source}")

        match_sources.append(match_source)

    df['score'] = scores
    df['match_reason'] = explanations
    df['match_summary'] = explanation_labels

    if len(df) != len(icp_sectors) or len(df) != len(mapped_industries):
        raise ValueError(f"Length mismatch: df has {len(df)} rows but expected arrays differ")

    df['icp_sector'] = icp_sectors
    df['title_category'] = title_categories
    df['fuzzy_score'] = fuzzy_scores
    df['geo_score'] = geo_scores
    df['scoring_breakdown'] = scoring_breakdowns
    df['resolved_country'] = resolved_countries
    df['mapped_industry'] = mapped_industries

    df["title_score"] = [2 if cat else 0 for cat in title_categories]

    fuzzy_threshold = settings.get("fuzzy_threshold", 95.5)

    df.drop(columns=["reference_sector"], inplace=True)

    # The is_keyword_sector flag is now set during row iteration and not reconstructed here.

    df["match_source"] = match_sources
    df["match_type"] = df.apply(lambda row: determine_match_type(row, fuzzy_threshold, priority_industries), axis=1)

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
