import json
import os
from datetime import datetime

def create_beautiful_report(json_file_path):
    """Convert the fact-check JSON report into a beautiful HTML report"""
    
    # Load the JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract ingredient name for cleaner display
    ingredient_display = data['ingredient_database_info']['name']
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ingredient Analysis Report: {ingredient_display}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.2em;
            margin-bottom: 20px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            display: block;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        .claim-card {{
            border-left: 4px solid #3498db;
            background: #f8f9fa;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
        }}
        
        .claim-card.verified {{
            border-left-color: #27ae60;
            background: #d5f4e6;
        }}
        
        .claim-card.disputed {{
            border-left-color: #e74c3c;
            background: #ffeaa7;
        }}
        
        .claim-card.unverified {{
            border-left-color: #f39c12;
            background: #fef9e7;
        }}
        
        .claim-card.misleading {{
            border-left-color: #8e44ad;
            background: #f4ecf7;
        }}
        
        .claim-text {{
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .claim-reasoning {{
            color: #555;
            margin-bottom: 10px;
        }}
        
        .claim-meta {{
            display: flex;
            gap: 15px;
            font-size: 0.9em;
        }}
        
        .confidence {{
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        
        .confidence.high {{
            background: #27ae60;
            color: white;
        }}
        
        .confidence.medium {{
            background: #f39c12;
            color: white;
        }}
        
        .confidence.low {{
            background: #e74c3c;
            color: white;
        }}
        
        .risk {{
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        
        .risk.high {{
            background: #e74c3c;
            color: white;
        }}
        
        .risk.medium {{
            background: #f39c12;
            color: white;
        }}
        
        .risk.low {{
            background: #27ae60;
            color: white;
        }}
        
        .experience-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
        }}
        
        .positive {{
            border-left-color: #27ae60;
            background: #d5f4e6;
        }}
        
        .negative {{
            border-left-color: #e74c3c;
            background: #fadbd8;
        }}
        
        .subreddit-tag {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            margin: 2px;
        }}
        
        .alert {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: white;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 {ingredient_display}</h1>
            <div class="subtitle">AI-Powered Ingredient Analysis & Fact-Check Report</div>
            <div class="alert success">
                <strong>Analysis Complete!</strong> Generated from {data['data_sources']['reddit_posts']} Reddit posts and {data['data_sources']['total_claims_analyzed']} user claims
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{data['data_sources']['reddit_posts']}</span>
                <span class="stat-label">Reddit Posts</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{data['data_sources']['total_claims_analyzed']}</span>
                <span class="stat-label">Claims Analyzed</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{data['reddit_data_summary']['total_comments']}</span>
                <span class="stat-label">Comments Collected</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{len(data['reddit_data_summary']['subreddits_covered'])}</span>
                <span class="stat-label">Subreddits</span>
            </div>
        </div>
"""
    
    # Add subreddit coverage
    html_content += f"""
        <div class="section">
            <h2 class="section-title">📊 Data Sources</h2>
            <p><strong>Subreddits Covered:</strong></p>
            <div style="margin-top: 10px;">
"""
    for subreddit in data['reddit_data_summary']['subreddits_covered']:
        html_content += f'                <span class="subreddit-tag">r/{subreddit}</span>\n'
    
    html_content += """
            </div>
        </div>
"""
    
    # Parse fact-check analysis
    fact_check = data.get('fact_check_analysis', {})
    if 'raw_response' in fact_check:
        try:
            # Extract JSON from the raw response
            raw = fact_check['raw_response']
            if '```json' in raw:
                json_start = raw.find('{')
                json_end = raw.rfind('}') + 1
                fact_data = json.loads(raw[json_start:json_end])
            else:
                fact_data = json.loads(raw)
        except:
            fact_data = {}
    else:
        fact_data = fact_check
    
    # Add fact-check results
    if fact_data:
        html_content += """
        <div class="section">
            <h2 class="section-title">🔍 Fact-Check Analysis</h2>
"""
        
        # Verified claims
        if 'verified_claims' in fact_data and fact_data['verified_claims']:
            html_content += """
            <h3 style="color: #27ae60; margin-bottom: 15px;">✅ Verified Claims</h3>
"""
            for claim in fact_data['verified_claims']:
                html_content += f"""
            <div class="claim-card verified">
                <div class="claim-text">"{claim.get('claim', 'N/A')[:150]}..."</div>
                <div class="claim-reasoning">{claim.get('reasoning', 'No reasoning provided')}</div>
                <div class="claim-meta">
                    <span class="confidence {claim.get('confidence', 'medium').lower()}">{claim.get('confidence', 'Medium')} Confidence</span>
                </div>
            </div>
"""
        
        # Disputed claims
        if 'disputed_claims' in fact_data and fact_data['disputed_claims']:
            html_content += """
            <h3 style="color: #e74c3c; margin-bottom: 15px;">❌ Disputed Claims</h3>
"""
            for claim in fact_data['disputed_claims']:
                html_content += f"""
            <div class="claim-card disputed">
                <div class="claim-text">"{claim.get('claim', 'N/A')[:150]}..."</div>
                <div class="claim-reasoning">{claim.get('reasoning', 'No reasoning provided')}</div>
                <div class="claim-meta">
                    <span class="confidence {claim.get('confidence', 'medium').lower()}">{claim.get('confidence', 'Medium')} Confidence</span>
                    <span class="risk {claim.get('risk_level', 'medium').lower()}">{claim.get('risk_level', 'Medium')} Risk</span>
                </div>
            </div>
"""
        
        # Unverified claims
        if 'unverified_claims' in fact_data and fact_data['unverified_claims']:
            html_content += """
            <h3 style="color: #f39c12; margin-bottom: 15px;">⚠️ Unverified Claims</h3>
"""
            for claim in fact_data['unverified_claims']:
                html_content += f"""
            <div class="claim-card unverified">
                <div class="claim-text">"{claim.get('claim', 'N/A')[:150]}..."</div>
                <div class="claim-reasoning">{claim.get('reasoning', 'No reasoning provided')}</div>
                <div class="claim-meta">
                    <span class="confidence {claim.get('confidence', 'medium').lower()}">{claim.get('confidence', 'Medium')} Confidence</span>
                </div>
            </div>
"""
        
        # Overall assessment
        if 'overall_assessment' in fact_data:
            html_content += f"""
            <div class="alert">
                <strong>Overall Assessment:</strong> {fact_data['overall_assessment']}
            </div>
"""
        
        html_content += """
        </div>
"""
    
    # Parse user experience analysis
    user_exp = data.get('user_experience_analysis', {})
    if 'raw_response' in user_exp:
        try:
            # Extract JSON from the raw response
            raw = user_exp['raw_response']
            if '```json' in raw:
                json_start = raw.find('{')
                json_end = raw.rfind('}') + 1
                exp_data = json.loads(raw[json_start:json_end])
            else:
                exp_data = json.loads(raw)
        except:
            exp_data = {}
    else:
        exp_data = user_exp
    
    # Add user experience analysis
    if exp_data:
        html_content += """
        <div class="section">
            <h2 class="section-title">👥 User Experience Analysis</h2>
"""
        
        # Positive experiences
        if 'positive_experiences' in exp_data and exp_data['positive_experiences']:
            html_content += """
            <h3 style="color: #27ae60; margin-bottom: 15px;">😊 Positive Experiences</h3>
"""
            for exp in exp_data['positive_experiences']:
                html_content += f"""
            <div class="experience-card positive">
                <div class="claim-text">{exp.get('experience', 'N/A')}</div>
                <div class="claim-meta">
                    <span>Frequency: {exp.get('frequency', 'Unknown')}</span>
                    <span class="confidence {exp.get('credibility', 'medium').lower()}">{exp.get('credibility', 'Medium')} Credibility</span>
                </div>
            </div>
"""
        
        # Negative experiences
        if 'negative_experiences' in exp_data and exp_data['negative_experiences']:
            html_content += """
            <h3 style="color: #e74c3c; margin-bottom: 15px;">😟 Negative Experiences</h3>
"""
            for exp in exp_data['negative_experiences']:
                html_content += f"""
            <div class="experience-card negative">
                <div class="claim-text">{exp.get('experience', 'N/A')}</div>
                <div class="claim-meta">
                    <span>Frequency: {exp.get('frequency', 'Unknown')}</span>
                    <span class="risk {exp.get('severity', 'medium').lower()}">{exp.get('severity', 'Medium')} Severity</span>
                </div>
            </div>
"""
        
        # Sentiment summary
        if 'sentiment_summary' in exp_data:
            html_content += f"""
            <div class="alert">
                <strong>Sentiment Summary:</strong> {exp_data['sentiment_summary']}
            </div>
"""
        
        html_content += """
        </div>
"""
    
    # Add footer
    analysis_time = datetime.fromisoformat(data['analysis_timestamp'].replace('Z', '+00:00'))
    html_content += f"""
        <div class="footer">
            Report generated on {analysis_time.strftime('%B %d, %Y at %I:%M %p')} | 
            Powered by AI Analysis Pipeline
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    # Find the fact-check report file
    import glob
    
    fact_files = glob.glob("*_fact_check_report.json")
    if not fact_files:
        print("[ERROR] No fact-check report files found!")
        return
    
    latest_file = max(fact_files, key=os.path.getmtime)
    print(f"[BEAUTIFY] Processing: {latest_file}")
    
    # Generate beautiful HTML report
    html_content = create_beautiful_report(latest_file)
    
    # Save HTML file
    html_filename = latest_file.replace('_fact_check_report.json', '_beautiful_report.html')
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[OK] Beautiful report created: {html_filename}")
    print(f"[INFO] Open {html_filename} in your web browser to view the report!")

if __name__ == "__main__":
    main()
