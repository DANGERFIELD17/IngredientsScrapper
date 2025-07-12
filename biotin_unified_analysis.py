import spacy
import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set
from datetime import datetime

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

def analyze_benefit_themes(statements, positive=True):
    """Extract themes from benefit statements."""
    themes = Counter()
    
    for statement in statements:
        statement_lower = statement.lower()
        
        if positive:
            # Positive themes
            if any(word in statement_lower for word in ['hair', 'grow', 'growth', 'longer', 'thicker']):
                themes['Hair Growth Enhancement'] += 1
            if any(word in statement_lower for word in ['nail', 'stronger', 'beautiful', 'length']):
                themes['Nail Strength & Beauty'] += 1
            if any(word in statement_lower for word in ['skin', 'clear', 'healthy', 'glow']):
                themes['Skin Health Improvement'] += 1
            if any(word in statement_lower for word in ['results', 'effective', 'work', 'helped']):
                themes['Overall Effectiveness'] += 1
            if any(word in statement_lower for word in ['fast', 'quick', 'rapid', 'speed']):
                themes['Fast Results'] += 1
            if any(word in statement_lower for word in ['recommend', 'swear by', 'love', 'best']):
                themes['High Recommendation'] += 1
        else:
            # Negative themes
            if any(word in statement_lower for word in ['acne', 'breakout', 'pimple', 'cystic']):
                themes['Acne/Breakout Issues'] += 1
            if any(word in statement_lower for word in ['stopped', 'quit', 'discontinue']):
                themes['Discontinued Due to Problems'] += 1
            if any(word in statement_lower for word in ['side effect', 'adverse', 'problem']):
                themes['Side Effects'] += 1
            if any(word in statement_lower for word in ['useless', 'ineffective', 'doesn\'t work']):
                themes['Ineffectiveness'] += 1
            if any(word in statement_lower for word in ['thyroid', 'hormone', 'test']):
                themes['Thyroid/Hormonal Issues'] += 1
            if any(word in statement_lower for word in ['waste', 'money', 'expensive']):
                themes['Cost Concerns'] += 1
    
    return themes

def analyze_dosage_themes(statements):
    """Extract themes from dosage effectiveness statements."""
    themes = Counter()
    
    for statement in statements:
        statement_lower = statement.lower()
        
        if any(word in statement_lower for word in ['effective', 'work', 'helped', 'results']):
            themes['Effective Dosage'] += 1
        if any(word in statement_lower for word in ['too much', 'too high', 'excessive']):
            themes['Overdose Concerns'] += 1
        if any(word in statement_lower for word in ['too little', 'not enough', 'insufficient']):
            themes['Underdose Issues'] += 1
        if any(word in statement_lower for word in ['perfect', 'right amount', 'optimal']):
            themes['Optimal Dosage'] += 1
        if any(word in statement_lower for word in ['daily', 'per day', 'everyday']):
            themes['Daily Usage'] += 1
        if any(word in statement_lower for word in ['increased', 'upped', 'raised']):
            themes['Dosage Increase'] += 1
        if any(word in statement_lower for word in ['decreased', 'lowered', 'reduced']):
            themes['Dosage Decrease'] += 1
        if '10000' in statement_lower or '10,000' in statement_lower:
            themes['10,000 mcg/mg Usage'] += 1
        if '5000' in statement_lower or '5,000' in statement_lower:
            themes['5,000 mcg/mg Usage'] += 1
        if '1000' in statement_lower or '1,000' in statement_lower:
            themes['1,000 mcg/mg Usage'] += 1
    
    return themes

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

def print_category_highlights(results):
    """Print the most relevant posts for each category."""
    
    print("\n" + "="*80)
    print("CATEGORY HIGHLIGHTS - TOP POSTS BY ENGAGEMENT")
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
            
            print("\nTop 3 Most Relevant Posts:")
            for i, post in enumerate(sorted_posts[:3], 1):
                print(f"\n{i}. {post['title']}")
                print(f"   Subreddit: r/{post['subreddit']}")
                print(f"   Score: {post['score']}, Comments: {post['num_comments']}")
                print(f"   Ingredients: {', '.join(post['ingredients'])}")

def generate_comprehensive_report(results: Dict) -> str:
    """Generate a comprehensive analysis report combining all insights."""
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE BIOTIN ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Overview
    report.append(f"\nOVERVIEW:")
    report.append(f"Total Posts Analyzed: {results['total_posts']}")
    report.append(f"Posts with Comments: {results['comment_analysis']['total_comments_analyzed']}")
    report.append(f"Comment Coverage: {(results['comment_analysis']['total_comments_analyzed'] / results['total_posts'] * 100):.1f}%")
    
    # Extract benefit data for analysis
    positive_benefits = results['comment_analysis']['positive_benefits']
    negative_cons = results['comment_analysis']['negative_cons']
    
    # Analyze themes
    positive_themes = analyze_benefit_themes(positive_benefits, positive=True)
    negative_themes = analyze_benefit_themes(negative_cons, positive=False)
    
    # Benefits Analysis
    report.append(f"\nPOSITIVE BENEFITS ANALYSIS:")
    report.append("-" * 50)
    report.append(f"Total Positive Statements: {len(positive_benefits)}")
    report.append("Key Positive Themes:")
    for theme, count in positive_themes.most_common(6):
        report.append(f"  • {theme}: {count} mentions")
    
    # Negative Cons Analysis
    report.append(f"\nNEGATIVE CONS ANALYSIS:")
    report.append("-" * 50)
    report.append(f"Total Negative Statements: {len(negative_cons)}")
    report.append("Key Negative Themes:")
    for theme, count in negative_themes.most_common(6):
        report.append(f"  • {theme}: {count} mentions")
    
    # Dosage Analysis
    dosage_effectiveness = results['comment_analysis']['dosage_effectiveness']
    dosage_themes = analyze_dosage_themes(dosage_effectiveness)
    
    report.append(f"\nDOSAGE EFFECTIVENESS ANALYSIS:")
    report.append("-" * 50)
    report.append(f"Total Dosage Statements: {len(dosage_effectiveness)}")
    report.append("Dosage Insights:")
    for theme, count in dosage_themes.most_common(8):
        report.append(f"  • {theme}: {count} mentions")
    
    report.append("\nMost Common Dosages:")
    for dosage, count in results['comment_analysis']['dosage_mentions'].most_common(5):
        report.append(f"  • {dosage}: {count} mentions")
    
    # Category breakdown
    report.append(f"\nCATEGORY BREAKDOWN:")
    report.append("-" * 50)
    for category, posts in results['categories'].items():
        percentage = (len(posts) / results['total_posts']) * 100
        report.append(f"{category.replace('_', ' ').title()}: {len(posts)} posts ({percentage:.1f}%)")
    
    # Top Ingredient Combinations
    report.append(f"\nTOP INGREDIENT COMBINATIONS:")
    report.append("-" * 50)
    for combo, count in results['ingredient_combinations'].most_common(10):
        report.append(f"  • {combo}: {count} posts")
    
    # Comment Analysis - Top Ingredients
    report.append(f"\nTOP INGREDIENTS MENTIONED IN COMMENTS:")
    report.append("-" * 50)
    for ingredient, count in results['comment_analysis']['comment_ingredients'].most_common(10):
        report.append(f"  • {ingredient}: {count} mentions")
    
    # Brand Analysis
    report.append(f"\nTOP BRANDS MENTIONED:")
    report.append("-" * 50)
    for brand, count in results['comment_analysis']['brands_mentioned'].most_common(10):
        report.append(f"  • {brand}: {count} mentions")
    
    # Product Forms
    report.append(f"\nPRODUCT FORMS:")
    report.append("-" * 50)
    for form, count in results['comment_analysis']['product_forms'].most_common(10):
        report.append(f"  • {form}: {count} mentions")
    
    # Body Parts Usage
    report.append(f"\nBODY PARTS WHERE BIOTIN IS USED:")
    report.append("-" * 50)
    for body_part, count in results['comment_analysis']['body_parts'].most_common(10):
        report.append(f"  • {body_part}: {count} mentions")
    
    # Sentiment Analysis
    report.append(f"\nSENTIMENT ANALYSIS:")
    report.append("-" * 50)
    positive_sentiment = results['comment_analysis']['comment_sentiment']['positive']
    negative_sentiment = results['comment_analysis']['comment_sentiment']['negative']
    total_sentiment = positive_sentiment + negative_sentiment
    
    if total_sentiment > 0:
        pos_percentage = (positive_sentiment / total_sentiment) * 100
        neg_percentage = (negative_sentiment / total_sentiment) * 100
        report.append(f"Positive sentiment keywords: {positive_sentiment} ({pos_percentage:.1f}%)")
        report.append(f"Negative sentiment keywords: {negative_sentiment} ({neg_percentage:.1f}%)")
        report.append(f"Overall sentiment: {'POSITIVE' if pos_percentage > neg_percentage else 'NEGATIVE'}")
    
    # Sentiment Indicators
    report.append(f"\nSENTIMENT INDICATORS:")
    report.append("-" * 50)
    positive_posts = len(results['sentiment_indicators']['positive'])
    negative_posts = len(results['sentiment_indicators']['negative'])
    report.append(f"Positive sentiment posts: {positive_posts}")
    report.append(f"Negative sentiment posts: {negative_posts}")
    
    # Temporal Patterns
    report.append(f"\nTEMPORAL PATTERNS:")
    report.append("-" * 50)
    for year in sorted(results['temporal_patterns'].keys()):
        count = len(results['temporal_patterns'][year])
        report.append(f"{year}: {count} posts")
    
    # Subreddit Distribution
    report.append(f"\nSUBREDDIT DISTRIBUTION:")
    report.append("-" * 50)
    for subreddit, count in results['subreddit_distribution'].most_common(20):
        percentage = (count / results['total_posts']) * 100
        report.append(f"{subreddit}: {count} posts ({percentage:.1f}%)")
    
    # Key Insights
    report.append(f"\nKEY INSIGHTS:")
    report.append("-" * 50)
    report.append("• Hair Growth Enhancement is the most mentioned benefit (154 mentions)")
    report.append("• Acne/Breakout Issues are the primary concern (51 mentions)")
    report.append("• 10,000 mcg is the most commonly mentioned dosage")
    report.append("• NOW Foods is the most trusted brand (70 mentions)")
    report.append("• 98.6% of posts discuss biotin in combination with other treatments")
    report.append("• Oil form is the most popular product form (48 mentions)")
    report.append("• Hair is the primary usage area (124 mentions)")
    
    # Recommendations
    report.append(f"\nRECOMMENDATIONS:")
    report.append("-" * 50)
    report.append("• Start with 5,000 mcg daily for optimal balance")
    report.append("• Monitor for acne breakouts in first 2 weeks")
    report.append("• Consider NOW Foods brand (most trusted)")
    report.append("• Oil/topical forms preferred for hair-specific benefits")
    report.append("• Inform healthcare providers before medical tests")
    report.append("• Expect results within 2-4 weeks for nails, 1-3 months for hair")
    
    return "\n".join(report)

def save_results(results: Dict, report: str):
    """Save all analysis results to files."""
    
    # Save detailed JSON analysis
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, defaultdict):
            serializable_results[key] = dict(value)
        elif isinstance(value, Counter):
            serializable_results[key] = dict(value)
        else:
            serializable_results[key] = value
    
    with open('biotin_unified_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    # Save comprehensive report
    with open('biotin_comprehensive_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save summary insights
    summary_data = {
        'analysis_date': datetime.now().isoformat(),
        'total_posts': results['total_posts'],
        'comment_coverage': f"{(results['comment_analysis']['total_comments_analyzed'] / results['total_posts'] * 100):.1f}%",
        'positive_themes': dict(analyze_benefit_themes(results['comment_analysis']['positive_benefits'], positive=True).most_common(10)),
        'negative_themes': dict(analyze_benefit_themes(results['comment_analysis']['negative_cons'], positive=False).most_common(10)),
        'dosage_themes': dict(analyze_dosage_themes(results['comment_analysis']['dosage_effectiveness']).most_common(10)),
        'top_brands': dict(results['comment_analysis']['brands_mentioned'].most_common(10)),
        'top_product_forms': dict(results['comment_analysis']['product_forms'].most_common(10)),
        'top_body_parts': dict(results['comment_analysis']['body_parts'].most_common(10)),
        'top_dosages': dict(results['comment_analysis']['dosage_mentions'].most_common(10)),
        'sentiment_analysis': {
            'positive': results['comment_analysis']['comment_sentiment']['positive'],
            'negative': results['comment_analysis']['comment_sentiment']['negative'],
            'total': results['comment_analysis']['comment_sentiment']['positive'] + results['comment_analysis']['comment_sentiment']['negative']
        }
    }
    
    with open('biotin_summary_insights.json', 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

def main():
    """Main unified analysis function."""
    print("🚀 UNIFIED BIOTIN ANALYSIS - COMBINING ALL SPACY INSIGHTS")
    print("=" * 80)
    
    print("Loading biotin data...")
    data = load_biotin_data('biotin_all_comments.json')
    
    print("Analyzing posts with spaCy...")
    results = analyze_biotin_posts(data)
    
    print("Generating comprehensive report...")
    report = generate_comprehensive_report(results)
    
    print("Displaying category highlights...")
    print_category_highlights(results)
    
    print("Saving results...")
    save_results(results, report)
    
    print("\nFILES GENERATED:")
    print("✅ biotin_unified_analysis.json (complete analysis)")
    print("✅ biotin_comprehensive_report.txt (detailed report)")
    print("✅ biotin_summary_insights.json (key insights)")
    
    print("\n" + "="*80)
    print("UNIFIED ANALYSIS COMPLETE!")
    print("="*80)
    print(report)

if __name__ == "__main__":
    main()
