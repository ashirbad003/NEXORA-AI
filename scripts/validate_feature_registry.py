import re
import sys
import os

REQUIRED_FIELDS = [
    "- **Category:**",
    "- **Description:**",
    "- **Frontend Requirements:**",
    "- **Backend Requirements:**",
    "- **Database Requirements:**",
    "- **API Requirements:**",
    "- **Security Requirements:**",
    "- **Acceptance Criteria:**",
    "- **Test Cases:**",
    "- **Status:**",
    "- **Dependencies:**"
]

MODULE_CODES = [
    "BRAIN", "COPILOT", "ASSESS", "CODING", "CODEREV", "INTERVIEW",
    "LEARN", "REVISION", "DSAVIZ", "RESUME", "GITHUB", "JOB",
    "PLACE", "ADMIN", "PEER", "NOTIF", "SEC", "SYS"
]

def parse_feature_registry(file_path):
    if not os.path.exists(file_path):
        return None, [f"File not found: {file_path}"]
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    errors = []
    features = {}
    
    # Split by feature header
    sections = re.split(r'\n(?=### FEAT-\d{3}: )', content)
    
    # First section is document header
    header = sections[0]
    feature_sections = sections[1:]
    
    for sec in feature_sections:
        lines = sec.strip().split("\n")
        header_line = lines[0]
        m = re.match(r'### (FEAT-(\d{3})): (.*)', header_line)
        if not m:
            errors.append(f"Invalid feature header format: {header_line}")
            continue
            
        full_id = m.group(1)
        num_id = int(m.group(2))
        title = m.group(3).strip()
        
        if full_id in features:
            errors.append(f"Duplicate feature ID detected: {full_id}")
            
        parsed_fields = {}
        for req_field in REQUIRED_FIELDS:
            field_m = re.search(re.escape(req_field) + r'\s+(.*)', sec)
            if not field_m or not field_m.group(1).strip():
                errors.append(f"Feature {full_id} missing or empty field: {req_field}")
            else:
                parsed_fields[req_field] = field_m.group(1).strip()
                
        features[full_id] = {
            "num_id": num_id,
            "title": title,
            "fields": parsed_fields,
            "raw": sec
        }
        
    return features, errors

def validate_traceability_matrix(file_path, registered_ids):
    if not os.path.exists(file_path):
        return [f"File not found: {file_path}"]
        
    errors = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = [line.strip() for line in content.split("\n") if line.strip().startswith("| FEAT-")]
    matrix_ids = set()
    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if not parts:
            continue
        fid = parts[0]
        if fid in matrix_ids:
            errors.append(f"Traceability matrix contains duplicate ID: {fid}")
        matrix_ids.add(fid)
        
    missing_in_matrix = registered_ids - matrix_ids
    extra_in_matrix = matrix_ids - registered_ids
    
    if missing_in_matrix:
        errors.append(f"Missing from Traceability Matrix: {sorted(list(missing_in_matrix))}")
    if extra_in_matrix:
        errors.append(f"Extraneous in Traceability Matrix: {sorted(list(extra_in_matrix))}")
        
    return errors

def validate_implementation_status(file_path, registered_ids):
    if not os.path.exists(file_path):
        return [f"File not found: {file_path}"]
        
    errors = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = [line.strip() for line in content.split("\n") if line.strip().startswith("| FEAT-")]
    status_ids = set()
    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if not parts:
            continue
        fid = parts[0]
        if fid in status_ids:
            errors.append(f"Implementation status contains duplicate ID: {fid}")
        status_ids.add(fid)
        
    missing = registered_ids - status_ids
    extra = status_ids - registered_ids
    if missing:
        errors.append(f"Missing from Implementation Status: {sorted(list(missing))}")
    if extra:
        errors.append(f"Extraneous in Implementation Status: {sorted(list(extra))}")
        
    return errors

def validate_dependency_map(file_path, registered_ids):
    if not os.path.exists(file_path):
        return [f"File not found: {file_path}"]
        
    errors = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check each feature's declared dependencies
    # Also verify that declared dependencies reference valid IDs
    dep_lines = [l.strip() for l in content.split("\n") if l.strip().startswith("- **FEAT-")]
    dep_ids = set()
    for l in dep_lines:
        m = re.match(r'- \*\*(FEAT-\d{3})', l)
        if m:
            dep_ids.add(m.group(1))
            
    missing = registered_ids - dep_ids
    if missing:
        errors.append(f"Missing from Dependency Map entries: {sorted(list(missing))}")
        
    return errors

def main():
    print("=== NEXORA AI: INDEPENDENT FEATURE REGISTRY AUDIT ===")
    registry_file = "docs/MASTER_FEATURE_REGISTRY.md"
    features, parse_errors = parse_feature_registry(registry_file)
    
    if parse_errors:
        print(f"Registry Parse Errors ({len(parse_errors)}):")
        for err in parse_errors[:10]:
            print(f"  - {err}")
        if len(parse_errors) > 10:
            print(f"  ... and {len(parse_errors)-10} more.")
            
    if not features:
        print("FATAL: No features parsed from registry.")
        sys.exit(1)
        
    total_features = len(features)
    print(f"Total parsed features: {total_features}")
    
    # 1. Exact count check
    if total_features != 346:
        print(f"ERROR: Expected exactly 346 features, got {total_features}")
    else:
        print("PASSED: Exactly 346 registered features.")
        
    # 2. Sequence continuity check (FEAT-001 through FEAT-346)
    expected_ids = {f"FEAT-{i:03d}" for i in range(1, 347)}
    actual_ids = set(features.keys())
    
    missing_ids = expected_ids - actual_ids
    unexpected_ids = actual_ids - expected_ids
    
    if missing_ids:
        print(f"ERROR: Missing expected feature IDs: {sorted(list(missing_ids))}")
    else:
        print("PASSED: Zero missing feature IDs in range FEAT-001 through FEAT-346.")
        
    if unexpected_ids:
        print(f"ERROR: Unexpected feature IDs: {sorted(list(unexpected_ids))}")
    else:
        print("PASSED: Zero unexpected feature IDs.")
        
    # 3. Duplicate titles check
    titles = [f["title"].lower() for f in features.values()]
    seen_titles = set()
    duplicate_titles = []
    for t in titles:
        if t in seen_titles:
            duplicate_titles.append(t)
        seen_titles.add(t)
    if duplicate_titles:
        print(f"WARNING: Potential duplicate feature titles detected ({len(duplicate_titles)}): {duplicate_titles}")
    else:
        print("PASSED: Zero duplicate feature titles detected.")
        
    # 4. Traceability Matrix Audit
    matrix_errors = validate_traceability_matrix("docs/FEATURE_TRACEABILITY_MATRIX.md", actual_ids)
    if matrix_errors:
        print(f"Traceability Matrix Errors ({len(matrix_errors)}):")
        for err in matrix_errors[:5]:
            print(f"  - {err}")
    else:
        print("PASSED: Traceability Matrix 100% matches registered features.")
        
    # 5. Implementation Status Audit
    status_errors = validate_implementation_status("docs/FEATURE_IMPLEMENTATION_STATUS.md", actual_ids)
    if status_errors:
        print(f"Implementation Status Errors ({len(status_errors)}):")
        for err in status_errors[:5]:
            print(f"  - {err}")
    else:
        print("PASSED: Implementation Status 100% matches registered features.")
        
    # 6. Dependency Map Audit
    dep_errors = validate_dependency_map("docs/FEATURE_DEPENDENCY_MAP.md", actual_ids)
    if dep_errors:
        print(f"Dependency Map Errors ({len(dep_errors)}):")
        for err in dep_errors[:5]:
            print(f"  - {err}")
    else:
        print("PASSED: Dependency Map 100% covers all registered features.")
        
    # 7. Check Dependency Targets Validity
    # All dependencies like FEAT-311, FEAT-313 must exist
    broken_deps = []
    for fid, f in features.items():
        dep_str = f["fields"].get("- **Dependencies:**", "")
        referenced_fids = re.findall(r'FEAT-\d{3}', dep_str)
        for ref in referenced_fids:
            if ref not in actual_ids:
                broken_deps.append((fid, ref))
    if broken_deps:
        print(f"ERROR: Broken dependency references detected ({len(broken_deps)}): {broken_deps}")
    else:
        print("PASSED: All referenced feature dependencies exist in registry.")
        
    all_passed = (
        not parse_errors and 
        total_features == 346 and 
        not missing_ids and 
        not unexpected_ids and 
        not duplicate_titles and 
        not matrix_errors and 
        not status_errors and 
        not dep_errors and 
        not broken_deps
    )
    
    if all_passed:
        print("\n>>> INDEPENDENT FEATURE REGISTRY AUDIT: 100% VERIFIED AND PASSING <<<")
        return 0
    else:
        print("\n>>> INDEPENDENT FEATURE REGISTRY AUDIT: FAILED QUALITY GATES <<<")
        return 1

if __name__ == "__main__":
    sys.exit(main())
