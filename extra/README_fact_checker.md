# Ingredient Fact Checker - Usage Guide

## Overview
This script combines Reddit discussions with scientific ingredient data to provide AI-powered fact-checking analysis.

## What it does:
1. **Loads your ingredient database** (`all_ingredients_merged[1].json`)
2. **Loads Reddit data** from your `llama.py` output
3. **Extracts claims** from Reddit posts and comments
4. **Uses AI to fact-check** claims against scientific data
5. **Analyzes user experiences** and sentiment
6. **Generates comprehensive report** with verified/disputed claims

## Files needed:
- `all_ingredients_merged[1].json` - Your ingredient database
- `{ingredient}_all_comments.json` - Output from llama.py
- `fact_checker.py` - This script

## How to use:

### Step 1: Run your Reddit scraper first
```bash
python llama.py
```
This creates: `salicylic acid_all_comments.json`

### Step 2: Run the fact checker
```bash
python fact_checker.py
```

### Step 3: Check your results
The script creates: `salicylic acid_fact_check_report.json`

## Configuration:
Edit these variables in `fact_checker.py`:
```python
INGREDIENT_NAME = "salicylic acid"  # Change to your ingredient
REDDIT_DATA_FILE = f"{INGREDIENT_NAME}_all_comments.json"
DATABASE_FILE = "all_ingredients_merged[1].json"
```

## Output Report Structure:
```json
{
  "ingredient": "salicylic acid",
  "fact_check_analysis": {
    "verified_claims": [...],      // Claims backed by science
    "disputed_claims": [...],      // Claims contradicting science
    "unverified_claims": [...],    // Claims lacking evidence
    "misleading_claims": [...]     // Partially true but misleading
  },
  "user_experience_analysis": {
    "positive_experiences": [...],
    "negative_experiences": [...],
    "usage_patterns": [...],
    "common_misconceptions": [...]
  },
  "reddit_data_summary": {...}
}
```

## Requirements:
- Python 3.7+
- Ollama running locally (for AI analysis)
- `requests` library: `pip install requests`

## Troubleshooting:
- Make sure Ollama is running: `ollama serve`
- Check that your ingredient exists in the database
- Ensure Reddit data file exists from llama.py output
- Check file paths and names match exactly
