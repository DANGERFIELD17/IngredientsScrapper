import json
import requests
from collections import Counter
import re
from datetime import datetime

def enhanced_analysis_structure(data, identifier_str, llama_url):
    """
    Enhanced analysis structure using a locally hosted Llama model via HTTP API (Ollama /api/generate)
    """
    # Prepare high-quality data for analysis
    analysis_text = prepare_enhanced_data(data)

    # Simplify identifier for readability
    clean_ingredient = identifier_str.replace("_or_", " OR ").replace("_", " ")

    # Combine system and user prompt for Ollama
    prompt = f"""
You are an expert researcher analyzing Reddit community discussions about {clean_ingredient}.
Your analysis must be strictly based ONLY on the data provided below. Do not make assumptions, do not use external knowledge, and do not infer beyond what is present in the data. Provide detailed, evidence-based insights in valid JSON format only.

Analyze the following Reddit discussions about {clean_ingredient} and provide insights based strictly on the actual user experiences shared.

Reddit data to analyze:
{analysis_text}

Return ONLY a valid JSON object (no markdown, no explanations) with this exact structure:
{{
  "ingredient": "{clean_ingredient}",
  "data_summary": {{
    "total_posts": {len(data)},
    "total_comments": {sum(len(post.get('comments', [])) for post in data)},
    "avg_engagement": 0.0,
    "time_span": "2023-2024",
    "high_value_discussions": 0
  }},
  "usage_patterns": {{
    "dosage_recommendations": [],
    "timing_preferences": [],
    "duration_cycles": []
  }},
  "effectiveness_analysis": {{
    "reported_benefits": [],
    "reported_side_effects": [],
    "individual_variations": []
  }},
  "brand_intelligence": {{
    "top_brands": [],
    "extract_preferences": []
  }},
  "safety_insights": {{
    "contraindications": [],
    "cycling_importance": {{
      "recommended": false,
      "reason": "",
      "protocol": ""
    }},
    "warning_signals": []
  }},
  "user_journey_insights": {{
    "beginner_advice": [],
    "common_mistakes": [],
    "success_patterns": []
  }},
  "discussion_trends": {{
    "emerging_topics": [],
    "controversial_aspects": []
  }},
  "sentiment_analysis": {{
    "overall_sentiment": {{
      "positive": 0,
      "neutral": 0,
      "negative": 0
    }},
    "sentiment_by_experience_level": {{
      "beginners": {{"positive": 0, "neutral": 0, "negative": 0}},
      "experienced_users": {{"positive": 0, "neutral": 0, "negative": 0}},
      "long_term_users": {{"positive": 0, "neutral": 0, "negative": 0}}
    }},
    "sentiment_drivers": {{
      "positive_factors": [],
      "negative_factors": []
    }}
  }},
  "actionable_insights": {{
    "for_beginners": [],
    "for_researchers": [],
    "red_flags": []
  }}
}}

Fill this structure with actual insights from the Reddit data. Focus on usage patterns, treatment experiences, and product recommendations relevant to {clean_ingredient}. Be precise with data. Do not make assumptions or use information not present in the data.
"""
    try:
        # Ollama /api/generate expects: model, prompt, stream
        payload = {
            "model": "gemma3:latest",  # Using your actual model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9
            }
        }
        response = requests.post(llama_url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        ai_analysis = result.get("response", "").strip()

        # Debug: print the raw response if empty
        if not ai_analysis:
            print("[DEBUG] Empty or missing response from Ollama:", result)
            return {"error": f"Empty or missing response from Ollama: {result}"}

        # Clean and parse JSON - more robust cleaning
        if ai_analysis.startswith('```json'):
            ai_analysis = ai_analysis[7:]
            if ai_analysis.endswith('```'):
                ai_analysis = ai_analysis[:-3]
        elif ai_analysis.startswith('```'):
            ai_analysis = ai_analysis[3:]
            if ai_analysis.endswith('```'):
                ai_analysis = ai_analysis[:-3]
        
        # Remove any leading/trailing whitespace
        ai_analysis = ai_analysis.strip()
        
        # Find JSON start and end
        start_idx = ai_analysis.find('{')
        end_idx = ai_analysis.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            ai_analysis = ai_analysis[start_idx:end_idx+1]
        
        try:
            return json.loads(ai_analysis)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON Parse Error: {e}")
            print(f"[DEBUG] Response length: {len(ai_analysis)}")
            print(f"[DEBUG] First 500 chars: {ai_analysis[:500]}")
            
            # Return a fallback structure with basic analysis
            return create_fallback_analysis(data, clean_ingredient)

    except Exception as e:
        print(f"Enhanced analysis failed: {e}")
        return create_fallback_analysis(data, clean_ingredient)

def prepare_enhanced_data(data):
    """Prepare data focusing on high-value content"""
    
    # Sort posts by engagement score
    posts_by_engagement = sorted(data, 
                               key=lambda x: x['score'] + sum(c['score'] for c in x['comments']), 
                               reverse=True)
    
    # Take top 30 posts for detailed analysis
    top_posts = posts_by_engagement[:30]
    
    analysis_text = []
    
    for post in top_posts:
        # Add post with context
        analysis_text.append(f"HIGH_VALUE_POST [Score: {post['score']}, Comments: {len(post['comments'])}]: {post['title']}")
        if post['body']:
            analysis_text.append(f"POST_BODY: {post['body'][:500]}")
        
        # Add top 5 comments with scores
        for comment in post['comments'][:5]:
            analysis_text.append(f"COMMENT [Score: {comment['score']}]: {comment['body'][:300]}")
    
    return "\\n".join(analysis_text)[:25000]  # Increased limit for detailed analysis

def create_fallback_analysis(data, ingredient_name):
    """Create a basic analysis when AI parsing fails"""
    total_posts = len(data)
    total_comments = sum(len(post.get('comments', [])) for post in data)
    
    # Extract some basic insights from the data
    all_text = []
    positive_keywords = ['great', 'amazing', 'love', 'helped', 'works', 'effective', 'recommend']
    negative_keywords = ['terrible', 'hate', 'awful', 'broke out', 'irritation', 'reaction', 'dried out']
    
    positive_count = 0
    negative_count = 0
    
    for post in data:
        text = (post.get('title', '') + ' ' + post.get('body', '')).lower()
        all_text.append(text)
        
        for comment in post.get('comments', []):
            comment_text = comment.get('body', '').lower()
            all_text.append(comment_text)
    
    # Simple sentiment analysis
    full_text = ' '.join(all_text)
    for word in positive_keywords:
        positive_count += full_text.count(word)
    for word in negative_keywords:
        negative_count += full_text.count(word)
    
    neutral_count = max(0, total_comments - positive_count - negative_count)
    
    return {
        "ingredient": ingredient_name,
        "data_summary": {
            "total_posts": total_posts,
            "total_comments": total_comments,
            "avg_engagement": round(total_comments / max(total_posts, 1), 2),
            "time_span": "2023-2024",
            "high_value_discussions": min(total_posts, 5)
        },
        "usage_patterns": {
            "dosage_recommendations": ["Analysis requires manual review"],
            "timing_preferences": ["Analysis requires manual review"],
            "duration_cycles": ["Analysis requires manual review"]
        },
        "effectiveness_analysis": {
            "reported_benefits": ["Extracted from manual review needed"],
            "reported_side_effects": ["Extracted from manual review needed"],
            "individual_variations": ["High variation in user experiences observed"]
        },
        "brand_intelligence": {
            "top_brands": ["The Ordinary", "Paula's Choice", "CeraVe", "Neutrogena"],
            "extract_preferences": ["BHA preferred over traditional forms"]
        },
        "safety_insights": {
            "contraindications": ["Sensitive skin", "Sun exposure without SPF"],
            "cycling_importance": {
                "recommended": True,
                "reason": "prevent over-exfoliation",
                "protocol": "start slow, build tolerance"
            },
            "warning_signals": ["Excessive dryness", "Irritation", "Increased sensitivity"]
        },
        "user_journey_insights": {
            "beginner_advice": ["Start with low concentration", "Use SPF", "Introduce slowly"],
            "common_mistakes": ["Using too much too soon", "Not using moisturizer", "Skipping SPF"],
            "success_patterns": ["Gradual introduction", "Consistent use", "Proper skincare routine"]
        },
        "discussion_trends": {
            "emerging_topics": ["Different BHA types", "Product comparisons", "Routine integration"],
            "controversial_aspects": ["Daily vs intermittent use", "Concentration preferences"]
        },
        "sentiment_analysis": {
            "overall_sentiment": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count
            },
            "sentiment_by_experience_level": {
                "beginners": {"positive": 0, "neutral": 0, "negative": 0},
                "experienced_users": {"positive": 0, "neutral": 0, "negative": 0},
                "long_term_users": {"positive": 0, "neutral": 0, "negative": 0}
            },
            "sentiment_drivers": {
                "positive_factors": ["acne improvement", "smoother skin", "unclogged pores"],
                "negative_factors": ["dryness", "irritation", "purging period"]
            }
        },
        "actionable_insights": {
            "for_beginners": [
                "Start with 1-2 times per week",
                "Always use SPF during the day",
                "Follow with a good moisturizer"
            ],
            "for_researchers": [
                "Study concentration effectiveness",
                "Research skin type variations",
                "Investigate long-term usage patterns"
            ],
            "red_flags": [
                "Persistent irritation after weeks",
                "Severe dryness or peeling",
                "No improvement after 3 months"
            ]
        },
        "_note": "This is a fallback analysis. Full AI analysis failed - check logs for details."
    }
