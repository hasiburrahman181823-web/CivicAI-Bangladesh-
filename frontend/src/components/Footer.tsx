import React from 'react';
import { ShieldAlert, PhoneCall, Globe, CheckCircle2, Heart } from 'lucide-react';

interface FooterProps {
  onNavigate: (tab: string) => void;
  lang: 'en' | 'bn';
}

export const Footer: React.FC<FooterProps> = ({ onNavigate, lang }) => {
  return (
    <footer className="bg-slate-900 text-slate-300 border-t border-slate-800">
      {/* Emergency Hotlines Strip */}
      <div className="bg-slate-950 border-b border-slate-800/80 py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-2 text-primary-400 font-semibold">
            <PhoneCall className="w-4 h-4 text-primary-400" />
            <span>{lang === 'bn' ? 'বাংলাদেশ জরুরি সেবা হটলাইন নম্বরসমূহ:' : 'National Citizen Emergency Hotlines:'}</span>
          </div>
          <div className="flex flex-wrap items-center gap-6 text-slate-300">
            <div>
              <span className="text-slate-500 font-medium">National Emergency: </span>
              <strong className="text-white bg-slate-800 px-2 py-0.5 rounded">999</strong>
            </div>
            <div>
              <span className="text-slate-500 font-medium">Government Information: </span>
              <strong className="text-white bg-slate-800 px-2 py-0.5 rounded">333</strong>
            </div>
            <div>
              <span className="text-slate-500 font-medium">Anti-Corruption Commission: </span>
              <strong className="text-white bg-slate-800 px-2 py-0.5 rounded">106</strong>
            </div>
            <div>
              <span className="text-slate-500 font-medium">Disaster Alert: </span>
              <strong className="text-white bg-slate-800 px-2 py-0.5 rounded">1090</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Col */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">CivicAI Bangladesh</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              {lang === 'bn'
                ? 'নাগরিক সেবা ও অভিযোগ নিষ্পত্তিতে কৃত্রিম বুদ্ধিমত্তা ভিত্তিক স্বচ্ছ প্ল্যাটফর্ম। সারা বাংলাদেশের যেকোনো এলাকার সমস্যা সহজেই জানান।'
                : 'Next-generation AI-powered public complaint and municipal management platform. Bridging citizens and civic authorities across Bangladesh.'}
            </p>
            <div className="flex items-center space-x-2 text-xs text-primary-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>BanglaPSG NLP Trained Engine</span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              {lang === 'bn' ? 'পোর্টাল লিংক' : 'Quick Navigation'}
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <button onClick={() => onNavigate('home')} className="hover:text-white transition">
                  {lang === 'bn' ? 'হোম পেজ' : 'Home Portal'}
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('feed')} className="hover:text-white transition">
                  {lang === 'bn' ? 'পাবলিক অভিযোগ ড্যাশবোর্ড' : 'Public Complaints Feed'}
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('map')} className="hover:text-white transition">
                  {lang === 'bn' ? 'লাইভ ভৌগোলিক ম্যাপ' : 'Interactive Geospatial Map'}
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('submit')} className="hover:text-white transition">
                  {lang === 'bn' ? 'অভিযোগ জমা দিন (গেস্ট / লগইন)' : 'Submit a Complaint (Guest)'}
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('track')} className="hover:text-white transition">
                  {lang === 'bn' ? 'ট্র্যাকিং আইডি দিয়ে খুঁজুন' : 'Track by ID'}
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('stats')} className="hover:text-white transition">
                  {lang === 'bn' ? 'স্বচ্ছতা ও সমাধান অ্যানালিটিক্স' : 'Analytics & Transparency'}
                </button>
              </li>
            </ul>
          </div>

          {/* Civic Domains */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              {lang === 'bn' ? 'সেবা খাতসমূহ' : 'Civic Domains'}
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-400">
              <li>Roads & Highway Infrastructure</li>
              <li>Water Supply & Drainage (WASA)</li>
              <li>City Waste Management</li>
              <li>Electricity & Power (DPDC/DESCO)</li>
              <li>Public Safety & Law Enforcement</li>
              <li>Pollution & Environment (DoE)</li>
              <li>Healthcare & Dengue Prevention</li>
            </ul>
          </div>

          {/* Legal & Governance */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              {lang === 'bn' ? 'নীতিমালা ও সহায়তা' : 'Governance & Policy'}
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <button onClick={() => onNavigate('privacy')} className="hover:text-white transition">
                  Privacy Policy & Data Protection
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('terms')} className="hover:text-white transition">
                  Terms & Public Conditions
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('about')} className="hover:text-white transition">
                  AI Architecture & Methodology
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('contact')} className="hover:text-white transition">
                  Contact Citizen Helpdesk
                </button>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500">
          <p>© {new Date().getFullYear()} CivicAI Bangladesh. Open Civic Governance Platform.</p>
          <div className="flex items-center space-x-1 mt-2 md:mt-0">
            <span>Built for the Citizens of Bangladesh with</span>
            <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
            <span>& AI Engineering</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
