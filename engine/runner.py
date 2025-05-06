import argparse
import os
import pandas as pd
from datetime import datetime
from .utils import load_config, load_reference_companies
from .engine import score_leads

def main(config_name):
    company_map, settings = load_config(config_name)

    data_path = os.path.join("data", config_name)
    leads_path = os.path.join(data_path, "Source_Data.csv")
    ref_path = os.path.join(data_path, "Reference_Companies.csv")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"Scored_Leads_{timestamp}.csv"
    output_path = os.path.join(data_path, output_file)

    leads_df = pd.read_csv(leads_path)
    reference_df = load_reference_companies(ref_path)

    scored_df = score_leads(leads_df, reference_df, company_map, settings)
    scored_df.to_csv(output_path, index=False)
    print(f"\n✅ Scoring complete. Output saved to:\n  → {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    main(args.config)
