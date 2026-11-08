import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ArrowRight,
  PlusCircle,
  Search,
  MapPin,
  CheckCircle2,
  Sparkles,
  Zap,
  TrendingUp,
  Flame,
  AlertTriangle,
  Building2,
  Droplets,
  Trash2,
  Lightbulb,
  Radio,
  FileCheck2
} from 'lucide-react';
import { fetchFeed } from '../api';
import { ComplaintListItem } from '../types';
import { ComplaintCard } from '../components/ComplaintCard';

interface HomePageProps {
  onNavigate: (tab: string, meta?: any) => void;
  onSelectComplaint: (id: number) => void;
  lang: 'en' | 'bn';
}

export const HomePage: React.FC<HomePageProps> = ({
  onNavigate,
  onSelectComplaint,
  lang
}) => {
  const [quickTrackId, setQuickTrackId] = useState('');
  const [featuredComplaints, setFeaturedComplaints] = useState<ComplaintListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeed({ limit: 6, sort_by: 'priority' })
      .then((data) => setFeaturedComplaints(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleQuickTrack = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickTrackId.trim()) {
      onNavigate('track', { trackingId: quickTrackId.trim() });
    }
  };

  const civicCategories = [
    { name: 'Infrastructure', bn: 'সড়ক ও অবকাঠামো', icon: Building2, desc: 'Potholes, collapsed culverts, footpaths' },
    { name: 'Water & Drainage', bn: 'পানি ও পয়ঃনিষ্কাশন', icon: Droplets, desc: 'Waterlogging, contaminated supply, open manholes' },
    { name: 'Waste Management', bn: 'বর্জ্য ব্যবস্থাপনা', icon: Trash2, desc: 'Garbage piles, illegal dumping, biohazard waste' },
    { name: 'Electricity & Power', bn: 'বিদ্যুৎ ও জ্বালানি', icon: Zap, desc: 'Snapped high-tension wires, transformer failure' },
    { name: 'Streetlight & Lighting', bn: 'সড়কবাতি', icon: Lightbulb, desc: 'Dead streetlights, dark alleys, exposed wires' },
    { name: 'Public Safety & Law', bn: 'জননিরাপত্তা', icon: ShieldAlert, desc: 'Mugging spots, harassment, public hazards' },
    { name: 'Environment & Pollution', bn: 'পরিবেশ ও দূষণ', icon: Flame, desc: 'Industrial chemical runoff, black smoke, dumping' },
    { name: 'Transport & Traffic', bn: 'পরিবহন ও ট্রাফিক', icon: Radio, desc: 'Reckless speeding, missing overbridges, illegal stands' }
  ];

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-primary-50/60 via-white to-slate-50 border-b border-slate-200/80 pt-16 pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            {/* Government AI Badge */}
            <div className="inline-flex items-center space-x-2 bg-primary-100/80 border border-primary-200 text-primary-800 px-3.5 py-1.5 rounded-full text-xs font-bold tracking-wide shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-primary-600" />
              <span>
                {lang === 'bn'
                  ? 'কৃত্রিম বুদ্ধিমত্তা চালিত বাংলাদেশ নাগরিক সেবা প্ল্যাটফর্ম'
                  : 'AI-Powered Citizen Grievance & Municipal Resolution Platform'}
              </span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15]">
              {lang === 'bn' ? (
                <>
                  আপনার এলাকার সমস্যা জানান, <br />
                  <span className="text-primary-600">স্বচ্ছ সমাধান পান।</span>
                </>
              ) : (
                <>
                  Report Local Civic Problems, <br />
                  <span className="text-primary-600">Track Transparent Solutions.</span>
                </>
              )}
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
              {lang === 'bn'
                ? 'লগইন ছাড়াই মাত্র ২ মিনিটে অভিযোগ জমা দিন। আমাদের এআই সিস্টেম স্বয়ংক্রিয়ভাবে অভিযোগ বিশ্লেষণ, গুরুত্ব নির্ধারণ ও সংশ্লিষ্ট বিভাগকে দ্রুত পদক্ষেপের নির্দেশ দেয়।'
                : 'Submit complaints without logging in. Our Bangla-English AI intelligence engine automatically classifies categories, predicts severity, ranks priority, and routes issues to municipal authorities.'}
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              <button
                onClick={() => onNavigate('submit')}
                className="w-full sm:w-auto bg-primary-600 hover:bg-primary-700 text-white font-bold px-7 py-3.5 rounded-xl shadow-lg shadow-primary-600/25 transition flex items-center justify-center space-x-2.5 text-sm"
              >
                <PlusCircle className="w-5 h-5" />
                <span>{lang === 'bn' ? 'লগইন ছাড়াই অভিযোগ করুন (গেস্ট মোড)' : 'Report Issue (Guest Mode)'}</span>
              </button>

              <button
                onClick={() => onNavigate('feed')}
                className="w-full sm:w-auto bg-white hover:bg-slate-50 text-slate-800 font-semibold px-6 py-3.5 rounded-xl border border-slate-300 shadow-sm transition flex items-center justify-center space-x-2 text-sm"
              >
                <Search className="w-4 h-4 text-slate-500" />
                <span>{lang === 'bn' ? 'পাবলিক অভিযোগ দেখুন' : 'Explore Public Feed'}</span>
              </button>

              <button
                onClick={() => onNavigate('map')}
                className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-white font-semibold px-6 py-3.5 rounded-xl shadow-sm transition flex items-center justify-center space-x-2 text-sm"
              >
                <MapPin className="w-4 h-4 text-primary-400" />
                <span>{lang === 'bn' ? 'লাইভ ম্যাপ দেখুন' : 'Live Map'}</span>
              </button>
            </div>

            {/* Quick Tracking Search Bar */}
            <form
              onSubmit={handleQuickTrack}
              className="mt-8 max-w-xl mx-auto flex items-center bg-white p-2 rounded-2xl border border-slate-300 shadow-md focus-within:ring-2 focus-within:ring-primary-600 focus-within:border-transparent transition"
            >
              <div className="pl-3 text-slate-400">
                <Search className="w-5 h-5 text-primary-600" />
              </div>
              <input
                type="text"
                value={quickTrackId}
                onChange={(e) => setQuickTrackId(e.target.value)}
                placeholder={lang === 'bn' ? 'ট্র্যাকিং আইডি লিখুন (যেমন BD-2026-X8F4K2)...' : 'Enter Tracking ID (e.g. BD-2026-10001)...'}
                className="flex-1 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
              />
              <button
                type="submit"
                className="bg-primary-600 hover:bg-primary-700 text-white font-bold text-xs uppercase px-5 py-2.5 rounded-xl transition shadow-sm"
              >
                {lang === 'bn' ? 'খুঁজুন' : 'Track'}
              </button>
            </form>
          </div>
        </div>

        {/* Live Metrics Counter Strip */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-14">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white/90 backdrop-blur-md p-6 rounded-2xl border border-slate-200/80 shadow-sm text-center">
            <div className="border-r border-slate-100 last:border-0 p-2">
              <div className="text-3xl font-extrabold text-slate-900 tracking-tight">2,100+</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wide">
                Complaints Processed
              </div>
            </div>
            <div className="border-r border-slate-100 last:border-0 p-2">
              <div className="text-3xl font-extrabold text-primary-600 tracking-tight">98.2%</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wide">
                AI Classification Accuracy
              </div>
            </div>
            <div className="border-r border-slate-100 last:border-0 p-2">
              <div className="text-3xl font-extrabold text-slate-900 tracking-tight">64 Districts</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wide">
                Nationwide Coverage
              </div>
            </div>
            <div className="p-2">
              <div className="text-3xl font-extrabold text-emerald-600 tracking-tight">24-48 hrs</div>
              <div className="text-xs font-semibold text-slate-500 mt-1 uppercase tracking-wide">
                Emergency SLA Response
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Urgent Issues Breaking Ticker */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3 overflow-hidden">
            <span className="bg-rose-600 text-white text-xs font-extrabold px-2.5 py-1 rounded-md uppercase tracking-wider flex items-center space-x-1 shrink-0">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Urgent Alerts</span>
            </span>
            <div className="text-xs text-rose-900 font-medium truncate">
              🔴 Live 11kV snapped wire hazard in Uttara Sector 4 (Field Unit Dispatched) • 🔴 Open manhole flooding in Mirpur 10 • 🟠 Bridge erosion alert in Dhanmondi
            </div>
          </div>
          <button
            onClick={() => onNavigate('map')}
            className="text-xs font-bold text-rose-700 hover:text-rose-900 underline shrink-0 pl-3"
          >
            View on Map →
          </button>
        </div>
      </section>

      {/* How CivicAI Works Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {lang === 'bn' ? 'কিভাবে কাজ করে CivicAI Bangladesh?' : 'How CivicAI Bangladesh Works'}
          </h2>
          <p className="text-sm text-slate-500 mt-2">
            A seamless, transparent 4-stage pipeline combining genuine AI with verified administrative accountability.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative group hover:border-primary-400 transition">
            <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold text-lg mb-4">
              1
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Instant Public Report</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Submit in Bangla, English, or Banglish without login. Attach GPS location and photos. Receive unique Tracking ID.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative group hover:border-primary-400 transition">
            <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold text-lg mb-4">
              2
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">AI Multilingual NLP</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              BanglaPSG trained models automatically classify category, predict severity, check duplicates, and compute priority score.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative group hover:border-primary-400 transition">
            <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold text-lg mb-4">
              3
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Human Verification</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Municipal officers review AI recommendations, verify evidence, assign official departments (RHD, WASA, Power), and set SLA.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative group hover:border-primary-400 transition">
            <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold text-lg mb-4">
              4
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Transparent Resolution</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Field units upload before/after photos and resolution notes. Citizens verify and provide public satisfaction feedback.
            </p>
          </div>
        </div>
      </section>

      {/* Civic Categories Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              {lang === 'bn' ? 'সেবা ও অভিযোগের খাতসমূহ' : 'Civic Issue Categories'}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Select any civic sector to view active complaints and municipal resolution teams.
            </p>
          </div>
          <button
            onClick={() => onNavigate('feed')}
            className="text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center space-x-1"
          >
            <span>View All</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {civicCategories.map((cat) => {
            const Icon = cat.icon;
            return (
              <div
                key={cat.name}
                onClick={() => onNavigate('feed', { category: cat.name })}
                className="bg-white p-5 rounded-xl border border-slate-200 hover:border-primary-400 hover:shadow-md cursor-pointer transition group"
              >
                <div className="w-10 h-10 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center mb-3 group-hover:bg-primary-600 group-hover:text-white transition">
                  <Icon className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-bold text-slate-900 mb-1">
                  {lang === 'bn' ? cat.bn : cat.name}
                </h4>
                <p className="text-[11px] text-slate-500 leading-snug">{cat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Featured Urgent Complaints Feed */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-primary-600" />
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              {lang === 'bn' ? 'জরুরি অগ্রাধিকারপ্রাপ্ত অভিযোগসমূহ' : 'High Priority Community Issues'}
            </h2>
          </div>
          <button
            onClick={() => onNavigate('feed')}
            className="text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center space-x-1"
          >
            <span>Explore All Feed</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="bg-white p-6 rounded-xl border border-slate-200 animate-pulse h-52"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {featuredComplaints.slice(0, 6).map((c) => (
              <ComplaintCard
                key={c.id}
                complaint={c}
                onSelect={onSelectComplaint}
                onUpvote={() => {}}
                lang={lang}
              />
            ))}
          </div>
        )}
      </section>

      {/* Citizen Call-to-action Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-primary-700 via-primary-600 to-primary-800 rounded-2xl p-8 sm:p-12 text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {lang === 'bn' ? 'আপনার এলাকায় কোনো নাগরিক সমস্যা দেখেছেন?' : 'Spotted a problem in your neighborhood?'}
            </h3>
            <p className="text-sm text-primary-100 leading-relaxed">
              Help your community today. Report broken roads, waterlogging, or power hazards. No login required.
            </p>
          </div>
          <button
            onClick={() => onNavigate('submit')}
            className="bg-white text-primary-800 hover:bg-primary-50 font-extrabold px-8 py-3.5 rounded-xl shadow-lg transition text-sm shrink-0"
          >
            {lang === 'bn' ? 'এখনই অভিযোগ জমা দিন' : 'Report Now (Guest Access)'}
          </button>
        </div>
      </section>
    </div>
  );
};
