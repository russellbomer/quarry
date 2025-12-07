#!/usr/bin/env python3
"""Profile framework detection performance."""

import time
from pathlib import Path

from bs4 import BeautifulSoup

from quarry.framework_profiles import (
    FRAMEWORK_PROFILES,
    detect_all_frameworks,
    detect_framework,
)

HEADER_WIDTH = 80
SLOW_THRESHOLD_MS = 1.0
GOOD_THRESHOLD_MS = 0.5
LARGE_REGISTRY_THRESHOLD = 15


def load_fixtures() -> dict[str, str]:
    """Load test fixtures."""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"

    fixtures = {}
    for fixture_file in fixtures_dir.glob("*.html"):
        fixtures[fixture_file.stem] = fixture_file.read_text()

    return fixtures


def profile_detection(html: str, name: str, iterations: int = 100) -> dict:
    """Profile framework detection performance."""
    # Warm up
    detect_framework(html)

    # Time single detection
    start = time.perf_counter()
    for _ in range(iterations):
        detect_framework(html)
    end = time.perf_counter()

    single_time = (end - start) / iterations * 1000  # ms

    # Time all frameworks detection
    start = time.perf_counter()
    for _ in range(iterations):
        detect_all_frameworks(html)
    end = time.perf_counter()

    all_time = (end - start) / iterations * 1000  # ms

    # Get detection results
    framework = detect_framework(html)
    all_frameworks = detect_all_frameworks(html)

    return {
        "name": name,
        "html_size": len(html),
        "single_detection_ms": round(single_time, 3),
        "all_detection_ms": round(all_time, 3),
        "detected_framework": framework.name if framework else None,
        "all_frameworks": [(f.name, score) for f, score in all_frameworks[:3]],
        "num_profiles": len(FRAMEWORK_PROFILES),
    }


def profile_selector_generation(html: str, name: str, iterations: int = 100) -> dict:
    """Profile selector generation performance."""
    soup = BeautifulSoup(html, "html.parser")
    item = soup.find("div") or soup.find("tr") or soup.find("article")

    if not item:
        return {"name": name, "error": "No item element found"}

    framework = detect_framework(html, item)
    if not framework:
        return {"name": name, "error": "No framework detected"}

    # Time selector generation
    field_types = ["title", "link", "date", "description", "price", "image"]

    start = time.perf_counter()
    for _ in range(iterations):
        for field_type in field_types:
            framework.generate_field_selector(item, field_type)
    end = time.perf_counter()

    selector_time = (end - start) / iterations / len(field_types) * 1000  # ms per field

    return {
        "name": name,
        "framework": framework.name,
        "selector_generation_ms": round(selector_time, 3),
        "field_types_tested": len(field_types),
    }


def print_banner(title: str, border_char: str = "=") -> None:
    """Print a banner with consistent styling."""
    print(border_char * HEADER_WIDTH)
    print(title)
    print(border_char * HEADER_WIDTH)


def run_detection_benchmarks(fixtures: dict[str, str]) -> list[dict]:
    """Run detection benchmarks and print results."""
    print("-" * HEADER_WIDTH)
    print("Framework Detection Performance")
    print("-" * HEADER_WIDTH)
    print(f"{'Fixture':<20} {'Size':<10} {'Single (ms)':<15} {'All (ms)':<15} {'Detected':<20}")
    print("-" * HEADER_WIDTH)

    results: list[dict] = []
    for name, html in sorted(fixtures.items()):
        result = profile_detection(html, name)
        results.append(result)

        detected = result.get('detected_framework') or 'None'
        print(
            f"{result['name']:<20} "
            f"{result['html_size']:<10} "
            f"{result['single_detection_ms']:<15.3f} "
            f"{result['all_detection_ms']:<15.3f} "
            f"{detected:<20}"
        )

    return results


def run_selector_benchmarks(fixtures: dict[str, str]) -> list[dict]:
    """Run selector generation benchmarks and print results."""
    print("\n" + "-" * HEADER_WIDTH)
    print("Selector Generation Performance")
    print("-" * HEADER_WIDTH)
    print(f"{'Fixture':<20} {'Framework':<20} {'Per Field (ms)':<15}")
    print("-" * HEADER_WIDTH)

    results: list[dict] = []
    for name, html in sorted(fixtures.items()):
        result = profile_selector_generation(html, name)
        results.append(result)

        if "error" in result:
            print(f"{result['name']:<20} {result['error']:<40}")
        else:
            print(
                f"{result['name']:<20} "
                f"{result['framework']:<20} "
                f"{result['selector_generation_ms']:<15.3f}"
            )

    return results


def summarize_results(
    detection_results: list[dict], selector_results: list[dict]
) -> float | None:
    """Print summary statistics and return avg single detection time."""
    print("\n" + "=" * HEADER_WIDTH)
    print("Summary Statistics")
    print("=" * HEADER_WIDTH)

    avg_single: float | None = None

    valid_detection = [r for r in detection_results if "error" not in r]
    if valid_detection:
        avg_single = sum(r["single_detection_ms"] for r in valid_detection) / len(
            valid_detection
        )
        avg_all = sum(r["all_detection_ms"] for r in valid_detection) / len(valid_detection)

        print("\nDetection Performance:")
        print(f"  Average single framework: {avg_single:.3f} ms")
        print(f"  Average all frameworks:   {avg_all:.3f} ms")
        print(f"  Per-profile overhead:     {avg_single / len(FRAMEWORK_PROFILES):.3f} ms")

    valid_selector = [r for r in selector_results if "error" not in r]
    if valid_selector:
        avg_selector = sum(r["selector_generation_ms"] for r in valid_selector) / len(
            valid_selector
        )
        print("\nSelector Generation:")
        print(f"  Average per field: {avg_selector:.3f} ms")

    return avg_single


def recommend_optimizations(avg_single: float | None) -> None:
    """Print optimization recommendations based on average timing."""
    print("\n" + "=" * HEADER_WIDTH)
    print("Optimization Recommendations")
    print("=" * HEADER_WIDTH)

    if avg_single is None:
        print("\n⚠️  No detection benchmarks available")
        return

    if avg_single > SLOW_THRESHOLD_MS:
        print("\n⚠️  Detection is slow (>1ms per page)")
        print("   Consider:")
        print("   - Add regex compilation caching")
        print("   - Add lazy profile loading")
        print("   - Optimize detect() methods")
    elif avg_single > GOOD_THRESHOLD_MS:
        print("\n✅ Detection performance is good (0.5-1ms)")
        print("   Minor optimizations possible:")
        print("   - Cache compiled regexes")
        print("   - Consider lazy loading for rarely-used profiles")
    else:
        print("\n✅ Detection performance is excellent (<0.5ms)")


def warn_on_large_registry() -> None:
    """Warn if the profile registry is getting large."""
    if len(FRAMEWORK_PROFILES) > LARGE_REGISTRY_THRESHOLD:
        print("\n📊 Large profile registry detected")
        print(f"   {len(FRAMEWORK_PROFILES)} profiles registered")
        print("   Consider categorization or lazy loading as registry grows")


def main():
    """Run profiling benchmarks."""
    print_banner("Framework Detection Performance Profile")

    fixtures = load_fixtures()
    print(f"\nLoaded {len(fixtures)} test fixtures")
    print(f"Testing against {len(FRAMEWORK_PROFILES)} framework profiles\n")

    detection_results = run_detection_benchmarks(fixtures)
    selector_results = run_selector_benchmarks(fixtures)
    avg_single = summarize_results(detection_results, selector_results)
    recommend_optimizations(avg_single)
    warn_on_large_registry()
    print("\n" + "=" * HEADER_WIDTH)


if __name__ == "__main__":
    main()
