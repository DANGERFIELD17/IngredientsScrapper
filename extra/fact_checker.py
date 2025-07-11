import json
import requests
import sys
from datetime import datetime

class IngredientFactChecker:
    def __init__(self, llama_url="http://localhost:11434/api/generate"):
        self.llama_url = llama_url
        self.ingredient_database = None
        self.reddit_data = None
        
    def load_ingredient_database(self, database_path="all_ingredients_merged[1].json"):
        """Load the ingredient database JSON file"""
        try:
            with open(database_path, "r", encoding="utf-8") as f:
                self.ingredient_database = json.load(f)
            print(f"[OK] Loaded ingredient database with {len(self.ingredient_database)} ingredients")
            return True
        except FileNotFoundError:
            print(f"[ERROR] Database file not found: {database_path}")
            return False
        except Exception as e:
            print(f"[ERROR] Error loading database: {e}")
            return False
    
    def find_ingredient_data(self, ingredient_name):
        """Find specific ingredient data from the database"""
        if not self.ingredient_database:
            print("[ERROR] Database not loaded")
            return None
            
        # Search for ingredient (case-insensitive)
        ingredient_lower = ingredient_name.lower()
        
        # First try exact match
        for item in self.ingredient_database:
            if "ingredient" in item:
                if ingredient_lower == item["ingredient"].lower():
                    print(f"[OK] Found exact match: {item['ingredient']}")
                    return item
        
        # Then try partial match for complex names like "SALICYLIC_ACID_or_..."
        search_terms = []
        if "_or_" in ingredient_lower:
            search_terms = ingredient_lower.split("_or_")
        else:
            search_terms = [ingredient_lower]
        
        # Clean up search terms
        search_terms = [term.replace("_", " ").strip() for term in search_terms]
        
        print(f"[SEARCH] Looking for ingredients matching: {search_terms}")
        
        # Try to find any of the search terms
        for item in self.ingredient_database:
            if "ingredient" in item:
                item_name = item["ingredient"].lower()
                for term in search_terms:
                    if term in item_name or item_name in term:
                        print(f"[OK] Found partial match: {item['ingredient']} (matches '{term}')")
                        return item
        
        print(f"[WARNING] Ingredient '{ingredient_name}' not found in database")
        print(f"[INFO] Searched for: {search_terms}")
        return None
    
    def load_reddit_data(self, reddit_file_path):
        """Load Reddit data from the llama.py output"""
        try:
            with open(reddit_file_path, "r", encoding="utf-8") as f:
                self.reddit_data = json.load(f)
            print(f"[OK] Loaded Reddit data with {len(self.reddit_data)} posts")
            return True
        except FileNotFoundError:
            print(f"[ERROR] Reddit data file not found: {reddit_file_path}")
            return False
        except Exception as e:
            print(f"[ERROR] Error loading Reddit data: {e}")
            return False
    
    def extract_reddit_claims(self):
        """Extract claims and statements from Reddit data"""
        if not self.reddit_data:
            return []
            
        claims = []
        
        for post in self.reddit_data:
            # Extract claims from post title and body
            if post.get("title"):
                claims.append({
                    "source": "post_title",
                    "text": post["title"],
                    "score": post.get("score", 0),
                    "subreddit": post.get("subreddit", "unknown")
                })
            
            if post.get("body"):
                claims.append({
                    "source": "post_body",
                    "text": post["body"],
                    "score": post.get("score", 0),
                    "subreddit": post.get("subreddit", "unknown")
                })
            
            # Extract claims from comments
            for comment in post.get("comments", []):
                if comment.get("body") and len(comment["body"]) > 20:  # Filter out very short comments
                    claims.append({
                        "source": "comment",
                        "text": comment["body"],
                        "score": comment.get("score", 0),
                        "subreddit": post.get("subreddit", "unknown"),
                        "author": comment.get("author", "unknown")
                    })
        
        return claims
    
    def call_llama(self, prompt, model="gemma3:latest"):
        """Make API call to Llama for analysis"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more factual responses
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(self.llama_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error calling Llama API: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return None
    
    def fact_check_claims(self, ingredient_name, ingredient_data, reddit_claims):
        """Use AI to fact-check Reddit claims against ingredient database"""
        
        # Prepare ingredient facts for AI analysis
        ingredient_facts = {
            "name": ingredient_data.get("ingredient", "Unknown"),
            "search_results": ingredient_data.get("search_results", []),
            "detailed_info": ingredient_data.get("detailed_info", []),
            "has_scientific_data": len(ingredient_data.get("detailed_info", [])) > 0
        }
        
        # Prepare Reddit claims summary
        high_score_claims = [claim for claim in reddit_claims if claim.get("score", 0) > 5]
        claims_text = "\n".join([f"- {claim['text'][:200]}..." for claim in high_score_claims[:10]])
        
        fact_check_prompt = f"""
You are an expert fact-checker analyzing claims about the ingredient "{ingredient_name}".

SCIENTIFIC DATA AVAILABLE:
{json.dumps(ingredient_facts, indent=2)}

REDDIT CLAIMS TO FACT-CHECK:
{claims_text}

Please analyze each Reddit claim and categorize them as:

1. VERIFIED - Claims that align with scientific data
2. DISPUTED - Claims that contradict scientific data  
3. UNVERIFIED - Claims that lack scientific backing but aren't necessarily false
4. MISLEADING - Claims that are partially true but could mislead users

For each category, provide:
- The specific claim
- Your reasoning
- Confidence level (High/Medium/Low)
- Potential risks if the claim is false

Format your response as JSON:
{{
    "verified_claims": [
        {{"claim": "...", "reasoning": "...", "confidence": "High"}}
    ],
    "disputed_claims": [
        {{"claim": "...", "reasoning": "...", "confidence": "High", "risk_level": "High/Medium/Low"}}
    ],
    "unverified_claims": [
        {{"claim": "...", "reasoning": "...", "confidence": "Medium"}}
    ],
    "misleading_claims": [
        {{"claim": "...", "reasoning": "...", "confidence": "High", "risk_level": "High/Medium/Low"}}
    ],
    "overall_assessment": "Summary of the fact-checking analysis"
}}
"""
        
        print("[AI] Running AI fact-checking analysis...")
        response = self.call_llama(fact_check_prompt)
        
        if response:
            try:
                # Try to parse JSON response
                return json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {"raw_response": response}
        else:
            return {"error": "Failed to get AI response"}
    
    def analyze_user_experiences(self, reddit_claims):
        """Analyze user experiences and sentiment"""
        
        experience_claims = [claim for claim in reddit_claims if 
                           any(keyword in claim['text'].lower() for keyword in 
                               ['worked', 'helped', 'side effect', 'reaction', 'experience', 'result'])]
        
        experiences_text = "\n".join([f"- {claim['text'][:300]}..." for claim in experience_claims[:15]])
        
        experience_prompt = f"""
Analyze these user experiences and extract insights:

USER EXPERIENCES:
{experiences_text}

Please provide a structured analysis:

{{
    "positive_experiences": [
        {{"experience": "...", "frequency": "mentioned X times", "credibility": "High/Medium/Low"}}
    ],
    "negative_experiences": [
        {{"experience": "...", "frequency": "mentioned X times", "severity": "High/Medium/Low"}}
    ],
    "usage_patterns": [
        {{"pattern": "...", "effectiveness": "..."}}
    ],
    "common_misconceptions": [
        {{"misconception": "...", "correction": "..."}}
    ],
    "sentiment_summary": "Overall sentiment analysis"
}}
"""
        
        print("[AI] Analyzing user experiences...")
        response = self.call_llama(experience_prompt)
        
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"raw_response": response}
        else:
            return {"error": "Failed to get AI response"}
    
    def generate_comprehensive_report(self, ingredient_name):
        """Generate a comprehensive fact-checked report"""
        
        if not self.ingredient_database or not self.reddit_data:
            print("[ERROR] Missing required data. Load both ingredient database and Reddit data first.")
            return None
        
        # Find ingredient data
        ingredient_data = self.find_ingredient_data(ingredient_name)
        if not ingredient_data:
            return None
        
        # Extract Reddit claims
        reddit_claims = self.extract_reddit_claims()
        
        print(f"[STATS] Extracted {len(reddit_claims)} claims from Reddit data")
        
        # Perform fact-checking
        fact_check_results = self.fact_check_claims(ingredient_name, ingredient_data, reddit_claims)
        
        # Analyze user experiences
        experience_analysis = self.analyze_user_experiences(reddit_claims)
        
        # Compile comprehensive report
        report = {
            "ingredient": ingredient_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "data_sources": {
                "reddit_posts": len(self.reddit_data),
                "total_claims_analyzed": len(reddit_claims),
                "scientific_data_available": len(ingredient_data.get("detailed_info", [])) > 0
            },
            "ingredient_database_info": {
                "name": ingredient_data.get("ingredient"),
                "has_search_results": len(ingredient_data.get("search_results", [])) > 0,
                "has_detailed_info": len(ingredient_data.get("detailed_info", [])) > 0,
                "database_status": "error" if "error" in ingredient_data else "success"
            },
            "fact_check_analysis": fact_check_results,
            "user_experience_analysis": experience_analysis,
            "reddit_data_summary": {
                "subreddits_covered": list(set([post.get("subreddit") for post in self.reddit_data])),
                "total_comments": sum([len(post.get("comments", [])) for post in self.reddit_data]),
                "avg_post_score": sum([post.get("score", 0) for post in self.reddit_data]) / len(self.reddit_data) if self.reddit_data else 0
            }
        }
        
        return report
    
    def save_report(self, report, filename):
        """Save the fact-checking report to a JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"[OK] Report saved to {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Error saving report: {e}")
            return False

def find_reddit_data_file():
    """Auto-detect Reddit data files from llama.py output"""
    import glob
    import os
    
    # Look for files matching the pattern from llama.py
    patterns = [
        "*_all_comments.json",
        "*_enhanced_analysis.json"
    ]
    
    found_files = []
    for pattern in patterns:
        found_files.extend(glob.glob(pattern))
    
    # Filter out enhanced_analysis files and prefer _all_comments.json
    reddit_files = [f for f in found_files if "_all_comments.json" in f]
    
    if reddit_files:
        # Use the most recently modified file
        latest_file = max(reddit_files, key=os.path.getmtime)
        # Extract ingredient name from filename
        ingredient = latest_file.replace("_all_comments.json", "").replace(" ", "_")
        return latest_file, ingredient
    
    return None, None

def main():
    print("[START] Ingredient Fact Checker - AI-Powered Analysis")
    print("=" * 50)
    
    # Auto-detect Reddit data file
    print("[SEARCH] Auto-detecting Reddit data files...")
    reddit_file, detected_ingredient = find_reddit_data_file()
    
    if not reddit_file:
        print("[ERROR] No Reddit data files found!")
        print("[INFO] Please run llama.py first to generate Reddit data")
        print("   Expected file pattern: {ingredient}_all_comments.json")
        sys.exit(1)
    
    print(f"[OK] Found Reddit data: {reddit_file}")
    print(f"[OK] Detected ingredient: {detected_ingredient}")
    
    # Configuration
    INGREDIENT_NAME = detected_ingredient
    REDDIT_DATA_FILE = reddit_file
    DATABASE_FILE = "all_ingredients_merged[1].json"
    OUTPUT_FILE = f"{INGREDIENT_NAME}_fact_check_report.json"
    
    # Initialize fact checker
    fact_checker = IngredientFactChecker()
    
    # Load data
    print("[LOAD] Loading data sources...")
    
    if not fact_checker.load_ingredient_database(DATABASE_FILE):
        print("[ERROR] Failed to load ingredient database. Exiting.")
        sys.exit(1)
    
    if not fact_checker.load_reddit_data(REDDIT_DATA_FILE):
        print("[ERROR] Failed to load Reddit data. Make sure you've run llama.py first.")
        sys.exit(1)
    
    # Generate comprehensive report
    print(f"\n[AI] Generating fact-check report for '{INGREDIENT_NAME}'...")
    report = fact_checker.generate_comprehensive_report(INGREDIENT_NAME)
    
    if report:
        # Save report
        fact_checker.save_report(report, OUTPUT_FILE)
        
        # Print summary
        print(f"\n[REPORT] FACT-CHECK REPORT SUMMARY")
        print("=" * 40)
        print(f"Ingredient: {report['ingredient']}")
        print(f"Reddit Posts Analyzed: {report['data_sources']['reddit_posts']}")
        print(f"Total Claims Extracted: {report['data_sources']['total_claims_analyzed']}")
        print(f"Scientific Data Available: {report['data_sources']['scientific_data_available']}")
        
        if 'fact_check_analysis' in report and 'verified_claims' in report['fact_check_analysis']:
            verified = len(report['fact_check_analysis'].get('verified_claims', []))
            disputed = len(report['fact_check_analysis'].get('disputed_claims', []))
            print(f"[OK] Verified Claims: {verified}")
            print(f"[ERROR] Disputed Claims: {disputed}")
        
        print(f"\n[SAVE] Full report saved to: {OUTPUT_FILE}")
        
    else:
        print("[ERROR] Failed to generate report")

if __name__ == "__main__":
    main()
