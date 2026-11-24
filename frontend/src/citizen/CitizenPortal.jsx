import React, {lazy, Suspense, useEffect, useRef, useState} from 'react';
import {
  ArrowLeft, ArrowRight, Bot, CheckCircle2, ClipboardList, Construction,
  Download, Droplets, FileText, Info, LockKeyhole, MapPin, Moon, Paperclip, Search, ShieldCheck,
  Sparkles, Sun, Trash2, UserRound, X, Zap,
} from 'lucide-react';
import {request} from '../api/client';
import {MediaTools} from '../components/ModelTools';
import {TicketActivity} from '../components/TicketActivity';
import {FirstAdminSetup, PasswordRecovery, RecoveryCode, recoveryLabel} from './AccountRecovery';
import {PublicDashboard} from './PublicDashboard';
import {copy} from './copy';
import {translateWorkspace, WorkspaceLanguage} from '../workspaceLanguage';
import './portal.css';

const Workspace = lazy(() => import('../Workspace'));
const launchYear = 2026;
const issueIcons = [Construction, Droplets, Trash2, Zap];
const languages = ['Bangla', 'English', 'Banglish'];
const emptyForm = {title: '', area: '', text: '', time: '', language: '', latitude: '', longitude: '', mobile: ''};
const isPreview = import.meta.env.VITE_UI_PREVIEW === '1';
const evidenceTypes = ['image/jpeg', 'image/png', 'image/webp'];
const mobileFormat = /^(?:\+?88)?01[3-9][0-9]{8}$/;

function errorCopy(t, problem, context) {
  if (problem.status === 429) return t.rateLimited;
  if (!problem.status || problem.status >= 500 || problem.status < 400) return t.serviceUnavailable;
  if (context === 'track') return t.trackMissing;
  if (context === 'auth') {
    if (problem.status === 422) return t.auth.invalidFields;
    return t.auth.failed;
  }
  return t.invalidReport;
}

function Brand({t}) {
  return <a className="citizen-brand" href="#home">
    <img src="/favicon.svg" alt="" width="40" height="40"/>
    <span><strong>{t.brand}</strong><small>{t.country}</small></span>
  </a>;
}

function LanguageSwitcher({language, onChange, label}) {
  return <div className="citizen-language" role="group" aria-label={label}>
    <button type="button" lang="bn" aria-pressed={language === 'bn'} onClick={() => onChange('bn')}>বাংলা</button>
    <button type="button" lang="en" aria-pressed={language === 'en'} onClick={() => onChange('en')}>EN</button>
  </div>;
}

function HeroOverview({t, language, headingRef, show}) {
  const [summary, setSummary] = useState(null);
  const labels = t.homeReport;
  const number = new Intl.NumberFormat(language === 'bn' ? 'bn-BD' : 'en-GB');

  useEffect(() => {
    if (!show || isPreview) return;
    const abort = new AbortController();
    request('/public/summary', {signal: abort.signal})
      .then(result => { if (!abort.signal.aborted) setSummary(result); })
      .catch(() => {});
    return () => abort.abort();
  }, [show]);

  return <div className="citizen-hero-copy">
    <div className="citizen-service"><span aria-hidden="true"/><span>{t.service}</span><i aria-hidden="true"/><span>{labels.serviceDetail}</span></div>
    <h1 tabIndex={-1} ref={headingRef}>{t.heading[0]} <em>{t.heading[1]}</em></h1>
    <p>{t.intro}</p>
    <a className="citizen-hero-banner" href="#track">
      <span className="citizen-assurance-icon"><Search size={21} aria-hidden="true"/></span>
      <span><strong>{t.trackLink}</strong><small>{t.dashboard.trackHelp}</small></span>
      <ArrowRight size={18} aria-hidden="true"/>
    </a>
    {summary && <dl className="citizen-hero-numbers">
      {[[labels.totals, summary.total], [labels.resolved, summary.resolved], [labels.active, summary.in_progress]].map(([label, value]) => (
        <div key={label}><dt>{label}</dt><dd>{number.format(value)}</dd></div>
      ))}
    </dl>}
  </div>;
}

export function CitizenPortal() {
  const [language, setLanguage] = useState(() => localStorage.getItem('civic-language') === 'en' ? 'en' : 'bn');
  const [dark, setDark] = useState(() => localStorage.getItem('civic-theme') === 'dark');
  const [route, setRoute] = useState(() => window.location.hash);
  const [session, setSession] = useState(null);
  const [account, setAccount] = useState(false);
  const [checkingSession, setCheckingSession] = useState(!isPreview);
  const [models, setModels] = useState(null);
  const [recovery, setRecovery] = useState(null);
  const [accountError, setAccountError] = useState(null);
  const [trackingReceipt, setTrackingReceipt] = useState(null);
  const trackHeading = useRef(null);
  const reportPanel = useRef(null);
  const homeHeading = useRef(null);
  const dashboardHeading = useRef(null);
  const t = copy[language];
  const dashboard = route === '#dashboard';
  const tracking = route === '#track';
  const profile = !isPreview && route === '#profile';
  const admin = !isPreview && route === '#admin';
  const recovering = !isPreview && (route === '#forgot-password' || route === '#reset-password' || route.startsWith('#reset-password/'));
  const settingUpAdmin = !isPreview && route === '#admin-setup';
  const workspaceOpen = (admin && session?.role === 'admin') || (isPreview && route === '#admin-preview');
  const languageControl = <LanguageSwitcher language={language} onChange={setLanguage} label={t.language}/>;
  const workspaceLanguage = {language, t: (message, values) => translateWorkspace(language, message, values)};

  useEffect(() => {
    let active = true;
    if (!isPreview) {
      request('/health').then(value => { if (active) setModels(value); }).catch(() => {});
      request('/auth/recovery/options')
        .then(value => { if (active) setRecovery(value); })
        .catch(() => { if (active) setRecovery({email_recovery: false, admin_setup: false}); });
      request('/auth/me')
        .then(value => { if (active) setSession(value); })
        .catch(error => { if (active && error.status !== 401) setAccountError(error); })
        .finally(() => { if (active) setCheckingSession(false); });
    }
    function hashChanged() { setRoute(window.location.hash); }
    window.addEventListener('hashchange', hashChanged);
    return () => {
      active = false;
      window.removeEventListener('hashchange', hashChanged);
    };
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    localStorage.setItem('civic-language', language);
  }, [language]);

  useEffect(() => {
    const theme = dark ? 'dark' : 'light';
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('civic-theme', theme);
  }, [dark]);

  useEffect(() => {
    const section = dashboard ? dashboardHeading.current
      : route === '#track' ? trackHeading.current
      : route === '#report' ? reportPanel.current
      : route === '#home' ? homeHeading.current : null;
    if (section && !workspaceOpen) section.focus();
  }, [dashboard, route, workspaceOpen]);

  async function signOut() {
    try {
      await request('/auth/logout', {method: 'POST'});
      setSession(null);
      setAccountError(null);
    } catch (error) {
      setAccountError(error);
    }
  }

  function signedIn(value) {
    setSession(value);
    setAccount(false);
    setAccountError(null);
    if (!admin) window.location.hash = account === 'report' ? 'report' : 'dashboard';
  }

  function trackReport(receipt) {
    setTrackingReceipt(receipt);
    window.location.hash = 'track';
  }

  return <>
    <div className="citizen-shell" hidden={workspaceOpen}>
      <a className="citizen-skip" href="#content">{t.skip}</a>
      <header className="citizen-header">
        <div className="citizen-container citizen-header-inner">
          <Brand t={t}/>
          <nav className="citizen-nav" aria-label={t.navigation}>
            <a href="#home" aria-current={!route || route === '#home' ? 'page' : undefined}>{t.home}</a>
            <a href="#dashboard" aria-current={dashboard ? 'page' : undefined}>{t.dashboard.nav}</a>
            <a href="#report" aria-current={route === '#report' ? 'page' : undefined}>{t.report}</a>
            <a href="#track" aria-current={tracking ? 'page' : undefined}>{t.track}</a>
          </nav>
          <div className="citizen-actions">
            {languageControl}
            <button type="button" className="citizen-account citizen-theme" aria-label={dark ? t.dayMode : t.nightMode}
              onClick={() => setDark(value => !value)}>
              {dark ? <Sun size={17} aria-hidden="true"/> : <Moon size={17} aria-hidden="true"/>}
            </button>
            {session
              ? <a className="citizen-account" href="#profile" aria-current={profile ? 'page' : undefined}>
                <UserRound size={17} aria-hidden="true"/>{t.profile.title}
              </a>
              : <button type="button" className="citizen-account" disabled={isPreview || checkingSession} onClick={() => setAccount(true)}>
                <UserRound size={17} aria-hidden="true"/>{t.signIn}
              </button>}
          </div>
        </div>
      </header>

      {isPreview && <div className="citizen-preview">
        <span>{t.preview}</span><a href="#admin-preview">{workspaceLanguage.t('Preview admin workspace')}</a>
      </div>}
      {accountError && <p className="citizen-container citizen-error" role="alert">{errorCopy(t, accountError, 'auth')}</p>}

      <main className="citizen-main" id="content" tabIndex={-1}>
        <div hidden={dashboard || tracking || profile || admin || recovering || settingUpAdmin}>
          <section className="citizen-hero">
            <div className="citizen-hero-photo" aria-hidden="true">
              <img src="/civicai-home-reference.jpg" width="1344" height="756" alt="" fetchPriority={route === '#home' || !route ? 'high' : 'auto'}/>
            </div>
            <div className="citizen-hero-waves" aria-hidden="true"/>
            <div className="citizen-container citizen-hero-inner">
              <HeroOverview t={t} language={language} headingRef={homeHeading} show={!dashboard && !tracking && !profile && !admin && !recovering && !settingUpAdmin}/>
              <section className="citizen-card citizen-report" id="report" tabIndex={-1} ref={reportPanel} aria-label={t.formTitle}>
                <ComplaintForm t={t} language={language} onTrack={trackReport} models={models}
                  session={session} checkingSession={checkingSession} onExpired={() => setSession(null)}
                  onSignIn={() => setAccount('report')}/>
              </section>
            </div>
          </section>
          <section className="citizen-container citizen-issues">
            <h2>{t.issuesTitle}</h2>
            <ul>
              {t.issues.map(([title, detail], index) => {
                const Icon = issueIcons[index];
                return <li key={title}><span className="citizen-issue-icon"><Icon size={22} aria-hidden="true"/></span><div><h3>{title}</h3><p>{detail}</p></div></li>;
              })}
            </ul>
          </section>
        </div>
        {dashboard && <WorkspaceLanguage.Provider value={workspaceLanguage}>
          <PublicDashboard t={t} language={language} headingRef={dashboardHeading} models={models}
            preview={isPreview} session={session} onSignIn={() => setAccount(true)}/>
        </WorkspaceLanguage.Provider>}
        {tracking && <section className="citizen-container citizen-tracking">
          <a className="citizen-back" href="#home"><ArrowLeft size={17} aria-hidden="true"/>{t.home}</a>
          <div className="citizen-card">
            <CardHeader Icon={Search} title={t.track} intro={t.trackIntro} headingRef={trackHeading} primaryHeading/>
            <TrackingForm t={t} receipt={trackingReceipt}/>
          </div>
        </section>}
        {(recovering || settingUpAdmin) && <section className="citizen-container citizen-tracking">
          <a className="citizen-back" href={settingUpAdmin ? '#admin' : '#home'}>
            <ArrowLeft size={17} aria-hidden="true"/>{settingUpAdmin ? t.workspace : t.home}
          </a>
          <div className="citizen-card citizen-profile">
            {settingUpAdmin
              ? <FirstAdminSetup t={t} language={language} enabled={recovery ? recovery.admin_setup : null} onComplete={() => {
                setSession(null);
                setRecovery(current => current && {...current, admin_setup: false});
              }}/>
              : <PasswordRecovery key={route} t={t} language={language} route={route} emailAvailable={recovery?.email_recovery}
                onReset={() => setSession(null)} onSignIn={() => setAccount(true)}/>}
          </div>
        </section>}
        {(profile || admin) && <section className="citizen-container citizen-tracking">
          <a className="citizen-back" href="#home"><ArrowLeft size={17} aria-hidden="true"/>{t.home}</a>
          <div className="citizen-card citizen-profile">
            <CardHeader Icon={admin ? ShieldCheck : UserRound} title={admin ? t.workspace : t.profile.title}
              intro={admin ? t.auth.adminHelp : t.profile.intro} primaryHeading/>
            {checkingSession
              ? <p role="status">{t.auth.wait}</p>
              : admin
                ? session
                  ? <div className="citizen-profile-actions">
                    <p>{t.auth.adminOnly}</p>
                    <button className="citizen-text-button" type="button" onClick={signOut}>{t.signOut}</button>
                  </div>
                  : <AccountForm t={t} admin onLogin={signedIn}/>
                : session
                  ? <CitizenProfile key={session.email} t={t} language={language} session={session}
                    onSignOut={signOut} onExpired={() => { setSession(null); setAccount(true); }}/>
                  : <div className="citizen-form">
                    <button className="citizen-button citizen-submit" type="button" onClick={() => setAccount(true)}>{t.signIn}</button>
                    <a className="citizen-text-button" href="#forgot-password">{recoveryLabel(language, 'forgot')}</a>
                  </div>}
            {admin && recovery?.admin_setup && <a className="citizen-text-button citizen-admin-link" href="#admin-setup">
              {recoveryLabel(language, 'admin')}
            </a>}
          </div>
        </section>}
      </main>

      <footer className="citizen-footer">
        <div className="citizen-container citizen-footer-inner">
          <Brand t={t}/>
          <p>{t.footer}</p>
          <small className="citizen-created">{t.created} <time dateTime={String(launchYear)}>{new Intl.NumberFormat(language === 'bn' ? 'bn-BD' : 'en-GB', {useGrouping: false}).format(launchYear)}</time></small>
        </div>
      </footer>
      {account && <AccountDialog t={t} language={language} onClose={() => setAccount(false)} onLogin={signedIn}/>}
    </div>
    {workspaceOpen && <WorkspaceLanguage.Provider value={workspaceLanguage}>
      <Suspense fallback={<p className="citizen-loading" role="status">{t.auth.wait}</p>}>
        <Workspace initialSession={session} languageControl={languageControl} preview={isPreview} dark={dark} setDark={setDark}
          onExit={() => { window.location.hash = 'dashboard'; }} onLogout={() => setSession(null)}/>
      </Suspense>
    </WorkspaceLanguage.Provider>}
  </>;
}

function CardHeader({Icon, title, intro, headingRef, primaryHeading = false, action}) {
  return <div className="citizen-card-header">
    <span className="citizen-card-icon"><Icon size={23} aria-hidden="true"/></span>
    <div>
      <div className="citizen-card-title">
        {primaryHeading
          ? <h1 ref={headingRef} tabIndex={-1}>{title}</h1>
          : <h2 ref={headingRef} tabIndex={headingRef ? -1 : undefined}>{title}</h2>}
        {action}
      </div>
      <p>{intro}</p>
    </div>
  </div>;
}

function ComplaintForm({t, language, onTrack, models, session, checkingSession, onExpired, onSignIn}) {
  const [form, setForm] = useState(emptyForm);
  const [receipt, setReceipt] = useState(null);
  const [action, setAction] = useState(null);
  const [error, setError] = useState(null);
  const [suggestion, setSuggestion] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const receiptHeading = useRef(null);
  const busy = action !== null;
  const number = new Intl.NumberFormat(language === 'bn' ? 'bn-BD' : 'en-GB');
  const report = t.homeReport;
  const complaintLanguage = form.language || (/[\u0980-\u09ff]/.test(form.text) ? 'Bangla' : form.text.trim() ? 'English' : language === 'bn' ? 'Bangla' : 'English');
  const normalizedMobile = form.mobile.replace(/[০-৯]/g, digit => String(digit.charCodeAt(0) - 2534)).replace(/[\s()-]/g, '');
  const nationalMobile = /^1[3-9][0-9]{8}$/.test(normalizedMobile) ? '0' + normalizedMobile : normalizedMobile;
  const validMobile = mobileFormat.test(nationalMobile);

  useEffect(() => { if (receipt) receiptHeading.current?.focus(); }, [receipt]);

  function change(event) {
    const {name, value} = event.target;
    setForm(current => ({...current, [name]: value}));
    setError(null);
    if (name !== 'mobile') setSuggestion(null);
  }

  async function submit(event, previewing = false) {
    event.preventDefault();
    if (isPreview || busy || checkingSession) return;
    const {title, area, text, latitude, longitude} = form;
    if (title.trim().length < 5 || area.trim().length < 2 || text.trim().length < 10) {
      setError('shortReport');
      return;
    }
    const date = form.time ? new Date(form.time) : new Date();
    if (Number.isNaN(date.getTime()) || date.getTime() > Date.now()) {
      setError('invalidTime');
      return;
    }
    if ((latitude === '') !== (longitude === '')) {
      setError('coordinatePair');
      return;
    }
    if (!previewing && !session && !validMobile) {
      setError('mobileError');
      return;
    }
    if (!previewing && session?.role === 'citizen' && evidence &&
      (!evidenceTypes.includes(evidence.type) || evidence.size > 2 * 1024 * 1024)) {
      setError('evidenceError');
      return;
    }
    setAction(previewing ? 'suggest' : 'submit');
    setError(null);
    try {
      const result = await request(previewing ? '/analyze' : '/complaints', {
        method: 'POST',
        body: JSON.stringify({
          title: title.trim(), area: area.trim(), text: text.trim(),
          occurred_at: date.toISOString(), language: complaintLanguage,
          latitude: latitude === '' ? null : Number(latitude),
          longitude: longitude === '' ? null : Number(longitude),
          ...(!previewing && !session ? {mobile: nationalMobile} : {}),
        }),
      });
      if (previewing) {
        setSuggestion(result);
        return;
      }
      if (!result?.id || !result?.tracking_key) throw new Error('Missing receipt');
      let attachment;
      if (evidence && session?.role === 'citizen') {
        const body = new FormData();
        body.append('file', evidence);
        try {
          await request('/tickets/' + result.id + '/evidence', {method: 'POST', body});
          attachment = 'evidenceAdded';
        } catch {
          attachment = 'evidenceRetry';
        }
      }
      setReceipt({id: result.id, tracking_key: result.tracking_key, analysis: result.analysis, attachment});
      setEvidence(null);
      setForm(emptyForm);
      setSuggestion(null);
    } catch (problem) {
      if (problem.message === 'A Bangladesh mobile number is required for guest complaints') {
        onExpired();
        setError('mobileError');
      } else setError(problem);
    } finally {
      setAction(null);
    }
  }

  if (receipt) return <div className="citizen-receipt">
    <CardHeader Icon={CheckCircle2} title={t.success} intro={t.savePrompt} headingRef={receiptHeading}/>
    {receipt.attachment && <p className="citizen-receipt-attachment" role="status">{report[receipt.attachment]}</p>}
    <dl>
      <div><dt>{t.reportId}</dt><dd><code>{receipt.id}</code></dd></div>
      <div><dt>{t.trackingKey}</dt><dd><code>{receipt.tracking_key}</code></dd></div>
    </dl>
    <button type="button" className="citizen-button citizen-submit" onClick={() => {
      const {id, tracking_key} = receipt;
      const url = URL.createObjectURL(new Blob([JSON.stringify({id, tracking_key}, null, 2)], {type: 'application/json'}));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'civicai-tracking.json';
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }}><Download size={18} aria-hidden="true"/>{t.saveReceipt}</button>
    <div className="citizen-receipt-links">
      <button type="button" className="citizen-text-button" onClick={() => onTrack(receipt)}>{t.trackLink}<ArrowRight size={16} aria-hidden="true"/></button>
      <button type="button" className="citizen-text-button" onClick={() => setReceipt(null)}>{t.newReport}</button>
    </div>
    {receipt.analysis && <TriageSuggestion result={receipt.analysis} t={t} language={language} number={number}/>}
  </div>;

  return <>
    <CardHeader Icon={ClipboardList} title={t.formTitle} intro={t.formIntro}
      action={<span className="citizen-ai-chip"><Bot size={14} aria-hidden="true"/>{report.assistant}</span>}/>
    {!session && !checkingSession && <p className="citizen-guest-note">
      <Info size={16} aria-hidden="true"/><span><strong>{report.guestLabel}.</strong> {report.guestInfo}</span>
    </p>}
    <form className="citizen-form" onSubmit={submit}>
      <div className="citizen-form-row">
        <label>{t.title}
          <input name="title" value={form.title} onChange={change} placeholder={t.titlePlaceholder} minLength={5} maxLength={120} required disabled={busy}/>
        </label>
        <label>{t.area}
          <span className="citizen-location-input"><MapPin size={16} aria-hidden="true"/>
            <input name="area" value={form.area} onChange={change} placeholder={t.areaPlaceholder} minLength={2} maxLength={120} required disabled={busy}/>
          </span>
        </label>
      </div>
      <div className="citizen-description">
        <label htmlFor="complaint-description">{t.details}</label>
        <div className="citizen-description-box">
          <textarea id="complaint-description" name="text" value={form.text} onChange={change}
            placeholder={t.detailsPlaceholder} minLength={10} maxLength={1000} rows={2} required disabled={busy}
            aria-describedby="complaint-privacy"/>
          <div className="citizen-description-tools">
            <button className="citizen-ai-chip" type="button" onClick={event => submit(event, true)}
              disabled={busy || isPreview || checkingSession}>
              <Bot size={14} aria-hidden="true"/>{action === 'suggest' ? t.checking : report.detailsAnalysis}
            </button>
            <small className="citizen-counter">{number.format(form.text.length)} / {number.format(1000)}</small>
          </div>
        </div>
      </div>
      {suggestion && <TriageSuggestion result={suggestion} t={t} language={language} number={number}/>}
      {!session && !checkingSession && <label className="citizen-mobile-field">{report.mobile} <span className="citizen-field-qualifier">({report.required})</span>
        <span className="citizen-phone-control">
          <span className="citizen-phone-prefix" aria-hidden="true"><span className="citizen-flag"/> +880</span>
          <input name="mobile" type="tel" inputMode="tel" autoComplete="tel-national" value={form.mobile}
            onChange={change} placeholder="01XXXXXXXXX" maxLength={32} required disabled={busy}
            aria-invalid={error === 'mobileError' || undefined} aria-describedby="guest-mobile-note"/>
          {validMobile && <span className="citizen-ai-chip"><CheckCircle2 size={14} aria-hidden="true"/>{report.mobileFormat}</span>}
        </span>
        <small id="guest-mobile-note">{report.mobilePrivacy}</small>
      </label>}
      {session?.role === 'citizen' && <label className="citizen-evidence-control">
        <Paperclip size={17} aria-hidden="true"/><span>{evidence?.name || report.evidence} {!evidence && <span className="citizen-field-qualifier">({t.optional})</span>}</span>
        <input type="file" accept={evidenceTypes.join(',')} disabled={busy}
          aria-label={report.evidence} onChange={event => { setEvidence(event.target.files[0] || null); setError(null); }}/>
      </label>}
      {!session && !checkingSession && <button className="citizen-evidence-control" type="button" onClick={onSignIn} disabled={isPreview}>
        <Paperclip size={17} aria-hidden="true"/><span>{report.signInEvidence} <span className="citizen-field-qualifier">({t.optional})</span></span>
      </button>}
      <details className="citizen-optional">
        <summary>{t.extra}<span>{t.optional}</span></summary>
        <div className="citizen-form-row">
          <label>{t.time}
            <input name="time" type="datetime-local" value={form.time} onChange={change} disabled={busy}/>
            <small>{t.timeHint}</small>
          </label>
          <label>{t.complaintLanguage}
            <select name="language" value={complaintLanguage} onChange={change} disabled={busy}>
              {languages.map(value => <option key={value} value={value}>{t.languageNames[value]}</option>)}
            </select>
          </label>
        </div>
        <div className="citizen-form-row">
          <label>{t.latitude}<input name="latitude" type="number" step="any" min="-90" max="90" value={form.latitude} onChange={change} disabled={busy}/></label>
          <label>{t.longitude}<input name="longitude" type="number" step="any" min="-180" max="180" value={form.longitude} onChange={change} disabled={busy}/></label>
        </div>
        <small>{t.coordinateHint}</small>
      </details>
      {error && <p className="citizen-error" role="alert">{typeof error === 'string' ? report[error] || t[error] : errorCopy(t, error, 'report')}</p>}
      <button className="citizen-button citizen-submit" type="submit" value="submit" disabled={busy || isPreview || checkingSession}>
        <Sparkles size={18} aria-hidden="true"/><span>{action === 'submit' ? t.sending : report.submit}</span>
      </button>
    </form>
    {!session && !checkingSession && <button className="citizen-report-account" type="button" onClick={onSignIn} disabled={isPreview}>
      <UserRound size={16} aria-hidden="true"/>{report.accountHelp}<ArrowRight size={15} aria-hidden="true"/>
    </button>}
    {(models?.voice || models?.image) && <MediaTools
      voiceAvailable={models.voice}
      imageAvailable={models.image}
      language={complaintLanguage}
      uiLanguage={language}
      onTranscript={text => {
        setForm(previous => ({...previous, text: text.slice(0, 1000)}));
        setError(null);
        setSuggestion(null);
      }}
    />}
    <p id="complaint-privacy" className="citizen-form-privacy"><LockKeyhole size={15} aria-hidden="true"/>{t.privacyText}</p>
  </>;
}

function TriageSuggestion({result, t, language, number}) {
  const translate = message => translateWorkspace(language, message);
  return <section className="citizen-triage" aria-live="polite">
    <h3>{t.suggestion}</h3>
    <dl>
      <div><dt>{translate('Category')}</dt><dd>{translate(result.category)}</dd></div>
      <div><dt>{translate('Priority')}</dt><dd>{translate(result.priority)}</dd></div>
      <div><dt>{translate('Priority score')}</dt><dd>{number.format(result.score)} / {number.format(100)}</dd></div>
    </dl>
    <details>
      <summary>{t.explanation}</summary>
      <ul>
        {result.breakdown.map(step => {
          const label = step.label.startsWith('Trained severity: ')
            ? translateWorkspace(language, 'Trained severity: {severity}', {severity: translate(step.label.slice(18))})
            : translate(step.label);
          return <li key={step.label}><span>{label}</span><strong>+{number.format(step.points)}</strong></li>;
        })}
      </ul>
      <p>{translate(result.method)}</p>
    </details>
    <p>{t.humanReview}</p>
  </section>;
}

function TrackingForm({t, receipt}) {
  const [id, setId] = useState(receipt?.id || '');
  const [key, setKey] = useState(receipt?.tracking_key || '');
  const [item, setItem] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (isPreview || busy) return;
    if (!id.trim() || !key.trim()) {
      setError({status: 422});
      return;
    }
    setBusy(true);
    setItem(null);
    setError(null);
    try {
      setItem(await request('/track/' + encodeURIComponent(id.trim()), {
        method: 'POST', body: JSON.stringify({tracking_key: key.trim()}),
      }));
    } catch (problem) {
      setError(problem);
    } finally {
      setBusy(false);
    }
  }

  return <form className="citizen-form" onSubmit={submit}>
    <label>{t.reportId}<input value={id} onChange={event => {setId(event.target.value); setItem(null); setError(null);}} required maxLength={128} disabled={busy} autoComplete="off"/></label>
    <label>{t.trackingKey}<input type="password" value={key} onChange={event => {setKey(event.target.value); setItem(null); setError(null);}} required maxLength={128} disabled={busy} autoComplete="off"/></label>
    {error && <p className="citizen-error" role="alert">{errorCopy(t, error, 'track')}</p>}
    <button type="submit" className="citizen-button citizen-submit" disabled={busy || isPreview}><span>{busy ? t.checking : t.trackButton}</span><ArrowRight size={19} aria-hidden="true"/></button>
    {item && <section className="citizen-tracking-result" aria-live="polite">
      <p>{t.latestStatus}</p>
      <h2>{t.status[item.status] || item.status}</h2>
      {item.title && <p><FileText size={16} aria-hidden="true"/>{item.title}</p>}
      {item.area && <p><MapPin size={16} aria-hidden="true"/>{item.area}</p>}
    </section>}
  </form>;
}

function CitizenProfile({t, language, session, onSignOut, onExpired}) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const [activeTicket, setActiveTicket] = useState(null);
  const [updates, setUpdates] = useState([]);
  const words = language === 'bn' ? {
    updates: 'সাম্প্রতিক হালনাগাদ', reply: 'পর্যালোচনা দলের উত্তর', noUpdates: 'নতুন কোনো হালনাগাদ নেই।',
  } : {updates: 'Recent updates', reply: 'Reply from the review team', noUpdates: 'No updates yet.'};

  useEffect(() => {
    const controller = new AbortController();
    let running = false;
    async function refresh() {
      if (running || document.visibilityState === 'hidden') return;
      running = true;
      try {
        const [reports, activity] = await Promise.all([
          request('/auth/me/complaints', {signal: controller.signal}),
          request('/auth/me/updates', {signal: controller.signal}),
        ]);
        if (!controller.signal.aborted) {
          setItems(reports);
          setUpdates(activity);
          setError(null);
        }
      } catch (error) {
        if (!controller.signal.aborted) setError(error);
      } finally {
        running = false;
      }
    }
    refresh();
    const timer = window.setInterval(refresh, 20000);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      controller.abort();
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, [attempt]);

  const dateFormat = new Intl.DateTimeFormat(language === 'bn' ? 'bn-BD' : 'en-GB', {
    dateStyle: 'medium', timeZone: 'Asia/Dhaka',
  });

  return <>
    <div className="citizen-profile-actions">
      <dl><dt>{t.auth.email}</dt><dd>{session.email}</dd></dl>
      <div className="citizen-profile-links">
        {session.role === 'admin' && <a className="citizen-text-button" href="#admin">{t.workspace}</a>}
        <button className="citizen-text-button" type="button" onClick={onSignOut}>{t.signOut}</button>
      </div>
    </div>
    <section className="citizen-profile-complaints">
      <h2>{t.profile.complaints}</h2>
      {error ? <>
        <p className="citizen-error" role="alert">{error.status === 401 ? t.auth.expired : errorCopy(t, error)}</p>
        <button type="button" className="citizen-text-button" onClick={() => {
          if (error.status === 401) onExpired();
          else {
            setError(null);
            setAttempt(value => value + 1);
          }
        }}>{error.status === 401 ? t.signIn : t.profile.retry}</button>
      </> : items === null ? <p role="status">{t.auth.wait}</p> : items.length === 0
        ? <p>{t.profile.empty}</p>
        : <ul className="citizen-profile-list">
          {items.map(item => <li key={item.id}>
            <div><button type="button" className="ticket-list-button" aria-pressed={activeTicket === item.id}
              onClick={() => setActiveTicket(current => current === item.id ? null : item.id)}>{item.title}</button>
              <small>{item.area} · <time dateTime={item.created_at}>{dateFormat.format(new Date(item.created_at))}</time></small>
            </div>
            <span>{t.status[item.status] || item.status}</span>
          </li>)}
        </ul>}
      {activeTicket && <TicketActivity key={activeTicket} id={activeTicket} language={language}/>}
      <a className="citizen-text-button" href="#report">{t.report}<ArrowRight size={16} aria-hidden="true"/></a>
    </section>
    {!error && items !== null && <section className="citizen-profile-complaints">
      <h2>{words.updates}</h2>
      {updates.length ? <ul className="citizen-profile-list" aria-live="polite">
        {updates.slice(0, 5).map(entry => <li key={entry.kind + entry.id}>
          <div><button type="button" className="ticket-list-button"
            onClick={() => setActiveTicket(entry.ticket_id)}>{entry.title}</button>
            <small>{entry.kind === 'reply' ? words.reply : t.status[entry.kind]}</small></div>
          <time dateTime={entry.created_at}>{dateFormat.format(new Date(entry.created_at))}</time>
        </li>)}
      </ul> : <p>{words.noUpdates}</p>}
    </section>}
    {session.role === 'citizen' && <RecoveryCode t={t} language={language}/>}
  </>;
}

function AccountDialog({t, language, onClose, onLogin}) {
  const dialog = useRef(null);
  useEffect(() => { dialog.current?.showModal(); }, []);

  return <dialog ref={dialog} className="citizen-dialog citizen-card" onClose={onClose} aria-labelledby="citizen-account-heading">
    <button type="button" className="citizen-close" aria-label={t.auth.close} onClick={() => dialog.current.close()}>
      <X size={22} aria-hidden="true"/>
    </button>
    <span className="citizen-card-icon"><UserRound size={22} aria-hidden="true"/></span>
    <AccountForm t={t} onLogin={onLogin}/>
    <a className="citizen-text-button citizen-admin-link" href="#forgot-password" onClick={() => dialog.current.close()}>
      {recoveryLabel(language, 'forgot')}
    </a>
  </dialog>;
}

function AccountForm({t, admin = false, onLogin}) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState(null);
  const [created, setCreated] = useState(false);
  const heading = admin ? t.auth.adminSignIn : register ? t.auth.register : t.auth.signIn;

  async function submit(event) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const credentials = {email: String(fields.get('email')).trim(), password: fields.get('password')};
    setBusy(true);
    setDetail(null);
    setCreated(false);
    try {
      const account = await request(register ? '/auth/register' : '/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      if (register) {
        setRegister(false);
        setCreated(true);
      } else {
        onLogin(account);
      }
    } catch (problem) {
      setDetail(problem);
    } finally {
      setBusy(false);
    }
  }

  return <>
    {!admin && <h2 id="citizen-account-heading">{heading}</h2>}
    <form className="citizen-form" onSubmit={submit}>
      <label>{t.auth.email}<input name="email" type="email" autoComplete="email" required maxLength={254} disabled={busy}/></label>
      <label>{t.auth.password}
        <input key={register} name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} minLength={10} maxLength={128} required disabled={busy}/>
        {register && <small>{t.auth.passwordHint}</small>}
      </label>
      {created && <p role="status">{t.auth.created}</p>}
      {detail && <p className="citizen-error" role="alert">{errorCopy(t, detail, 'auth')}</p>}
      <button type="submit" className="citizen-button citizen-submit" disabled={busy}>{busy ? t.auth.wait : heading}<ArrowRight size={18} aria-hidden="true"/></button>
    </form>
    {!admin && <button type="button" className="citizen-text-button" disabled={busy} onClick={() => {setRegister(!register); setDetail(null); setCreated(false);}}>
      {register ? t.auth.signIn : t.auth.register}
    </button>}
  </>;
}
