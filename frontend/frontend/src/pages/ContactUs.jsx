import React from 'react';
import { Link } from 'react-router-dom';
import Footer from '../components/Footer';
import '../App.css';

const ContactUs = () => {
  return (
    <div className="app" style={{background: '#f9fafb', minHeight: '100vh'}}>
      <div className="benefits-content" style={{paddingTop: '2rem'}}>
        <Link to="/" className="logo-text" style={{fontSize: '1rem', marginBottom: '2rem', display: 'inline-block', textDecoration: 'none', color: '#9333ea'}}>
          ← Back to Citation Checker
        </Link>

        <div style={{background: 'white', borderRadius: '1rem', padding: '3rem', boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)'}}>
          <h1 style={{fontSize: '3rem', fontWeight: '700', color: '#1f2937', marginBottom: '1rem', textAlign: 'center'}}>Contact Us</h1>
          <p style={{color: '#6b7280', marginBottom: '3rem', textAlign: 'center'}}>We're here to help with your citation formatting needs</p>

          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem'}}>
            <div style={{background: '#f0f9ff', borderRadius: '1rem', padding: '2rem'}}>
              <h2 style={{fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', marginBottom: '2rem'}}>Get in Touch</h2>

              <div style={{marginBottom: '2rem'}}>
                <h3 style={{fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Email Support</h3>
                <div style={{background: 'white', borderRadius: '0.5rem', padding: '1.5rem', border: '1px solid #3b82f6'}}>
                  <p style={{fontSize: '1.5rem', fontWeight: '700', color: '#3b82f6', marginBottom: '0.5rem'}}>
                    support@citationformatchecker.com
                  </p>
                  <p style={{fontSize: '0.875rem', color: '#6b7280'}}>
                    We typically respond within 24-48 hours
                  </p>
                </div>
              </div>

              <div>
                <h3 style={{fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>What we can help with:</h3>
                <ul style={{color: '#374151', lineHeight: '1.6'}}>
                  <li style={{marginBottom: '0.5rem', display: 'flex', alignItems: 'flex-start'}}>
                    <span style={{color: '#3b82f6', marginRight: '0.5rem'}}>•</span>
                    Technical issues and bug reports
                  </li>
                  <li style={{marginBottom: '0.5rem', display: 'flex', alignItems: 'flex-start'}}>
                    <span style={{color: '#3b82f6', marginRight: '0.5rem'}}>•</span>
                    Account and billing questions
                  </li>
                  <li style={{marginBottom: '0.5rem', display: 'flex', alignItems: 'flex-start'}}>
                    <span style={{color: '#3b82f6', marginRight: '0.5rem'}}>•</span>
                    Feature suggestions and feedback
                  </li>
                  <li style={{marginBottom: '0.5rem', display: 'flex', alignItems: 'flex-start'}}>
                    <span style={{color: '#3b82f6', marginRight: '0.5rem'}}>•</span>
                    Questions about citation formats
                  </li>
                </ul>
              </div>
            </div>

            <div style={{display: 'flex', flexDirection: 'column', gap: '2rem'}}>
              <div style={{background: '#f9fafb', borderRadius: '1rem', padding: '2rem'}}>
                <h2 style={{fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', marginBottom: '2rem'}}>Before You Contact Us</h2>

                <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
                  <div>
                    <h3 style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Check Our Documentation</h3>
                    <p style={{color: '#374151', fontSize: '0.875rem'}}>
                      Browse our help guides and FAQs for quick answers to common questions.
                    </p>
                  </div>

                  <div>
                    <h3 style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Validation Results</h3>
                    <p style={{color: '#374151', fontSize: '0.875rem'}}>
                      Remember that our AI-powered validation is a tool to help identify potential issues.
                      Always verify citations against official style guides.
                    </p>
                  </div>

                  <div>
                    <h3 style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Service Status</h3>
                    <p style={{color: '#374151', fontSize: '0.875rem'}}>
                      Check if there are any known service issues that might be affecting your experience.
                    </p>
                  </div>
                </div>
              </div>

              <div style={{background: '#fef3c7', borderRadius: '1rem', padding: '2rem'}}>
                <h2 style={{fontSize: '1.5rem', fontWeight: '600', color: '#1f2937', marginBottom: '2rem'}}>Response Times</h2>
                <ul style={{color: '#374151', lineHeight: '1.6'}}>
                  <li style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                    <span>Technical Support:</span>
                    <span style={{fontWeight: '500'}}>24-48 hours</span>
                  </li>
                  <li style={{display: 'flex', justifyContent: 'space-between', marginBottom: '1rem'}}>
                    <span>Billing Questions:</span>
                    <span style={{fontWeight: '500'}}>1-2 business days</span>
                  </li>
                  <li style={{display: 'flex', justifyContent: 'space-between'}}>
                    <span>Feature Requests:</span>
                    <span style={{fontWeight: '500'}}>We review all submissions</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div style={{marginTop: '2rem', padding: '2rem', background: '#f3f4f6', borderRadius: '1rem'}}>
            <h2 style={{fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem'}}>Privacy & Security</h2>
            <p style={{color: '#374151', fontSize: '0.875rem', lineHeight: '1.6'}}>
              When you contact us, we only collect the information necessary to respond to your inquiry.
              We never share your contact information with third parties. For more details, please review our
              <Link to="/privacy" style={{color: '#3b82f6', textDecoration: 'none', marginLeft: '0.25rem'}}>
                Privacy Policy
              </Link>.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default ContactUs;