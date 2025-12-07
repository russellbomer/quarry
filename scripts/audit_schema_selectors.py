#!/usr/bin/env python3
"""
Schema Selector Audit Tool

Analyzes existing schemas for brittle selectors and suggests robust alternatives.
Helps migrate to resilient selector patterns for modern frameworks.

Usage:
    python audit_schema_selectors.py examples/schemas/nyt.yml
    python audit_schema_selectors.py examples/schemas/*.yml
"""

import re
import sys
import traceback
from pathlib import Path

import yaml

# Add quarry to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from quarry.lib.selectors import (
    build_robust_selector,
)

MAX_SELECTOR_DEPTH = 4
MIN_SCHEMA_ARGS = 2


def analyze_selector(selector: str) -> dict:
    """Analyze a selector for brittleness"""
    issues = []
    suggestions = []
    severity = "ok"

    # Check for dynamic classes
    dynamic_classes = re.findall(r'\.(css-[\w-]+|emotion-[\w-]+|sc-[\w-]+)', selector)
    if dynamic_classes:
        issues.append(f"Dynamic CSS classes: {', '.join(dynamic_classes)}")
        suggestions.append("Use structural selectors instead (tag hierarchy)")
        severity = "high"

    # Check for ID patterns
    dynamic_ids = re.findall(r'#[\w-]+-\d+', selector)
    if dynamic_ids:
        issues.append(f"Dynamic IDs: {', '.join(dynamic_ids)}")
        suggestions.append("Remove ID-based selectors or use data attributes")
        severity = "high"

    # Check for deep nesting
    parts = selector.split()
    if len(parts) > MAX_SELECTOR_DEPTH:
        issues.append(f"Deep nesting: {len(parts)} levels")
        suggestions.append("Simplify to 2-3 levels for maintainability")
        if severity == "ok":
            severity = "medium"

    # Check for attribute selectors with generated values
    attr_patterns = re.findall(r'\[([^\]]+)\]', selector)
    for attr in attr_patterns:
        if any(pat in attr for pat in ['test-id', 'data-reactid', 'data-reactroot']):
            issues.append(f"React-generated attribute: {attr}")
            suggestions.append("Prefer semantic HTML attributes or structural selectors")
            if severity == "ok":
                severity = "medium"

    # Positive patterns
    good_patterns = []
    if re.search(r'\b(article|section|header|footer|nav|main)\b', selector):
        good_patterns.append("Uses semantic HTML5 tags")

    if '::attr(' in selector:
        good_patterns.append("Uses attribute extraction (stable)")

    if re.search(r'^[a-z]+(\s+[a-z]+)*(\s*::attr\([^)]+\))?$', selector.lower()):
        good_patterns.append("Pure structural selector (excellent)")

    return {
        'selector': selector,
        'severity': severity,
        'issues': issues,
        'suggestions': suggestions,
        'good_patterns': good_patterns,
        'robust_alternative': build_robust_selector(selector, ['tag'])
        if severity != 'ok'
        else None,
    }


def audit_schema(schema_path: Path) -> dict:
    """Audit a schema file for selector quality"""

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    results = {
        'path': str(schema_path),
        'job_name': schema.get('job', 'unknown'),
        'selectors': {},
        'summary': {'ok': 0, 'medium': 0, 'high': 0},
    }

    # Extract selectors from schema
    if 'selectors' in schema:
        sel_config = schema['selectors']

        # Item selector
        if 'item' in sel_config:
            analysis = analyze_selector(sel_config['item'])
            results['selectors']['item'] = analysis
            results['summary'][analysis['severity']] += 1

        # Field selectors
        if 'fields' in sel_config:
            results['selectors']['fields'] = {}
            for field_name, field_selector in sel_config['fields'].items():
                if isinstance(field_selector, str):
                    analysis = analyze_selector(field_selector)
                    results['selectors']['fields'][field_name] = analysis
                    results['summary'][analysis['severity']] += 1

    return results


def print_audit_results(results: dict):
    """Print audit results in a readable format"""

    print(f"\n{'=' * 80}")
    print(f"Schema: {results['path']}")
    print(f"Job: {results['job_name']}")
    print(f"{'=' * 80}")

    summary = results['summary']
    total = sum(summary.values())

    if total == 0:
        print("\n⚠️  No selectors found in schema")
        return

    # Print summary
    print(f"\n📊 Summary: {total} selectors analyzed")
    print(f"   ✅ OK:     {summary['ok']}")
    print(f"   ⚠️  Medium: {summary['medium']}")
    print(f"   🔴 High:   {summary['high']}")

    # Item selector
    if 'item' in results['selectors']:
        item = results['selectors']['item']
        print("\n🎯 Item Selector")
        print_selector_analysis(item)

    # Field selectors
    if 'fields' in results['selectors']:
        print("\n📝 Field Selectors")
        for field_name, analysis in results['selectors']['fields'].items():
            print(f"\n  Field: {field_name}")
            print_selector_analysis(analysis, indent=4)

    # Overall recommendation
    if summary['high'] > 0:
        print(
            "\n🔴 RECOMMENDATION: Update "
            f"{summary['high']} high-priority selectors before deploying"
        )
    elif summary['medium'] > 0:
        print(
            f"\n⚠️  RECOMMENDATION: Consider updating {summary['medium']} medium-priority selectors"
        )
    else:
        print("\n✅ SCHEMA LOOKS GOOD: All selectors use resilient patterns")


def print_selector_analysis(analysis: dict, indent: int = 2):
    """Print individual selector analysis"""
    prefix = ' ' * indent

    severity_emoji = {
        'ok': '✅',
        'medium': '⚠️',
        'high': '🔴',
    }

    print(f"{prefix}{severity_emoji[analysis['severity']]} {analysis['selector']}")

    if analysis['good_patterns']:
        for pattern in analysis['good_patterns']:
            print(f"{prefix}  ✓ {pattern}")

    if analysis['issues']:
        for issue in analysis['issues']:
            print(f"{prefix}  ✗ {issue}")

    if analysis['suggestions']:
        print(f"{prefix}  💡 Suggestions:")
        for suggestion in analysis['suggestions']:
            print(f"{prefix}     - {suggestion}")

    if analysis['robust_alternative']:
        print(f"{prefix}  🔧 Robust alternative: {analysis['robust_alternative']}")


def generate_migration_report(all_results: list[dict]) -> str:
    """Generate markdown migration report"""

    report = ["# Schema Selector Migration Report\n"]
    report.append(f"Analyzed {len(all_results)} schema(s)\n")

    # Summary table
    report.append("## Summary\n")
    report.append("| Schema | Total | OK | Medium | High |")
    report.append("|--------|-------|----|----|------|")

    for result in all_results:
        s = result['summary']
        total = sum(s.values())
        report.append(
            f"| {Path(result['path']).name} | {total} | {s['ok']} | {s['medium']} | {s['high']} |"
        )

    report.append("\n## Detailed Findings\n")

    for result in all_results:
        if result['summary']['high'] == 0 and result['summary']['medium'] == 0:
            continue

        report.append(f"### {Path(result['path']).name}\n")

        # List problematic selectors
        if 'item' in result['selectors']:
            item = result['selectors']['item']
            if item['severity'] != 'ok':
                report.append(f"**Item selector:** `{item['selector']}`")
                if item['robust_alternative']:
                    report.append(f"  - Suggested: `{item['robust_alternative']}`")
                report.append("")

        if 'fields' in result['selectors']:
            for field_name, analysis in result['selectors']['fields'].items():
                if analysis['severity'] != 'ok':
                    report.append(f"**Field `{field_name}`:** `{analysis['selector']}`")
                    for issue in analysis['issues']:
                        report.append(f"  - ⚠️ {issue}")
                    if analysis['robust_alternative']:
                        report.append(f"  - Suggested: `{analysis['robust_alternative']}`")
                    report.append("")

    return '\n'.join(report)


def main():
    if len(sys.argv) < MIN_SCHEMA_ARGS:
        print("Usage: python audit_schema_selectors.py <schema.yml> [schema2.yml ...]")
        print("\nExample:")
        print("  python audit_schema_selectors.py examples/schemas/nyt.yml")
        print("  python audit_schema_selectors.py examples/schemas/*.yml")
        sys.exit(1)

    schema_paths = [Path(p) for p in sys.argv[1:]]
    all_results = []

    for schema_path in schema_paths:
        if not schema_path.exists():
            print(f"⚠️  Schema not found: {schema_path}")
            continue

        try:
            results = audit_schema(schema_path)
            all_results.append(results)
            print_audit_results(results)

        except Exception as e:
            print(f"\n❌ Error analyzing {schema_path}: {e}")
            traceback.print_exc()

    # Generate migration report
    if len(all_results) > 1:
        print(f"\n{'=' * 80}")
        print("MIGRATION REPORT")
        print(f"{'=' * 80}")

        report = generate_migration_report(all_results)

        # Save report
        report_path = Path('schema_migration_report.md')
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\n📄 Detailed report saved to: {report_path}")


if __name__ == "__main__":
    main()
