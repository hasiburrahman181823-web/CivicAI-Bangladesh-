import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, Radio, Layers, ThumbsUp, AlertCircle } from 'lucide-react';
import { fetchFeed, upvoteComplaint, fetchDivisions } from '../api';
import { ComplaintListItem } from '../types';
import { ComplaintCard } from '../components/ComplaintCard';

interface FeedPageProps {
  onSelectComplaint: (id: number) => void;
  initialCategory?: string;
  lang: 'en' | 'bn';
}

export const FeedPage: React.FC<FeedPageProps> = ({
  onSelectComplaint,
  initialCategory = 'All',
  lang
}) => {
  const [complaints, setComplaints] = useState<ComplaintListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedDivision, setSelectedDivision] = useState('All');
  const [selectedDistrict, setSelectedDistrict] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [selectedSeverity, setSelectedSeverity] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [sortBy, setSortBy] = useState('priority');
  const [divisionsData, setDivisionsData] = useState<Record<string, any>>({});
  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);

  useEffect(() => {
    fetchDivisions().then(data => setDivisionsData(data)).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedDivision !== 'All' && divisionsData[selectedDivision]) {
      setAvailableDistricts(Object.keys(divisionsData[selectedDivision].districts || {}));
    } else {
      setAvailableDistricts([]);
      setSelectedDistrict('All');
    }
  }, [selectedDivision, divisionsData]);

  const loadFeed = async () => {
    setLoading(true);
    try {
      const data = await fetchFeed({
        search,
        division: selectedDivision,
        district: selectedDistrict,
        category: selectedCategory,
        severity: selectedSeverity,
        status: selectedStatus,
        sort_by: sortBy,
      });
      setComplaints(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeed();
  }, [selectedDivision, selectedDistrict, selectedCategory, selectedSeverity, selectedStatus, sortBy]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadFeed();
  };

  const handleUpvote = async (id: number) => {
    try {
      const res = await upvoteComplaint(id);
      setComplaints(prev => prev.map(c => c.id === id ? { ...c, upvotes_count: res.upvotes_count } : c));
    } catch (err) {
      console.error(err);
    }
  };

  const categories = [
    'All',
    'Infrastructure',
    'Water & Drainage',
    'Waste Management',
    'Electricity & Power',
    'Streetlight & Lighting',
    'Public Safety & Law',
    'Environment & Pollution',
    'Healthcare & Sanitation',
    'Transport & Traffic',
    'Corruption & Governance'
  ];

  const statuses = [
    { id: 'All', label: 'All Statuses' },
    { id: 'Verified', label: 'Verified by Officer' },
    { id: 'In_Progress', label: 'Active Field Work' },
    { id: 'Resolved', label: 'Resolved Issues' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header and Live indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {lang === 'bn' ? 'পাবলিক অভিযোগ ড্যাশবোর্ড' : 'Public Complaints Dashboard'}
            </h1>
            <span className="flex items-center space-x-1 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold px-2.5 py-0.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              <span>Live Updates</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Browse, filter, and endorse community complaints prioritized by genuine AI across 64 districts.
          </p>
        </div>

        {/* Sort and Refresh */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-500 font-medium">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 font-semibold text-slate-700 focus:ring-2 focus:ring-primary-600 focus:outline-none"
            >
              <option value="priority">🔥 Highest AI Priority</option>
              <option value="date">🕒 Most Recent</option>
              <option value="upvotes">👍 Most Endorsed</option>
            </select>
          </div>

          <button
            onClick={loadFeed}
            title="Refresh Feed"
            className="p-2 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 text-slate-600 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        {/* Search Row */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by keywords, tracking ID, or road/area..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-600"
            />
          </div>
          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-700 text-white font-semibold text-xs px-5 py-2 rounded-xl transition"
          >
            Search
          </button>
        </form>

        {/* Cascaded Location Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Division</label>
            <select
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="w-full border border-slate-300 rounded-lg p-2 bg-white text-slate-700 font-medium"
            >
              <option value="All">All Divisions</option>
              {Object.keys(divisionsData).map((div) => (
                <option key={div} value={div}>{div}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-500 font-semibold mb-1">District</label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              disabled={selectedDivision === 'All'}
              className="w-full border border-slate-300 rounded-lg p-2 bg-white text-slate-700 font-medium disabled:bg-slate-100 disabled:text-slate-400"
            >
              <option value="All">All Districts</option>
              {availableDistricts.map((dist) => (
                <option key={dist} value={dist}>{dist}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-500 font-semibold mb-1">Severity Filter</label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="w-full border border-slate-300 rounded-lg p-2 bg-white text-slate-700 font-medium"
            >
              <option value="All">All Severity Levels</option>
              <option value="Critical">🔴 Critical (Life Hazard)</option>
              <option value="High">🟠 High Urgency</option>
              <option value="Medium">🔵 Medium</option>
              <option value="Low">🟢 Low</option>
            </select>
          </div>
        </div>

        {/* Category Pills Strip */}
        <div className="pt-2 border-t border-slate-100">
          <div className="text-xs font-semibold text-slate-500 mb-2">Filter by Civic Category:</div>
          <div className="flex flex-wrap gap-1.5">
            {categories.map((cat) => {
              const active = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
                    active
                      ? 'bg-primary-600 text-white font-semibold shadow-sm'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {cat}
                </button>
              );
            })}
          </div>
        </div>

        {/* Status Tab Filter */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
          {statuses.map((st) => (
            <button
              key={st.id}
              onClick={() => setSelectedStatus(st.id)}
              className={`text-xs px-3 py-1 rounded-full font-semibold transition ${
                selectedStatus === st.id
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {/* Complaints Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="bg-white p-6 rounded-xl border border-slate-200 animate-pulse h-60"></div>
          ))}
        </div>
      ) : complaints.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 space-y-3">
          <AlertCircle className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No complaints matched your criteria</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Try adjusting your search keywords, division, or category filter to discover reports.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {complaints.map((c) => (
            <ComplaintCard
              key={c.id}
              complaint={c}
              onSelect={onSelectComplaint}
              onUpvote={handleUpvote}
              lang={lang}
            />
          ))}
        </div>
      )}
    </div>
  );
};
