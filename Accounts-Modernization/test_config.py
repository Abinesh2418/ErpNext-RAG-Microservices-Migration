#!/usr/bin/env python3
"""
Test script to verify .env file is being loaded correctly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.config import Config

def test_config():
    """Test configuration loading"""
    print("\n" + "="*70)
    print("  TESTING CONFIGURATION LOADING FROM .ENV FILE")
    print("="*70 + "\n")
    
    config = Config()
    
    # Print paths
    print("📁 Directory Paths:")
    print(f"   Project Root: {config.project_root}")
    print(f"   Root Dir (.env location): {config.root_dir}")
    print(f"   .env file exists: {(config.root_dir / '.env').exists()}")
    print()
    
    # Print all loaded configuration
    print("⚙️  Loaded Configuration:")
    all_config = config.get_all()
    
    # Group by category
    ai_config = {k: v for k, v in all_config.items() if k in [
        'GROQ_API_KEY', 'GROQ_MODEL', 'EMBEDDING_MODEL', 
        'MAX_CONTEXT_TOKENS', 'AI_TEMPERATURE'
    ]}
    
    validation_config = {k: v for k, v in all_config.items() if k in [
        'ENABLE_SYNTAX_CHECK', 'ENABLE_COMPILE_CHECK', 
        'MAX_RETRY_ATTEMPTS', 'MAX_FILE_SIZE_MB'
    ]}
    
    logging_config = {k: v for k, v in all_config.items() if k in ['LOG_LEVEL']}
    
    dirs_config = {k: v for k, v in all_config.items() if k in [
        'LOG_DIR', 'RESULTS_DIR', 'MODERN_DIR', 'TESTS_DIR'
    ]}
    
    # AI Configuration
    print("\n   🤖 AI Configuration:")
    for key, value in ai_config.items():
        if key == 'GROQ_API_KEY':
            # Mask API key for security
            masked = value[:10] + "..." + value[-5:] if len(value) > 15 else "NOT_SET"
            print(f"      {key}: {masked}")
        else:
            print(f"      {key}: {value}")
    
    # Validation Configuration
    print("\n   ✅ Validation Configuration:")
    for key, value in validation_config.items():
        print(f"      {key}: {value}")
    
    # Logging Configuration
    print("\n   📝 Logging Configuration:")
    for key, value in logging_config.items():
        print(f"      {key}: {value}")
    
    # Directories
    print("\n   📂 Directories:")
    for key, value in dirs_config.items():
        print(f"      {key}: {value}")
    
    # Verification
    print("\n" + "="*70)
    print("  VERIFICATION RESULTS")
    print("="*70 + "\n")
    
    checks = []
    
    # Check GROQ_API_KEY
    groq_key = config.get('GROQ_API_KEY')
    if groq_key and len(groq_key) > 10:
        checks.append(("✅", "GROQ_API_KEY is set"))
    else:
        checks.append(("❌", "GROQ_API_KEY is NOT set or invalid"))
    
    # Check GROQ_MODEL
    groq_model = config.get('GROQ_MODEL')
    if groq_model == 'llama-3.3-70b-versatile':
        checks.append(("✅", f"GROQ_MODEL: {groq_model}"))
    else:
        checks.append(("⚠️", f"GROQ_MODEL: {groq_model} (unexpected value)"))
    
    # Check MAX_CONTEXT_TOKENS
    max_tokens = config.get('MAX_CONTEXT_TOKENS')
    if max_tokens == 8000:
        checks.append(("✅", f"MAX_CONTEXT_TOKENS: {max_tokens}"))
    else:
        checks.append(("⚠️", f"MAX_CONTEXT_TOKENS: {max_tokens} (expected 8000)"))
    
    # Check AI_TEMPERATURE
    temp = config.get('AI_TEMPERATURE')
    if temp == 0.7:
        checks.append(("✅", f"AI_TEMPERATURE: {temp}"))
    else:
        checks.append(("⚠️", f"AI_TEMPERATURE: {temp} (expected 0.7)"))
    
    # Check ENABLE_SYNTAX_CHECK
    syntax_check = config.get('ENABLE_SYNTAX_CHECK')
    if syntax_check is True:
        checks.append(("✅", f"ENABLE_SYNTAX_CHECK: {syntax_check}"))
    else:
        checks.append(("⚠️", f"ENABLE_SYNTAX_CHECK: {syntax_check} (expected True)"))
    
    # Check directories exist
    for dir_key in ['LOG_DIR', 'RESULTS_DIR', 'MODERN_DIR', 'TESTS_DIR']:
        dir_path = config.get(dir_key)
        if dir_path and dir_path.exists():
            checks.append(("✅", f"{dir_key} exists: {dir_path.name}/"))
        else:
            checks.append(("❌", f"{dir_key} does NOT exist"))
    
    # Print checks
    for status, message in checks:
        print(f"   {status} {message}")
    
    # Summary
    print("\n" + "="*70)
    success_count = sum(1 for status, _ in checks if status == "✅")
    total_count = len(checks)
    
    if success_count == total_count:
        print("  ✅ ALL CHECKS PASSED - Configuration loaded successfully!")
    else:
        print(f"  ⚠️  {success_count}/{total_count} checks passed")
        print("  Review the checks above and verify your .env file")
    print("="*70 + "\n")

if __name__ == '__main__':
    try:
        test_config()
    except Exception as e:
        print(f"\n❌ Error testing configuration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
