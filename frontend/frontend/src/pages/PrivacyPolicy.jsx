import React from 'react';
import Footer from '../components/Footer';
import '../App.css';

const PrivacyPolicy = () => {
  return (
    <div className="app" style={{background: '#f9fafb', minHeight: '100vh'}}>
      <div className="benefits-content" style={{paddingTop: '2rem'}}>
        <a href="/" className="logo-text" style={{fontSize: '1rem', marginBottom: '2rem', display: 'inline-block', textDecoration: 'none', color: '#9333ea'}}>
          ← Back to Citation Checker
        </a>

        <div style={{background: 'white', borderRadius: '1rem', padding: '3rem', boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)'}}>
          <h1 style={{fontSize: '3rem', fontWeight: '700', color: '#1f2937', marginBottom: '1rem', textAlign: 'center'}}>Privacy Policy</h1>
          <p style={{color: '#6b7280', marginBottom: '3rem', textAlign: 'center'}}>Last Updated: November 5, 2025</p>

          <div style={{lineHeight: '1.6'}}>
            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>Introduction</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>
                Citation Format Checker ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our citation validation service.
              </p>
              <p style={{color: '#374151'}}>
                By using Citation Format Checker, you agree to the collection and use of information in accordance with this policy.
              </p>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>Information We Collect</h2>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem'}}>Information You Provide</h3>
              <div style={{marginBottom: '2rem'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Citation Content:</p>
                <p style={{color: '#374151'}}>When you use our service, you submit citations for validation. We temporarily process this content to provide our service but do not permanently store it unless necessary for service functionality.</p>
              </div>

              <div style={{marginBottom: '2rem'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Contact Information:</p>
                <p style={{color: '#374151'}}>If you contact us at support@citationformatchecker.com, we collect your email address and any information you choose to provide in your communication.</p>
              </div>

              <div style={{marginBottom: '2rem'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Payment Information:</p>
                <p style={{color: '#374151'}}>When you purchase credits, payment information is processed through our third-party payment processor (Stripe). We do not store your credit card information on our servers.</p>
              </div>

              <h3 style={{fontSize: '1.5rem', fontWeight: '500', color: '#1f2937', marginBottom: '1rem', marginTop: '2rem'}}>Information Automatically Collected</h3>
              <div style={{marginBottom: '2rem'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Analytics Data:</p>
                <p style={{color: '#374151'}}>We use Google Analytics to collect information about how you interact with our service, including pages visited, time spent, device type, browser type, and general geographic location.</p>
              </div>

              <div style={{marginBottom: '2rem'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Usage Data:</p>
                <p style={{color: '#374151'}}>We collect information about your use of our service features, including number of citations validated, types of citation formats checked, and feature usage patterns.</p>
              </div>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>How We Use Your Information</h2>
              <ul style={{color: '#374151', paddingLeft: '1.5rem'}}>
                <li style={{marginBottom: '0.5rem'}}>To provide our citation validation service</li>
                <li style={{marginBottom: '0.5rem'}}>To manage your citation credit balance and usage</li>
                <li style={{marginBottom: '0.5rem'}}>To improve our service through analysis of usage patterns</li>
                <li style={{marginBottom: '0.5rem'}}>To communicate with you regarding support and service updates</li>
                <li style={{marginBottom: '0.5rem'}}>For analytics and research to improve citation validation accuracy</li>
              </ul>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>Third-Party Services</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>We use the following third-party services:</p>
              <ul style={{color: '#374151', paddingLeft: '1.5rem'}}>
                <li style={{marginBottom: '0.5rem'}}><strong>Language Model Providers:</strong> Your citation content is sent to AI providers for validation using enterprise APIs that do not train models on your data</li>
                <li style={{marginBottom: '0.5rem'}}><strong>Google Analytics:</strong> For collecting and analyzing usage data</li>
                <li style={{marginBottom: '0.5rem'}}><strong>Stripe:</strong> For secure payment processing</li>
              </ul>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>Data Retention</h2>
              <ul style={{color: '#374151', paddingLeft: '1.5rem'}}>
                <li style={{marginBottom: '0.5rem'}}>Citation content is processed in real-time and not permanently stored</li>
                <li style={{marginBottom: '0.5rem'}}>Analytics data is retained for up to 26 months</li>
                <li style={{marginBottom: '0.5rem'}}>Payment records are retained for up to 7 years for legal purposes</li>
                <li style={{marginBottom: '0.5rem'}}>Support communications are retained for up to 2 years</li>
              </ul>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>Your Rights and Choices</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>You have the right to:</p>
              <ul style={{color: '#374151', paddingLeft: '1.5rem'}}>
                <li style={{marginBottom: '0.5rem'}}>Access your personal information</li>
                <li style={{marginBottom: '0.5rem'}}>Request correction of inaccurate information</li>
                <li style={{marginBottom: '0.5rem'}}>Request deletion of your personal information</li>
                <li style={{marginBottom: '0.5rem'}}>Opt-out of analytics tracking</li>
                <li style={{marginBottom: '0.5rem'}}>Request a copy of your data</li>
              </ul>
            </section>

            <section style={{marginBottom: '3rem'}}>
              <h2 style={{fontSize: '2rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem'}}>Contact Us</h2>
              <p style={{color: '#374151', marginBottom: '1.5rem'}}>
                If you have questions about this Privacy Policy, please contact us at:
              </p>
              <div style={{background: '#f3f4f6', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e5e7eb'}}>
                <p style={{fontWeight: '500', color: '#1f2937', marginBottom: '0.5rem'}}>Email: support@citationformatchecker.com</p>
                <p style={{color: '#6b7280'}}>Subject: Privacy Policy Inquiry</p>
              </div>
            </section>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default PrivacyPolicy;