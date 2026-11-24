import React, {useEffect, useState} from 'react';
import {LockKeyhole, ShieldCheck} from 'lucide-react';
import {request} from '../api/client';

const codePattern = '(?:[A-Za-z0-9_]|-){43}';
const wording = {
  bn: {
    forgot: 'পাসওয়ার্ড ভুলে গেছেন?', emailIntro: 'অ্যাকাউন্টের ইমেইল ঠিকানায় পাসওয়ার্ড বদলানোর কোড নিন।',
    emailButton: 'ইমেইলে কোড পাঠান', emailOff: 'ইমেইলে কোড পাঠানো এখন অনুপলব্ধ।',
    emailSent: 'এই ঠিকানায় অ্যাকাউন্ট থাকলে ৬ সংখ্যার কোড আসবে। কোডটি ১০ মিনিট কার্যকর।',
    emailCode: 'ইমেইলে পাওয়া ৬ সংখ্যার কোড', changeEmail: 'অন্য ইমেইল দিন', resend: 'আবার কোড পাঠান',
    backup: 'রিকভারি কোড', useBackup: 'সংরক্ষিত রিকভারি কোড ব্যবহার করুন',
    backupIntro: 'পাসওয়ার্ড ভুলে গেলে এই একবার ব্যবহারযোগ্য কোড দিয়ে ফিরে আসতে পারবেন। নতুন কোড বানালে আগেরটি বাতিল হবে।',
    generate: 'রিকভারি কোড তৈরি করুন', save: 'কোডটি এখনই পাসওয়ার্ড ম্যানেজারে রাখুন। এটি আবার দেখানো হবে না।',
    backupCreated: 'রিকভারি কোড তৈরি হয়েছে।',
    reset: 'নতুন পাসওয়ার্ড সেট করুন', current: 'বর্তমান পাসওয়ার্ড', password: 'নতুন পাসওয়ার্ড', confirm: 'নতুন পাসওয়ার্ড আবার দিন',
    resetIntro: 'পাসওয়ার্ড বদলালে পুরোনো সেশন ও রিকভারি কোডগুলো বাতিল হবে।',
    resetDone: 'পাসওয়ার্ড বদলেছে। নতুন পাসওয়ার্ড দিয়ে সাইন ইন করুন।',
    mismatch: 'দুই ঘরে একই নতুন পাসওয়ার্ড দিন।', invalid: 'এই রিকভারি কোড বা লিংকটি ভুল অথবা মেয়াদ শেষ হয়েছে।',
    wrongPassword: 'বর্তমান পাসওয়ার্ডটি যাচাই করুন।',
    admin: 'প্রথম অ্যাডমিন সেটআপ', setupIntro: 'Render-এ সংরক্ষিত একবার ব্যবহারযোগ্য অ্যাডমিন সেটআপ কোডটি দিন।',
    setupCode: 'অ্যাডমিন সেটআপ কোড', continue: 'সেটআপ চালিয়ে যান', setupOff: 'অ্যাডমিন সেটআপ এখন বন্ধ আছে অথবা কোডটির মেয়াদ শেষ হয়েছে।',
    activate: 'অ্যাডমিন অ্যাকাউন্ট চালু করুন', setupDone: 'অ্যাডমিন অ্যাকাউন্ট চালু হয়েছে। ইমেইল ও নতুন পাসওয়ার্ড দিয়ে সাইন ইন করুন।',
    badSetup: 'অ্যাডমিন সেটআপ কোডটি ভুল অথবা মেয়াদ শেষ হয়েছে।',
    alreadySetup: 'এই সাইটে ইতিমধ্যে একটি অ্যাডমিন অ্যাকাউন্ট চালু আছে।',
    adminPasswordHint: 'অন্তত ১৫ অক্ষরের একটি নতুন, আলাদা পাসওয়ার্ড দিন।',
  },
  en: {
    forgot: 'Forgot password?', emailIntro: 'Request a password reset code at the email address for your account.',
    emailButton: 'Email me a code', emailOff: 'Email recovery is currently unavailable.',
    emailSent: 'If this address has an eligible account, a six-digit code will arrive by email. It expires in 10 minutes.',
    emailCode: 'Six-digit email code', changeEmail: 'Use another email', resend: 'Send a new code',
    backup: 'Recovery code', useBackup: 'Use a saved recovery code',
    backupIntro: 'Save a single-use code for when you forget your password. Generating a new code revokes the previous one.',
    generate: 'Generate recovery code', save: 'Save this code in your password manager now. It is shown only once.',
    backupCreated: 'Recovery code generated.',
    reset: 'Set a new password', current: 'Current password', password: 'New password', confirm: 'Confirm new password',
    resetIntro: 'Changing your password signs you out everywhere and revokes old recovery codes.',
    resetDone: 'Your password was changed. Sign in with the new password.',
    mismatch: 'Enter the same new password in both fields.', invalid: 'This recovery code or link is invalid or has expired.',
    wrongPassword: 'Check your current password.',
    admin: 'Set up the first administrator', setupIntro: 'Enter the one-time administrator setup code stored in Render.',
    setupCode: 'Administrator setup code', continue: 'Continue setup', setupOff: 'Administrator setup is disabled or the code has expired.',
    activate: 'Activate administrator account', setupDone: 'Administrator activated. Sign in with your email and new password.',
    badSetup: 'The administrator setup code is invalid or has expired.',
    alreadySetup: 'An administrator is already set up for this site.',
    adminPasswordHint: 'Use a new, unique password of at least 15 characters.',
  },
};

export function recoveryLabel(language, key) {
  return wording[language][key];
}

function submit(path, body) {
  return request('/auth/' + path, {method: 'POST', body: JSON.stringify(body)});
}

function message(t, labels, problem, field) {
  if (problem.status === 429) return t.rateLimited;
  if (!problem.status || problem.status >= 500) return t.serviceUnavailable;
  if (problem.status === 409) return labels.alreadySetup;
  return labels[field];
}

function NewPasswordFields({t, labels, admin = false, busy}) {
  const minimum = admin ? 15 : 10;
  return <>
    <label>{labels.password}
      <input name="password" type="password" autoComplete="new-password" minLength={minimum} maxLength={128} required disabled={busy}/>
      <small>{admin ? labels.adminPasswordHint : t.auth.passwordHint}</small>
    </label>
    <label>{labels.confirm}
      <input name="confirmation" type="password" autoComplete="new-password" minLength={minimum} maxLength={128} required disabled={busy}/>
    </label>
  </>;
}

function RecoveryHeading({title, intro, admin = false}) {
  const Icon = admin ? ShieldCheck : LockKeyhole;
  return <div className="citizen-card-header">
    <span className="citizen-card-icon"><Icon size={23} aria-hidden="true"/></span>
    <div><h1>{title}</h1>{intro && <p>{intro}</p>}</div>
  </div>;
}

export function PasswordRecovery({t, language, route, emailAvailable, onReset, onSignIn}) {
  const labels = wording[language];
  const [linkCode] = useState(() => route.split('/')[1] || '');
  const legacyReset = route.startsWith('#reset-password');
  const [email, setEmail] = useState('');
  const [emailPending, setEmailPending] = useState(false);
  const [resendAt, setResendAt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');
  const [done, setDone] = useState(false);
  const reset = legacyReset || emailPending;
  useEffect(() => {
    if (linkCode && window.location.hash === route) {
      history.replaceState(null, '', '#reset-password');
    }
  }, [linkCode, route]);

  useEffect(() => {
    if (!resendAt) return;
    const timer = window.setTimeout(() => setResendAt(0), Math.max(0, resendAt - Date.now()));
    return () => window.clearTimeout(timer);
  }, [resendAt]);

  async function requestCode(address) {
    setBusy(true);
    setFailure('');
    try {
      await submit('recovery/email', {email: address});
      setEmail(address);
      setEmailPending(true);
      setResendAt(Date.now() + 60000);
    } catch (problem) {
      setFailure(problem);
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    if (!reset) {
      await requestCode(String(fields.get('email')).trim());
      return;
    }
    const password = fields.get('password');
    if (reset && password !== fields.get('confirmation')) {
      setFailure('mismatch');
      return;
    }
    setBusy(true);
    setFailure('');
    try {
      const code = linkCode || String(fields.get('code')).trim();
      if (emailPending) {
        await submit('recovery/email/confirm', {
          email, password, code: code.replace(/[০-৯]/g, digit => String(digit.charCodeAt(0) - 2534)),
        });
      } else await submit('recovery/reset', {code, password});
      setDone(true);
      onReset();
    } catch (problem) {
      setFailure(problem);
    } finally {
      setBusy(false);
    }
  }

  return <>
    <RecoveryHeading title={reset ? labels.reset : labels.forgot}
      intro={emailPending ? labels.emailSent : legacyReset ? labels.resetIntro
        : emailAvailable === false ? labels.emailOff : labels.emailIntro}/>
    {done ? <div className="citizen-form">
      <p role="status">{labels.resetDone}</p>
      <button type="button" className="citizen-button citizen-submit" onClick={onSignIn}>{t.signIn}</button>
    </div> : <form key={reset ? 'reset' : 'email'} className="citizen-form" onSubmit={handleSubmit}>
      {reset ? <>
        {emailPending ? <label>{labels.emailCode}
          <input name="code" pattern="[0-9০-৯]{6}" inputMode="numeric" autoComplete="one-time-code" required disabled={busy} maxLength={6}/>
        </label> : !linkCode && <label>{labels.backup}
          <input name="code" pattern={codePattern} autoComplete="off" spellCheck={false} required disabled={busy} maxLength={43}/>
        </label>}
        <NewPasswordFields t={t} labels={labels} busy={busy}/>
      </> : <label>{t.auth.email}
        <input name="email" type="email" autoComplete="email" defaultValue={email} required maxLength={254} disabled={busy}/>
      </label>}
      {failure && <p className="citizen-error" role="alert">{failure === 'mismatch' ? labels.mismatch : message(t, labels, failure, 'invalid')}</p>}
      <button type="submit" className="citizen-button citizen-submit" disabled={busy || (!reset && emailAvailable !== true)}>
        {busy ? t.auth.wait : reset ? labels.reset : labels.emailButton}
      </button>
    </form>}
    {!reset && <a className="citizen-text-button citizen-admin-link" href="#reset-password">{labels.useBackup}</a>}
    {legacyReset && !done && <a className="citizen-text-button citizen-admin-link" href="#forgot-password">{labels.forgot}</a>}
    {emailPending && !done && <div className="citizen-account-actions">
      <button type="button" className="citizen-text-button" disabled={busy || !!resendAt}
        onClick={() => requestCode(email)}>{labels.resend}</button>
      <button type="button" className="citizen-text-button" disabled={busy}
        onClick={() => {setEmailPending(false); setFailure('');}}>{labels.changeEmail}</button>
    </div>}
  </>;
}

export function RecoveryCode({t, language}) {
  const labels = wording[language];
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);

  async function generate(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const {password} = Object.fromEntries(new FormData(form));
    setBusy(true);
    setFailure(null);
    try {
      const result = await submit('recovery/code', {password});
      form.reset();
      setCode(result.code);
    } catch (problem) {
      setFailure(problem);
    } finally {
      setBusy(false);
    }
  }

  return <details className="citizen-optional citizen-recovery-code" onToggle={event => {
    if (!event.currentTarget.open) setCode('');
  }}>
    <summary>{labels.backup}</summary>
    <p>{labels.backupIntro}</p>
    <form className="citizen-form" onSubmit={generate}>
      <label>{labels.current}<input name="password" type="password" autoComplete="current-password" required maxLength={128} disabled={busy}/></label>
      {failure && <p className="citizen-error" role="alert">{message(t, labels, failure, 'wrongPassword')}</p>}
      <button type="submit" className="citizen-text-button" disabled={busy}>{busy ? t.auth.wait : labels.generate}</button>
    </form>
    {code && <div className="citizen-secret-value">
      <strong role="status">{labels.backupCreated}</strong>
      <p>{labels.save}</p>
      <code dir="ltr">{code}</code>
    </div>}
  </details>;
}

export function FirstAdminSetup({t, language, enabled, onComplete}) {
  const labels = wording[language];
  const [challenge, setChallenge] = useState(null);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const password = fields.get('password');
    if (challenge && password !== fields.get('confirmation')) {
      setFailure('mismatch');
      return;
    }
    setBusy(true);
    setFailure(null);
    try {
      if (!challenge) {
        const code = fields.get('code').trim();
        const data = await submit('admin-setup/challenge', {code});
        setChallenge({...data, code});
      } else {
        await submit('admin-setup/complete', {code: challenge.code, password});
        setChallenge(null);
        setDone(true);
        onComplete();
      }
    } catch (problem) {
      setFailure(problem);
    } finally {
      setBusy(false);
    }
  }

  return <>
    <RecoveryHeading title={labels.admin} intro={enabled === true && !done ? labels.setupIntro : null} admin/>
    {done ? <div className="citizen-form">
      <p role="status">{labels.setupDone}</p>
      <a className="citizen-button citizen-submit" href="#admin">{t.workspace}</a>
    </div> : enabled !== true ? <p role="status">{enabled === null ? t.auth.wait : labels.setupOff}</p>
      : <form key={challenge ? 'confirm' : 'start'} className="citizen-form" onSubmit={handleSubmit}>
        {challenge ? <>
          <p>{t.auth.email} · {challenge.email}</p>
          <NewPasswordFields t={t} labels={labels} admin busy={busy}/>
        </> : <label>{labels.setupCode}
          <input name="code" type="password" pattern={codePattern} autoComplete="off" required disabled={busy} maxLength={43}/>
        </label>}
        {failure && <p className="citizen-error" role="alert">{failure === 'mismatch' ? labels.mismatch : message(t, labels, failure, 'badSetup')}</p>}
        <button type="submit" className="citizen-button citizen-submit" disabled={busy}>
          {busy ? t.auth.wait : challenge ? labels.activate : labels.continue}
        </button>
      </form>}
  </>;
}
