import os
import sys

def test_phase_0_deliverables():
    required_files = [
        "README.md",
        "docs/PROJECT_ARCHITECTURE.md",
        "docs/PHASED_DEVELOPMENT_PLAN.md",
        "docs/MASTER_FEATURE_REGISTRY.md",
        "docs/FEATURE_TRACEABILITY_MATRIX.md",
        "docs/FEATURE_IMPLEMENTATION_STATUS.md",
        "docs/FEATURE_DEPENDENCY_MAP.md"
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
        else:
            size = os.path.getsize(f)
            if size == 0:
                missing.append(f"{f} (empty file)")
                
    if missing:
        print(f"FAILED: Missing or empty files: {missing}")
        sys.exit(1)
        
    # Verify feature registry contains at least 300 features
    with open("docs/MASTER_FEATURE_REGISTRY.md", "r", encoding="utf-8") as f:
        content = f.read()
        count = content.count("### FEAT-")
        if count < 300:
            print(f"FAILED: Feature count is {count}, expected >= 300")
            sys.exit(1)
        print(f"PASSED: Feature count in registry = {count}")
        
    print("ALL PHASE 0 VERIFICATION GATES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase_0_deliverables()
