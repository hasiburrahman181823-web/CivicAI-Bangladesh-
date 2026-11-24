import React, {useEffect, useState} from 'react';
import {Activity, ArrowRight, BarChart3, CheckCircle2, ClipboardList, Clock, Download, Search, UserRound} from 'lucide-react';
import {request} from '../api/client';
import {ClosureBenchmark} from '../components/ModelTools';
import {useWorkspaceLanguage} from '../workspaceLanguage';

export function PublicDashboard({t, language, headingRef, models, preview, session, onSignIn}) {
  const {t: translate} = useWorkspaceLanguage();
  const [summary, setSummary] = useState(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const number = new Intl.NumberFormat(language === 'bn' ? 'bn-BD' : 'en-GB');
  const d = t.dashboard;

  useEffect(() => {
    if (preview) return;
    const controller = new AbortController();
    request('/public/summary', {signal: controller.signal})
      .then(setSummary)
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [attempt, preview]);

  function refresh() {
    setSummary(null);
    setFailed(false);
    setAttempt(value => value + 1);
  }

  const stats = [
    [ClipboardList, d.total, 'total'],
    [Clock, d.awaiting, 'awaiting_action'],
    [Activity, t.status['In progress'], 'in_progress'],
    [CheckCircle2, t.status.Resolved, 'resolved'],
  ];

  return <section className="citizen-container citizen-dashboard">
    <div className="citizen-dashboard-heading">
      <h1 ref={headingRef} tabIndex={-1}>{d.title}</h1>
      <p>{d.intro}</p>
    </div>
    <div className="citizen-dashboard-actions">
      <a className="citizen-card" href="#report">
        <ClipboardList size={23} aria-hidden="true"/><strong>{t.report}</strong><span>{t.privacyTitle}</span>
        <ArrowRight size={17} aria-hidden="true"/>
      </a>
      <a className="citizen-card" href="#track">
        <Search size={23} aria-hidden="true"/><strong>{t.track}</strong><span>{d.trackHelp}</span>
        <ArrowRight size={17} aria-hidden="true"/>
      </a>
      <button className="citizen-card" type="button" disabled={preview} onClick={() => {
        if (session) window.location.hash = 'profile';
        else onSignIn();
      }}>
        <UserRound size={23} aria-hidden="true"/><strong>{t.profile.complaints}</strong><span>{d.accountHelp}</span>
        <ArrowRight size={17} aria-hidden="true"/>
      </button>
    </div>

    <section className="citizen-card citizen-public-stats" aria-labelledby="citizen-stats-heading">
      <div className="citizen-dashboard-section-title">
        <div><h2 id="citizen-stats-heading">{d.stats}</h2><p>{d.statsHelp}</p></div>
        {!preview && <button className="citizen-text-button" type="button" onClick={refresh} disabled={!summary && !failed}>{d.refresh}</button>}
      </div>
      {preview ? <p>{d.previewStats}</p> : failed ? <p className="citizen-error" role="alert">{t.serviceUnavailable}</p>
        : !summary ? <p role="status">{t.auth.wait}</p> : <>
          <dl className="citizen-dashboard-metrics">
            {stats.map(([Icon, label, key]) => <div key={key}>
              <dt><Icon size={16} aria-hidden="true"/>{label}</dt>
              <dd>{number.format(summary[key])}</dd>
            </div>)}
          </dl>
          <h3><BarChart3 size={18} aria-hidden="true"/>{d.categories}</h3>
          {summary.categories.length ? <ul className="citizen-dashboard-categories">
            {summary.categories.map(category => <li key={category.name}>
              <span>{translate(category.name)}</span><meter min="0" max={summary.total} value={category.count} aria-label={translate(category.name)}/>
              <strong>{number.format(category.count)}</strong>
            </li>)}
          </ul> : <p>{d.noCategories}</p>}
        </>}
    </section>

    <section className="citizen-card citizen-dashboard-research" aria-labelledby="citizen-research-heading">
      <h2 id="citizen-research-heading">{d.research}</h2>
      <p>{d.researchHelp}</p>
      <a className="citizen-text-button" href="/research/model-evaluation.md" download>
        <Download size={16} aria-hidden="true"/>{d.evaluation}
      </a>
      {models?.closure_benchmark && <div className="citizen-research-benchmark"><ClosureBenchmark/></div>}
    </section>
  </section>;
}
