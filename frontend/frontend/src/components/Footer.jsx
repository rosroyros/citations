import React from 'react';
import './Footer.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';

const Footer = () => {
  const { trackNavigationClick } = useAnalyticsTracking();

  const handleNavClick = (element, url) => {
    trackNavigationClick(element, url);
  };

  return (
    <footer className="footer">
      <div className="footer-content">
        {/* Citation Guides Section */}
        <div className="footer-guides">
          <h3 className="footer-section-title">Citation Guides</h3>
          <div className="footer-guides-grid">
            <a href="/guide/apa-graduate-students/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-graduate-students/')}>
              APA for Graduate Students
            </a>
            <a href="/guide/apa-title-page/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-title-page/')}>
              APA Title Page
            </a>
            <a href="/guide/apa-reference-list/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-reference-list/')}>
              APA Reference List
            </a>
            <a href="/guide/apa-in-text-citations/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-in-text-citations/')}>
              In-Text Citations
            </a>
            <a href="/guide/apa-citation-errors/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-citation-errors/')}>
              Common Citation Errors
            </a>
            <a href="/guide/fix-apa-citation-errors/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/fix-apa-citation-errors/')}>
              Fix Citation Errors
            </a>
            <a href="/guide/check-apa-citations/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/check-apa-citations/')}>
              Check Citations
            </a>
            <a href="/guide/validate-reference-list/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/validate-reference-list/')}>
              Validate Reference List
            </a>
            <a href="/guide/apa-citations-psychology/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-citations-psychology/')}>
              APA for Psychology
            </a>
            <a href="/guide/apa-citations-education/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-citations-education/')}>
              APA for Education
            </a>
            <a href="/guide/apa-citations-nursing/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-citations-nursing/')}>
              APA for Nursing
            </a>
            <a href="/guide/apa-7th-edition-changes/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-7th-edition-changes/')}>
              APA 7th Edition Changes
            </a>
            <a href="/guide/apa-vs-mla-vs-chicago/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-vs-mla-vs-chicago/')}>
              APA vs MLA vs Chicago
            </a>
            <a href="/guide/apa-citation-workflow/" className="footer-guide-link" onClick={() => handleNavClick('footer_guide', '/guide/apa-citation-workflow/')}>
              Citation Workflow
            </a>
          </div>
        </div>

        <div className="footer-divider"></div>

        {/* Footer Links */}
        <div className="footer-links">
          <a
            href="/privacy"
            className="footer-link"
            onClick={() => handleNavClick('footer_link', '/privacy')}
          >
            Privacy Policy
          </a>
          <span className="footer-separator">•</span>
          <a
            href="/terms"
            className="footer-link"
            onClick={() => handleNavClick('footer_link', '/terms')}
          >
            Terms of Service
          </a>
          <span className="footer-separator">•</span>
          <a
            href="/contact"
            className="footer-link"
            onClick={() => handleNavClick('footer_link', '/contact')}
          >
            Contact Us
          </a>
        </div>
      <p className="footer-text">© 2025 Citation Checker. All rights reserved.</p>
      <p className="footer-tagline">Built for researchers, by researchers</p>
      </div>
    </footer>
  );
};

export default Footer;