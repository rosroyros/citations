import React from 'react';
import Footer from '../components/Footer';
import '../App.css';

const TermsOfService = () => {
  return (
    <div className="app" style={{background: '#f9fafb', minHeight: '100vh'}}>
      <div className="benefits-content" style={{paddingTop: '2rem'}}>
        <a href="/" className="logo-text" style={{fontSize: '1rem', marginBottom: '2rem', display: 'inline-block', textDecoration: 'none', color: '#9333ea'}}>
          ← Back to Citation Checker
        </a>

        <div style={{background: 'white', borderRadius: '1rem', padding: '3rem', boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)'}}>
          <h1 style={{fontSize: '3rem', fontWeight: '700', color: '#1f2937', marginBottom: '1rem', textAlign: 'center'}}>Terms of Service</h1>
          <p style={{color: '#6b7280', marginBottom: '3rem', textAlign: 'center'}}>Last Updated: November 5, 2025</p>

          <div style={{lineHeight: '1.6'}}>
            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>1. Acceptance of Terms</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>
                Welcome to Citation Format Checker. These Terms of Service ("Terms") govern your access to and use of our citation validation service, website, and related services (collectively, the "Service").
              </p>
              <p style={{color: '#374151'}}>
                By accessing or using the Service, you agree to be bound by these Terms. If you do not agree to these Terms, do not use the Service.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>2. Description of Service</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>
                Citation Format Checker is a web-based service that helps users validate the formatting of academic citations. Our Service:
              </p>
              <ul style={{color: '#374151', paddingLeft: '1.5rem', marginBottom: '2rem'}}>
                <li style={{marginBottom: '0.5rem'}}>Analyzes citation text submitted by users</li>
                <li style={{marginBottom: '0.5rem'}}>Identifies formatting errors and inconsistencies</li>
                <li style={{marginBottom: '0.5rem'}}>Provides detailed feedback and suggestions for corrections</li>
                <li style={{marginBottom: '0.5rem'}}>Supports multiple citation styles (APA, MLA, Chicago, and others)</li>
                <li style={{marginBottom: '0.5rem'}}>Offers both free and paid credit-based usage tiers</li>
              </ul>
              <p style={{color: '#374151', fontStyle: 'italic'}}>
                The Service uses artificial intelligence and language models to analyze citations. While we strive for accuracy, automated validation is not perfect and should be used as a helpful tool, not a replacement for manual review.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>3. User Accounts and Credits</h2>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Free Usage</h3>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                The Service offers limited free usage for users without an account. Free usage is subject to daily limits and may be restricted based on service capacity.
              </p>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Credit System</h3>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                Users may purchase credits to access additional validation capabilities. Credits are non-transferable between users and are consumed upon each citation validation request.
              </p>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Account Security</h3>
              <p style={{color: '#374151'}}>
                If you create an account, you are responsible for maintaining the confidentiality of your account credentials and all activities that occur under your account.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>4. User Obligations and Acceptable Use</h2>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Permitted Use</h3>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                You may use the Service only for lawful purposes and in accordance with these Terms. You agree to use the Service responsibly and professionally.
              </p>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Prohibited Activities</h3>
              <p style={{color: '#374151', marginBottom: '1rem'}}>You agree NOT to:</p>
              <ul style={{color: '#374151', paddingLeft: '1.5rem', marginBottom: '2rem'}}>
                <li style={{marginBottom: '0.5rem'}}><strong>Abuse or Exploit the Service:</strong> Attempt to circumvent usage limits, share account credentials, or use automated scripts without authorization</li>
                <li style={{marginBottom: '0.5rem'}}><strong>Submit Inappropriate Content:</strong> Submit content that is illegal, harmful, or infringes intellectual property rights</li>
                <li style={{marginBottom: '0.5rem'}}><strong>Misrepresent or Deceive:</strong> Impersonate any person or entity, or falsify affiliations</li>
                <li style={{marginBottom: '0.5rem'}}><strong>Interfere with Others:</strong> Disrupt other users' use of the Service or attempt unauthorized access</li>
                <li style={{marginBottom: '0.5rem'}}><strong>Commercial Misuse:</strong> Resell or redistribute the Service without authorization</li>
              </ul>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>5. Intellectual Property Rights</h2>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Our Intellectual Property</h3>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                The Service, including all content, features, functionality, software, code, design, graphics, and user interface, is owned by Citation Format Checker and is protected by copyright, trademark, and other intellectual property laws.
              </p>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                You are granted a limited, non-exclusive, non-transferable, revocable license to access and use the Service for your personal or internal business purposes, subject to these Terms.
              </p>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>User Content</h3>
              <p style={{color: '#374151'}}>
                You retain ownership of the citation text and content you submit to the Service. We do not claim ownership of your content and do not use it for any purpose other than providing validation services.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>6. Disclaimer of Warranties</h2>
              <div style={{background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '0.5rem', padding: '1.5rem', marginBottom: '2rem'}}>
                <p style={{fontWeight: '700', color: '#92400e', marginBottom: '0.5rem'}}>IMPORTANT DISCLAIMER:</p>
                <p style={{color: '#92400e'}}>
                  THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND.
                </p>
              </div>
              <p style={{color: '#374151', marginBottom: '1rem'}}>
                We disclaim all warranties, including but not limited to:
              </p>
              <ul style={{color: '#374151', paddingLeft: '1.5rem', marginBottom: '2rem'}}>
                <li style={{marginBottom: '0.5rem'}}>Warranties of merchantability and fitness for a particular purpose</li>
                <li style={{marginBottom: '0.5rem'}}>Service availability, reliability, or accuracy</li>
                <li style={{marginBottom: '0.5rem'}}>Validation accuracy - results may contain errors and should be verified manually</li>
                <li style={{marginBottom: '0.5rem'}}>Performance of third-party services</li>
              </ul>
              <p style={{color: '#374151'}}>
                Use of the Service is at your own risk. You are responsible for verifying citation accuracy and appropriateness.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>7. Limitation of Liability</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>
                To the fullest extent permitted by law, Citation Format Checker shall not be liable for:
              </p>
              <ul style={{color: '#374151', paddingLeft: '1.5rem', marginBottom: '2rem'}}>
                <li style={{marginBottom: '0.5rem'}}>Indirect, incidental, special, consequential, or punitive damages</li>
                <li style={{marginBottom: '0.5rem'}}>Loss of profits, revenue, data, or use</li>
                <li style={{marginBottom: '0.5rem'}}>Cost of substitute services</li>
              </ul>
              <p style={{color: '#374151'}}>
                In no event shall our total liability to you exceed the amount you paid us in the twelve (12) months preceding the claim, or $100 USD, whichever is greater.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>8. Payment Terms</h2>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Refunds</h3>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                All credit purchases are final and non-refundable. We do not offer refunds for unused credits, duplicate purchases, or dissatisfaction with validation results.
              </p>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Billing Disputes</h3>
              <p style={{color: '#374151'}}>
                If you believe you have been charged incorrectly, contact us at support@citationformatchecker.com within 30 days of the charge.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>9. Privacy and Data Protection</h2>
              <p style={{color: '#374151'}}>
                Your use of the Service is subject to our Privacy Policy, which explains how we collect, use, and protect your information. By using the Service, you consent to the collection and use of information as described in our Privacy Policy.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>10. Termination</h2>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                You may stop using the Service at any time. We reserve the right to suspend or terminate your access to the Service at any time, with or without cause, with or without notice.
              </p>
              <p style={{color: '#374151'}}>
                Upon termination, your right to access the Service immediately ceases and unused credits are forfeited (credits are non-refundable).
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>11. Contact Information</h2>
              <p style={{color: '#374151', marginBottom: '2rem'}}>
                For questions or concerns about these Terms, contact us at:
              </p>
              <div style={{background: '#f3f4f6', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e5e7eb'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Email: support@citationformatchecker.com</p>
                <p style={{color: '#6b7280'}}>Subject: Terms of Service Inquiry</p>
              </div>
            </section>

            <div style={{marginTop: '4rem', padding: '2rem', background: '#fef3c7', borderRadius: '1rem', border: '1px solid #fbbf24'}}>
              <h2 style={{fontSize: '1.5rem', fontWeight: '700', color: '#92400e', marginBottom: '1rem', textAlign: 'center'}}>Acknowledgment</h2>
              <p style={{color: '#92400e', fontWeight: '500', textAlign: 'center'}}>
                BY USING CITATION FORMAT CHECKER, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREE TO BE BOUND BY THESE TERMS OF SERVICE.
              </p>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default TermsOfService;