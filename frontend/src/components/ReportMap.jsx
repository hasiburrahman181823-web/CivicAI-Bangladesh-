import React, {useState} from 'react';
import {useWorkspaceLanguage} from '../workspaceLanguage';
import outline from './bangladesh-outline.json';

const bounds = {west: 87.9, east: 92.8, south: 20.5, north: 26.75};
const width = 350;
const height = 310;
const margin = 25;
const scale = 40;

function project(longitude, latitude) {
  return [
    (width - (bounds.east - bounds.west) * scale) / 2 + (longitude - bounds.west) * scale,
    margin + (bounds.north - latitude) * scale,
  ];
}

const boundary = outline.rings.map(ring => ring.map(([lng, lat], index) => {
  const [x, y] = project(lng, lat);
  return (index === 0 ? 'M' : 'L') + x.toFixed(1) + ' ' + y.toFixed(1);
}).join(' ') + ' Z').join(' ');

export function isMapped(report) {
  const {latitude, longitude} = report;
  return Number.isFinite(latitude) && Number.isFinite(longitude)
    && latitude >= bounds.south && latitude <= bounds.north
    && longitude >= bounds.west && longitude <= bounds.east;
}

export function ReportMap({records, onSelect}) {
  const {t, language} = useWorkspaceLanguage();
  const [selectedGroup, setSelectedGroup] = useState(null);
  const groups = new Map();
  const number = new Intl.NumberFormat(language === 'bn' ? 'bn-BD' : 'en-GB');
  for (const report of records.filter(isMapped)) {
    const [x, y] = project(report.longitude, report.latitude);
    const key = [Math.round(x / 16), Math.round(y / 16)].join(':');
    if (!groups.has(key)) groups.set(key, {x, y, reports: []});
    groups.get(key).reports.push(report);
  }
  const opened = groups.get(selectedGroup);

  return <div className="report-map">
    <svg viewBox={`0 0 ${width} ${height}`} role="group" aria-label={t('Bangladesh complaint map')}>
      <path d={boundary} className="report-map-boundary"/>
      {[['DHAKA', 90.40, 23.81], ['CHATTOGRAM', 91.83, 22.36], ['SYLHET', 91.87, 24.90]].map(([name, lng, lat]) => {
        const [x, y] = project(lng, lat);
        return <text key={name} x={x + 13} y={y + 15} className="report-map-place">{t(name)}</text>;
      })}
      {Array.from(groups, ([key, {x, y, reports}]) => {
        const multiple = reports.length > 1;
        function select() {
          if (multiple) setSelectedGroup(value => value === key ? null : key);
          else {
            setSelectedGroup(null);
            onSelect(reports[0]);
          }
        }
        return <g key={key} className="report-map-marker" role="button" tabIndex={0}
          aria-label={multiple ? t('{count} reports at this location', {count: number.format(reports.length)}) : reports[0].title}
          aria-expanded={multiple ? selectedGroup === key : undefined}
          transform={`translate(${x} ${y})`} onClick={select} onKeyDown={event => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              select();
            }
          }}>
          <circle r="21" fill="transparent"/>
          <circle r={multiple ? 11 : 5}/>
          {multiple && <text textAnchor="middle" dominantBaseline="central">{number.format(reports.length)}</text>}
        </g>;
      })}
    </svg>
    {!groups.size && <p className="report-map-caption">{t('No mappable reports match these filters.')}</p>}
    {opened && <ul className="report-map-list">
      {opened.reports.map(report => <li key={report.id}>
        <button className="text-button" onClick={() => onSelect(report)}>{report.title} · {report.area}</button>
      </li>)}
    </ul>}
    <small className="report-map-source">Natural Earth</small>
  </div>;
}
