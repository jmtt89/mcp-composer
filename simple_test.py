import sys
print("Test starts")

# Test basic imports
try:
    from src.composer import Composer
    print("✓ Composer imported successfully")
except Exception as e:
    print(f"✗ Error importing Composer: {e}")
    
print("Test complete")
