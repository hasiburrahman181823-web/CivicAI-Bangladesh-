import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Filter, Layers, Navigation, Sparkles } from 'lucide-react';
import { fetchMapMarkers } from '../api';

interface LiveMapProps {
  onSelectComplaint: (id: number) => void;
  lang: 'en' | 'bn';
}

export const LiveMap: React.FC<LiveMapProps> = ({ onSelectComplaint, lang }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  const [markersData, setMarkersData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDivision, setSelectedDivision] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedSeverity, setSelectedSeverity] = useState('All');

  // Load marker data from API
  const loadMarkers = async () => {
    setLoading(true);
    try {
      const data = await fetchMapMarkers({
        division: selectedDivision,
        category: selectedCategory,
        severity: selectedSeverity,
      });
      setMarkersData(data);
    } catch (err) {
      console.error('Failed to load map markers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMarkers();
  }, [selectedDivision, selectedCategory, selectedSeverity]);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center of Bangladesh
    const map = L.map(mapContainerRef.current).setView([23.8103, 90.4125], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors | CivicAI Bangladesh',
      maxZoom: 18,
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    markersLayerRef.current = layerGroup;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update markers on map
  useEffect(() => {
    if (!markersLayerRef.current || !mapInstanceRef.current) return;

    markersLayerRef.current.clearLayers();

    markersData.forEach((item) => {
      if (!item.latitude || !item.longitude) return;

      // Color based on severity
      let color = '#059669'; // low
      if (item.severity === 'Critical') color = '#e11d48';
      else if (item.severity === 'High') color = '#d97706';
      else if (item.severity === 'Medium') color = '#0284c7';

      const circle = L.circleMarker([item.latitude, item.longitude], {
        radius: item.severity === 'Critical' ? 10 : 8,
        fillColor: color,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      });

      const popupContent = `
        <div style="font-family: Inter, sans-serif; min-width: 200px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 10px; font-weight: 700; color: #059669; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;">${item.category}</span>
            <span style="font-size: 10px; font-weight: 700; color: ${color};">${item.severity}</span>
          </div>
          <h4 style="font-size: 13px; font-weight: 700; margin: 4px 0 6px 0; color: #0f172a; line-height: 1.3;">${item.title}</h4>
          <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
            📍 ${item.upazila}, ${item.district}
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #e2e8f0; padding-top: 6px;">
            <span style="font-size: 10px; font-weight: 600; color: #475569;">Priority: <strong>${item.ai_priority_score}/100</strong></span>
            <button id="marker-btn-${item.id}" style="background: #059669; color: white; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px; font-weight: 600; cursor: pointer;">
              View Details
            </button>
          </div>
        </div>
      `;

      circle.bindPopup(popupContent);

      circle.on('popupopen', () => {
        const btn = document.getElementById(`marker-btn-${item.id}`);
        if (btn) {
          btn.onclick = () => onSelectComplaint(item.id);
        }
      });

      circle.addTo(markersLayerRef.current!);
    });
  }, [markersData]);

  const handleDistrictJump = (coords: [number, number], zoom = 11) => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(coords, zoom, { duration: 1.5 });
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[750px]">
      {/* Map Control Header */}
      <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Layers className="w-5 h-5 text-primary-600" />
          <h3 className="text-sm font-bold text-slate-800">
            {lang === 'bn' ? 'সরাসরি ভৌগোলিক মানচিত্র' : 'Live Bangladesh Complaint Map'}
          </h3>
          <span className="text-xs bg-primary-100 text-primary-800 font-bold px-2 py-0.5 rounded-full">
            {markersData.length} Live Pins
          </span>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Division Filter */}
          <select
            value={selectedDivision}
            onChange={(e) => setSelectedDivision(e.target.value)}
            className="border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 font-medium focus:ring-2 focus:ring-primary-600"
          >
            <option value="All">All Divisions</option>
            <option value="Dhaka">Dhaka</option>
            <option value="Chattogram">Chattogram</option>
            <option value="Sylhet">Sylhet</option>
            <option value="Rajshahi">Rajshahi</option>
            <option value="Khulna">Khulna</option>
            <option value="Barishal">Barishal</option>
            <option value="Rangpur">Rangpur</option>
            <option value="Mymensingh">Mymensingh</option>
          </select>

          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 font-medium focus:ring-2 focus:ring-primary-600"
          >
            <option value="All">All Severities</option>
            <option value="Critical">🔴 Critical</option>
            <option value="High">🟠 High</option>
            <option value="Medium">🔵 Medium</option>
            <option value="Low">🟢 Low</option>
          </select>

          {/* Quick Division Fly Buttons */}
          <div className="hidden lg:flex items-center space-x-1 pl-2 border-l border-slate-300">
            <span className="text-[11px] text-slate-400 font-semibold mr-1">Jump to:</span>
            <button
              onClick={() => handleDistrictJump([23.8103, 90.4125])}
              className="bg-white hover:bg-primary-50 text-slate-700 hover:text-primary-700 border border-slate-200 px-2 py-1 rounded text-[11px] font-medium"
            >
              Dhaka
            </button>
            <button
              onClick={() => handleDistrictJump([22.3569, 91.7832])}
              className="bg-white hover:bg-primary-50 text-slate-700 hover:text-primary-700 border border-slate-200 px-2 py-1 rounded text-[11px] font-medium"
            >
              Chattogram
            </button>
            <button
              onClick={() => handleDistrictJump([24.8949, 91.8687])}
              className="bg-white hover:bg-primary-50 text-slate-700 hover:text-primary-700 border border-slate-200 px-2 py-1 rounded text-[11px] font-medium"
            >
              Sylhet
            </button>
          </div>
        </div>
      </div>

      {/* Map Viewport Container */}
      <div className="relative flex-1 w-full h-full">
        <div ref={mapContainerRef} className="w-full h-full z-0" />

        {/* Legend Overlay */}
        <div className="absolute bottom-4 left-4 z-[400] bg-white/95 backdrop-blur-md p-3 rounded-xl border border-slate-200 shadow-md text-xs space-y-1.5">
          <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider mb-1">
            Severity Legend
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-600"></span>
            <span className="text-slate-600 font-medium">Critical (Immediate Hazard)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-500"></span>
            <span className="text-slate-600 font-medium">High Severity</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-sky-500"></span>
            <span className="text-slate-600 font-medium">Medium</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-emerald-600"></span>
            <span className="text-slate-600 font-medium">Low Priority</span>
          </div>
        </div>
      </div>
    </div>
  );
};
