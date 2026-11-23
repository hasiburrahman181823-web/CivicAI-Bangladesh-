import React, {useEffect, useState} from 'react';
import {LockKeyhole, ShieldCheck} from 'lucide-react';
import {request} from '../api/client';

const codePattern = '(?:[A-Za-z0-9_]|-){43}';
const wording = {
  bn: {
    forgot: 'পাসওয়ার্ড ভুলে গেছেন?', emailIntro: 'অ্যাকাউন্টের ইমেইল ঠিকানায় পাসওয়ার্ড রিসেট লিংক নিন।',
    emailButton: 'রিসেট লিংক পাঠান', emailOff: 'ইমেইলে রিসেট লিংক পাঠানোর ব্যবস্থা এখনো চালু হয়নি।',
    emailSent: 'এই ঠিকানায় পুনরুদ্ধারযোগ্য অ্যাকাউন্ট থাকলে রিসেট লিংক পাঠানো হবে। লিংকটি ২০ মিনিট কার্যকর।',
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
    authenticator: 'অথেনটিকেটর অ্যাপে Time based অ্যাকাউন্ট যোগ করে নিচের কী দিন। তারপর CivicAI Bangladesh-এর কোড ব্যবহার করুন।',
    activate: 'অ্যাডমিন অ্যাকাউন্ট চালু করুন', setupDone: 'অ্যাডমিন অ্যাকাউন্ট চালু হয়েছে। অ্যাপে পরের ৬ সংখ্যার কোড এলে সাইন ইন করুন।',
    badSetup: 'অ্যাডমিন সেটআপ কোডটি ভুল অথবা মেয়াদ শেষ হয়েছে।',
    invalidOtp: 'কোডটি মেলেনি। অ্যাপে CivicAI Bangladesh-এর নতুন কোড এলে সেটি দিন। সমস্যাটি থাকলে সেটআপ কী ও ফোনের স্বয়ংক্রিয় সময় যাচাই করুন।',
    alreadySetup: 'এই সাইটে ইতিমধ্যে একটি অ্যাডমিন অ্যাকাউন্ট চালু আছে।',
    adminPasswordHint: 'অন্তত ১২ অক্ষরের একটি নতুন, আলাদা পাসওয়ার্ড দিন।',
  },
  en: {
    forgot: 'Forgot password?', emailIntro: 'Request a reset link at the email address for your account.',
    emailButton: 'Send reset link', emailOff: 'Email recovery is currently unavailable.',
    emailSent: 'If this address has an eligible account, a reset link will arrive by email. The link lasts 20 minutes.',
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
    authenticator: 'Add a time-based account in your authenticator app using the key below. Then use the code for CivicAI Bangladesh.',
    activate: 'Activate administrator account', setupDone: 'Administrator activated. Sign in with the next 6-digit code shown by your app.',
    badSetup: 'The administrator setup code is invalid or has expired.',
    invalidOtp: 'The code did not match. Try the next code for CivicAI Bangladesh. If it still fails, check the setup key and your phone’s automatic time.',
    alreadySetup: 'An administrator is already set up for this site.',
    adminPasswordHint: 'Use a new, unique password of at least 12 characters.',
  },
};

export function recoveryLabel(language, key) {
  return wording[language][key];
}

export function AuthenticatorCodeInput({label, disabled}) {
  return <label>{label}
    <input name="otp" inputMode="numeric" pattern="[0-9]{6}" autoComplete="one-time-code" dir="ltr" required disabled={disabled}
      onChange={event => {
        const input = event.currentTarget;
        input.value = input.value.replace(/[০-৯]/g, digit => String(digit.charCodeAt(0) - 0x09e6)).replace(/\s/g, '');
      }}/>
  </label>;
}

function submit(path, body) {
  return request('/auth/' + path, {method: 'POST', body: JSON.stringify(body)});
}

function message(t, labels, problem, field) {
  if (problem.status === 429) return t.rateLimited;
  if (!problem.status || problem.status >= 500) return t.serviceUnavailable;
  if (problem.status === 409) return labels.alreadySetup;
  if (problem.message === 'Enter a current authenticator code') return labels.invalidOtp;
  return labels[field];
}

function NewPasswordFields({t, labels, admin = false, busy}) {
  const minimum = admin ? 12 : 10;
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
  const reset = route.startsWith('#reset-password');
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (linkCode && window.location.hash === route) {
      history.replaceState(null, '', '#reset-password');
    }
  }, [linkCode, route]);

  async function handleSubmit(event) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const password = fields.get('password');
    if (reset && password !== fields.get('confirmation')) {
      setFailure('mismatch');
      return;
    }
    setBusy(true);
    setFailure('');
    try {
      await (reset
        ? submit('recovery/reset', {code: linkCode || fields.get('code').trim(), password})
        : submit('recovery/email', {email: fields.get('email').trim()}));
      setDone(true);
      if (reset) onReset();
    } catch (problem) {
      setFailure(problem);
    } finally {
      setBusy(false);
    }
  }

  return <>
    <RecoveryHeading title={reset ? labels.reset : labels.forgot}
      intro={reset ? labels.resetIntro : emailAvailable ? labels.emailIntro : labels.emailOff}/>
    {done ? <div className="citizen-form">
      <p role="status">{reset ? labels.resetDone : labels.emailSent}</p>
      {reset && <button type="button" className="citizen-button citizen-submit" onClick={onSignIn}>{t.signIn}</button>}
    </div> : (reset || emailAvailable) && <form className="citizen-form" onSubmit={handleSubmit}>
      {reset ? <>
        {!linkCode && <label>{labels.backup}
          <input name="code" pattern={codePattern} autoComplete="off" spellCheck={false} required disabled={busy} maxLength={43}/>
        </label>}
        <NewPasswordFields t={t} labels={labels} busy={busy}/>
      </> : <label>{t.auth.email}
        <input name="email" type="email" autoComplete="email" required maxLength={254} disabled={busy}/>
      </label>}
      {failure && <p className="citizen-error" role="alert">{failure === 'mismatch' ? labels.mismatch : message(t, labels, failure, 'invalid')}</p>}
      <button type="submit" className="citizen-button citizen-submit" disabled={busy}>
        {busy ? t.auth.wait : reset ? labels.reset : labels.emailButton}
      </button>
    </form>}
    {!reset && <a className="citizen-text-button citizen-admin-link" href="#reset-password">{labels.useBackup}</a>}
    {reset && !done && <a className="citizen-text-button citizen-admin-link" href="#forgot-password">{labels.forgot}</a>}
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
        await submit('admin-setup/complete', {code: challenge.code, password, otp: fields.get('otp')});
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
          <div className="citizen-secret-value">
            <p>{labels.authenticator}</p>
            <code dir="ltr">{challenge.authenticator_key}</code>
          </div>
          <NewPasswordFields t={t} labels={labels} admin busy={busy}/>
          <AuthenticatorCodeInput label={t.auth.otp} disabled={busy}/>
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
