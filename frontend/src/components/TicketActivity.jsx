import React, {useEffect, useRef, useState} from 'react';
import {Bell, Clock3, Download, FilePlus2, MessageCircle, ShieldCheck} from 'lucide-react';
import {API, request} from '../api/client';
import {evidenceAccept, validEvidence} from '../api/evidence';
import './ticket.css';

const en = {
  loading: 'Loading ticket…', unavailable: 'The ticket could not be loaded.', retry: 'Retry',
  estimate: 'Estimated resolution', noEstimate: 'An estimate will appear when there are enough resolved reports in this category.',
  hours: 'Typical time from submission', samples: 'Past reports used', passed: 'The estimated time has passed.',
  history: 'Status history', discussion: 'Ticket messages', none: 'No messages yet.',
  staff: 'Review team', citizen: 'Citizen', write: 'Write an update', send: 'Send message',
  evidence: 'Photos and videos', pick: 'Choose a photo or video', upload: 'Upload evidence',
  mediaHint: 'Photos up to 2 MB. MP4, MOV or WebM videos up to 12 MB and 30 seconds. Up to five files per ticket.',
  noFiles: 'No files attached.', downloadPhoto: 'Download photo', downloadVideo: 'Download video', update: 'New ticket activity',
  guest: 'This guest report has no account for replies.', problem: 'The request could not be completed. Check the information and try again.',
  tooLarge: 'Photos must be 2 MB or smaller and videos 12 MB or smaller.',
  format: 'Choose a JPEG, PNG or WebP photo, or a playable MP4, MOV or WebM video of 30 seconds or less.',
  limit: 'This ticket already has five files.', rate: 'Too many requests. Please wait a minute.',
  expired: 'Your session has expired. Sign in again to see this ticket.',
  assessment: 'AI assessment', suggested: 'Suggested first step', summary: 'Summary',
  sentiment: 'Sentiment', flags: 'Review signals', noFlags: 'No flags',
  caution: 'Review signals indicate language or submission patterns. A reviewer must independently verify the complaint.',
  contact: 'Contact and intake', noContact: 'No intake contact recorded.', verified: 'Mobile verified',
  unverified: 'Mobile unverified', reveal: 'View restricted details', reason: 'Reason for accessing restricted data',
  contactError: 'Contact access could not be completed.', hide: 'Hide restricted details',
  mobile: 'Mobile', ip: 'Connection address', device: 'Reported device', unknown: 'Unknown',
  positive: 'Positive', neutral: 'Neutral', negative: 'Negative', uncertain: 'Uncertain',
  promotional_language: 'Promotional language', potential_abuse: 'Potential abuse',
  automated_pattern: 'Repetitive text or links',
  Submitted: 'Submitted', 'Under review': 'Under review', 'In progress': 'In progress', Resolved: 'Resolved',
  mobileDevice: 'Mobile', tablet: 'Tablet', desktop_or_other: 'Desktop or other',
};
const bn = {
  loading: 'টিকিট লোড হচ্ছে…', unavailable: 'টিকিট লোড করা যায়নি।', retry: 'আবার চেষ্টা করুন',
  estimate: 'সমাধানের আনুমানিক সময়', noEstimate: 'এই বিভাগে পর্যাপ্ত অভিযোগ নিষ্পত্তি হলে আনুমানিক সময় দেখা যাবে।',
  hours: 'জমা দেওয়ার পর সাধারণত যত সময় লাগে', samples: 'বিশ্লেষণে ব্যবহৃত আগের অভিযোগ', passed: 'আনুমানিক সময় পার হয়েছে।',
  history: 'অবস্থার ইতিহাস', discussion: 'টিকিটের বার্তা', none: 'এখনও কোনো বার্তা নেই।',
  staff: 'পর্যালোচনা দল', citizen: 'নাগরিক', write: 'হালনাগাদ লিখুন', send: 'বার্তা পাঠান',
  evidence: 'প্রমাণের ছবি ও ভিডিও', pick: 'ছবি বা ভিডিও বাছাই করুন', upload: 'প্রমাণ আপলোড করুন',
  mediaHint: 'ছবি ২ MB পর্যন্ত। MP4, MOV বা WebM ভিডিও ১২ MB ও ৩০ সেকেন্ড পর্যন্ত। প্রতি টিকিটে সর্বোচ্চ ৫টি ফাইল।',
  noFiles: 'কোনো ফাইল সংযুক্ত নেই।', downloadPhoto: 'ছবি ডাউনলোড করুন', downloadVideo: 'ভিডিও ডাউনলোড করুন', update: 'টিকিটে নতুন আপডেট এসেছে',
  guest: 'অতিথির এই অভিযোগে উত্তর পাঠানোর জন্য কোনো অ্যাকাউন্ট নেই।',
  problem: 'কাজটি সম্পন্ন হয়নি। তথ্য যাচাই করে আবার চেষ্টা করুন।',
  tooLarge: 'ছবি ২ MB ও ভিডিও ১২ MB-এর মধ্যে রাখুন।',
  format: 'JPEG, PNG বা WebP ছবি অথবা ৩০ সেকেন্ডের মধ্যে চালানো যায় এমন MP4, MOV বা WebM ভিডিও দিন।',
  limit: 'এই টিকিটে ইতিমধ্যে ৫টি ফাইল আছে।', rate: 'অনেকবার চেষ্টা করা হয়েছে। এক মিনিট অপেক্ষা করুন।',
  expired: 'সেশনের মেয়াদ শেষ হয়েছে। টিকিট দেখতে আবার সাইন ইন করুন।',
  assessment: 'এআই বিশ্লেষণ', suggested: 'প্রস্তাবিত প্রথম পদক্ষেপ', summary: 'সারসংক্ষেপ',
  sentiment: 'ভাষার আবেগ', flags: 'যাচাইয়ের সংকেত', noFlags: 'কোনো সংকেত নেই',
  caution: 'এই সংকেত ভাষা বা জমা দেওয়ার ধরন নির্দেশ করে। অভিযোগটি আলাদাভাবে যাচাই করুন।',
  contact: 'যোগাযোগ ও জমার তথ্য', noContact: 'যোগাযোগের তথ্য সংরক্ষিত নেই।', verified: 'মোবাইল যাচাই করা হয়েছে',
  unverified: 'মোবাইল যাচাই করা হয়নি', reveal: 'সুরক্ষিত তথ্য দেখুন', reason: 'তথ্য দেখার কারণ লিখুন',
  contactError: 'যোগাযোগের তথ্য দেখা যায়নি।', hide: 'সুরক্ষিত তথ্য লুকান',
  mobile: 'মোবাইল', ip: 'সংযোগের ঠিকানা', device: 'ডিভাইসের ধরন', unknown: 'অজানা',
  positive: 'ইতিবাচক', neutral: 'নিরপেক্ষ', negative: 'নেতিবাচক', uncertain: 'অনিশ্চিত',
  promotional_language: 'প্রচারমূলক ভাষা', potential_abuse: 'সম্ভাব্য আপত্তিকর ভাষা',
  automated_pattern: 'পুনরাবৃত্ত লেখা বা লিংক',
  Submitted: 'জমা হয়েছে', 'Under review': 'পর্যালোচনাধীন', 'In progress': 'চলমান', Resolved: 'সমাধান হয়েছে',
  mobileDevice: 'মোবাইল', tablet: 'ট্যাবলেট', desktop_or_other: 'ডেস্কটপ বা অন্য ডিভাইস',
};

function activityProblem(problem) {
  return {401: 'expired', 409: 'limit', 413: 'tooLarge', 429: 'rate'}[problem.status] || 'problem';
}

function AdminIntake({item, t, language, path}) {
  const [restricted, setRestricted] = useState(null);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const assessment = item.assessment;

  async function reveal(event) {
    event.preventDefault();
    setBusy(true);
    setFailed(false);
    try {
      setRestricted(await request(path + '/contact', {method: 'POST', body: JSON.stringify({reason})}));
      setReason('');
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return <>
    {assessment && <section className="ticket-section">
      <h3><ShieldCheck size={18}/>{t.assessment}</h3>
      <p className="ticket-label">{assessment.department[language]} · {t.sentiment} {t[assessment.sentiment]}</p>
      <dl className="ticket-definition">
        <div><dt>{t.summary}</dt><dd>{assessment.summary}</dd></div>
        <div><dt>{t.suggested}</dt><dd>{assessment.suggested_action[language]}</dd></div>
        <div><dt>{t.flags}</dt><dd>{assessment.flags.length ? assessment.flags.map(flag => t[flag]).join(' · ') : t.noFlags}</dd></div>
      </dl>
      <small>{t.caution}</small>
    </section>}
    <section className="ticket-section">
      <h3>{t.contact}</h3>
      <p>{item.intake?.mobile ? <>{item.intake.mobile} · {t[item.intake.verified ? 'verified' : 'unverified']}</> : t.noContact}</p>
      {item.intake && item.can_reveal && (restricted ? <>
        <dl className="ticket-definition">
          <div><dt>{t.mobile}</dt><dd>{restricted.mobile || t.unknown}</dd></div>
          <div><dt>{t.ip}</dt><dd>{restricted.source_ip || t.unknown}</dd></div>
          <div><dt>{t.device}</dt><dd>{t[restricted.device === 'mobile' ? 'mobileDevice' : restricted.device] || t.unknown}</dd></div>
        </dl>
        <button type="button" className="ticket-button" onClick={() => setRestricted(null)}>{t.hide}</button>
      </> : <form onSubmit={reveal} className="ticket-form">
        <label>{t.reason}<input value={reason} onChange={event => setReason(event.target.value)} minLength={10} maxLength={300} required/></label>
        <button type="submit" className="ticket-button" disabled={busy}>{t.reveal}</button>
        {failed && <p role="alert">{t.contactError}</p>}
      </form>)}
    </section>
  </>;
}

export function TicketActivity({id, language, admin = false}) {
  const t = language === 'bn' ? bn : en;
  const path = '/tickets/' + id;
  const [item, setItem] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [problem, setProblem] = useState(null);
  const [message, setMessage] = useState('');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0);
  const [notice, setNotice] = useState(false);
  const signature = useRef(null);
  const fileInput = useRef(null);
  const locale = language === 'bn' ? 'bn-BD' : 'en-GB';
  const datetime = new Intl.DateTimeFormat(locale, {dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Dhaka'});
  const hours = value => new Intl.NumberFormat(locale, {style: 'unit', unit: 'hour', unitDisplay: 'long'}).format(value);

  useEffect(() => {
    const controller = new AbortController();
    let fetching = false;
    async function refresh() {
      if (fetching || document.visibilityState === 'hidden') return;
      fetching = true;
      try {
        const result = await request(path, {signal: controller.signal});
        if (controller.signal.aborted) return;
        const current = [result.status, result.history.at(-1)?.id, result.messages.filter(message => message.role === 'admin').at(-1)?.id].join('|');
        if (signature.current !== null && signature.current !== current) setNotice(true);
        signature.current = current;
        setItem(result);
        setLoadError(null);
      } catch (error) {
        if (!controller.signal.aborted) setLoadError(error.status === 401 ? 'expired' : 'unavailable');
      } finally {
        fetching = false;
      }
    }
    refresh();
    const timer = window.setInterval(refresh, 12000);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      controller.abort();
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, [path, version]);

  async function update(event, evidence) {
    event.preventDefault();
    setProblem(null);
    if (evidence && !file) return;
    if (evidence && !validEvidence(file)) {
      setProblem('format');
      return;
    }
    setBusy(true);
    try {
      let body = JSON.stringify({body: message});
      if (evidence) {
        body = new FormData();
        body.set('file', file);
      }
      await request(path + (evidence ? '/evidence' : '/messages'), {method: 'POST', body});
      if (evidence) {
        setFile(null);
        fileInput.current.value = '';
      } else setMessage('');
      setVersion(previous => previous + 1);
    } catch (error) {
      setProblem(evidence && error.status === 422 ? 'format' : activityProblem(error));
    } finally {
      setBusy(false);
    }
  }

  if (loadError === 'expired' || (!item && loadError)) return <div className="ticket-activity">
    <p role="alert">{t[loadError]}</p>
    <button className="ticket-button" type="button" onClick={() => setVersion(previous => previous + 1)}>{t.retry}</button>
  </div>;
  if (!item) return <p className="ticket-activity" role="status">{t.loading}</p>;
  const estimate = item.estimate;

  return <div className="ticket-activity">
    {notice && <p className="ticket-notice" role="status"><Bell size={16}/>{t.update}</p>}
    {loadError && <p role="status">{t[loadError]}</p>}
    {!admin && <>
      <div className="ticket-heading"><div><h3>{item.title}</h3><p>{item.area}</p></div><strong>{t[item.status]}</strong></div>
      <p className="ticket-description">{item.text}</p>
      {item.status !== 'Resolved' && <section className="ticket-section">
        <h3><Clock3 size={18}/>{t.estimate}</h3>
        {estimate ? <>
          <p>{new Date(estimate.estimated_at) < new Date() ? t.passed : datetime.format(new Date(estimate.estimated_at))}</p>
          <small>{t.hours} {hours(estimate.typical_min_hours)} – {hours(estimate.typical_max_hours)} · {t.samples} {new Intl.NumberFormat(locale).format(estimate.sample_size)}</small>
        </> : <p>{t.noEstimate}</p>}
      </section>}
    </>}
    {admin && <AdminIntake item={item} t={t} language={language} path={path}/>}
    <section className="ticket-section">
      <h3><Bell size={18}/>{t.history}</h3>
      <ul className="ticket-timeline">{[...item.history].reverse().map(event => <li key={event.id}>
        <strong>{t[event.status]}</strong><time dateTime={event.created_at}>{datetime.format(new Date(event.created_at))}</time>
      </li>)}</ul>
    </section>
    <section className="ticket-section">
      <h3><MessageCircle size={18}/>{t.discussion}</h3>
      {item.messages.length ? <ul className="ticket-messages">{item.messages.map(entry => <li key={entry.id}>
        <strong>{entry.role === 'admin' ? t.staff : t.citizen}</strong>
        <time dateTime={entry.created_at}>{datetime.format(new Date(entry.created_at))}</time>
        <p>{entry.body}</p>
      </li>)}</ul> : <p>{t.none}</p>}
      {(!admin || item.can_reply) ? <form className="ticket-form" onSubmit={event => update(event, false)}>
        <label>{t.write}<textarea rows={2} minLength={2} maxLength={1000} required value={message} onChange={event => setMessage(event.target.value)}/></label>
        <button className="ticket-button" type="submit" disabled={busy}>{t.send}</button>
      </form> : <small>{t.guest}</small>}
    </section>
    <section className="ticket-section">
      <h3><FilePlus2 size={18}/>{t.evidence}</h3>
      {item.evidence.length ? <ul className="ticket-files">{item.evidence.map((entry, index) => <li key={entry.id}>
        <a href={API + '/api' + path + '/evidence/' + entry.id}><Download size={15}/>
          {entry.content_type?.startsWith('video/') ? t.downloadVideo : t.downloadPhoto} {new Intl.NumberFormat(locale).format(index + 1)}
        </a>
      </li>)}</ul> : <p>{t.noFiles}</p>}
      {!admin && item.evidence.length < 5 && <form className="ticket-form" onSubmit={event => update(event, true)}>
        <label>{t.pick}<input ref={fileInput} type="file" accept={evidenceAccept} required onChange={event => setFile(event.target.files[0])}/></label>
        <small>{t.mediaHint}</small>
        <button className="ticket-button" type="submit" disabled={busy || !file}>{t.upload}</button>
      </form>}
    </section>
    {problem && <p className="ticket-notice" role="alert">{t[problem]}</p>}
  </div>;
}
