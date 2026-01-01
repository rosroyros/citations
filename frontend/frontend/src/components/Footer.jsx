import React from 'react';
import './Footer.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';

const Footer = () => {
  const { trackNavigationClick } = useAnalyticsTracking();

  const handleNavClick = (element, url) => {
    trackNavigationClick(element, url);
  };

  // APA 7th Edition guides - top 5 most useful
  const apaGuides = [
    { name: "Complete Guide", url: "/guide/apa-7th-edition/" },
    { name: "For Graduate Students", url: "/guide/apa-graduate-students/" },
    { name: "Title Page", url: "/guide/apa-title-page/" },
    { name: "Reference List", url: "/guide/apa-reference-list/" },
    { name: "In-Text Citations", url: "/guide/apa-in-text-citations/" },
  ];

  // MLA 9th Edition guides - top 5 most useful
  const mlaGuides = [
    { name: "Complete Guide", url: "/mla/guide/mla-9th-edition/" },
    { name: "Cite Book", url: "/mla/how-to-cite-book-mla/" },
    { name: "Cite YouTube", url: "/mla/cite-youtube-mla/" },
    { name: "Cite Wikipedia", url: "/mla/cite-wikipedia-mla/" },
    { name: "Cite New York Times", url: "/mla/cite-new-york-times-mla/" },
  ];

  return (
    <footer className="footer">
      <div className="footer-content">
        {/* Citation Guides Section - Two Column Layout */}
        <div className="footer-guides">
          <h3 className="footer-section-title">Citation Guides</h3>
          <div className="footer-guides-columns">
            {/* APA Column */}
            <div className="footer-column">
              <h4 className="footer-column-title">APA 7th Edition</h4>
              <div className="footer-column-links">
                {apaGuides.map((guide) => (
                  <a
                    key={guide.url}
                    href={guide.url}
                    className="footer-guide-link"
                    onClick={() => handleNavClick('footer_guide', guide.url)}
                  >
                    {guide.name}
                  </a>
                ))}
                <a
                  href="/guide/apa-7th-edition/"
                  className="footer-view-all"
                  onClick={() => handleNavClick('footer_guide', '/guide/apa-7th-edition/')}
                >
                  View All APA Guides →
                </a>
              </div>
            </div>

            {/* MLA Column */}
            <div className="footer-column">
              <h4 className="footer-column-title">MLA 9th Edition</h4>
              <div className="footer-column-links">
                {mlaGuides.map((guide) => (
                  <a
                    key={guide.url}
                    href={guide.url}
                    className="footer-guide-link"
                    onClick={() => handleNavClick('footer_guide', guide.url)}
                  >
                    {guide.name}
                  </a>
                ))}
                <a
                  href="/mla/guide/mla-9th-edition/"
                  className="footer-view-all"
                  onClick={() => handleNavClick('footer_guide', '/mla/guide/mla-9th-edition/')}
                >
                  View All MLA Guides →
                </a>
              </div>
            </div>
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