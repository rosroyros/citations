#!/usr/bin/env python3
"""
Human Review CLI for PSEO content
Interactive command-line interface for reviewing LLM-reviewed pages
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class HumanReviewCLI:
    """Interactive CLI for human review of generated content"""

    def __init__(self, review_dir: str = "content/review_queue"):
        """Initialize CLI with directory paths"""
        self.review_dir = Path(review_dir)
        self.review_dir.mkdir(exist_ok=True)
        self.approved_dir = Path("content/approved")
        self.approved_dir.mkdir(exist_ok=True)
        self.rejected_dir = Path("content/rejected")
        self.rejected_dir.mkdir(exist_ok=True)

    def run(self):
        """Main CLI loop"""
        while True:
            pages = self._get_pending_pages()

            if not pages:
                print("\n✅ All pages reviewed!")
                print(f"Approved: {len(list(self.approved_dir.glob('*')))}")
                print(f"Rejected: {len(list(self.rejected_dir.glob('*')))}")
                break

            self._show_menu(pages)
            choice = input("\n> ").strip()

            if choice.lower() == 'q':
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(pages):
                self._review_page(pages[int(choice) - 1])
            elif choice.lower() == 's':
                continue
            else:
                print("Invalid choice. Please try again.")

    def _get_pending_pages(self) -> List[Dict]:
        """Get list of pages pending review"""
        pages = []

        for page_file in self.review_dir.glob("*.json"):
            try:
                page_data = json.loads(page_file.read_text())
                pages.append({
                    "file": page_file,
                    "title": page_data.get("title", page_file.stem),
                    "type": page_data.get("page_type", "unknown"),
                    "word_count": page_data.get("word_count", 0),
                    "llm_verdict": page_data.get("llm_review", {}).get("overall_verdict", "UNKNOWN"),
                    "issues_count": len(page_data.get("llm_review", {}).get("issues_found", []))
                })
            except Exception as e:
                print(f"Error reading {page_file}: {e}")

        return pages

    def _show_menu(self, pages: List[Dict]):
        """Show menu of pending pages"""
        print(f"\n=== Pages Pending Review ({len(pages)} pages) ===\n")

        for i, page in enumerate(pages, 1):
            status_icon = "✓" if page["llm_verdict"] == "PASS" else "⚠"
            print(f"[{i}] {page['title']} ({page['type']})")
            print(f"    {status_icon} LLM: {page['llm_verdict']} | {page['word_count']:,} words | {page['issues_count']} issues")

        print("\nCommands:")
        print("[number] Review now  [s] Show all  [q] Quit")

    def _review_page(self, page: Dict):
        """Review individual page"""
        page_data = json.loads(page["file"].read_text())
        llm_review = page_data.get("llm_review", {})

        while True:
            self._show_page_overview(page, page_data, llm_review)
            choice = input("\n> ").strip().lower()

            if choice == 'v':
                self._view_full_content(page_data["content"])
            elif choice == 'r':
                self._view_llm_review(llm_review)
            elif choice == 'p':
                self._approve_page(page["file"], page_data)
                break
            elif choice == 'x':
                self._reject_page(page["file"], page_data)
                break
            elif choice == 'n':
                break
            else:
                print("Invalid choice. v=view, r=review, p=approve, x=reject, n=next")

    def _show_page_overview(self, page: Dict, page_data: Dict, llm_review: Dict):
        """Show page overview"""
        print(f"\n=== Reviewing: {page['title']} ===")
        print(f"Type: {page['type']} | Words: {page['word_count']:,}")
        print(f"LLM Verdict: {llm_review.get('overall_verdict', 'UNKNOWN')}")

        if llm_review.get("issues_found"):
            print(f"\nIssues Found ({len(llm_review['issues_found'])}):")
            for issue in llm_review["issues_found"][:3]:
                icon = "🔴" if issue["severity"] == "high" else "🟡" if issue["severity"] == "medium" else "🟢"
                print(f"  {icon} {issue['issue']}")

            if len(llm_review["issues_found"]) > 3:
                print(f"  ... and {len(llm_review['issues_found']) - 3} more")

        print("\nOptions:")
        print("[v] View full content  [r] View LLM review  [p] Approve  [x] Reject  [n] Next")

    def _view_full_content(self, content: str):
        """Show full page content"""
        print("\n" + "="*60)
        print(content[:2000])  # Show first 2000 chars

        if len(content) > 2000:
            print(f"\n... ({len(content) - 2000} more characters)")
            show_more = input("Show more? (y/n): ").lower()
            if show_more == 'y':
                print(content[2000:4000])

        print("\n" + "="*60)
        input("Press Enter to continue...")

    def _view_llm_review(self, llm_review: Dict):
        """Show detailed LLM review"""
        print("\n" + "="*60)
        print("LLM REVIEW DETAILS:")
        print(f"Overall: {llm_review.get('overall_verdict', 'UNKNOWN')}")
        print(f"Summary: {llm_review.get('review_summary', 'No summary')}")

        if llm_review.get("issues_found"):
            print("\nISSUES:")
            for i, issue in enumerate(llm_review["issues_found"], 1):
                print(f"\n{i}. {issue['issue'].upper()}")
                print(f"   Severity: {issue['severity']}")
                print(f"   Location: {issue['location']}")
                print(f"   Suggestion: {issue['suggestion']}")

        print("\n" + "="*60)
        input("Press Enter to continue...")

    def _approve_page(self, page_file: Path, page_data: Dict):
        """Approve page and move to approved directory"""
        # Add human approval metadata
        page_data["human_review"] = {
            "approved": True,
            "approved_date": datetime.now().isoformat(),
            "approved_by": "human_review"
        }

        # Move to approved directory
        approved_file = self.approved_dir / page_file.name
        approved_file.write_text(json.dumps(page_data, indent=2))
        page_file.unlink()

        print(f"✅ Approved: {page_data['title']}")

    def _reject_page(self, page_file: Path, page_data: Dict):
        """Reject page and move to rejected directory"""
        reason = input("Reason for rejection: ").strip()

        page_data["human_review"] = {
            "approved": False,
            "rejected_date": datetime.now().isoformat(),
            "rejected_by": "human_review",
            "reason": reason
        }

        # Move to rejected directory
        rejected_file = self.rejected_dir / page_file.name
        rejected_file.write_text(json.dumps(page_data, indent=2))
        page_file.unlink()

        print(f"❌ Rejected: {page_data['title']} - {reason}")


if __name__ == "__main__":
    cli = HumanReviewCLI()
    cli.run()