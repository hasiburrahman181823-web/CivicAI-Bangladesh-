import React, { useState } from 'react';
import {
  ShieldAlert,
  FileText,
  MapPin,
  Search,
  BarChart3,
  User as UserIcon,
  LogOut,
  Menu,
  X,
  Compass,
  PlusCircle,
  ExternalLink
} from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentUser: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  lang: 'en' | 'bn';
  setLang: (lang: 'en' | 'bn') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onOpenAuth,
  onLogout,
  lang,
  setLang
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'home', label: lang === 'bn' ? 'হোম' : 'Home', icon: Compass },
    { id: 'feed', label: lang === 'bn' ? 'অভিযোগসমূহ' : 'Complaints Feed', icon: FileText },
    { id: 'map', label: lang === 'bn' ? 'লাইভ ম্যাপ' : 'Live Map', icon: MapPin },
    { id: 'track', label: lang === 'bn' ? 'ট্র্যাকিং' : 'Track Status', icon: Search },
    { id: 'stats', label: lang === 'bn' ? 'পরিসংখ্যান' : 'Transparency Stats', icon: BarChart3 },
    { id: 'about', label: lang === 'bn' ? 'আমাদের সম্পর্কে' : 'About', icon: ExternalLink },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
      {/* Top National Ribbon */}
      <div className="bg-slate-900 text-slate-300 text-xs py-1.5 px-4 font-medium tracking-wide">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="inline-block w-2 h-2 rounded-full bg-primary-500 animate-pulse"></span>
            <span>
              {lang === 'bn'
                ? 'গণপ্রজাতন্ত্রী বাংলাদেশ — এআই ভিত্তিক পাবলিক অভিযোগ ও সেবা পোর্টাল'
                : "People's Republic of Bangladesh — AI-Powered Smart Public Complaint & Governance Portal"}
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setLang(lang === 'en' ? 'bn' : 'en')}
              className="text-white hover:text-primary-400 font-semibold transition flex items-center space-x-1"
            >
              <span>{lang === 'en' ? 'বাংলা সংস্করণ' : 'English Version'}</span>
            </button>
            <span className="hidden md:inline text-slate-500">|</span>
            <span className="hidden md:inline text-slate-400">Emergency Helpline: 999 / 333</span>
          </div>
        </div>
      </div>

      {/* Main Header Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div
            onClick={() => setActiveTab('home')}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center text-white shadow-md shadow-primary-600/20 group-hover:bg-primary-700 transition">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">
                  Civic<span className="text-primary-600">AI</span>
                </span>
                <span className="text-xs bg-primary-100 text-primary-800 font-semibold px-1.5 py-0.5 rounded">
                  BD
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">Smart Public Grievance Platform</p>
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center space-x-1.5 ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-primary-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}

            {/* Admin Portal Tab (visible to admin or officer) */}
            {currentUser && (currentUser.role === 'admin' || currentUser.role === 'officer') && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`px-3 py-2 rounded-lg text-sm font-semibold transition ${
                  activeTab === 'admin'
                    ? 'bg-primary-600 text-white'
                    : 'text-primary-700 bg-primary-50 hover:bg-primary-100'
                }`}
              >
                {lang === 'bn' ? 'অ্যাডমিন প্যানেল' : 'Admin Panel'}
              </button>
            )}
          </nav>

          {/* Action CTAs */}
          <div className="hidden md:flex items-center space-x-3">
            <button
              onClick={() => setActiveTab('submit')}
              className="bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-sm shadow-primary-600/30 transition flex items-center space-x-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{lang === 'bn' ? 'অভিযোগ জানান' : 'Report Issue'}</span>
            </button>

            {currentUser ? (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
                <div className="text-right">
                  <div className="text-xs font-semibold text-slate-900">{currentUser.full_name}</div>
                  <div className="text-[10px] text-slate-500 capitalize">{currentUser.role}</div>
                </div>
                <button
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-2 text-slate-500 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="text-sm font-semibold text-slate-700 hover:text-slate-900 px-3 py-2 rounded-lg hover:bg-slate-100 transition flex items-center space-x-1"
              >
                <UserIcon className="w-4 h-4 text-slate-500" />
                <span>{lang === 'bn' ? 'লগইন' : 'Sign In'}</span>
              </button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('submit')}
              className="bg-primary-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg"
            >
              Report
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-600 hover:text-slate-900 focus:outline-none"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-200 px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 ${
                  activeTab === item.id ? 'bg-primary-50 text-primary-700 font-semibold' : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
          {currentUser && (currentUser.role === 'admin' || currentUser.role === 'officer') && (
            <button
              onClick={() => {
                setActiveTab('admin');
                setMobileMenuOpen(false);
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold bg-primary-50 text-primary-700"
            >
              Admin Panel
            </button>
          )}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            {currentUser ? (
              <div className="flex items-center justify-between w-full">
                <span className="text-xs font-medium text-slate-700">{currentUser.full_name}</span>
                <button
                  onClick={() => {
                    onLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="text-xs text-rose-600 font-semibold"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  onOpenAuth();
                  setMobileMenuOpen(false);
                }}
                className="w-full text-center text-sm font-semibold text-primary-600 py-2 border border-primary-200 rounded-lg"
              >
                Sign In / Register
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
