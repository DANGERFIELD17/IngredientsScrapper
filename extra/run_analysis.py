import subprocess
import sys
import os
import time
import glob

def run_command(command, description):
    """Run a command and handle output"""
    print(f"\n🔧 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            return True
        else:
            print(f"❌ {description} failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_prerequisites():
    """Check if required files exist"""
    required_files = [
        "llama.py",
        "fact_checker.py", 
        "all_ingredients_merged[1].json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def find_reddit_data_files():
    """Find generated Reddit data files"""
    return glob.glob("*_all_comments.json")

def main():
    print("🚀 Automated Ingredient Analysis Pipeline")
    print("=" * 60)
    
    # Check prerequisites
    print("📋 Checking prerequisites...")
    if not check_prerequisites():
        print("\n💡 Make sure all required files are in the current directory:")
        print("   - llama.py (Reddit scraper)")
        print("   - fact_checker.py (Fact checking script)")
        print("   - all_ingredients_merged[1].json (Ingredient database)")
        sys.exit(1)
    
    # Step 1: Run Reddit scraper
    print(f"\n⏰ Starting analysis pipeline at {time.strftime('%H:%M:%S')}")
    
    if not run_command("python llama.py", "Running Reddit data collection (llama.py)"):
        print("❌ Reddit data collection failed. Cannot proceed.")
        sys.exit(1)
    
    # Wait a moment for file system
    time.sleep(2)
    
    # Check if Reddit data was generated
    reddit_files = find_reddit_data_files()
    if not reddit_files:
        print("❌ No Reddit data files were generated. Check llama.py output.")
        sys.exit(1)
    
    print(f"✅ Generated Reddit data files: {reddit_files}")
    
    # Step 2: Run fact checker
    if not run_command("python fact_checker.py", "Running AI fact-checking analysis"):
        print("❌ Fact-checking analysis failed.")
        sys.exit(1)
    
    # Step 3: Show results
    print(f"\n🎉 ANALYSIS PIPELINE COMPLETE!")
    print("=" * 50)
    
    # List all generated files
    analysis_files = glob.glob("*_fact_check_report.json")
    reddit_files = glob.glob("*_all_comments.json")
    
    print(f"📂 Generated Files:")
    print(f"   Reddit Data: {reddit_files}")
    print(f"   Fact-Check Reports: {analysis_files}")
    
    if analysis_files:
        latest_report = max(analysis_files, key=os.path.getmtime)
        print(f"\n📊 Latest Report: {latest_report}")
        print("💡 Open this file to view your ingredient analysis!")
    
    print(f"\n⏰ Pipeline completed at {time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
