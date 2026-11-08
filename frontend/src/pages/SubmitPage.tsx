import React, { useState, useEffect } from 'react';
import {
  Shield,
  MapPin,
  Sparkles,
  Camera,
  AlertTriangle,
  CheckCircle,
  Copy,
  ExternalLink,
  HelpCircle,
  Upload,
  UserCheck
} from 'lucide-react';
import {
  fetchDivisions,
  previewAI,
  submitGuestComplaint,
  submitAuthenticatedComplaint,
  uploadFile
} from '../api';
import { User, AIPreviewResult } from '../types';

interface SubmitPageProps {
  currentUser: User | null;
  onOpenAuth: () => void;
  onTrackNavigate: (trackingId: string) => void;
  lang: 'en' | 'bn';
}

export const SubmitPage: React.FC<SubmitPageProps> = ({
  currentUser,
  onOpenAuth,
  onTrackNavigate,
  lang
}) => {
  const [mode, setMode] = useState<'guest' | 'registered'>(currentUser ? 'registered' : 'guest');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedDivision, setSelectedDivision] = useState('Dhaka');
  const [selectedDistrict, setSelectedDistrict] = useState('Dhaka');
  const [selectedUpazila, setSelectedUpazila] = useState('Mirpur');
  const [areaName, setAreaName] = useState('');
  const [latitude, setLatitude] = useState<number | null>(23.8068);
  const [longitude, setLongitude] = useState<number | null>(90.3687);
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [honeypot, setHoneypot] = useState(''); // Anti-bot honeypot
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [uploadingImage, setUploadingImage] = useState(false);

  // Administrative Divisions Tree
  const [divisionsData, setDivisionsData] = useState<Record<string, any>>({});
  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);
  const [availableUpazilas, setAvailableUpazilas] = useState<string[]>([]);

  // AI Live Preview state
  const [aiPreview, setAiPreview] = useState<AIPreviewResult | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successModalData, setSuccessModalData] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

  // Load administrative divisions
  useEffect(() => {
    fetchDivisions().then(data => {
      setDivisionsData(data);
      if (data['Dhaka'] && data['Dhaka'].districts['Dhaka']) {
        setAvailableDistricts(Object.keys(data['Dhaka'].districts));
        setAvailableUpazilas(data['Dhaka'].districts['Dhaka']);
      }
    }).catch(console.error);
  }, []);

  // Sync districts when division changes
  useEffect(() => {
    if (divisionsData[selectedDivision]) {
      const dists = Object.keys(divisionsData[selectedDivision].districts || {});
      setAvailableDistricts(dists);
      if (dists.length > 0 && !dists.includes(selectedDistrict)) {
        setSelectedDistrict(dists[0]);
      }
    }
  }, [selectedDivision, divisionsData]);

  // Sync upazilas when district changes
  useEffect(() => {
    if (divisionsData[selectedDivision] && divisionsData[selectedDivision].districts[selectedDistrict]) {
      const upzs = divisionsData[selectedDivision].districts[selectedDistrict];
      setAvailableUpazilas(upzs);
      if (upzs.length > 0 && !upzs.includes(selectedUpazila)) {
        setSelectedUpazila(upzs[0]);
      }
    }
  }, [selectedDistrict, selectedDivision, divisionsData]);

  // Live AI preview debounce
  useEffect(() => {
    if (title.length < 5 || description.length < 15) {
      setAiPreview(null);
      return;
    }

    const timer = setTimeout(async () => {
      setAiLoading(true);
      try {
        const preview = await previewAI(title, description);
        setAiPreview(preview);
      } catch (err) {
        console.error('AI preview error:', err);
      } finally {
        setAiLoading(false);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [title, description]);

  // Handle GPS location auto-detect
  const detectGPS = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(pos.coords.latitude);
          setLongitude(pos.coords.longitude);
        },
        (err) => {
          alert('GPS location access denied or unavailable. You can enter coordinates manually.');
        }
      );
    }
  };

  // Handle Image Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploadingImage(true);
    try {
      const res = await uploadFile(file);
      setUploadedImages(prev => [...prev, res.url]);
    } catch (err: any) {
      alert(err.message || 'Image upload failed');
    } finally {
      setUploadingImage(false);
    }
  };

  // Submit Complaint Handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);

    const payload = {
      title,
      description,
      division: selectedDivision,
      district: selectedDistrict,
      upazila: selectedUpazila,
      area_name: areaName,
      latitude,
      longitude,
      image_urls: uploadedImages,
      contact_email: contactEmail || undefined,
      contact_phone: contactPhone || undefined,
      is_anonymous: isAnonymous,
      website_url_hp: honeypot, // Honeypot field
    };

    try {
      let res;
      if (mode === 'guest' || !currentUser) {
        res = await submitGuestComplaint(payload);
      } else {
        res = await submitAuthenticatedComplaint(payload);
      }
      setSuccessModalData(res);
    } catch (err: any) {
      setSubmitError(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <div className="inline-flex items-center space-x-1.5 text-primary-700 bg-primary-50 px-3 py-1 rounded-full text-xs font-bold">
          <Shield className="w-3.5 h-3.5" />
          <span>National Civic Reporting Service</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          {lang === 'bn' ? 'পাবলিক অভিযোগ দাখিল করুন' : 'Report a Civic Grievance'}
        </h1>
        <p className="text-xs text-slate-500">
          Report municipal or infrastructure hazards across Bangladesh. Real-time AI analysis & departmental dispatch.
        </p>

        {/* Mode Selector Tabs */}
        <div className="inline-flex bg-slate-100 p-1 rounded-xl text-xs font-semibold mt-4">
          <button
            type="button"
            onClick={() => setMode('guest')}
            className={`px-4 py-2 rounded-lg transition ${
              mode === 'guest'
                ? 'bg-white text-slate-900 shadow-sm font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            🛡️ Guest Mode (No Login)
          </button>
          <button
            type="button"
            onClick={() => {
              if (!currentUser) onOpenAuth();
              else setMode('registered');
            }}
            className={`px-4 py-2 rounded-lg transition ${
              mode === 'registered'
                ? 'bg-white text-slate-900 shadow-sm font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {currentUser ? `👤 Registered (${currentUser.full_name})` : '👤 Registered User Mode'}
          </button>
        </div>
      </div>

      {submitError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{submitError}</span>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        {/* Anti-bot Honeypot field (Hidden from real users) */}
        <div className="hidden" aria-hidden="true">
          <label>Do not fill this field</label>
          <input
            type="text"
            name="website_url_hp"
            value={honeypot}
            onChange={(e) => setHoneypot(e.target.value)}
            tabIndex={-1}
            autoComplete="off"
          />
        </div>

        {/* Title */}
        <div>
          <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide mb-1.5">
            Complaint Title / Headline <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. কালভার্ট ধসে পড়েছে / 11kV live snapped wire hanging on road / Drain overflow"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
          />
          <p className="text-[11px] text-slate-400 mt-1">
            Supports Bangla, English, and Banglish. Be clear and specific.
          </p>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide mb-1.5">
            Detailed Description <span className="text-rose-500">*</span>
          </label>
          <textarea
            required
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the severity, exact location landmarks, potential hazards, and how long this issue has persisted..."
            className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent leading-relaxed"
          />
        </div>

        {/* Live AI Assistance Card */}
        {(aiLoading || aiPreview) && (
          <div className="p-4 bg-primary-50/70 border border-primary-200 rounded-xl space-y-3 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-primary-800 font-bold text-xs uppercase tracking-wide">
                <Sparkles className="w-4 h-4 text-primary-600 animate-spin" />
                <span>AI Live Intelligence Assistant (BanglaPSG Aligned)</span>
              </div>
              {aiLoading && <span className="text-[11px] text-primary-600 font-medium">Analyzing NLP features...</span>}
            </div>

            {aiPreview && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="bg-white p-2.5 rounded-lg border border-primary-100">
                  <span className="text-slate-400 text-[10px] font-semibold uppercase block">Predicted Category</span>
                  <strong className="text-slate-800 font-bold">{aiPreview.predicted_category}</strong>
                  <span className="text-[10px] text-primary-600 ml-1">({Math.round(aiPreview.category_confidence * 100)}%)</span>
                </div>

                <div className="bg-white p-2.5 rounded-lg border border-primary-100">
                  <span className="text-slate-400 text-[10px] font-semibold uppercase block">Estimated Severity</span>
                  <strong className="text-rose-700 font-bold">{aiPreview.predicted_severity}</strong>
                  <span className="text-[10px] text-slate-500 ml-1">({Math.round(aiPreview.severity_confidence * 100)}%)</span>
                </div>

                <div className="bg-white p-2.5 rounded-lg border border-primary-100">
                  <span className="text-slate-400 text-[10px] font-semibold uppercase block">Estimated Priority Index</span>
                  <strong className="text-primary-700 font-extrabold text-sm">{aiPreview.estimated_priority_score}/100</strong>
                  <span className="text-[10px] text-slate-500 ml-1">({aiPreview.priority_level})</span>
                </div>

                {/* Duplicate Warning */}
                {aiPreview.is_duplicate_flagged && aiPreview.potential_duplicates.length > 0 && (
                  <div className="col-span-full p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-xs flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="font-bold">Similar complaint already reported nearby!</strong>
                      <p className="text-[11px] mt-0.5">
                        Issue #{aiPreview.potential_duplicates[0].tracking_id} ("{aiPreview.potential_duplicates[0].title}") was reported in your vicinity. Your report will be cross-referenced to accelerate response.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Administrative Location Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Division *</label>
            <select
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="w-full border border-slate-300 rounded-xl p-2.5 text-sm bg-white font-medium"
            >
              {Object.keys(divisionsData).map((div) => (
                <option key={div} value={div}>{div}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">District *</label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="w-full border border-slate-300 rounded-xl p-2.5 text-sm bg-white font-medium"
            >
              {availableDistricts.map((dist) => (
                <option key={dist} value={dist}>{dist}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Upazila / Thana *</label>
            <select
              value={selectedUpazila}
              onChange={(e) => setSelectedUpazila(e.target.value)}
              className="w-full border border-slate-300 rounded-xl p-2.5 text-sm bg-white font-medium"
            >
              {availableUpazilas.map((upz) => (
                <option key={upz} value={upz}>{upz}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Area Name / Landmark */}
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Area / Road / Landmark</label>
          <input
            type="text"
            value={areaName}
            onChange={(e) => setAreaName(e.target.value)}
            placeholder="e.g. Block C, Road 14, in front of City High School"
            className="w-full px-4 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-600"
          />
        </div>

        {/* GPS Coordinates & Auto Detect Button */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 flex items-center space-x-1.5">
              <MapPin className="w-4 h-4 text-primary-600" />
              <span>GPS Coordinates (Optional for precision map placing)</span>
            </span>
            <button
              type="button"
              onClick={detectGPS}
              className="text-xs font-bold text-primary-700 bg-white border border-primary-200 hover:bg-primary-50 px-3 py-1.5 rounded-lg transition shadow-sm"
            >
              📍 Auto-Detect My Location
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-500 font-medium">Latitude:</span>
              <input
                type="number"
                step="any"
                value={latitude || ''}
                onChange={(e) => setLatitude(parseFloat(e.target.value) || null)}
                placeholder="23.8068"
                className="w-full mt-1 p-2 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div>
              <span className="text-slate-500 font-medium">Longitude:</span>
              <input
                type="number"
                step="any"
                value={longitude || ''}
                onChange={(e) => setLongitude(parseFloat(e.target.value) || null)}
                placeholder="90.3687"
                className="w-full mt-1 p-2 border border-slate-300 rounded-lg text-xs"
              />
            </div>
          </div>
        </div>

        {/* Media Photo Upload */}
        <div>
          <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide mb-1.5">
            Attach Evidence Photos (Max 10 MB)
          </label>
          <div className="flex items-center space-x-3">
            <label className="cursor-pointer bg-white border border-slate-300 hover:border-primary-500 px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:text-primary-600 flex items-center space-x-2 transition shadow-sm">
              <Upload className="w-4 h-4" />
              <span>{uploadingImage ? 'Uploading...' : 'Choose File'}</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                disabled={uploadingImage}
                className="hidden"
              />
            </label>
            <span className="text-xs text-slate-400">
              {uploadedImages.length} image(s) attached
            </span>
          </div>
          {uploadedImages.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {uploadedImages.map((url, i) => (
                <div key={i} className="relative w-16 h-16 rounded-lg overflow-hidden border border-slate-200">
                  <img src={url} alt="upload" className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Guest Optional Contact Info */}
        {mode === 'guest' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Contact Phone (Optional - for SMS updates)
              </label>
              <input
                type="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="+8801812345678"
                className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Contact Email (Optional)
              </label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="citizen@example.com"
                className="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs"
              />
            </div>
          </div>
        )}

        {/* Anonymous Checkbox */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="anon-check"
            checked={isAnonymous}
            onChange={(e) => setIsAnonymous(e.target.checked)}
            className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
          />
          <label htmlFor="anon-check" className="text-xs font-medium text-slate-700">
            Keep this submission strictly anonymous (Hides contact info from public portal)
          </label>
        </div>

        {/* Submit CTA */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-extrabold py-3.5 rounded-xl shadow-lg shadow-primary-600/30 transition text-sm disabled:opacity-50"
        >
          {submitting
            ? 'Submitting & Running AI Intelligence Analysis...'
            : 'Submit Complaint (Submit & Get Tracking ID)'}
        </button>
      </form>

      {/* Success Modal */}
      {successModalData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-8 space-y-6 border border-slate-100 shadow-2xl text-center">
            <div className="w-16 h-16 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center mx-auto shadow-inner">
              <CheckCircle className="w-10 h-10" />
            </div>

            <div className="space-y-1">
              <h3 className="text-2xl font-extrabold text-slate-900">Complaint Successfully Registered!</h3>
              <p className="text-xs text-slate-500">
                Your issue has been analyzed by CivicAI and prioritized for administrative field response.
              </p>
            </div>

            {/* Tracking ID & PIN Box */}
            <div className="bg-slate-50 border-2 border-primary-500/30 p-5 rounded-2xl space-y-3">
              <div>
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                  Your Unique Tracking ID:
                </span>
                <div className="flex items-center justify-center space-x-2 mt-1">
                  <span className="text-2xl font-mono font-extrabold text-primary-700 tracking-wider">
                    {successModalData.tracking_id}
                  </span>
                  <button
                    onClick={() => copyToClipboard(successModalData.tracking_id)}
                    className="p-1.5 text-slate-500 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition"
                    title="Copy Tracking ID"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                {copied && <span className="text-[10px] text-emerald-600 font-bold">Copied to clipboard!</span>}
              </div>

              {successModalData.access_pin && (
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                    Guest Access PIN:
                  </span>
                  <span className="text-lg font-mono font-bold text-slate-800">
                    {successModalData.access_pin}
                  </span>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Save this PIN to verify identity when checking confidential complaint updates.
                  </p>
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-slate-400 block text-[10px]">AI Priority:</span>
                <strong className="text-primary-700">{successModalData.priority_score}/100 ({successModalData.priority_level})</strong>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg">
                <span className="text-slate-400 block text-[10px]">Assigned Routing:</span>
                <strong className="text-slate-800 truncate block">{successModalData.recommended_department}</strong>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3">
              <button
                onClick={() => onTrackNavigate(successModalData.tracking_id)}
                className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 rounded-xl transition text-xs flex items-center justify-center space-x-1"
              >
                <span>Track This Complaint Now</span>
                <ExternalLink className="w-4 h-4" />
              </button>
              <button
                onClick={() => setSuccessModalData(null)}
                className="px-5 py-3 border border-slate-300 hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
