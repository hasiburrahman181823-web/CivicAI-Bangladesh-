import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { AuthModal } from './components/AuthModal';
import { HomePage } from './pages/HomePage';
import { FeedPage } from './pages/FeedPage';
import { SubmitPage } from './pages/SubmitPage';
import { TrackPage } from './pages/TrackPage';
import { DetailPage } from './pages/DetailPage';
import { StatsPage } from './pages/StatsPage';
import { AdminPage } from './pages/AdminPage';
import { LiveMap } from './components/LiveMap';
import { InfoPages } from './pages/InfoPages';
import { User } from './types';
import { getStoredUser, logoutUser } from './api';
import { Bell, X } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [selectedComplaintId, setSelectedComplaintId] = useState<number | null>(null);
  const [trackTargetId, setTrackTargetId] = useState('');
  const [feedCategoryFilter, setFeedCategoryFilter] = useState('All');
  const [currentUser, setCurrentUser] = useState<User | null>(getStoredUser());
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [lang, setLang] = useState<'en' | 'bn'>('en');

  // Live WebSocket notifications
  const [liveToast, setLiveToast] = useState<{ title: string; message: string } | null>(null);

  useEffect(() => {
    // Establish real-time WebSocket connection
    const wsUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
      (window.location.hostname || 'localhost') + ':8000/ws/complaints';

    let socket: WebSocket | null = null;
    try {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === 'NEW_COMPLAINT') {
            setLiveToast({
              title: 'New Complaint Registered',
              message: `#${payload.data.tracking_id} in ${payload.data.upazila}, ${payload.data.district} (Priority: ${payload.data.ai_priority_score}/100)`
            });
            setTimeout(() => setLiveToast(null), 5000);
          } else if (payload.event === 'STATUS_CHANGED') {
            setLiveToast({
              title: 'Complaint Status Updated',
              message: `Issue #${payload.data.complaint_id} marked as ${payload.data.new_status}`
            });
            setTimeout(() => setLiveToast(null), 5000);
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };
    } catch (e) {
      console.warn('WebSocket connection not established:', e);
    }

    return () => {
      if (socket) socket.close();
    };
  }, []);

  const handleNavigate = (tab: string, meta?: any) => {
    if (tab === 'track' && meta?.trackingId) {
      setTrackTargetId(meta.trackingId);
    }
    if (tab === 'feed' && meta?.category) {
      setFeedCategoryFilter(meta.category);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectComplaint = (id: number) => {
    setSelectedComplaintId(id);
    setActiveTab('detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTrackNavigate = (trackingId: string) => {
    setTrackTargetId(trackingId);
    setActiveTab('track');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={handleNavigate}
        currentUser={currentUser}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
        lang={lang}
        setLang={setLang}
      />

      {/* Real-time WebSocket Live Alert Toast */}
      {liveToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white p-4 rounded-2xl shadow-2xl border border-slate-700 flex items-start space-x-3 max-w-sm animate-in slide-in-from-bottom-5">
          <div className="p-2 bg-primary-600 rounded-xl text-white shrink-0 mt-0.5">
            <Bell className="w-4 h-4 animate-bounce" />
          </div>
          <div className="flex-1">
            <h4 className="text-xs font-bold text-white">{liveToast.title}</h4>
            <p className="text-[11px] text-slate-300 mt-0.5 leading-snug">{liveToast.message}</p>
          </div>
          <button
            onClick={() => setLiveToast(null)}
            className="text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Page Body Routing */}
      <main className="flex-1">
        {activeTab === 'home' && (
          <HomePage
            onNavigate={handleNavigate}
            onSelectComplaint={handleSelectComplaint}
            lang={lang}
          />
        )}

        {activeTab === 'feed' && (
          <FeedPage
            onSelectComplaint={handleSelectComplaint}
            initialCategory={feedCategoryFilter}
            lang={lang}
          />
        )}

        {activeTab === 'map' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <LiveMap
              onSelectComplaint={handleSelectComplaint}
              lang={lang}
            />
          </div>
        )}

        {activeTab === 'submit' && (
          <SubmitPage
            currentUser={currentUser}
            onOpenAuth={() => setAuthModalOpen(true)}
            onTrackNavigate={handleTrackNavigate}
            lang={lang}
          />
        )}

        {activeTab === 'track' && (
          <TrackPage
            initialTrackingId={trackTargetId}
            lang={lang}
          />
        )}

        {activeTab === 'detail' && selectedComplaintId && (
          <DetailPage
            complaintId={selectedComplaintId}
            onBack={() => setActiveTab('feed')}
            currentUser={currentUser}
            lang={lang}
          />
        )}

        {activeTab === 'stats' && (
          <StatsPage lang={lang} />
        )}

        {activeTab === 'admin' && (
          <AdminPage
            currentUser={currentUser}
            onOpenAuth={() => setAuthModalOpen(true)}
            lang={lang}
          />
        )}

        {['about', 'contact', 'privacy', 'terms'].includes(activeTab) && (
          <InfoPages page={activeTab as any} lang={lang} />
        )}
      </main>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(u) => {
          setCurrentUser(u);
          setAuthModalOpen(false);
        }}
        lang={lang}
      />

      {/* Footer */}
      <Footer onNavigate={handleNavigate} lang={lang} />
    </div>
  );
}

export default App;
