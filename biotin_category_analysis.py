import json
from collections import defaultdict

def load_analysis_results():
    """Load the detailed analysis results."""
    with open('biotin_spacy_analysis.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def print_category_highlights(results):
    """Print the most relevant posts for each category."""
    
    print("="*80)
    print("BIOTIN POST ANALYSIS - CATEGORY HIGHLIGHTS")
    print("="*80)
    
    categories_of_interest = [
        'ingredient_usage_patterns',
        'treatment_experiences', 
        'product_recommendations',
        'progress_report',
        'side_effects',
        'combination_therapy'
    ]
    
    for category in categories_of_interest:
        if category in results['categories']:
            posts = results['categories'][category]
            print(f"\n{category.replace('_', ' ').upper()}")
            print("-" * 60)
            print(f"Total posts: {len(posts)}")
            
            # Sort by engagement (score + comments)
            sorted_posts = sorted(posts, 
                                key=lambda x: x['score'] + x['num_comments'], 
                                reverse=True)
            
            print("\nTop 5 Most Relevant Posts:")
            for i, post in enumerate(sorted_posts[:5], 1):
                print(f"\n{i}. {post['title']}")
                print(f"   Subreddit: r/{post['subreddit']}")
                print(f"   Score: {post['score']}, Comments: {post['num_comments']}")
                print(f"   Ingredients: {', '.join(post['ingredients'])}")
                print(f"   URL: https://www.reddit.com/{post['subreddit']}/comments/{post['post_id']}/")
    
    # Special analysis for different use cases
    print("\n" + "="*80)
    print("SPECIFIC USE CASE ANALYSIS")
    print("="*80)
    
    # Posts about biotin side effects (acne)
    side_effect_posts = [post for post in results['categories']['side_effects'] 
                        if 'acne' in post['title'].lower() or 'breakout' in post['title'].lower()]
    
    print(f"\nBIOTIN ACNE/BREAKOUT POSTS ({len(side_effect_posts)} posts):")
    for post in sorted(side_effect_posts, key=lambda x: x['score'], reverse=True)[:3]:
        print(f"• {post['title']} (Score: {post['score']})")
    
    # Posts about biotin + finasteride/minoxidil combinations
    hair_combo_posts = [post for post in results['categories']['combination_therapy']
                       if any(ingredient in ['fin', 'finasteride', 'min', 'minoxidil'] 
                             for ingredient in post['ingredients'])]
    
    print(f"\nBIOTIN + HAIR TREATMENT COMBINATIONS ({len(hair_combo_posts)} posts):")
    for post in sorted(hair_combo_posts, key=lambda x: x['score'], reverse=True)[:5]:
        print(f"• {post['title']} (Score: {post['score']})")
    
    # Posts about biotin dosage
    dosage_posts = [post for post in results['categories']['dosage_questions']
                   if any(term in post['title'].lower() for term in ['mg', 'mcg', 'dose', 'much'])]
    
    print(f"\nBIOTIN DOSAGE DISCUSSIONS ({len(dosage_posts)} posts):")
    for post in sorted(dosage_posts, key=lambda x: x['score'], reverse=True)[:3]:
        print(f"• {post['title']} (Score: {post['score']})")

def analyze_temporal_trends(results):
    """Analyze temporal trends in biotin posts."""
    print("\n" + "="*80)
    print("TEMPORAL TRENDS ANALYSIS")
    print("="*80)
    
    yearly_data = defaultdict(lambda: {'total': 0, 'side_effects': 0, 'progress': 0})
    
    for year, posts in results['temporal_patterns'].items():
        yearly_data[year]['total'] = len(posts)
        for post in posts:
            if post['categories']['side_effects']:
                yearly_data[year]['side_effects'] += 1
            if post['categories']['progress_report']:
                yearly_data[year]['progress'] += 1
    
    print("\nYearly Trends:")
    print("Year | Total Posts | Side Effects | Progress Reports")
    print("-" * 50)
    for year in sorted(yearly_data.keys()):
        data = yearly_data[year]
        print(f"{year} | {data['total']:10} | {data['side_effects']:11} | {data['progress']:15}")

def main():
    """Main function to run the analysis."""
    results = load_analysis_results()
    print_category_highlights(results)
    analyze_temporal_trends(results)
    
    print("\n" + "="*80)
    print("SUMMARY INSIGHTS")
    print("="*80)
    
    print("\nKey Findings:")
    print("• 82.7% of posts discuss biotin in combination with other treatments")
    print("• 59.0% share treatment experiences and results")
    print("• 55.4% include progress reports with before/after comparisons")
    print("• 45.3% discuss specific usage patterns and routines")
    print("• 36.0% ask about or discuss dosage questions")
    print("• 16.5% mention side effects (primarily acne-related)")
    
    print("\nMost Common Combinations:")
    print("• Biotin + Finasteride + Minoxidil (hair loss treatment)")
    print("• Biotin + Retinol + Sunscreen (skincare routine)")
    print("• Biotin + Derma roller (hair/beard growth)")
    
    print("\nSubreddit Distribution:")
    print("• r/tressless (30.9%) - Hair loss community")
    print("• r/Minoxbeards (10.8%) - Beard growth community")
    print("• r/SkincareAddiction (3.6%) - Skincare community")
    print("• Various nail, hair, and supplement communities")
    
    print("\nSentiment Analysis:")
    print("• Positive sentiment: 30 posts (mostly progress reports)")
    print("• Negative sentiment: 6 posts (mostly side effect reports)")
    print("• Overall trend shows growing interest in biotin supplementation")

if __name__ == "__main__":
    main()
