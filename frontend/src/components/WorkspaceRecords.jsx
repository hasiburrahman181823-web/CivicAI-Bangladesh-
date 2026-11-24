import React, {useEffect, useState} from 'react';
import {request} from '../api/client';
import {useWorkspaceLanguage} from '../workspaceLanguage';

export const emptyFilters = {area: '', start: '', end: ''};

const dhakaDay = new Intl.DateTimeFormat('sv-SE', {
  timeZone: 'Asia/Dhaka', year: 'numeric', month: '2-digit', day: '2-digit',
});

export function utcDate(value) {
  return new Date(/(?:Z|[+-]\d\d:\d\d)$/i.test(value) ? value : value + 'Z');
}

export function dateKey(value) {
  return dhakaDay.format(utcDate(value));
}

export function filterWorkspaceRecords(records, {area, start, end}) {
  const location = area.trim().normalize('NFKC').toLocaleLowerCase();
  if (start && end && start > end) return [];
  return records.filter(report => {
    if (location && !report.area.normalize('NFKC').toLocaleLowerCase().includes(location)) return false;
    if (!start && !end) return true;
    const day = dateKey(report.occurred_at);
    return (!start || day >= start) && (!end || day <= end);
  });
}

export function WorkspaceFilters({filters, setFilters}) {
  const {t} = useWorkspaceLanguage();
  function change(event) {
    const {name, value} = event.target;
    setFilters(previous => ({...previous, [name]: value}));
  }
  return <div className="workspace-filters panel">
    <div className="workspace-filter-fields">
      <label>{t('Filter by area')}<input name="area" value={filters.area} onChange={change} maxLength={120}/></label>
      <label>{t('Incident from (Bangladesh time)')}<input name="start" type="date" value={filters.start} onChange={change}/></label>
      <label>{t('Incident through (Bangladesh time)')}<input name="end" type="date" value={filters.end} onChange={change}/></label>
      <button className="secondary" type="button" onClick={() => setFilters(emptyFilters)}
        disabled={!Object.values(filters).some(Boolean)}>{t('Clear location and date filters')}</button>
    </div>
    {filters.start && filters.end && filters.start > filters.end && <p className="error" role="alert">
      {t('The start date must be on or before the end date.')}
    </p>}
  </div>;
}

export function ReviewAudit({preview}) {
  const {t, language} = useWorkspaceLanguage();
  const [reviewLog, setReviewLog] = useState(null);
  const [failure, setFailure] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    if (preview) return;
    const controller = new AbortController();
    request('/admin/audit', {signal: controller.signal})
      .then(items => { if (!controller.signal.aborted) setReviewLog(items); })
      .catch(() => { if (!controller.signal.aborted) setFailure(true); });
    return () => controller.abort();
  }, [preview, refresh]);
  const format = new Intl.DateTimeFormat(language === 'bn' ? 'bn-BD' : 'en-GB', {
    timeZone: 'Asia/Dhaka', dateStyle: 'medium', timeStyle: 'short',
  });
  return <article className="panel workspace-audit">
    <h2>{t('Latest review actions')}</h2>
    {preview ? <p>{t('The review audit is available in the live admin workspace.')}</p>
      : failure ? <p className="error" role="alert">{t('The audit log could not be loaded.')}</p>
      : reviewLog === null ? <p role="status">{t('Loading audit log…')}</p>
      : !reviewLog.length ? <p>{t('No reviews have been recorded yet.')}</p>
      : <ul>
        {reviewLog.map(entry => <AuditEntry key={entry.id} entry={entry} t={t} format={format}/>)}
      </ul>}
    {!preview && <button type="button" className="secondary" onClick={() => {
      setReviewLog(null);
      setFailure(false);
      setRefresh(value => value + 1);
    }}>{t('Refresh audit log')}</button>}
  </article>;
}

function AuditEntry({entry, t, format}) {
  let action;
  try { action = JSON.parse(entry.action); } catch { action = null; }
  const eventLabel = {
    complaint_export: 'CSV export', contact_access: 'Contact data accessed',
    evidence_download: 'Evidence downloaded', ticket_reply: 'Reply sent',
  }[action?.event] || 'Review recorded';
  return <li>
    <strong>{action?.status ? t(action.status) : t(eventLabel)}{action?.priority && ' · ' + t(action.priority)}</strong>
    <time dateTime={entry.created_at}>{format.format(utcDate(entry.created_at))}</time>
    {entry.complaint_id && <small>{t('Complaint ID')} · {entry.complaint_id}</small>}
    {entry.actor_id && <small>{t('Administrator ID')} · {entry.actor_id}</small>}
    {action?.count != null && <small>{t('{count} records', {count: action.count})}</small>}
    {action?.note && <p>{action.note}</p>}
    {action?.reason && <p>{action.reason}</p>}
    {action?.duplicate_of && <small>{t('Linked complaint')} · {action.duplicate_of}</small>}
  </li>;
}
