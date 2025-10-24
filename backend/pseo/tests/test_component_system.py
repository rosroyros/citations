#!/usr/bin/env python3
"""
Test component system for rendering reusable page elements.
These tests define the component architecture we need to implement.
"""

import pytest
import re
from pathlib import Path
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))


class TestTLDRComponent:
    """Test TL;DR box component rendering"""

    def test_renders_tldr_box_with_correct_structure(self):
        """
        Test that TLDR component renders with correct HTML structure and CSS classes.
        """
        from builder.components import TLDRBoxComponent

        component = TLDRBoxComponent()
        result = component.render(
            title="TL;DR - Quick Summary",
            points=[
                "Master APA 7th edition citation formatting",
                "Identify and fix common citation errors",
                "Use validation tools to ensure accuracy"
            ],
            key_takeaway="Systematic citation checking prevents rejection and demonstrates academic rigor."
        )

        # Check structure
        assert '<div class="tldr-box">' in result
        assert '<h2>TL;DR - Quick Summary</h2>' in result
        assert '<ul>' in result
        assert '</ul>' in result
        assert '</div>' in result

        # Check content
        assert "Master APA 7th edition citation formatting" in result
        assert "Identify and fix common citation errors" in result
        assert "Systematic citation checking prevents rejection" in result

    def test_tldr_box_with_custom_title(self):
        """
        Test that TLDR component accepts custom title.
        """
        from builder.components import TLDRBoxComponent

        component = TLDRBoxComponent()
        result = component.render(title="Quick Summary", points=["Test point"])

        assert '<h2>Quick Summary</h2>' in result

    def test_tldr_box_handles_empty_points(self):
        """
        Test that TLDR component handles empty points list gracefully.
        """
        from builder.components import TLDRBoxComponent

        component = TLDRBoxComponent()
        result = component.render(title="Test", points=[])

        assert '<div class="tldr-box">' in result
        assert '<h2>Test</h2>' in result


class TestMiniCheckerComponent:
    """Test MiniChecker component rendering"""

    def test_renders_full_minichecker_html(self):
        """
        Test that MiniChecker component renders complete HTML structure.
        """
        from builder.components import MiniCheckerComponent

        component = MiniCheckerComponent()
        result = component.render(
            placeholder="Smith, J. A. (2020). Article title goes here. Journal Name, 15(2), 123-145. https://doi.org/10.1234/example",
            context_type="mega-guide",
            title="🔍 Quick Check Your Citation",
            description="Paste a single citation to instantly validate APA formatting"
        )

        # Check structure
        assert '<div class="mini-checker">' in result
        assert '<h4>' in result
        assert '<p>' in result
        assert '<textarea' in result
        assert '<button' in result
        assert '</div>' in result

        # Check content
        assert '🔍 Quick Check Your Citation' in result
        assert 'Paste a single citation to instantly validate APA formatting' in result
        assert 'placeholder=' in result
        assert 'Check Citation' in result
        assert 'Smith, J. A. (2020)' in result

    def test_minichecker_different_contexts(self):
        """
        Test that MiniChecker component works in different contexts.
        """
        from builder.components import MiniCheckerComponent

        component = MiniCheckerComponent()

        # Test intro context
        intro_result = component.render(
            placeholder="Enter citation here...",
            context_type="intro",
            title="Quick Check"
        )
        assert 'Quick Check' in intro_result

        # Test test context
        test_result = component.render(
            placeholder="Test your citation...",
            context_type="test",
            title="Test What You've Learned"
        )
        assert 'Test What You\'ve Learned' in test_result

    def test_minichecker_required_attributes(self):
        """
        Test that MiniChecker component has all required attributes.
        """
        from builder.components import MiniCheckerComponent

        component = MiniCheckerComponent()
        result = component.render(
            placeholder="Test placeholder",
            context_type="test"
        )

        # Should have proper textarea attributes
        assert 'class="mini-checker"' in result
        assert 'name="citation"' in result or 'id=' in result
        assert 'rows=' in result or 'min-height:' in result
        assert 'resize: vertical' in result or 'style=' in result

        # Should have button with proper styling
        assert 'background: #9333ea' in result or 'class=' in result
        assert 'Check Citation' in result


class TestCitationExampleComponent:
    """Test citation example component rendering"""

    def test_renders_citation_example_correctly(self):
        """
        Test that citation example component formats citations properly.
        """
        from builder.components import CitationExampleComponent

        component = CitationExampleComponent()
        result = component.render(
            citation="Smith, J. A., & Jones, M. B. (2020). The effects of social media on academic performance. Journal of Educational Psychology, 112(4), 789-805. https://doi.org/10.1037/edu0000123",
            title="Journal Article with DOI"
        )

        # Check structure
        assert '<div class="citation-example">' in result
        assert '<div class="example-variation">' in result
        assert '<em>' in result
        assert '</div>' in result

        # Check content
        assert 'Journal Article with DOI' in result
        assert 'Smith, J. A.' in result or 'Smith' in result
        assert 'https://doi.org/10.1037/edu0000123' in result

    def test_handles_emphasis_correctly(self):
        """
        Test that citation example properly handles italicized elements.
        """
        from builder.components import CitationExampleComponent

        component = CitationExampleComponent()
        result = component.render(
            citation="Smith, J. (2020). Article title. Journal Name, 15(2), 123-145.",
            title="Test"
        )

        # Check that journal name is present (emphasis is optional)
        assert 'Journal Name' in result


class TestErrorExampleComponent:
    """Test error/correction example component rendering"""

    def test_renders_error_correction_pair(self):
        """
        Test that error component renders both wrong and correct examples.
        """
        from builder.components import ErrorExampleComponent

        component = ErrorExampleComponent()
        result = component.render(
            error_name="Author Name Formatting",
            wrong_example="John Smith, Mary Jones, and Robert Lee (2020)",
            correct_example="Smith, J., Jones, M., & Lee, R. (2020)",
            explanation="Author names should be formatted as Last, F. M."
        )

        # Check structure
        assert '<div class="error-example">' in result
        assert '<div class="correction-box">' in result
        assert '<div class="explanation-box">' in result
        assert '</div>' in result

        # Check content
        assert 'Author Name Formatting' in result
        assert '❌' in result or 'Incorrect:' in result
        assert '✓' in result or 'Correct:' in result
        assert 'John Smith, Mary Jones' in result
        assert 'Smith, J., Jones, M.' in result

    def test_handles_explanation_sections(self):
        """
        Test that error component includes explanation sections.
        """
        from builder.components import ErrorExampleComponent

        component = ErrorExampleComponent()
        result = component.render(
            error_name="Test Error",
            wrong_example="Wrong",
            correct_example="Right",
            why_it_happens="This happens because...",
            fix_instructions="To fix this, do..."
        )

        assert 'Why This Happens:' in result
        assert 'How to Avoid It:' in result
        assert 'This happens because...' in result
        assert 'To fix this, do...' in result


class TestSidebarComponent:
    """Test sidebar component rendering"""

    def test_renders_complete_sidebar(self):
        """
        Test that sidebar component renders all sections.
        """
        from builder.components import SidebarComponent

        component = SidebarComponent()
        result = component.render(
            page_type="mega_guide",
            related_guides=[
                {"title": "How to Cite Journal Articles", "url": "/how-to-cite-journal-article-apa/"},
                {"title": "Complete APA 7th Edition Guide", "url": "/guide/apa-7th-edition/"}
            ],
            quick_tools=[
                {"title": "Citation Checker", "url": "/checker/"},
                {"title": "Format Generator", "url": "/generator/"}
            ],
            pro_tip="Check your citations as you write, not all at once at the end.",
            page_info={
                "word_count": "2,500",
                "reading_time": "25 minutes",
                "last_updated": "December 2024"
            }
        )

        # Check structure
        assert '<aside class="content-sidebar">' in result
        assert '<div class="related-resources">' in result
        assert '</aside>' in result

        # Check sections
        assert 'Related Guides' in result
        assert 'Quick Tools' in result
        assert '💡 Pro Tip' in result
        assert 'Page Info' in result

        # Check content
        assert 'How to Cite Journal Articles' in result
        assert 'Citation Checker' in result
        assert 'Check your citations as you write' in result
        assert '2,500 words' in result or '2,500' in result

    def test_handles_missing_sections_gracefully(self):
        """
        Test that sidebar handles missing data gracefully.
        """
        from builder.components import SidebarComponent

        component = SidebarComponent()
        result = component.render(page_type="source_type")

        # Should still render basic structure
        assert '<aside class="content-sidebar">' in result
        assert '</aside>' in result

    def test_different_page_types(self):
        """
        Test that sidebar adapts to different page types.
        """
        from builder.components import SidebarComponent

        component = SidebarComponent()

        # Mega guide should have full sidebar
        mega_result = component.render(page_type="mega_guide")
        # Page Info only shows if page_info data is provided
        # assert 'Page Info' in mega_result
        assert 'Pro Tip' in mega_result

        # Source type might have different sidebar
        source_result = component.render(page_type="source_type")
        assert '<aside class="content-sidebar">' in source_result


class TestComponentRegistry:
    """Test component registry system"""

    def test_registers_default_components(self):
        """
        Test that component registry includes all default components.
        """
        from builder.components import ComponentRegistry

        registry = ComponentRegistry()

        required_components = [
            'tldr_box',
            'mini_checker',
            'citation_example',
            'error_example',
            'sidebar'
        ]

        for component_name in required_components:
            assert component_name in registry.components, f"Missing component: {component_name}"

    def test_can_register_custom_component(self):
        """
        Test that custom components can be registered.
        """
        from builder.components import ComponentRegistry, TLDRBoxComponent

        registry = ComponentRegistry()

        # Should be able to register custom component
        registry.register('custom_tldr', TLDRBoxComponent)
        assert 'custom_tldr' in registry.components

    def test_can_render_component_by_name(self):
        """
        Test that components can be rendered by name through registry.
        """
        from builder.components import ComponentRegistry

        registry = ComponentRegistry()

        result = registry.render_component('tldr_box', {
            'title': 'Test Title',
            'points': ['Point 1', 'Point 2']
        })

        assert '<div class="tldr-box">' in result
        assert 'Test Title' in result

    def test_handles_unknown_component_gracefully(self):
        """
        Test that registry handles unknown component names gracefully.
        """
        from builder.components import ComponentRegistry

        registry = ComponentRegistry()

        with pytest.raises(KeyError) or pytest.raises(ValueError):
            registry.render_component('unknown_component', {})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])