import React from 'react';
import { Shield, PhoneCall, CheckCircle, FileText, Lock, Globe, Mail } from 'lucide-react';

interface InfoPagesProps {
  page: 'about' | 'contact' | 'privacy' | 'terms';
  lang: 'en' | 'bn';
}

export const InfoPages: React.FC<InfoPagesProps> = ({ page, lang }) => {
  if (page === 'contact') {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Citizen Helpdesk & Emergency Contacts
          </h1>
          <p className="text-xs text-slate-500">
            For immediate life-threatening incidents, please contact Bangladesh National Emergency Services directly.
          </p>
        </div>

        {/* Hotlines */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-bold text-slate-500 uppercase">National Police & Fire</span>
            <div className="text-3xl font-black text-rose-600 mt-1">999</div>
            <span className="text-[11px] text-slate-400 mt-1 block">Toll-free 24/7</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-bold text-slate-500 uppercase">Govt Citizen Info</span>
            <div className="text-3xl font-black text-primary-600 mt-1">333</div>
            <span className="text-[11px] text-slate-400 mt-1 block">Municipal & Relief Services</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-bold text-slate-500 uppercase">Anti-Corruption (ACC)</span>
            <div className="text-3xl font-black text-amber-600 mt-1">106</div>
            <span className="text-[11px] text-slate-400 mt-1 block">Bribery & Extortion Hotline</span>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
            <span className="text-xs font-bold text-slate-500 uppercase">Women & Child Helpline</span>
            <div className="text-3xl font-black text-blue-600 mt-1">109</div>
            <span className="text-[11px] text-slate-400 mt-1 block">Confidential Support</span>
          </div>
        </div>

        {/* Office addresses */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 text-xs">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
            Central Citizen Operations Secretariat
          </h3>
          <p className="text-slate-600 leading-relaxed">
            CivicAI Central Coordination Cell, Nagar Bhaban Complex, Fulbaria, Dhaka-1000, Bangladesh.
          </p>
          <div className="flex items-center space-x-2 text-slate-600">
            <Mail className="w-4 h-4 text-primary-600" />
            <span>citizen.help@civicai.gov.bd</span>
          </div>
        </div>
      </div>
    );
  }

  if (page === 'privacy') {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-6">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Privacy Policy & Citizen Data Security</h1>
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4 text-xs leading-relaxed text-slate-700">
          <h3 className="text-sm font-bold text-slate-900">1. Anonymous & Guest Submissions</h3>
          <p>
            Citizens can report public hazards in complete anonymity. When submitting via Guest Mode or marking a complaint as anonymous, your IP address is cryptographically hashed with SHA-256 for abuse mitigation only and is never published or shared with field departments.
          </p>
          <h3 className="text-sm font-bold text-slate-900">2. Data Encryption</h3>
          <p>
            All registered citizen accounts utilize bcrypt password hashing (12 rounds) and JWT authentication. No plain-text passwords or sensitive private numbers are visible in public complaint feeds.
          </p>
          <h3 className="text-sm font-bold text-slate-900">3. Photographic Evidence</h3>
          <p>
            Uploaded photos are sanitized, stripped of proprietary metadata, and scanned before public display to protect citizen privacy.
          </p>
        </div>
      </div>
    );
  }

  if (page === 'terms') {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-6">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Terms & Conditions of Public Access</h1>
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4 text-xs leading-relaxed text-slate-700">
          <h3 className="text-sm font-bold text-slate-900">1. Proper Civic Reporting</h3>
          <p>
            This platform is dedicated to real-world community infrastructure, environmental, and public service problems across Bangladesh. Submissions containing fraudulent, defamatory, or abusive content will be automatically rejected and IP addresses blacklisted.
          </p>
          <h3 className="text-sm font-bold text-slate-900">2. AI-Assisted Decision Making</h3>
          <p>
            CivicAI uses genuine machine learning models trained on the BanglaPSG corpus to aid and recommend prioritization for municipal administrators. Final administrative decisions and field resource dispatches are confirmed by verified public officers.
          </p>
        </div>
      </div>
    );
  }

  // Default: About Page
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 text-primary-700 bg-primary-50 px-3 py-1 rounded-full text-xs font-bold">
          <Shield className="w-3.5 h-3.5" />
          <span>About CivicAI Bangladesh</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          AI-Powered Smart Public Grievance & Municipal Resolution Platform
        </h1>
        <p className="text-xs text-slate-500">
          Designed for citizens, researchers, and public governance in Bangladesh.
        </p>
      </div>

      <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6 text-xs text-slate-700 leading-relaxed">
        <div className="space-y-2">
          <h3 className="text-sm font-bold text-slate-900">Vision & Core Objective</h3>
          <p>
            CivicAI Bangladesh is a full-stack, production-ready AI platform designed to transform public complaint resolution across all 64 districts of Bangladesh. By combining citizen accessibility with genuine multilingual Natural Language Processing (NLP), the platform empowers anyone to report real-world civic problems without friction.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-bold text-slate-900">The 7 AI Models & Pipeline Architecture</h3>
          <ul className="list-disc pl-5 space-y-1.5">
            <li><strong>AI Model 1 (Civic Category Classification):</strong> Classifies complaints into 10 domains (Infrastructure, Water & Drainage, Waste, Power, etc.) using sublinear TF-IDF and calibrated classifiers.</li>
            <li><strong>AI Model 2 (Severity Prediction):</strong> Estimates risk levels (Critical, High, Medium, Low) with 99%+ accuracy.</li>
            <li><strong>AI Model 3 (Priority Ranking Engine):</strong> Formulates a dynamic 0-100 priority score factoring severity, urgency signals, citizen endorsements, location sensitivity, and aging.</li>
            <li><strong>AI Model 4 (Duplicate Detection):</strong> Combines cosine similarity of text vectors with Haversine distance (&lt;3km) to cluster identical reports.</li>
            <li><strong>AI Model 5 (Multilingual NLP Preprocessor):</strong> Robust handling of Bangla Unicode, English, and phonetic Banglish.</li>
            <li><strong>AI Model 6 (Sentiment & Urgency Extraction):</strong> Identifies imminent danger and hazard tokens.</li>
            <li><strong>AI Model 7 (Explainability & Decision Support):</strong> Generates human-interpretable rationale for why an issue was prioritized.</li>
          </ul>
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-bold text-slate-900">BanglaPSG Dataset Alignment</h3>
          <p>
            The models were trained on 2,100+ curated records aligned with the BanglaPSG (Bangla Public & Social Governance) framework, evaluated across separate test sets for Bangla, English, and Banglish to prevent data leakage and ensure real-world robustness.
          </p>
        </div>
      </div>
    </div>
  );
};
