#!/usr/bin/env python3
"""
Simple script to compare content similarity between generated guides.
Uses basic text analysis to identify common phrases and calculate similarity percentages.
"""

import json
import re
from pathlib import Path
from collections import Counter

def clean_text(text):
    """Clean text for comparison - remove HTML tags, normalize whitespace"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove extra formatting
    text = text.replace('---', '').replace('**', '').replace('##', '').replace('###', '')
    return text.strip().lower()

def extract_phrases(text, min_length=3, max_length=8):
    """Extract phrases of specified word length"""
    words = text.split()
    phrases = []

    for length in range(min_length, max_length + 1):
        for i in range(len(words) - length + 1):
            phrase = ' '.join(words[i:i + length])
            phrases.append(phrase)

    return phrases

def calculate_similarity(text1, text2):
    """Calculate similarity percentage between two texts"""
    phrases1 = set(extract_phrases(clean_text(text1)))
    phrases2 = set(extract_phrases(clean_text(text2)))

    if not phrases1 or not phrases2:
        return 0

    intersection = phrases1.intersection(phrases2)
    union = phrases1.union(phrases2)

    similarity = len(intersection) / len(union) * 100
    return similarity

def find_common_phrases(texts, min_occurrence=3):
    """Find phrases that appear in multiple guides"""
    phrase_counts = Counter()

    for text in texts:
        phrases = set(extract_phrases(clean_text(text)))
        for phrase in phrases:
            phrase_counts[phrase] += 1

    # Only return phrases that appear in multiple guides
    common_phrases = {phrase: count for phrase, count in phrase_counts.items() if count >= min_occurrence}
    return sorted(common_phrases.items(), key=lambda x: x[1], reverse=True)

def analyze_guides():
    """Analyze similarity between generated guides"""
    output_dir = Path(__file__).parent / "dist" / "mega-guides-improved"

    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return

    # Load all JSON files
    guides = []
    for json_file in output_dir.glob("mega_guide_*-improved.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                guides.append({
                    'filename': json_file.name,
                    'title': data['title'],
                    'content': data['content'],
                    'word_count': data['word_count']
                })
        except Exception as e:
            print(f"❌ Error loading {json_file}: {e}")

    if not guides:
        print("❌ No guides found to analyze")
        return

    print(f"📊 Analyzing {len(guides)} guides for content similarity\n")

    # Basic info
    total_words = sum(g['word_count'] for g in guides)
    print(f"📈 Total words across all guides: {total_words:,}")
    print(f"📈 Average words per guide: {total_words // len(guides):,}\n")

    # Extract all content texts
    contents = [g['content'] for g in guides]

    # Find common phrases
    print("🔍 Common phrases appearing in multiple guides:")
    common_phrases = find_common_phrases(contents, min_occurrence=2)

    for phrase, count in common_phrases[:20]:  # Top 20
        print(f"  • \"{phrase}\" - appears in {count}/{len(guides)} guides")

    # Similarity matrix
    print(f"\n📊 Content Similarity Matrix (%):")
    print("Guide" + " " * 50 + "| Similarity")
    print("-" * 70)

    total_similarity = 0
    comparison_count = 0

    for i, guide1 in enumerate(guides):
        for j, guide2 in enumerate(guides[i+1:], i+1):
            similarity = calculate_similarity(guide1['content'], guide2['content'])
            total_similarity += similarity
            comparison_count += 1

            title1 = guide1['title'][:40] + "..." if len(guide1['title']) > 40 else guide1['title']
            title2 = guide2['title'][:40] + "..." if len(guide2['title']) > 40 else guide2['title']

            print(f"{title1:<45} | {title2:<45} | {similarity:.1f}%")

    if comparison_count > 0:
        avg_similarity = total_similarity / comparison_count
        print(f"\n📈 Average similarity across all comparisons: {avg_similarity:.1f}%")

        if avg_similarity > 70:
            print("⚠️  HIGH SIMILARITY - Guides may be too similar for SEO")
        elif avg_similarity > 50:
            print("⚠️  MODERATE SIMILARITY - Some content overlap detected")
        else:
            print("✅ GOOD DIVERSITY - Guides have acceptable uniqueness")

if __name__ == "__main__":
    analyze_guides()