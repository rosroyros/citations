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
        <p className="footer-text">© 2025 Citation Format Checker. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;