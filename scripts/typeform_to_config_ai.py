from openai import OpenAI
import os
import json
import pandas as pd

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load approved industries from your master mapping file
def get_approved_industries(path="configs/shared/industry_sector_map.csv"):
    df = pd.read_csv(path)
    return sorted(df["Industry"].dropna().unique())

# Build the OpenAI prompt from a Typeform row + approved list
def build_prompt_from_typeform(row, approved_list):
    industry_list_str = "\n- " + "\n- ".join(approved_list)

    prompt = f"""
You are helping configure a lead scoring engine. Based on the following client onboarding responses, generate a JSON config containing:

- priority_industries: select 3–5 industry names that match the client's ICP from the approved list provided.
- sector_keywords: a dictionary where each key is one of the selected industries and the value is a list of 3–6 related keyword phrases or common search terms.
- blacklist_terms: terms that should be excluded from matching (e.g. "2D only", "internship").
- job_title_categories: groupings such as "Major Studios", "Outsourcing Agencies", etc., each with a list of 5–8 job title fragments or LinkedIn titles that might be found at companies of that type.
- role_seniority: split common titles into senior, mid, and junior. Ensure that C-level (CEO, CTO, CMO, etc.), VP, and Director titles are always considered senior.

### Client Input:
Target Market:
{row.get("Target Market", "")}

Dream Clients:
{row.get("Dream Clients", "")}

The Buying Committee:
{row.get("The buying committee", "")}

Signals of Fit (job description phrases):
{row.get("What phrases would you expect to see in job descriptions or LinkedIn profiles that indicate someone is a fit?", "")}

Please ensure all 'priority_industries' values are selected from the following approved list:

{industry_list_str}

Respond only in valid JSON format, exactly like this:

{{
  "priority_industries": ["..."],
  "sector_keywords": {{
    "Industry Name": ["keyword1", "keyword2"]
  }},
  "blacklist_terms": ["..."],
  "job_title_categories": {{
    "Category Label": ["job title 1", "job title 2"]
  }},
  "role_seniority": {{
    "senior": ["..."],
    "mid": ["..."],
    "junior": ["..."]
  }}
}}
"""
    return prompt

# Call OpenAI with the generated prompt
def fetch_config_from_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant generating structured JSON config data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    reply = response.choices[0].message.content.strip()
    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        print("⚠️ Failed to parse JSON from OpenAI response.")
        print(reply)
        return {}

# Main execution
if __name__ == "__main__":
    # Load your Typeform Excel file
    df = pd.read_excel("K3C Client Onboarding TypeForm.xlsx")
    row = df.iloc[0]  # First client response

    # Load approved industries and build prompt
    approved = get_approved_industries()
    prompt = build_prompt_from_typeform(row, approved)

    # Get AI-generated config
    config_suggestions = fetch_config_from_openai(prompt)

    # Filter the priority_industries to enforce valid values
    filtered = [i for i in config_suggestions.get("priority_industries", []) if i in approved]
    config_suggestions["priority_industries"] = filtered

    # Save for inspection
    with open("openai_config_suggestions.json", "w") as f:
        json.dump(config_suggestions, f, indent=2)

    print("✅ Suggestions saved to openai_config_suggestions.json")
