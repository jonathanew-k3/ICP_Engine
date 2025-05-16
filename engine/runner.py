import argparse
import os
import pandas as pd
from datetime import datetime
from .utils import load_config, load_reference_companies, get_company_group_name
from .engine import score_leads

def main(config_name, input_file=None, limit=None):
    settings = load_config(config_name)
    shared_map_path = os.path.join("configs", "shared", "company_map.json")
    company_map = pd.read_json(shared_map_path)

    data_path = os.path.join("data", config_name)
    leads_path = input_file if input_file else os.path.join(data_path, "Source_Data.csv")
    ref_path = os.path.join("configs", config_name, "Reference_Companies.csv")

    leads_df = pd.read_csv(leads_path)
    if limit:
        leads_df = leads_df.head(limit)
    reference_df = load_reference_companies(ref_path)

    scored_df = score_leads(leads_df, reference_df, company_map, settings)

    # ✅ Add Company Group Name inside main
    scored_df.loc[:, "Company Group Name"] = scored_df["normalized_company"].apply(
        lambda x: get_company_group_name(x, company_map)
    )

    total_leads = len(scored_df)
    title_matches = scored_df["title_score"].gt(0).sum()
    reference_matches = (scored_df["match_source"] == "reference").sum()
    priority_industry_matches = (scored_df["match_source"] == "priority_industry").sum()
    keyword_sector_matches = (scored_df["match_source"] == "keyword_sector").sum()
    title_only_matches = (scored_df["match_type"] == "D - title_only").sum()

    reference_with_title = scored_df[(scored_df["match_source"] == "reference") & (scored_df["title_score"] > 0)].shape[0]
    priority_with_title = scored_df[(scored_df["match_source"] == "priority_industry") & (scored_df["title_score"] > 0)].shape[0]
    keyword_with_title = scored_df[(scored_df["match_source"] == "keyword_sector") & (scored_df["title_score"] > 0)].shape[0]

    print("\n✅ Summary:")
    print(f" - Total leads scored: {total_leads}")
    print(f" - Title matches: {title_matches}")
    print(f" - A - Reference matches: {reference_matches}")
    print(f" - B - Priority industry matches: {priority_industry_matches}")
    print(f" - C - Keyword-based matches: {keyword_sector_matches}")
    print(f" - D - Title-only matches: {title_only_matches}")
    print(f" - A - Reference matches with title: {reference_with_title}")
    print(f" - B - Priority industry matches with title: {priority_with_title}")
    print(f" - C - Keyword-based matches with title: {keyword_with_title}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=False, help="Optional input CSV file path")
    parser.add_argument("--limit", type=int, required=False, help="Optional row limit for sampling")
    args = parser.parse_args()
    main(args.config, args.input, args.limit)
