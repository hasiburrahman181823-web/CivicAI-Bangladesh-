import React, {lazy, Suspense, useEffect, useRef, useState} from 'react';
import {
  ArrowDown, ArrowLeft, ArrowRight, CheckCircle2, ClipboardList, Construction,
  Download, Droplets, FileText, LockKeyhole, MapPin, Search, ShieldCheck,
  Trash2, UserRound, X, Zap,
} from 'lucide-react';
import {request} from '../api/client';
import {MediaTools} from '../components/ModelTools';
import {copy} from './copy';
import {translateWorkspace, WorkspaceLanguage} from '../workspaceLanguage';
import './portal.css';

const Workspace = lazy(() => import('../Workspace'));
const issueIcons = [Construction, Droplets, Trash2, Zap];
const languages = ['Bangla', 'English', 'Banglish'];
const emptyForm = {title: '', area: '', text: '', time: '', language: ''};
const isPreview = import.meta.env.VITE_UI_PREVIEW === '1';

function errorCopy(t, problem, context) {
  if (problem.status === 429) return t.rateLimited;
  if (!problem.status || problem.status >= 500 || problem.status < 400) return t.serviceUnavailable;
  if (context === 'track') return t.trackMissing;
  if (context === 'auth') return t.auth.failed;
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

export function CitizenPortal() {
  const [language, setLanguage] = useState(() => localStorage.getItem('civic-language') === 'en' ? 'en' : 'bn');
  const [route, setRoute] = useState(() => window.location.hash);
  const [session, setSession] = useState(null);
  const [account, setAccount] = useState(false);
  const [workspace, setWorkspace] = useState(false);
  const [accountError, setAccountError] = useState(null);
  const [trackingReceipt, setTrackingReceipt] = useState(null);
  const trackHeading = useRef(null);
  const reportPanel = useRef(null);
  const homeHeading = useRef(null);
  const t = copy[language];
  const tracking = route === '#track';
  const workspaceOpen = workspace || (isPreview && route === '#admin-preview');
  const languageControl = <LanguageSwitcher language={language} onChange={setLanguage} label={t.language}/>;
  const workspaceLanguage = {language, t: (message, values) => translateWorkspace(language, message, values)};

  useEffect(() => {
    if (!isPreview) request('/auth/me').then(setSession).catch(() => {});
    function hashChanged() { setRoute(window.location.hash); }
    window.addEventListener('hashchange', hashChanged);
    return () => window.removeEventListener('hashchange', hashChanged);
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    localStorage.setItem('civic-language', language);
  }, [language]);

  useEffect(() => {
    const section = route === '#track' ? trackHeading.current
      : route === '#report' ? reportPanel.current
      : route === '#home' ? homeHeading.current : null;
    if (section && !workspaceOpen) section.focus();
  }, [route, workspaceOpen]);

  async function signOut() {
    try {
      await request('/auth/logout', {method: 'POST'});
      setSession(null);
      setAccountError(null);
    } catch (error) {
      setAccountError(error);
    }
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
            <a href="#home" aria-current={!tracking && route !== '#report' ? 'page' : undefined}>{t.home}</a>
            <a href="#report" aria-current={route === '#report' ? 'page' : undefined}>{t.report}</a>
            <a href="#track" aria-current={tracking ? 'page' : undefined}>{t.track}</a>
          </nav>
          <div className="citizen-actions">
            {languageControl}
            <button type="button" className="citizen-account" disabled={isPreview} onClick={() => session ? signOut() : setAccount(true)}>
              <UserRound size={17} aria-hidden="true"/><span>{session ? t.signOut : t.signIn}</span>
            </button>
          </div>
        </div>
      </header>

      {isPreview && <div className="citizen-preview">
        <span>{t.preview}</span><a href="#admin-preview">{workspaceLanguage.t('Preview admin workspace')}</a>
      </div>}
      {accountError && <p className="citizen-container citizen-error" role="alert">{errorCopy(t, accountError, 'auth')}</p>}

      <main className="citizen-main" id="content" tabIndex={-1}>
        <div hidden={tracking}>
          <section className="citizen-hero">
            <div className="citizen-container citizen-hero-inner">
              <div className="citizen-hero-copy">
                <div className="citizen-service"><span/><span>{t.service}</span></div>
                <h1 tabIndex={-1} ref={homeHeading}>{t.heading[0]} <em>{t.heading[1]}</em></h1>
                <p>{t.intro}</p>
                <div className="citizen-hero-actions">
                  <a className="citizen-button citizen-button-light" href="#report">{t.report}<ArrowDown size={18} aria-hidden="true"/></a>
                  <a className="citizen-hero-link" href="#track">{t.trackLink}<ArrowRight size={18} aria-hidden="true"/></a>
                </div>
                <div className="citizen-assurance">
                  <span className="citizen-assurance-icon"><ShieldCheck size={22} aria-hidden="true"/></span>
                  <div><strong>{t.privacyTitle}</strong><span>{t.privacyText}</span></div>
                </div>
              </div>
              <section className="citizen-card citizen-report" id="report" tabIndex={-1} ref={reportPanel} aria-label={t.formTitle}>
                <ComplaintForm t={t} language={language} onTrack={trackReport}/>
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
        {tracking && <section className="citizen-container citizen-tracking">
          <a className="citizen-back" href="#home"><ArrowLeft size={17} aria-hidden="true"/>{t.home}</a>
          <div className="citizen-card">
            <CardHeader Icon={Search} title={t.track} intro={t.trackIntro} headingRef={trackHeading} primaryHeading/>
            <TrackingForm t={t} receipt={trackingReceipt}/>
          </div>
        </section>}
      </main>

      <footer className="citizen-footer">
        <div className="citizen-container citizen-footer-inner">
          <Brand t={t}/>
          <p>{t.footer}</p>
          {session?.role === 'admin' && <button type="button" className="citizen-text-button" onClick={() => setWorkspace(true)}>
            {t.workspace}<ArrowRight size={16} aria-hidden="true"/>
          </button>}
        </div>
      </footer>
      {account && <AccountDialog t={t} onClose={() => setAccount(false)} onLogin={value => {
        setSession(value);
        setAccount(false);
        setAccountError(null);
        if (value.role === 'admin') setWorkspace(true);
      }}/>}
    </div>
    {workspaceOpen && <WorkspaceLanguage.Provider value={workspaceLanguage}>
      <Suspense fallback={<p className="citizen-loading" role="status">{t.auth.wait}</p>}>
        <Workspace initialSession={session} languageControl={languageControl} preview={isPreview} onExit={() => {
          setWorkspace(false);
          if (isPreview) window.location.hash = 'home';
        }} onLogout={() => {
          setSession(null);
          setWorkspace(false);
        }}/>
      </Suspense>
    </WorkspaceLanguage.Provider>}
  </>;
}

function CardHeader({Icon, title, intro, headingRef, primaryHeading = false}) {
  return <div className="citizen-card-header">
    <span className="citizen-card-icon"><Icon size={23} aria-hidden="true"/></span>
    <div>
      {primaryHeading
        ? <h1 ref={headingRef} tabIndex={-1}>{title}</h1>
        : <h2 ref={headingRef} tabIndex={headingRef ? -1 : undefined}>{title}</h2>}
      <p>{intro}</p>
    </div>
  </div>;
}

function ComplaintForm({t, language, onTrack}) {
  const [form, setForm] = useState(emptyForm);
  const [receipt, setReceipt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const receiptHeading = useRef(null);
  const complaintLanguage = form.language || (/[\u0980-\u09ff]/.test(form.text) ? 'Bangla' : form.text.trim() ? 'English' : language === 'bn' ? 'Bangla' : 'English');

  useEffect(() => { if (receipt) receiptHeading.current?.focus(); }, [receipt]);

  function change(event) {
    const {name, value} = event.target;
    setForm(current => ({...current, [name]: value}));
    setError(null);
  }

  async function submit(event) {
    event.preventDefault();
    if (isPreview || busy) return;
    const {title, area, text} = form;
    if (title.trim().length < 5 || area.trim().length < 2 || text.trim().length < 10) {
      setError('shortReport');
      return;
    }
    const date = form.time ? new Date(form.time) : new Date();
    if (Number.isNaN(date.getTime()) || date.getTime() > Date.now()) {
      setError('invalidTime');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await request('/complaints', {
        method: 'POST',
        body: JSON.stringify({
          title: title.trim(), area: area.trim(), text: text.trim(),
          occurred_at: date.toISOString(), language: complaintLanguage,
        }),
      });
      if (!result?.id || !result?.tracking_key) throw new Error('Missing receipt');
      setReceipt({id: result.id, tracking_key: result.tracking_key});
      setForm(emptyForm);
    } catch (problem) {
      setError(problem);
    } finally {
      setBusy(false);
    }
  }

  if (receipt) return <div className="citizen-receipt">
    <CardHeader Icon={CheckCircle2} title={t.success} intro={t.savePrompt} headingRef={receiptHeading}/>
    <dl>
      <div><dt>{t.reportId}</dt><dd><code>{receipt.id}</code></dd></div>
      <div><dt>{t.trackingKey}</dt><dd><code>{receipt.tracking_key}</code></dd></div>
    </dl>
    <button type="button" className="citizen-button citizen-submit" onClick={() => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(receipt, null, 2)], {type: 'application/json'}));
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
  </div>;

  return <>
    <CardHeader Icon={ClipboardList} title={t.formTitle} intro={t.formIntro}/>
    <form className="citizen-form" onSubmit={submit}>
      <div className="citizen-form-row">
        <label>{t.title}
          <input name="title" value={form.title} onChange={change} placeholder={t.titlePlaceholder} minLength={5} maxLength={120} required disabled={busy}/>
        </label>
        <label>{t.area}
          <input name="area" value={form.area} onChange={change} placeholder={t.areaPlaceholder} minLength={2} maxLength={120} required disabled={busy}/>
        </label>
      </div>
      <label>{t.details}
        <textarea name="text" value={form.text} onChange={change} placeholder={t.detailsPlaceholder} minLength={10} maxLength={1000} rows={3} required disabled={busy}/>
        <small className="citizen-counter">{new Intl.NumberFormat(language).format(form.text.length)} / {new Intl.NumberFormat(language).format(1000)}</small>
      </label>
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
      </details>
      {error && <p className="citizen-error" role="alert">{typeof error === 'string' ? t[error] : errorCopy(t, error, 'report')}</p>}
      <button className="citizen-button citizen-submit" type="submit" disabled={busy || isPreview}>
        <span>{busy ? t.sending : t.send}</span><ArrowRight size={19} aria-hidden="true"/>
      </button>
    </form>
    {!isPreview && <MediaTools
      language={complaintLanguage}
      uiLanguage={language}
      onTranscript={text => {
        setForm(previous => ({...previous, text: text.slice(0, 1000)}));
        setError(null);
      }}
    />}
    <p className="citizen-form-privacy"><LockKeyhole size={15} aria-hidden="true"/>{t.privacyText}</p>
  </>;
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

function AccountDialog({t, onClose, onLogin}) {
  const dialog = useRef(null);
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState(null);
  const [created, setCreated] = useState(false);
  const heading = register ? t.auth.register : t.auth.signIn;

  useEffect(() => { dialog.current?.showModal(); }, []);

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
        body: JSON.stringify(register ? credentials : {...credentials, otp: fields.get('otp') || null}),
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

  return <dialog ref={dialog} className="citizen-dialog citizen-card" onClose={onClose} aria-labelledby="citizen-account-heading">
    <button type="button" className="citizen-close" aria-label={t.auth.close} onClick={() => dialog.current.close()}><X size={22} aria-hidden="true"/></button>
    <span className="citizen-card-icon"><UserRound size={22} aria-hidden="true"/></span>
    <h2 id="citizen-account-heading">{heading}</h2>
    <p>{t.privacyTitle}</p>
    <form className="citizen-form" onSubmit={submit}>
      <label>{t.auth.email}<input name="email" type="email" autoComplete="email" required maxLength={254} disabled={busy}/></label>
      <label>{t.auth.password}<input key={register} name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} minLength={10} maxLength={128} required disabled={busy}/></label>
      {!register && <details className="citizen-optional">
        <summary>{t.auth.otpPrompt}</summary>
        <label>{t.auth.otp}<input name="otp" inputMode="numeric" pattern="[0-9]{6}" autoComplete="one-time-code" maxLength={6} disabled={busy}/></label>
      </details>}
      {created && <p role="status">{t.auth.created}</p>}
      {detail && <p className="citizen-error" role="alert">{errorCopy(t, detail, 'auth')}</p>}
      <button type="submit" className="citizen-button citizen-submit" disabled={busy}>{busy ? t.auth.wait : heading}<ArrowRight size={18} aria-hidden="true"/></button>
    </form>
    <button type="button" className="citizen-text-button" disabled={busy} onClick={() => {setRegister(!register); setDetail(null); setCreated(false);}}>
      {register ? t.auth.signIn : t.auth.register}
    </button>
  </dialog>;
}
