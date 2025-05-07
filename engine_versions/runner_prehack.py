import argparse
import os
import pandas as pd
from datetime import datetime
from .utils import load_config, load_reference_companies
from .engine import score_leads

def main(config_name, input_file=None, limit=None):
    company_map, settings = load_config(config_name)

    data_path = os.path.join("data", config_name)
    leads_path = input_file if input_file else os.path.join(data_path, "Source_Data.csv")
    ref_path = os.path.join(data_path, "Reference_Companies.csv")

    leads_df = pd.read_csv(leads_path)
    if limit:
        leads_df = leads_df.head(limit)
    reference_df = load_reference_companies(ref_path)

    scored_df = score_leads(leads_df, reference_df, company_map, settings)

    total_leads = len(scored_df)
    ref_matches = scored_df["is_reference"].sum()
    fuzzy_matches = scored_df["match_reason"].str.contains("Fuzzy match", case=False, na=False).sum()
    title_matches = scored_df["title_score"].gt(0).sum()
    reference_matches = (scored_df["match_source"] == "reference").sum()
    priority_industry_matches = (scored_df["match_source"] == "priority_industry").sum()
    keyword_sector_matches = (scored_df["match_source"] == "keyword_sector").sum()

    reference_with_title = scored_df[(scored_df["match_source"] == "reference") & (scored_df["title_score"] > 0)].shape[0]
    priority_with_title = scored_df[(scored_df["match_source"] == "priority_industry") & (scored_df["title_score"] > 0)].shape[0]
    keyword_with_title = scored_df[(scored_df["match_source"] == "keyword_sector") & (scored_df["title_score"] > 0)].shape[0]

    print("\n✅ Summary:")
    print(f" - Total leads scored: {total_leads}")
    print(f" - Matched reference companies: {ref_matches}")
    print(f" - Fuzzy company matches: {fuzzy_matches}")
    print(f" - Title matches: {title_matches}")
    print(f" - Matches from reference list: {reference_matches}")
    print(f" - Matches from priority industry list: {priority_industry_matches}")
    print(f" - Matches from sector keywords: {keyword_sector_matches}")
    print(f" - Matches from reference list with title match: {reference_with_title}")
    print(f" - Matches from priority industry list with title match: {priority_with_title}")
    print(f" - Matches from sector keywords with title match: {keyword_with_title}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=False, help="Optional input CSV file path")
    parser.add_argument("--limit", type=int, required=False, help="Optional row limit for sampling")
    args = parser.parse_args()
    main(args.config, args.input, args.limit)
