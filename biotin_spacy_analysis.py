import spacy
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set

# Load English model
nlp = spacy.load("en_core_web_sm")

def load_biotin_data(filename: str) -> List[Dict]:
    """Load biotin data from JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_title(title: str) -> str:
    """Clean and normalize title text."""
    # Remove Reddit tags like [Anti-Aging], [Acne], etc.
    title = re.sub(r'\[.*?\]', '', title)
    # Remove extra whitespace
    title = ' '.join(title.split())
    return title.strip()

def extract_ingredients(text: str) -> Set[str]:
    """Extract ingredient names from text using pattern matching."""
    ingredients = set()
    
    # Common skincare/haircare ingredients
    ingredient_patterns = [
        r'\b(finasteride|fin)\b',
        r'\b(minoxidil|min|rogaine)\b',
        r'\b(biotin)\b',
        r'\b(retinol|tretinoin)\b',
        r'\b(ketoconazole|nizoral|keto)\b',
        r'\b(microneedling|derma\s*roll\w*)\b',
        r'\b(vitamin\s*[a-z]?\d*)\b',
        r'\b(zinc|iron|omega)\b',
        r'\b(niacinamide|salicylic\s*acid)\b',
        r'\b(sunscreen|spf)\b'
    ]
    
    text_lower = text.lower()
    for pattern in ingredient_patterns:
        matches = re.findall(pattern, text_lower)
        ingredients.update(matches)
    
    return ingredients

def extract_comments_text(comments: List[Dict]) -> str:
    """Extract and combine text from all comments."""
    comment_texts = []
    
    for comment in comments:
        if isinstance(comment, dict) and 'body' in comment:
            body = comment['body']
            if body and isinstance(body, str) and body.strip():
                # Skip deleted/removed comments
                if body not in ['[deleted]', '[removed]', '']:
                    comment_texts.append(body)
    
    return ' '.join(comment_texts)

def analyze_comments_with_spacy(comments_text: str) -> Dict:
    """Analyze comments using spaCy for entities and sentiment patterns."""
    if not comments_text.strip():
        return {
            'entities': [],
            'ingredients': set(),
            'sentiment_keywords': {'positive': 0, 'negative': 0},
            'dosage_mentions': [],
            'experience_keywords': 0,
            'positive_benefits': [],
            'negative_cons': [],
            'brands_mentioned': [],
            'product_forms': [],
            'body_parts': [],
            'dosage_effectiveness': []
        }
    
    # Process with spaCy (limit text length to avoid memory issues)
    text_sample = comments_text[:5000]  # Limit to first 5000 chars
    doc = nlp(text_sample)
    
    # Extract entities
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # Extract ingredients from comments
    ingredients = extract_ingredients(comments_text)
    
    # Sentiment analysis based on keywords
    positive_keywords = ['great', 'amazing', 'excellent', 'perfect', 'love', 'best', 'wonderful', 'fantastic', 'helped', 'improved', 'better', 'works', 'effective']
    negative_keywords = ['terrible', 'awful', 'worst', 'hate', 'horrible', 'disappointing', 'useless', 'bad', 'worse', 'problem', 'issue', 'side effect', 'acne', 'breakout']
    
    text_lower = comments_text.lower()
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    
    # Extract positive benefits statements
    positive_benefits = extract_benefit_statements(comments_text, positive=True)
    
    # Extract negative cons statements
    negative_cons = extract_benefit_statements(comments_text, positive=False)
    
    # Extract brand mentions
    brands_mentioned = extract_brands(comments_text)
    
    # Extract product forms
    product_forms = extract_product_forms(comments_text)
    
    # Extract body parts mentioned
    body_parts = extract_body_parts(comments_text)
    
    # Extract dosage effectiveness mentions
    dosage_effectiveness = extract_dosage_effectiveness(comments_text)
    
    # Find dosage mentions
    dosage_pattern = r'\b(\d+\.?\d*)\s*(mg|mcg|micrograms?|milligrams?)\b'
    dosage_mentions = re.findall(dosage_pattern, text_lower)
    
    # Count experience-related keywords
    experience_keywords = ['experience', 'tried', 'using', 'taking', 'months', 'years', 'weeks', 'results', 'progress']
    experience_count = sum(1 for word in experience_keywords if word in text_lower)
    
    return {
        'entities': entities,
        'ingredients': ingredients,
        'sentiment_keywords': {'positive': positive_count, 'negative': negative_count},
        'dosage_mentions': dosage_mentions,
        'experience_keywords': experience_count,
        'positive_benefits': positive_benefits,
        'negative_cons': negative_cons,
        'brands_mentioned': brands_mentioned,
        'product_forms': product_forms,
        'body_parts': body_parts,
        'dosage_effectiveness': dosage_effectiveness
    }

def extract_benefit_statements(text: str, positive: bool = True) -> List[str]:
    """Extract positive benefit or negative con statements from text."""
    statements = []
    text_lower = text.lower()
    
    if positive:
        # Positive benefit patterns
        benefit_patterns = [
            r'biotin.*(?:helped|improved|better|works|effective|great|amazing).*(?:hair|skin|nails|growth)',
            r'(?:hair|skin|nails).*(?:grew|stronger|thicker|healthier|improved).*biotin',
            r'biotin.*(?:results|progress|difference|improvement)',
            r'(?:love|recommend|best).*biotin',
            r'biotin.*(?:fixed|solved|helped with)'
        ]
    else:
        # Negative con patterns
        benefit_patterns = [
            r'biotin.*(?:caused|triggered|gave me).*(?:acne|breakout|cystic|pimples)',
            r'(?:stopped|quit|discontinued).*biotin.*(?:because|due to)',
            r'biotin.*(?:side effect|problem|issue|bad|worse)',
            r'(?:acne|breakout|cystic).*biotin',
            r'biotin.*(?:doesn\'t work|useless|ineffective|disappointing)'
        ]
    
    for pattern in benefit_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            if context and len(context) > 20:
                statements.append(context)
    
    return statements[:5]  # Return top 5

def extract_brands(text: str) -> List[str]:
    """Extract brand mentions from text."""
    brands = []
    text_lower = text.lower()
    
    # Common supplement/cosmetic brands
    brand_patterns = [
        r'\b(nature\'s bounty|natures bounty)\b',
        r'\b(viviscal)\b',
        r'\b(nutrafol)\b',
        r'\b(sports research)\b',
        r'\b(now foods|now)\b',
        r'\b(solgar)\b',
        r'\b(jarrow)\b',
        r'\b(life extension)\b',
        r'\b(thorne)\b',
        r'\b(garden of life)\b',
        r'\b(nordic naturals)\b',
        r'\b(nature made)\b',
        r'\b(centrum)\b',
        r'\b(one a day)\b',
        r'\b(vitafusion)\b',
        r'\b(natrol)\b',
        r'\b(gnc)\b',
        r'\b(kirkland)\b',
        r'\b(amazon brand|amazon basic)\b',
        r'\b(costco|kirkland)\b'
    ]
    
    for pattern in brand_patterns:
        matches = re.findall(pattern, text_lower)
        brands.extend(matches)
    
    return list(set(brands))

def extract_product_forms(text: str) -> List[str]:
    """Extract product forms mentioned in text."""
    forms = []
    text_lower = text.lower()
    
    form_patterns = [
        r'\b(gummies|gummy)\b',
        r'\b(pills|pill|tablet|tablets)\b',
        r'\b(capsules|capsule)\b',
        r'\b(liquid|drops)\b',
        r'\b(powder)\b',
        r'\b(gel|topical)\b',
        r'\b(spray)\b',
        r'\b(cream|lotion)\b',
        r'\b(serum)\b',
        r'\b(oil)\b',
        r'\b(softgel|soft gel)\b',
        r'\b(chewable)\b'
    ]
    
    for pattern in form_patterns:
        matches = re.findall(pattern, text_lower)
        forms.extend(matches)
    
    return list(set(forms))

def extract_body_parts(text: str) -> List[str]:
    """Extract body parts where biotin is used."""
    body_parts = []
    text_lower = text.lower()
    
    body_part_patterns = [
        r'\b(hair|scalp)\b',
        r'\b(nails|nail)\b',
        r'\b(skin|face|facial)\b',
        r'\b(beard|mustache)\b',
        r'\b(eyebrows|eyelashes)\b',
        r'\b(body hair)\b',
        r'\b(head|forehead)\b',
        r'\b(temples)\b',
        r'\b(crown)\b',
        r'\b(hairline)\b'
    ]
    
    for pattern in body_part_patterns:
        matches = re.findall(pattern, text_lower)
        body_parts.extend(matches)
    
    return list(set(body_parts))

def extract_dosage_effectiveness(text: str) -> List[str]:
    """Extract dosage effectiveness mentions."""
    effectiveness = []
    text_lower = text.lower()
    
    # Look for dosage + effectiveness patterns
    dosage_effect_patterns = [
        r'(\d+\.?\d*)\s*(mg|mcg).*(?:works|effective|helped|improved|better|results)',
        r'(?:taking|using)\s*(\d+\.?\d*)\s*(mg|mcg).*(?:daily|per day).*(?:for|and).*(?:hair|skin|nails)',
        r'(\d+\.?\d*)\s*(mg|mcg).*(?:too much|too little|not enough|perfect|right amount)',
        r'(?:increased|decreased|changed).*(?:to|from)\s*(\d+\.?\d*)\s*(mg|mcg)'
    ]
    
    for pattern in dosage_effect_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # Get surrounding context
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            if context and len(context) > 15:
                effectiveness.append(context)
    
    return effectiveness[:5]  # Return top 5

def categorize_post_intent(title: str, body: str = "", comments_text: str = "") -> Dict[str, bool]:
    """Categorize post intent based on title, body content, and comments."""
    combined_text = f"{title} {body} {comments_text}".lower()
    
    categories = {
        'ingredient_usage_patterns': False,
        'treatment_experiences': False,
        'product_recommendations': False,
        'progress_report': False,
        'side_effects': False,
        'dosage_questions': False,
        'combination_therapy': False,
        'scientific_discussion': False,
        'humor_meme': False,
        'seeking_advice': False
    }
    
    # Define keywords for each category
    patterns = {
        'ingredient_usage_patterns': [
            r'\b(routine|regimen|protocol|taking|using|applying)\b',
            r'\b(daily|weekly|monthly|times?\s*per\s*day)\b',
            r'\b(mcg|mg|dose|dosage)\b'
        ],
        'treatment_experiences': [
            r'\b(results?|progress|experience|journey)\b',
            r'\b(months?|years?|weeks?)\b.*\b(of|on|with)\b',
            r'\b(before|after|update)\b'
        ],
        'product_recommendations': [
            r'\b(recommend|suggest|best|brand|product)\b',
            r'\b(which|what|anyone\s*know)\b',
            r'\b(review|comparison)\b'
        ],
        'progress_report': [
            r'\b(\d+\s*(month|year|week|day)s?)\b',
            r'\b(progress|results?|update|before.*after)\b',
            r'\b(pics?|pictures?|photos?)\b'
        ],
        'side_effects': [
            r'\b(side\s*effects?|acne|breakout|cystic)\b',
            r'\b(stopped|quit|discontinue)\b',
            r'\b(problem|issue|horror|bad)\b'
        ],
        'dosage_questions': [
            r'\b(\d+\s*(mcg|mg|micrograms?|milligrams?))\b',
            r'\b(dose|dosage|amount|how\s*much)\b',
            r'\b(daily|per\s*day|twice)\b'
        ],
        'combination_therapy': [
            r'\b(fin|min|finasteride|minoxidil)\b',
            r'\b(derma.*roll|microneedling|keto)\b',
            r'\b(plus|with|and|\+|combo|combination)\b'
        ],
        'scientific_discussion': [
            r'\b(study|research|extraction|mechanism)\b',
            r'\b(chemistry|scientific|analysis)\b',
            r'\b(exactly|precise|grams?)\b'
        ],
        'humor_meme': [
            r'\b(lol|haha|funny|humor|joke)\b',
            r'[!]{2,}',
            r'\b(nobody.*cares|exactly)\b'
        ],
        'seeking_advice': [
            r'\b(help|advice|suggest|recommend)\b',
            r'\b(should\s*i|what.*do|anyone)\b',
            r'\?'
        ]
    }
    
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, combined_text):
                categories[category] = True
                break
    
    return categories

def analyze_biotin_posts(data: List[Dict]) -> Dict:
    """Analyze biotin posts using spaCy and categorize them."""
    results = {
        'total_posts': len(data),
        'categories': defaultdict(list),
        'ingredient_combinations': Counter(),
        'subreddit_distribution': Counter(),
        'temporal_patterns': defaultdict(list),
        'top_entities': Counter(),
        'sentiment_indicators': defaultdict(list),
        'comment_analysis': {
            'total_comments_analyzed': 0,
            'comment_ingredients': Counter(),
            'comment_sentiment': {'positive': 0, 'negative': 0},
            'dosage_mentions': Counter(),
            'comment_entities': Counter(),
            'positive_benefits': [],
            'negative_cons': [],
            'brands_mentioned': Counter(),
            'product_forms': Counter(),
            'body_parts': Counter(),
            'dosage_effectiveness': []
        }
    }
    
    for post in data:
        title = post['title']
        body = post.get('body', '')
        subreddit = post['subreddit']
        comments = post.get('comments', [])
        
        # Clean title
        clean_title_text = clean_title(title)
        
        # Process with spaCy
        doc = nlp(clean_title_text)
        
        # Extract entities from title
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        for ent_text, ent_label in entities:
            results['top_entities'][f"{ent_text} ({ent_label})"] += 1
        
        # Extract and analyze comments
        comments_text = extract_comments_text(comments)
        comment_analysis = analyze_comments_with_spacy(comments_text)
        
        # Update comment analysis results
        if comments_text.strip():
            results['comment_analysis']['total_comments_analyzed'] += 1
            
            # Add comment entities
            for ent_text, ent_label in comment_analysis['entities']:
                results['comment_analysis']['comment_entities'][f"{ent_text} ({ent_label})"] += 1
            
            # Add comment ingredients
            for ingredient in comment_analysis['ingredients']:
                results['comment_analysis']['comment_ingredients'][ingredient] += 1
            
            # Add sentiment
            results['comment_analysis']['comment_sentiment']['positive'] += comment_analysis['sentiment_keywords']['positive']
            results['comment_analysis']['comment_sentiment']['negative'] += comment_analysis['sentiment_keywords']['negative']
            
            # Add dosage mentions
            for dosage, unit in comment_analysis['dosage_mentions']:
                results['comment_analysis']['dosage_mentions'][f"{dosage} {unit}"] += 1
            
            # Add new analysis results
            results['comment_analysis']['positive_benefits'].extend(comment_analysis['positive_benefits'])
            results['comment_analysis']['negative_cons'].extend(comment_analysis['negative_cons'])
            results['comment_analysis']['dosage_effectiveness'].extend(comment_analysis['dosage_effectiveness'])
            
            # Count brands, forms, and body parts
            for brand in comment_analysis['brands_mentioned']:
                results['comment_analysis']['brands_mentioned'][brand] += 1
            for form in comment_analysis['product_forms']:
                results['comment_analysis']['product_forms'][form] += 1
            for body_part in comment_analysis['body_parts']:
                results['comment_analysis']['body_parts'][body_part] += 1
        
        # Extract ingredients from title and comments combined
        title_ingredients = extract_ingredients(title)
        comment_ingredients = comment_analysis['ingredients']
        all_ingredients = title_ingredients.union(comment_ingredients)
        
        if len(all_ingredients) > 1:
            combo = ', '.join(sorted(all_ingredients))
            results['ingredient_combinations'][combo] += 1
        
        # Categorize intent using title, body, and comments
        categories = categorize_post_intent(title, body, comments_text)
        
        # Store post data with analysis
        post_analysis = {
            'post_id': post['post_id'],
            'title': title,
            'clean_title': clean_title_text,
            'subreddit': subreddit,
            'score': post['score'],
            'num_comments': post['num_comments'],
            'created': post['created'],
            'ingredients': list(all_ingredients),
            'title_ingredients': list(title_ingredients),
            'comment_ingredients': list(comment_ingredients),
            'entities': entities,
            'comment_entities': comment_analysis['entities'],
            'categories': categories,
            'category_count': sum(categories.values()),
            'comment_sentiment': comment_analysis['sentiment_keywords'],
            'comment_dosage_mentions': comment_analysis['dosage_mentions'],
            'comment_experience_keywords': comment_analysis['experience_keywords']
        }
        
        # Add to category lists
        for category, is_match in categories.items():
            if is_match:
                results['categories'][category].append(post_analysis)
        
        # Track subreddit distribution
        results['subreddit_distribution'][subreddit] += 1
        
        # Temporal analysis
        year = post['created'][:4]
        results['temporal_patterns'][year].append(post_analysis)
        
        # Sentiment indicators (enhanced with comments)
        title_lower = title.lower()
        total_positive = comment_analysis['sentiment_keywords']['positive']
        total_negative = comment_analysis['sentiment_keywords']['negative']
        
        if any(word in title_lower for word in ['horror', 'worst', 'bad', 'stopped', 'quit']) or total_negative > total_positive:
            results['sentiment_indicators']['negative'].append(post_analysis)
        elif any(word in title_lower for word in ['great', 'amazing', 'progress', 'results']) or total_positive > total_negative:
            results['sentiment_indicators']['positive'].append(post_analysis)
    
    return results

def generate_analysis_report(results: Dict) -> str:
    """Generate a comprehensive analysis report."""
    report = []
    report.append("=" * 60)
    report.append("BIOTIN POST ANALYSIS REPORT")
    report.append("=" * 60)
    
    # Overview
    report.append(f"\nTOTAL POSTS ANALYZED: {results['total_posts']}")
    report.append(f"POSTS WITH COMMENTS ANALYZED: {results['comment_analysis']['total_comments_analyzed']}")
    
    # Category breakdown
    report.append("\nCATEGORY BREAKDOWN:")
    report.append("-" * 40)
    for category, posts in results['categories'].items():
        percentage = (len(posts) / results['total_posts']) * 100
        report.append(f"{category.replace('_', ' ').title()}: {len(posts)} posts ({percentage:.1f}%)")
    
    # Top 5 positive benefits
    report.append("\nTOP 5 POSITIVE BENEFITS:")
    report.append("-" * 40)
    unique_benefits = list(set(results['comment_analysis']['positive_benefits']))[:5]
    for i, benefit in enumerate(unique_benefits, 1):
        report.append(f"{i}. {benefit}")
    
    # Top 5 negative cons
    report.append("\nTOP 5 NEGATIVE CONS:")
    report.append("-" * 40)
    unique_cons = list(set(results['comment_analysis']['negative_cons']))[:5]
    for i, con in enumerate(unique_cons, 1):
        report.append(f"{i}. {con}")
    
    # Top brands mentioned
    report.append("\nTOP BRANDS MENTIONED:")
    report.append("-" * 40)
    for brand, count in results['comment_analysis']['brands_mentioned'].most_common(10):
        report.append(f"{brand}: {count} mentions")
    
    # Product forms
    report.append("\nPRODUCT FORMS:")
    report.append("-" * 40)
    for form, count in results['comment_analysis']['product_forms'].most_common(10):
        report.append(f"{form}: {count} mentions")
    
    # Body parts where used
    report.append("\nBODY PARTS WHERE BIOTIN IS USED:")
    report.append("-" * 40)
    for body_part, count in results['comment_analysis']['body_parts'].most_common(10):
        report.append(f"{body_part}: {count} mentions")
    
    # Dosage effectiveness
    report.append("\nDOSAGE EFFECTIVENESS MENTIONS:")
    report.append("-" * 40)
    unique_dosage_effects = list(set(results['comment_analysis']['dosage_effectiveness']))[:5]
    for i, effect in enumerate(unique_dosage_effects, 1):
        report.append(f"{i}. {effect}")
    
    # Top ingredient combinations
    report.append("\nTOP INGREDIENT COMBINATIONS:")
    report.append("-" * 40)
    for combo, count in results['ingredient_combinations'].most_common(10):
        report.append(f"{combo}: {count} posts")
    
    # Comment analysis
    report.append("\nCOMMENT ANALYSIS:")
    report.append("-" * 40)
    report.append(f"Total comments analyzed: {results['comment_analysis']['total_comments_analyzed']}")
    
    # Comment ingredients
    report.append("\nTOP INGREDIENTS MENTIONED IN COMMENTS:")
    report.append("-" * 40)
    for ingredient, count in results['comment_analysis']['comment_ingredients'].most_common(10):
        report.append(f"{ingredient}: {count} mentions")
    
    # Comment sentiment
    report.append("\nCOMMENT SENTIMENT ANALYSIS:")
    report.append("-" * 40)
    positive_comments = results['comment_analysis']['comment_sentiment']['positive']
    negative_comments = results['comment_analysis']['comment_sentiment']['negative']
    report.append(f"Positive sentiment keywords: {positive_comments}")
    report.append(f"Negative sentiment keywords: {negative_comments}")
    
    # Dosage mentions from comments
    report.append("\nDOSAGE MENTIONS IN COMMENTS:")
    report.append("-" * 40)
    for dosage, count in results['comment_analysis']['dosage_mentions'].most_common(10):
        report.append(f"{dosage}: {count} mentions")
    
    # Subreddit distribution
    report.append("\nSUBREDDIT DISTRIBUTION:")
    report.append("-" * 40)
    for subreddit, count in results['subreddit_distribution'].most_common():
        percentage = (count / results['total_posts']) * 100
        report.append(f"{subreddit}: {count} posts ({percentage:.1f}%)")
    
    # Sentiment indicators
    report.append("\nSENTIMENT INDICATORS:")
    report.append("-" * 40)
    positive_count = len(results['sentiment_indicators']['positive'])
    negative_count = len(results['sentiment_indicators']['negative'])
    report.append(f"Positive sentiment posts: {positive_count}")
    report.append(f"Negative sentiment posts: {negative_count}")
    
    # Temporal patterns
    report.append("\nTEMPORAL PATTERNS:")
    report.append("-" * 40)
    for year in sorted(results['temporal_patterns'].keys()):
        count = len(results['temporal_patterns'][year])
        report.append(f"{year}: {count} posts")
    
    return "\n".join(report)

def save_detailed_analysis(results: Dict, filename: str):
    """Save detailed analysis to JSON file."""
    # Convert defaultdict to regular dict for JSON serialization
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, defaultdict):
            serializable_results[key] = dict(value)
        elif isinstance(value, Counter):
            serializable_results[key] = dict(value)
        else:
            serializable_results[key] = value
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)

def create_category_summaries(results: Dict) -> Dict[str, List[str]]:
    """Create summaries for each category with example titles."""
    summaries = {}
    
    for category, posts in results['categories'].items():
        if not posts:
            continue
            
        # Sort by score (engagement) and get top examples
        sorted_posts = sorted(posts, key=lambda x: x['score'], reverse=True)
        top_posts = sorted_posts[:5]
        
        summaries[category] = {
            'count': len(posts),
            'description': get_category_description(category),
            'top_examples': [
                {
                    'title': post['title'],
                    'score': post['score'],
                    'subreddit': post['subreddit'],
                    'ingredients': post['ingredients'],
                    'title_ingredients': post.get('title_ingredients', []),
                    'comment_ingredients': post.get('comment_ingredients', []),
                    'comment_sentiment': post.get('comment_sentiment', {}),
                    'comment_dosage_mentions': post.get('comment_dosage_mentions', [])
                }
                for post in top_posts
            ]
        }
    
    return summaries

def get_category_description(category: str) -> str:
    """Get description for each category."""
    descriptions = {
        'ingredient_usage_patterns': "Posts discussing how biotin is used in routines and protocols",
        'treatment_experiences': "Posts sharing personal experiences with biotin treatment",
        'product_recommendations': "Posts asking for or providing product recommendations",
        'progress_report': "Posts showing before/after results or progress updates",
        'side_effects': "Posts discussing negative effects or problems with biotin",
        'dosage_questions': "Posts asking about or discussing biotin dosage",
        'combination_therapy': "Posts discussing biotin with other treatments",
        'scientific_discussion': "Posts with scientific or technical discussions about biotin",
        'humor_meme': "Humorous or meme posts related to biotin",
        'seeking_advice': "Posts asking for help or advice about biotin"
    }
    return descriptions.get(category, "")

def main():
    """Main analysis function."""
    print("Loading biotin data...")
    data = load_biotin_data('biotin_all_comments.json')
    
    print("Analyzing posts with spaCy...")
    results = analyze_biotin_posts(data)
    
    print("Generating analysis report...")
    report = generate_analysis_report(results)
    
    print("Creating category summaries...")
    summaries = create_category_summaries(results)
    
    # Save results
    print("Saving detailed analysis...")
    save_detailed_analysis(results, 'biotin_spacy_analysis.json')
    
    # Save summaries
    with open('biotin_category_summaries.json', 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    
    # Save report
    with open('biotin_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\nAnalysis complete!")
    print("Files generated:")
    print("- biotin_spacy_analysis.json (detailed analysis)")
    print("- biotin_category_summaries.json (category summaries)")
    print("- biotin_analysis_report.txt (summary report)")
    
    print("\n" + report)

if __name__ == "__main__":
    main()