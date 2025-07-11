import praw
import json
import sys
import time
from datetime import datetime, timezone, timedelta

# Step 1: Authenticate
try:
    reddit = praw.Reddit(
        client_id="T_5eO0s-SeLJnEnsxrbx2Q",
        client_secret="9y3zJDkBTbnYERNI8a4cfUNvfTc8Ww",
        user_agent="ingredient scraper by /u/Traditional_Cup7724"
    )
    
    # Test the authentication by trying to access the API
    print("[AUTH] Testing Reddit API authentication...")
    reddit.user.me()  # This will fail if credentials are wrong
    print("[OK] Authentication successful!")
    
except Exception as e:
    print(f"[ERROR] Authentication failed: {e}")
    print("Please check your Reddit API credentials:")
    print("1. Make sure your client_id and client_secret are correct")
    print("2. Ensure there are no extra spaces or characters")
    print("3. Verify your Reddit app is set to 'script' type")
    sys.exit(1)

# Step 2: Your configuration
OR_IDENTIFIERS = ["biotin"]  # Any of these terms will match (OR logic)
AND_IDENTIFIERS = ["hair"]  # All of these terms must be present (AND logic)
MONTHS_BACK = 1  # How many months back to search for limited mode
MAX_COMMENTS = 30 # Number of top comments to collect per post
UNLIMITED_MODE = True  # Set to True to remove timeline filter and get unlimited posts
MAX_POSTS = 139  # Maximum number of posts to process (set as needed)

# Build the search query string
search_terms = []
if OR_IDENTIFIERS:
    or_query = " OR ".join([f'title:"{term}"' for term in OR_IDENTIFIERS])
    search_terms.append(f'({or_query})')
if AND_IDENTIFIERS:
    and_query = " AND ".join([f'title:"{term}"' for term in AND_IDENTIFIERS])
    search_terms.append(and_query)
SEARCH_QUERY = " AND ".join(search_terms) if search_terms else ""

# Build a string for filenames and printouts based on identifiers
if OR_IDENTIFIERS:
    identifier_str = "_or_".join([term.replace(" ", "_") for term in OR_IDENTIFIERS])
elif AND_IDENTIFIERS:
    identifier_str = "_and_".join([term.replace(" ", "_") for term in AND_IDENTIFIERS])
else:
    identifier_str = "ingredient"

# ===== COMMENT COLLECTION OPTIONS =====
INCLUDE_NESTED_COMMENTS = True  # Set to False for faster processing (top-level only)
# True = Collects ALL comments including replies (slower but more comprehensive)
# False = Only top-level comments (faster but may miss valuable nested discussions)

# ===== SUBREDDIT TARGETING OPTIONS =====
# SEARCH_MODE options:
# "all"      - Search across all of Reddit (original behavior)
# "specific" - Search only in the subreddits listed in TARGET_SUBREDDITS
# "mixed"    - Combination: half from all Reddit, half from specific subreddits

SEARCH_MODE = "all"  # Change to "specific" or "mixed" for targeted searching

# High-quality subreddits for ingredient research
# Add or remove subreddits based on your ingredient type:
# - Skincare: SkincareAddiction, 30PlusSkinCare, AsianBeauty, tretinoin
# - Supplements: supplements, Nootropics, biohackers, ScientificNutrition
# - Fitness: Fitness, moreplatesmoredates, nattyorjuice
TARGET_SUBREDDITS = [
    "SkincareAddiction", "30PlusSkinCare", "AsianBeauty", "tretinoin",
    "supplements", "Nootropics", "biohackers", "ScientificNutrition",
    "nutrition", "Fitness", "moreplatesmoredates"
]

# Posts per subreddit (only used when SEARCH_MODE is "specific" or "mixed")
POSTS_PER_SUBREDDIT = 2

results = []

# Calculate cutoff date for unlimited search
cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * MONTHS_BACK)

def fetch_all_posts_unlimited(search_query, cutoff_date=None):
    """Fetch all posts with unlimited pagination, optionally filtering by date"""
    all_posts = []
    batch_num = 0
    total_fetched = 0
    print(f"[START] Starting unlimited pagination{' (no timeline filter)' if UNLIMITED_MODE else f' for last {MONTHS_BACK} months'}...")
    while True:
        batch_num += 1
        print(f"[BATCH] Batch {batch_num}...", end="", flush=True)
        try:
            if batch_num == 1:
                batch_posts = list(reddit.subreddit("all").search(
                    search_query,
                    sort="top",
                    time_filter="all" if UNLIMITED_MODE else "year",
                    limit=100
                ))
            else:
                if all_posts:
                    last_post_id = all_posts[-1].fullname
                    batch_posts = list(reddit.subreddit("all").search(
                        search_query,
                        sort="top",
                        time_filter="all" if UNLIMITED_MODE else "year",
                        limit=100,
                        params={'after': last_post_id}
                    ))
                else:
                    break
            # Filter by date and content (AND/OR in title or body)
            filtered_posts = []
            for post in batch_posts:
                post_date = datetime.fromtimestamp(post.created_utc, timezone.utc)
                if UNLIMITED_MODE or (cutoff_date and post_date >= cutoff_date):
                    if post_matches(post, OR_IDENTIFIERS, AND_IDENTIFIERS):
                        filtered_posts.append(post)
            all_posts.extend(batch_posts)
            total_fetched += len(batch_posts)
            print(f" [OK] {len(batch_posts)} posts, {len(filtered_posts)} {'(unlimited)' if UNLIMITED_MODE else f'from last {MONTHS_BACK} months'} (Total: {total_fetched})")
            if len(batch_posts) < 100:
                print(f"[END] Reached end after {batch_num} batches")
                break
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f" [ERROR] Error: {e}")
            break
    # Final filtering by date and content (AND/OR in title or body)
    final_posts = []
    for post in all_posts:
        post_date = datetime.fromtimestamp(post.created_utc, timezone.utc)
        if UNLIMITED_MODE or (cutoff_date and post_date >= cutoff_date):
            if post_matches(post, OR_IDENTIFIERS, AND_IDENTIFIERS):
                final_posts.append(post)
    return final_posts

# Step 3: Search across Reddit for posts
print(f"[SEARCH] Searching for posts about '{SEARCH_QUERY}'...")
print(f"Search mode: {SEARCH_MODE}")
print(f"Collecting top {MAX_COMMENTS} most upvoted comments per post")

def search_subreddit(subreddit_name, search_term, limit):
    """Helper function to search a specific subreddit"""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = list(subreddit.search(search_term, sort="top", time_filter="all", limit=limit))
        return posts
    except Exception as e:
        print(f"  [WARNING] Error searching r/{subreddit_name}: {e}")
        return []

def extract_all_comments(post, max_comments=10, include_nested=True):
    """
    Extract comments from a post - can include nested replies or just top-level
    Returns the top comments by score, regardless of nesting level
    """
    try:
        if include_nested:
            # Load all comment trees (this can take time for large posts)
            post.comments.replace_more(limit=None)  # Load ALL comments
        else:
            # Only load top-level comments (faster)
            post.comments.replace_more(limit=0)
        
        all_comments = []
        
        if include_nested:
            def collect_comments(comment_list):
                """Recursively collect all comments from the tree"""
                for comment in comment_list:
                    if hasattr(comment, 'author') and comment.author:  # Valid comment with author
                        all_comments.append({
                            "author": comment.author.name,
                            "body": comment.body.strip(),
                            "score": comment.score,
                            "is_top_level": comment.parent_id.startswith('t3_')  # t3_ means parent is post
                        })
                    
                    # Recursively get replies to this comment
                    if hasattr(comment, 'replies') and comment.replies:
                        collect_comments(comment.replies)
            
            # Start collecting from top-level comments
            collect_comments(post.comments)
        else:
            # Only collect top-level comments (original behavior)
            for comment in post.comments:
                if hasattr(comment, 'author') and comment.author:
                    all_comments.append({
                        "author": comment.author.name,
                        "body": comment.body.strip(),
                        "score": comment.score,
                        "is_top_level": True
                    })
        
        # Sort all comments by score (highest first) and take top N
        all_comments.sort(key=lambda x: x["score"], reverse=True)
        return all_comments[:max_comments]
        
    except Exception as e:
        print(f"Error extracting comments: {e}")
        return []

def post_matches(post, or_identifiers, and_identifiers):
    title_lower = post.title.lower()
    body_lower = post.selftext.lower() if post.selftext else ""
    or_match = not or_identifiers or any(term.lower() in title_lower or term.lower() in body_lower for term in or_identifiers)
    and_match = all(term.lower() in title_lower or term.lower() in body_lower for term in and_identifiers)
    return or_match and and_match

try:
    all_posts = []
    
    if SEARCH_MODE == "all":
        # Unlimited search across all of Reddit for the last N months or unlimited
        print(f"Searching all of Reddit for all posts {'(unlimited)' if UNLIMITED_MODE else f'from the last {MONTHS_BACK} months'}...")
        all_posts = fetch_all_posts_unlimited(SEARCH_QUERY, cutoff_date if not UNLIMITED_MODE else None)
        
    elif SEARCH_MODE == "specific":
        print(f"Searching in {len(TARGET_SUBREDDITS)} specific subreddits...")
        for subreddit_name in TARGET_SUBREDDITS:
            print(f"  [TARGET] Searching r/{subreddit_name}...", end="")
            posts = search_subreddit(subreddit_name, SEARCH_QUERY, 1000)
            all_posts.extend(posts)
            print(f" found {len(posts)} posts")
    elif SEARCH_MODE == "mixed":
        print(f"Mixed search: unlimited from all Reddit + targeted subreddits...")
        all_reddit_posts = fetch_all_posts_unlimited(SEARCH_QUERY, cutoff_date)
        all_posts.extend(all_reddit_posts)
        print(f"  [STATS] Found {len(all_reddit_posts)} posts from general search")
        for subreddit_name in TARGET_SUBREDDITS:
            posts = search_subreddit(subreddit_name, SEARCH_QUERY, 100)
            all_posts.extend(posts)
    
    # Remove duplicates and sort by score
    unique_posts = {}
    for post in all_posts:
        if post.id not in unique_posts:
            unique_posts[post.id] = post
    
    sorted_posts = sorted(unique_posts.values(), key=lambda x: x.score, reverse=True)
    # Limit to MAX_POSTS
    sorted_posts = sorted_posts[:MAX_POSTS]
    print(f"[STATS] Total unique posts found: {len(sorted_posts)} (limited to MAX_POSTS={MAX_POSTS})")
    
    # Process posts
    post_count = 0
    for post in sorted_posts:
        post_count += 1
        subreddit_display = f"r/{post.subreddit.display_name}"
        print(f"  [POST] Processing post {post_count}/{len(sorted_posts)} from {subreddit_display}: {post.title[:40]}...", end="", flush=True)
        
        try:
            # Use the new function to get comments (nested or top-level based on config)
            collection_type = "all comments" if INCLUDE_NESTED_COMMENTS else "top-level only"
            print(f" (extracting {collection_type}...)", end="", flush=True)
            all_comments = extract_all_comments(post, MAX_COMMENTS, INCLUDE_NESTED_COMMENTS)
            
            # Count top-level vs nested comments for information
            if INCLUDE_NESTED_COMMENTS:
                top_level_count = sum(1 for c in all_comments if c.get('is_top_level', False))
                nested_count = len(all_comments) - top_level_count
            else:
                top_level_count = len(all_comments)
                nested_count = 0

            # Add full post data
            results.append({
                "subreddit": post.subreddit.display_name,
                "post_id": post.id,
                "title": post.title,
                "url": f"https://www.reddit.com{post.permalink}",
                "score": post.score,
                "num_comments": post.num_comments,
                "created": datetime.fromtimestamp(post.created_utc, timezone.utc).isoformat(),
                "body": post.selftext,
                "flair_text": getattr(post, "link_flair_text", None),
                "flair_template_id": getattr(post, "link_flair_template_id", None),
                "comments": all_comments,
                "comment_breakdown": {
                    "total_collected": len(all_comments),
                    "top_level": top_level_count,
                    "nested_replies": nested_count
                }
            })
            
            print(f" [OK] ({len(all_comments)} comments: {top_level_count} top-level, {nested_count} replies)")
            
        except Exception as e:
            print(f" [ERROR] Error: {e}")
            continue
                
    print(f"[OK] Completed search - found {post_count} posts")
    if SEARCH_MODE == "specific":
        subreddit_breakdown = {}
        for post in results:
            sub = post['subreddit']
            subreddit_breakdown[sub] = subreddit_breakdown.get(sub, 0) + 1
        print(f"[STATS] Posts by subreddit: {dict(subreddit_breakdown)}")
    
    # Summary
    total_comments = sum(len(post['comments']) for post in results)
    print(f" Total comments collected: {total_comments}")
        
except Exception as e:
    print(f"[ERROR] Error searching Reddit: {e}")
    sys.exit(1)

# Step 4: Save raw data as JSON
with open(f"{identifier_str}_all_comments.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"[OK] Done! Saved {len(results)} posts to {identifier_str}_all_comments.json")

# # Step 5: Enhanced AI Analysis
# print("\n[AI] Starting Enhanced AI Analysis...")

# # Llama Configuration
# LLAMA_URL = "http://localhost:11434/api/generate"  # Ollama's /api/generate endpoint

# if len(results) > 0:
#     print("[AI] Analyzing Reddit discussions with Enhanced AI Analysis (Llama)...")
#     # Try enhanced analysis first (it's our best option)
#     try:
#         from enhanced_analysis import enhanced_analysis_structure
#         analysis = enhanced_analysis_structure(results, identifier_str, LLAMA_URL)
#         print("[OK] Enhanced analysis completed successfully!")
#         # Save enhanced analysis results
#         output_filename = f"{identifier_str}_enhanced_analysis.json"
#         with open(output_filename, "w", encoding="utf-8") as f:
#             json.dump(analysis, f, ensure_ascii=False, indent=2)
#         print(f"[OK] Enhanced Analysis complete! Saved to {output_filename}")
#         print("\n[STATS] Enhanced Analysis Summary:")
#         print(f"Analysis Sections: {len(analysis.keys())}")
#         if 'usage_patterns' in analysis:
#             usage = analysis['usage_patterns']
#             print(f"Dosage Recommendations: {len(usage.get('dosage_recommendations', []))}")
#             print(f"Timing Preferences: {len(usage.get('timing_preferences', []))}")
#         if 'brand_intelligence' in analysis:
#             brands = analysis['brand_intelligence']
#             print(f"Top Brands Analyzed: {len(brands.get('top_brands', []))}")
#         if 'effectiveness_analysis' in analysis:
#             effectiveness = analysis['effectiveness_analysis']
#             print(f"Benefits Identified: {len(effectiveness.get('reported_benefits', []))}")
#             print(f"Side Effects Found: {len(effectiveness.get('reported_side_effects', []))}")
#     except Exception as e:
#         print(f"[WARNING] Enhanced analysis failed: {e}")
#         print("[INFO] Make sure 'enhanced_analysis.py' is in the same directory")
# else:
#     print("[ERROR] No data to analyze")

# print("\n[COMPLETE] Analysis pipeline complete!")
# print(f"Raw data: {identifier_str}_all_comments.json")
# print(f"Analysis: {identifier_str}_enhanced_analysis.json")
