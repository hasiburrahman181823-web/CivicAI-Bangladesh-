import {useWorkspaceLanguage} from '../workspaceLanguage';
import React, {useEffect, useState} from 'react';
import {Activity, Image, Mic} from 'lucide-react';
import {request} from '../api/client';

const mediaCopy = {
  en: {
    summary: 'Voice recording or road photo',
    note: 'Review the transcript or detection results before using them.',
    voice: 'Voice', photo: 'Road photo', audioFile: 'Audio file, up to 60 seconds',
    imageFile: 'Road surface photo', processing: 'Processing…',
    transcribe: 'Transcribe recording', detect: 'Detect road damage',
    transcript: 'Transcript', noSpeech: 'No speech detected.', useText: 'Use in description',
    coordinates: 'Road damage detections', noDamage: 'No supported road damage detected.',
    evidence: 'A reviewer confirms the evidence.',
    error: 'The file could not be processed. Check the file type and size, then try again.',
    labels: {road_damage: 'Road damage'},
  },
  bn: {
    summary: 'ভয়েস রেকর্ডিং অথবা রাস্তার ছবি',
    note: 'ব্যবহারের আগে লেখা বা ছবি বিশ্লেষণের ফলাফল মিলিয়ে নিন।',
    voice: 'ভয়েস', photo: 'রাস্তার ছবি', audioFile: 'অডিও ফাইল, সর্বোচ্চ ৬০ সেকেন্ড',
    imageFile: 'রাস্তার ছবি', processing: 'প্রক্রিয়া চলছে…',
    transcribe: 'রেকর্ডিং থেকে লেখা তৈরি করুন', detect: 'রাস্তার ক্ষতি শনাক্ত করুন',
    transcript: 'রেকর্ডিং থেকে তৈরি লেখা', noSpeech: 'কোনো কথা শনাক্ত হয়নি।',
    useText: 'বিবরণে ব্যবহার করুন', coordinates: 'রাস্তার ক্ষতি শনাক্তকরণের ফলাফল',
    noDamage: 'ছবিতে শনাক্তযোগ্য রাস্তার ক্ষতি পাওয়া যায়নি।',
    evidence: 'বিশ্লেষণের ফলাফল পর্যালোচনা করে সিদ্ধান্ত নেওয়া হয়।',
    error: 'ফাইলটি প্রক্রিয়া করা যায়নি। ধরন ও আকার যাচাই করে আবার চেষ্টা করুন।',
    labels: {road_damage: 'রাস্তার ক্ষতি'},
  },
};

export function MediaTools({language, onTranscript, uiLanguage = 'en', voiceAvailable = true, imageAvailable = true}) {
  const t = mediaCopy[uiLanguage];
  const [kind, setKind] = useState(voiceAvailable ? 'voice' : 'image');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (kind !== 'image' || !file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [kind, file]);

  function selectKind(next) {
    setKind(next);
    setFile(null);
    setResult(null);
    setError('');
  }

  async function run() {
    setBusy(true);
    setResult(null);
    setError('');
    const body = new FormData();
    body.append('file', file);
    const selectedLanguage = {Bangla: 'bn', English: 'en'}[language];
    const audioPath = '/media/transcribe' + (selectedLanguage ? '?language=' + selectedLanguage : '');
    try {
      setResult(await request(kind === 'voice' ? audioPath : '/media/road-image', {
        method: 'POST', body
      }));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  return <details className="media-tools">
    <summary>{voiceAvailable && imageAvailable ? t.summary : voiceAvailable ? t.voice : t.photo}</summary>
    <p className="field-hint">{t.note}</p>
    <div className="media-options">
      {voiceAvailable && <button type="button" className="secondary" aria-pressed={kind === 'voice'} disabled={busy} onClick={() => selectKind('voice')}><Mic size={16}/>{t.voice}</button>}
      {imageAvailable && <button type="button" className="secondary" aria-pressed={kind === 'image'} disabled={busy} onClick={() => selectKind('image')}><Image size={16}/>{t.photo}</button>}
    </div>
    <label>{kind === 'voice' ? t.audioFile : t.imageFile}
      <input key={kind} type="file" accept={kind === 'voice' ? 'audio/*,.webm' : 'image/jpeg,image/png,image/webp'} disabled={busy}
        onChange={event => {setFile(event.target.files[0]); setResult(null); setError('');}}/>
    </label>
    <button type="button" disabled={!file || busy} className="secondary" onClick={run}>
      {busy ? t.processing : kind === 'voice' ? t.transcribe : t.detect}
    </button>
    {error && <p role="alert" className="error">{t.error}</p>}
    {kind === 'voice' && result && <div className="analysis-result">
      <h3>{t.transcript}</h3>
      <p>{result.text || t.noSpeech}</p>
      {result.text && <button type="button" className="secondary" onClick={() => onTranscript(result.text)}>{t.useText}</button>}
    </div>}
    {kind === 'image' && preview && <div className="evidence-preview">
      <img src={preview} alt={t.imageFile}/>
      {result && <svg viewBox={`0 0 ${result.width} ${result.height}`} aria-label={t.coordinates}>
        {result.detections.map(({box, label}, i) =>
          <rect key={i} x={box[0]} y={box[1]} width={box[2] - box[0]} height={box[3] - box[1]}>
            <title>{t.labels[label] ?? label.replaceAll('_',' ')}</title>
          </rect>
        )}
      </svg>}
    </div>}
    {kind === 'image' && result && <p className="field-hint">
      {result.detections.length
        ? result.detections.map(x => `${t.labels[x.label] ?? x.label.replaceAll('_', ' ')} (${Math.round(x.score * 100)}%)`).join(', ')
        : t.noDamage}
      {' '}{t.evidence}
    </p>}
  </details>;
}

export function ModelEvidence({analysis}) {
 const {t} = useWorkspaceLanguage();

  const fields = analysis.models;
  if (!fields) return <p className="field-hint">{t("This suggestion uses rules. Calibrated confidence is unavailable.")}</p>;
  return <div className="model-evidence">
    <h3><Activity size={15}/>{t("Model evidence")}</h3>
    {Object.entries(fields).map(([task, prediction]) => <div className="model-evidence-row" key={task}>
      <strong>{t(task === 'category' ? 'Category' : 'Severity')} · {t(prediction.label)}</strong>
      <span>{prediction.confidence !== null
        ? t('{confidence}% calibrated on BanglaPSG', {confidence: Math.round(prediction.confidence * 100)})
        : prediction.calibration_cohort?.startsWith('derived')
          ? t("Natural-language confidence unavailable. Calibration was evaluated on derived text.")
          : t("Calibration unavailable for this language.")}</span>
      {!!prediction.features.length && <small>{t("Influential text fragments ·")} {prediction.features.join(', ')}</small>}
      {prediction.policy_override && <small>{t('Suggested category adjusted to {category} by a policy rule.', {category: t(prediction.policy_override)})}</small>}
    </div>)}
    {analysis.low_confidence && <p>{t("Review recommended because confidence is low or unverified for this input.")}</p>}
    {analysis.forecast && <div className="model-evidence-row">
      <strong>{t("External closure-time benchmark ·")} {analysis.forecast.estimated_hours} {t("hours")}</strong>
      <span>{analysis.forecast.lower_hours}–{analysis.forecast.upper_hours} {t("hours, estimated 10th–90th percentiles.")}</span>
      <small>{t("Trained on NYC 311. Applicability to Bangladesh remains unverified.")}</small>
    </div>}
  </div>;
}

export function ClosureBenchmark() {
 const {t} = useWorkspaceLanguage();

  const [category, setCategory] = useState('Road');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function estimate(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const when = new Date(form.get('created_at'));
    if (Number.isNaN(+when)) return;
    const query = new URLSearchParams({ category, occurred_at: when.toISOString() });
    setBusy(true);
    setResult(null);
    setError('');
    try {
      setResult(await request('/research/closure-benchmark?' + query));
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  }

  return <article className="panel">
    <h2>{t("Closure-time research benchmark")}</h2>
    <p className="body-copy">{t("This experiment uses NYC 311 requests. The results do not estimate service times in Bangladesh.")}</p>
    <form onSubmit={estimate}>
      <div className="form-row">
        <label>{t("Category")} <select value={category} onChange={event => setCategory(event.target.value)}>
            {['Road', 'Waste', 'Water', 'Electricity', 'Food'].map(value => <option key={value} value={value}>{t(value)}</option>)}
          </select>
        </label>
        <label>{t("Example submission time")}<input name="created_at" type="datetime-local" required/></label>
      </div>
      <button className="secondary" disabled={busy}>{busy ? t("Calculating…") : t("Run benchmark prediction")}</button>
    </form>
    {error && <p role="alert" className="error">{t(error)}</p>}
    {result && <div className="analysis-result">
      <h3>{result.estimated_hours} {t("hours to closure")}</h3>
      <p>{result.lower_hours}–{result.upper_hours} {t("hours at the estimated 10th and 90th percentiles.")}</p>
    </div>}
  </article>;
}
