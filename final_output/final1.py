import json
import os
from openai import OpenAI
from pathlib import Path
import time


# Set your OpenAI API key here or set it as an environment variable
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

def get_matching_files(inci_folder, reddit_folder):
    """
    Find matching pairs of INCI JSON files and Reddit TXT files.
    
    Returns:
        list: List of tuples (ingredient_name, json_path, txt_path)
    """
    inci_files = list(Path(inci_folder).glob("*.json"))
    reddit_files = list(Path(reddit_folder).glob("*.txt"))
    
    matches = []
    
    for inci_file in inci_files:
        ingredient_base = inci_file.stem  # filename without extension
        
        # Look for matching reddit file
        for reddit_file in reddit_files:
            reddit_base = reddit_file.stem
            # Check if the ingredient name is in the reddit filename
            if ingredient_base.replace(" ", "_").lower() in reddit_base.lower():
                matches.append((ingredient_base, str(inci_file), str(reddit_file)))
                break
    
    return matches

def enhance_report_with_chatgpt(basic_report, ingredient_name):
    """
    Use ChatGPT API to enhance the basic report with additional insights.
    
    Parameters:
        basic_report (str): The basic report generated from JSON and Reddit data
        ingredient_name (str): Name of the ingredient
        
    Returns:
        str: Enhanced report with ChatGPT insights
    """
    try:
        prompt = f"""You are a cosmetic ingredient expert. I'll provide you with a basic report about the ingredient \"{ingredient_name}\" that includes technical data and Reddit user experiences. 

Please enhance this report by:
1. Adding scientific context about the ingredient's mechanisms of action
2. Providing professional interpretation of the user experiences
3. Adding safety considerations and recommendations
4. Summarizing the overall efficacy based on available data
5. Adding any relevant regulatory or industry insights

Here's the basic report to enhance:

{basic_report}

Please provide a comprehensive, professional enhancement that maintains the original structure but adds valuable scientific and professional insights."""


        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cosmetic chemist and ingredient expert with deep knowledge of skincare and haircare ingredients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        enhanced_content = response.choices[0].message.content

        # Combine original report with ChatGPT enhancement
        enhanced_report = f"""{basic_report}

🤖 AI EXPERT ANALYSIS & ENHANCEMENT
=====================================
{enhanced_content}

---
Report generated with AI assistance on {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

        return enhanced_report

    except Exception as e:
        print(f"Error with ChatGPT API: {e}")
        print("Returning basic report without AI enhancement.")
        return basic_report

def generate_ingredient_report(json_file_path, reddit_txt_path, output_path, use_chatgpt=True):
    """
    Generate a comprehensive report combining structured ingredient data and Reddit sentiment analysis.
    
    Parameters:
        json_file_path (str): Path to the ingredient JSON file
        reddit_txt_path (str): Path to the Reddit analysis .txt file
        output_path (str): Path where the final .txt report will be saved
        use_chatgpt (bool): Whether to enhance the report with ChatGPT API
    """
    
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ingredient_name = data['ingredient']
    main_entry = next((d for d in data['detailed_info'] if d['inci_name'].upper() == ingredient_name.upper()), None)
    
    if not main_entry:
        main_entry = data['detailed_info'][0] if data['detailed_info'] else {}

    # Extract structured fields
    inci_name = main_entry.get("inci_name", "N/A")
    cas = main_entry.get("cas", "N/A")
    functions = [f["name"] for f in main_entry.get("functions", [])]
    description = main_entry.get("description", "No description available")
    usage_data = main_entry.get("category_percentage", [])
    origin = [o["name"] for o in main_entry.get("origin", [])]
    dangers = main_entry.get("dangers", [])

    # Load Reddit analysis text
    with open(reddit_txt_path, 'r', encoding='utf-8') as f:
        reddit_content = f.read()

    # Compose the basic report
    basic_report = f"""COMPREHENSIVE {ingredient_name.upper()} REPORT
{'=' * (len(ingredient_name) + 25)}

🧪 INGREDIENT OVERVIEW
-----------------------
- INCI Name: {inci_name}
- CAS Number: {cas}
- Function(s): {", ".join(functions) if functions else "N/A"}
- Origin: {", ".join(origin) if origin else "N/A"}
- Description: {description}

⚠️ SAFETY INFORMATION
----------------------"""
    
    if dangers:
        for danger in dangers:
            basic_report += f"\n- Safety Score: {danger.get('value', 'N/A')}\n- Assessment: {danger.get('label', 'N/A')}"
    else:
        basic_report += "\n- No specific safety data available"

    basic_report += f"""

📊 PRODUCT USAGE DATA
-----------------------"""
    
    if usage_data:
        for cat in usage_data:
            basic_report += f"\n- {cat['category_name']}: {cat['percentage']}% (n={cat['count']})"
    else:
        basic_report += "\n- No usage data available"

    basic_report += f"""

📈 REDDIT COMMUNITY ANALYSIS
-----------------------------
{reddit_content}"""

    # Always generate the basic report only (no GPT enhancement)
    final_report = basic_report

    # Save the report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_report)

    print(f"✅ Report successfully written to: {output_path}")

def process_all_ingredients(inci_folder="inci", reddit_folder="reddit", output_folder="reports", use_chatgpt=True):
    """
    Process all matching ingredient files and generate reports for each.
    
    Parameters:
        inci_folder (str): Path to folder containing INCI JSON files
        reddit_folder (str): Path to folder containing Reddit analysis TXT files
        output_folder (str): Path to folder where reports will be saved
        use_chatgpt (bool): Whether to enhance reports with ChatGPT API
    """
    
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(exist_ok=True)
    
    # Find matching files
    matches = get_matching_files(inci_folder, reddit_folder)
    
    if not matches:
        print("❌ No matching files found between INCI and Reddit folders.")
        return
    
    print(f"📁 Found {len(matches)} matching ingredient pairs:")
    for ingredient_name, _, _ in matches:
        print(f"  - {ingredient_name}")
    
    print(f"\n🚀 Starting report generation...")
    
    # Process each match
    for i, (ingredient_name, json_path, reddit_path) in enumerate(matches, 1):
        print(f"\n[{i}/{len(matches)}] Processing: {ingredient_name}")
        
        # Create output filename
        safe_name = ingredient_name.replace(" ", "_").replace("/", "_")
        output_path = Path(output_folder) / f"{safe_name}_comprehensive_report.txt"
        
        try:
            generate_ingredient_report(json_path, reddit_path, str(output_path), use_chatgpt)
        except Exception as e:
            print(f"❌ Error processing {ingredient_name}: {e}")
            continue
    
    print(f"\n🎉 All reports generated in '{output_folder}' folder!")

if __name__ == "__main__":
    # Example usage
    print("🧪 INGREDIENT REPORT GENERATOR")
    print("=" * 40)
    
    # Option 1: Process all ingredients automatically
    print("\n1. Processing all ingredients...")
    process_all_ingredients(use_chatgpt=True)
    
    # Option 2: Process a single ingredient (uncomment to use)
    # print("\n2. Processing single ingredient...")
    # generate_ingredient_report(
    #     json_file_path="inci/Acacia Concinna Fruit Extract.json",
    #     reddit_txt_path="reddit/Acacia_Concinna_Fruit_Extract_or_Shikakai_fruit_extract_all_comments.txt",
    #     output_path="reports/Acacia_Concinna_single_report.txt",
    #     use_chatgpt=True
    # )