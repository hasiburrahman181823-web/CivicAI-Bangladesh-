import React, { useState } from 'react';
import { X, Shield, Lock, Mail, User as UserIcon, Phone, CheckCircle, AlertCircle } from 'lucide-react';
import { loginUser, registerUser } from '../api';
import { User } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
  lang: 'en' | 'bn';
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess, lang }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'login') {
        const res = await loginUser(email, password);
        onSuccess(res.user);
        onClose();
      } else {
        const res = await registerUser(email, fullName, password, phone);
        onSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (type: 'citizen' | 'admin') => {
    setMode('login');
    setError(null);
    if (type === 'admin') {
      setEmail('admin@civicai.gov.bd');
      setPassword('Admin@CivicAI2026!');
    } else {
      setEmail('citizen.dhaka@gmail.com');
      setPassword('Citizen@2026!');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-100">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center space-x-2 text-primary-400 mb-1">
            <Shield className="w-5 h-5" />
            <span className="text-xs uppercase tracking-wider font-bold">CivicAI Bangladesh Secure Auth</span>
          </div>
          <h3 className="text-xl font-bold text-white">
            {mode === 'login'
              ? (lang === 'bn' ? 'অ্যাকাউন্টে সাইন ইন করুন' : 'Sign in to Account')
              : (lang === 'bn' ? 'নতুন নাগরিক অ্যাকাউন্ট খুলুন' : 'Create Citizen Account')}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            {mode === 'login'
              ? 'Access your personal complaint dashboard and upvote history.'
              : 'Join fellow citizens in tracking and improving local communities.'}
          </p>

          {/* Tab Selector */}
          <div className="flex bg-slate-800/80 p-1 rounded-lg mt-4 text-xs font-semibold">
            <button
              onClick={() => { setMode('login'); setError(null); }}
              className={`flex-1 py-1.5 rounded-md transition ${mode === 'login' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setMode('register'); setError(null); }}
              className={`flex-1 py-1.5 rounded-md transition ${mode === 'register' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Register
            </button>
          </div>
        </div>

        {/* Form Body */}
        <div className="p-6">
          {/* Quick Demo Fillers */}
          <div className="mb-4 p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-2">
              ⚡ Instant Demo Testing:
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setDemoCredentials('citizen')}
                className="bg-white hover:bg-primary-50 text-slate-700 hover:text-primary-700 border border-slate-200 hover:border-primary-300 font-semibold py-1.5 px-2.5 rounded-lg transition text-left"
              >
                👤 Citizen Demo
              </button>
              <button
                type="button"
                onClick={() => setDemoCredentials('admin')}
                className="bg-white hover:bg-primary-50 text-slate-700 hover:text-primary-700 border border-slate-200 hover:border-primary-300 font-semibold py-1.5 px-2.5 rounded-lg transition text-left"
              >
                🛡️ Admin Demo
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3.5">
            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Tanvir Hossain"
                      className="w-full text-sm pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Phone Number (Optional)</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+8801812345678"
                      className="w-full text-sm pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full text-sm pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full text-sm pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 rounded-lg shadow-sm shadow-primary-600/30 transition text-sm disabled:opacity-50 mt-2"
            >
              {loading ? 'Authenticating...' : mode === 'login' ? 'Sign In to Portal' : 'Create Account'}
            </button>
          </form>

          <p className="text-[11px] text-slate-400 text-center mt-4">
            Protected by end-to-end bcrypt hashing and encrypted JWT sessions.
          </p>
        </div>
      </div>
    </div>
  );
};
