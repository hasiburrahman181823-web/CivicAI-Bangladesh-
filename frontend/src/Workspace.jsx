import {useWorkspaceLanguage} from './workspaceLanguage';
import React,{useEffect,useRef,useState} from 'react';
import {LayoutDashboard,FileText,ClipboardList,Copy,Sun,Moon,Search,Bell,ChevronDown,MapPin,ShieldCheck,Globe,Activity,Clock,X,Menu,LogOut,User,MoveUpRight,Droplets,Zap,Trash2,Construction,Heart,Flame,Download,CheckCircle2,Info,Lock,RefreshCw} from 'lucide-react';
import {ResponsiveContainer,AreaChart,Area,XAxis,YAxis,CartesianGrid,Tooltip} from 'recharts';
import {downloadCSV, request} from './api/client';
import {demoRecords} from './data';
import {ModelEvidence} from './components/ModelTools';
import {TicketActivity} from './components/TicketActivity';
import {isMapped, ReportMap} from './components/ReportMap';
import {dateKey, emptyFilters, filterWorkspaceRecords, ReviewAudit, WorkspaceFilters} from './components/WorkspaceRecords';
import './styles.css';
import './workspaceUpdates.css';

const icons={Water:Droplets,Electricity:Zap,Road:Construction,Waste:Trash2,Health:Heart,Food:FileText,Gas:Flame,Safety:ShieldCheck};
const nav=[['Overview',LayoutDashboard],['Complaints',FileText],['Duplicate review',Copy],['Review audit',ClipboardList]];
const statusClass=s=>s.toLowerCase().replaceAll(' ','-');
function Badge({value}){
 const {t} = useWorkspaceLanguage();
return <span className={'badge '+statusClass(value)}>{t(value)}</span>}
export default function Workspace({initialSession,onExit,onLogout,languageControl,preview=false,dark,setDark}){
 const {t,language} = useWorkspaceLanguage();

 const [page,setPage]=useState('Overview'),[mobile,setMobile]=useState(false),[toast,setToast]=useState(''),[query,setQuery]=useState(''),[filter,setFilter]=useState('All statuses'),[records,setRecords]=useState(() => preview ? demoRecords : []),[loading,setLoading]=useState(false),[selected,setSelected]=useState(null),[range,setRange]=useState('Last 7 days');
 const [filters, setFilters] = useState(emptyFilters);
 const [serverRecords, setServerRecords] = useState(null);
 const [reportPage, setReportPage] = useState(0);
 const [reportRefresh, setReportRefresh] = useState(0);
 const reportPageSize = 40;
 const session = initialSession;
 const mode = preview ? 'demo' : 'live';
 const searchParams = new URLSearchParams();
 if (query.trim()) searchParams.set('search', query.trim().slice(0, 120));
 if (filters.area.trim()) searchParams.set('area', filters.area.trim());
 if (filters.start) searchParams.set('after', filters.start + 'T00:00:00+06:00');
 if (filters.end) searchParams.set('before', filters.end + 'T23:59:59.999+06:00');
 if (filter === 'Awaiting human review') searchParams.set('review_only', 'true');
 else if (filter !== 'All statuses') searchParams.set('status', filter);
 const searchQuery = searchParams.toString();
 useEffect(() => { setReportPage(0); }, [searchQuery]);
 useEffect(() => {
   if (preview || page !== 'Complaints') return;
   if (filters.start && filters.end && filters.start > filters.end) {
     setServerRecords([]);
     return;
   }
   const controller = new AbortController();
   setServerRecords(null);
   const params = new URLSearchParams(searchQuery);
   params.set('offset', reportPage * reportPageSize);
   params.set('limit', reportPageSize + 1);
   const timer = window.setTimeout(async () => {
     try {
       setServerRecords(await request('/admin/complaints?' + params.toString(), {signal: controller.signal}));
     } catch {
       if (!controller.signal.aborted) {
         setServerRecords([]);
         setToast('Reports could not be loaded. Use Refresh data to try again.');
       }
     }
   }, 220);
   return () => { controller.abort(); window.clearTimeout(timer); };
 }, [preview, page, reportPage, reportRefresh, searchQuery, filters.start, filters.end]);
 useEffect(()=>{
  if (preview) return;
  sessionStorage.removeItem('civic-session');
  let mounted = true;
  setLoading(true);
  request('/admin/complaints').then(items => {
    if (mounted) setRecords(items);
  }).catch(() => {
    if (mounted) setToast('Reports could not be loaded. Use Refresh data to try again.');
  }).finally(() => {
    if (mounted) setLoading(false);
  });
  return () => { mounted = false; };
 },[preview]);
 useEffect(()=>{if(toast){const id=setTimeout(()=>setToast(''),5000);return()=>clearTimeout(id)}},[toast]);
 const notify=setToast;
 async function connect(){
  setLoading(true);
  try {
    setRecords(await request('/admin/complaints'));
    setReportRefresh(value => value + 1);
    notify('Backend connected. Showing live records.');
  } catch {
    notify('Reports could not be loaded. Use Refresh data to try again.');
  } finally {
    setLoading(false);
  }
 }
 const formatNumber=new Intl.NumberFormat(language==='bn'?'bn-BD':'en-GB');
 function navigate(value){setPage(value);setMobile(false);setQuery('');setFilter('All statuses')}
 async function logout(){
  try { await request('/auth/logout',{method:'POST'}); }
  catch (error) { notify(error.message); return; }
  onLogout();
 }
 const visibleRecords = filterWorkspaceRecords(records, filters);
 const needsReview = report => report.analysis?.requires_review !== false && report.status !== 'Resolved';
 const filtered = visibleRecords.filter(report => {
   const matchesStatus = filter === 'All statuses' || (filter === 'Awaiting human review' ? needsReview(report) : report.status === filter);
   const text = [report.title, report.id, report.area, report.category, t(report.category)].join(' ').toLowerCase();
   return matchesStatus && text.includes(query.trim().toLowerCase());
 });
 const active=visibleRecords.filter(r=>r.status!=='Resolved'),critical=visibleRecords.filter(r=>['High','Critical'].includes(r.priority)&&r.status!=='Resolved'),review=records.filter(needsReview),resolved=visibleRecords.filter(r=>r.status==='Resolved');
 const period=range==='Last 30 days'?30:7;
 const days=Array.from({length:period},(_,i)=>{
   const date=new Date(Date.now()-(period-1-i)*86400000);
   const day=dateKey(date.toISOString());
   const items=visibleRecords.filter(r=>dateKey(r.created_at)===day);
   return {name:date.toLocaleDateString(language==='bn'?'bn-BD':'en-GB',{day:'numeric',month:'short',timeZone:'Asia/Dhaka'}),submitted:items.length,resolved:items.filter(r=>r.status==='Resolved').length};
 });
 async function exportCSV() {
   if (!preview) {
     try { await downloadCSV('/admin/complaints/export?' + searchQuery); }
     catch (error) { notify(error.message); }
     return;
   }
   exportDemoCSV();
 }
 function exportDemoCSV(){const rows=[['ID','Title','Area','Incident time','Category','Priority','Status','Language'],...filtered.map(r=>[r.id,r.title,r.area,r.occurred_at,r.category,r.priority,r.status,r.language])];const safe=v=>{const s=String(v);return '"'+(/^[\s\u200b-\u200f]*[=+@\-]|^[\t\r\n]/.test(s)?"'"+s:s).replaceAll('"','""')+'"'};const blob=new Blob(['\uFEFF'+rows.map(r=>r.map(safe).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='civicai-complaints.csv';a.click();URL.revokeObjectURL(a.href)}
 return <div className="app-shell">
  {mobile&&<div className="sidebar-scrim" onClick={()=>setMobile(false)}/>}
  <aside className={'sidebar '+(mobile?'open':'')}>
   <a className="brand" href="#dashboard"><img src="/favicon.svg" alt="" width="39" height="39"/><span>{t("CivicAI")}<span className="brand-country">{t("BANGLADESH")}</span></span></a>
   <div className="workspace-label">{t("Administrator")}</div>
   <nav>{nav.map(([name,Icon])=><button key={name} className={page===name?'nav-item active':'nav-item'} onClick={()=>navigate(name)}><Icon size={19}/><span>{t(name)}</span>{name==='Complaints'&&<b>{formatNumber.format(records.length)}</b>}{name==='Duplicate review'&&<span className="nav-dot"/>}</button>)}</nav>
   <div className="sidebar-bottom"><ShieldCheck size={16}/><span>{t("Human-led. AI-assisted.")}</span></div>
   <button className="profile" onClick={()=>preview ? onExit() : logout()}><span className="avatar">{session?'HR':'C'}</span><span><strong>{session?session.email.split('@')[0]:t("Citizen workspace")}</strong><small>{session?t(session.role==='admin'?'Administrator':'Citizen')+t(' · Sign out'):t("Explore the demo")}</small></span>{session?<LogOut size={16}/>:<ChevronDown size={16}/>}</button>
  </aside>
  <div className="main-shell">
   <header className="topbar"><div className="breadcrumbs"><button className="icon-button mobile-menu" aria-label={t("Open navigation")} onClick={()=>setMobile(true)}><Menu size={21}/></button><span>{t("Workspace")}</span><span className="slash">/</span><strong>{t(page)}</strong></div><div className="top-actions">{languageControl}<span className="bangladesh"><span/>{t("Bangladesh")}</span><button className="icon-button theme-toggle" onClick={()=>setDark(!dark)} aria-label={t(dark?'Switch to day mode':'Switch to night mode')}>{dark?<Sun size={19}/>:<Moon size={19}/>}</button><button className="icon-button notification" aria-label={t("View review notifications")} onClick={()=>{setFilters(emptyFilters);navigate('Complaints');setFilter('Awaiting human review');notify({message:'{count} reports await human review',values:{count:formatNumber.format(review.length)}})}}><Bell size={19}/>{review.length > 0 && <i/>}</button><div className="top-divider"/><button className="sign-in" onClick={()=>preview ? onExit() : logout()}>{preview?t('Back to citizen portal'):session?t('Sign out'):t('Sign in')} <User size={16}/></button></div></header>
   <main>
    <div className="page-heading">
      <div>
        <h1>{t(page)}</h1>
        <p>{t({
          Overview: 'Monitor incoming complaints and the review queue.',
          Complaints: 'A clear view of citizen reports, suggested priorities and human decisions.',
          'Duplicate review': 'Review context before connecting reports about the same incident.',
          'Review audit': 'Review history for administrator decisions and linked complaints.',
        }[page])}</p>
      </div>
    </div>
    <div className="demo-banner"><span><Info size={16}/><strong>{mode==='demo'?t("Demo workspace"):t("Connected backend")}</strong><span>{mode==='demo'?t("Illustrative reports · stored in this browser · no official service connection"):t("Private records · human confirmation required")}</span></span><button onClick={connect} disabled={loading||preview}>{loading?t("Connecting…"):mode==='demo'?t("Connect backend"):t("Refresh data")}<RefreshCw size={13}/></button></div>
    {['Overview', 'Complaints', 'Duplicate review'].includes(page)
      && <WorkspaceFilters filters={filters} setFilters={setFilters}/>}
    {page==='Overview'&&<>
     <section className="stats-grid">{[[FileText,'Total complaints',visibleRecords.length,'Voices in this workspace','total'],[Activity,'Active incidents',active.length,'Open and being worked on','active'],[ShieldCheck,'Needs attention',critical.length,'High & critical suggestions','attention'],[CheckCircle2,'Resolved',resolved.length,'Marked resolved by a reviewer','resolved']].map(([Icon,label,value,caption,cls])=><article className={'stat-card '+cls} key={label}><div className="stat-top"><span>{t(label)}</span><Icon size={18}/></div><strong>{formatNumber.format(value)}</strong><div className="stat-bottom"><span className="mini-line"/>{t(caption)}</div></article>)}</section>
     <section className="overview-grid"><article className="panel activity-panel"><div className="panel-title"><div><h2>{t("Community pulse")}</h2><p>{t("A little perspective on everyday concerns.")}</p></div><select aria-label={t("Chart date range")} value={range} onChange={e=>setRange(e.target.value)}><option value="Last 7 days">{t("Last 7 days")}</option><option value="Last 30 days">{t("Last 30 days")}</option></select></div><div className="chart-legend"><span><i/>{t("Submitted")}</span><span><i className="muted"/>{t("Resolved")}</span></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={days} margin={{top:15,right:12,left:-30,bottom:0}}><defs><linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#087e80" stopOpacity={.22}/><stop offset="100%" stopColor="#087e80" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="4 5" vertical={false}/><XAxis dataKey="name" axisLine={false} tickLine={false} minTickGap={28}/><YAxis allowDecimals={false} axisLine={false} tickLine={false}/><Tooltip contentStyle={{background:'var(--surface)',border:'1px solid var(--line)',borderRadius:12}}/><Area type="monotone" dataKey="submitted" name={t('Submitted')} stroke="#087e80" strokeWidth={2.5} fill="url(#chartFill)"/><Area type="monotone" dataKey="resolved" name={t('Resolved')} stroke="#84b5b6" strokeWidth={2} strokeDasharray="5 4" fill="transparent"/></AreaChart></ResponsiveContainer></div><div className="chart-footer"><span><span className="live-dot"/>{t(mode==='demo'?'Based on {count} demo reports':'Based on {count} live reports',{count:formatNumber.format(visibleRecords.length)})}</span><button className="text-button" onClick={()=>navigate('Complaints')}>{t("View all complaints")} <MoveUpRight size={14}/></button></div></article>
     <article className="panel map-panel"><div className="panel-title"><div><h2>{t("Voices on the map")}</h2><p>{t("Local concerns. Shared responsibility.")}</p></div><span className="subtle-label">{t("Bangladesh")}</span></div><ReportMap records={visibleRecords} onSelect={setSelected}/><div className="map-footer"><span><MapPin size={14}/>{t('{count} located reports',{count:formatNumber.format(visibleRecords.filter(isMapped).length)})}</span></div></article></section>
     <div className="section-title"><div><h2>{t("Latest community reports")} <span className="count">{formatNumber.format(visibleRecords.length)}</span></h2><p>{t("Every report is a step toward a solution.")}</p></div><button className="text-button" onClick={()=>navigate('Complaints')}>{t("View all complaints")} <MoveUpRight size={15}/></button></div>
     <ComplaintTable records={visibleRecords.slice(0,4)} onSelect={setSelected}/>
    </>}
    {page==='Complaints'&&<><div className="toolbar"><div className="search-box"><Search size={18}/><input placeholder={t("Search reports, locations or IDs")} value={query} onChange={e=>setQuery(e.target.value)}/></div><select aria-label={t("Filter status")} value={filter} onChange={e=>setFilter(e.target.value)}>{['All statuses','Awaiting human review','Submitted','Under review','In progress','Resolved'].map(s=><option key={s} value={s}>{t(s)}</option>)}</select>{(mode==='demo'||session?.role==='admin')&&<button className="secondary" onClick={exportCSV}><Download size={16}/>{t("Export")}</button>}</div>{!preview && serverRecords === null
      ? <p role="status">{t('Loading reports…')}</p>
      : <ComplaintTable records={preview ? filtered : serverRecords.slice(0, reportPageSize)} onSelect={setSelected}/>}
    {!preview && (reportPage > 0 || serverRecords?.length > reportPageSize) && <div className="toolbar" aria-label={t('Complaint pages')}>
      <button type="button" className="secondary" disabled={!reportPage} onClick={() => setReportPage(value => value - 1)}>{t('Previous page')}</button>
      <span>{formatNumber.format(reportPage + 1)}</span>
      <button type="button" className="secondary" disabled={!serverRecords || serverRecords.length <= reportPageSize}
        onClick={() => setReportPage(value => value + 1)}>{t('Next page')}</button>
    </div>}</>}
    {page==='Duplicate review'&&<DuplicatePage key={JSON.stringify(filters)} records={visibleRecords} allRecords={records} mode={mode} onSelect={setSelected}/>}
    {page==='Review audit'&&<ReviewAudit preview={preview}/>}
    <footer><span>© {new Date().getFullYear()} {t("CivicAI Bangladesh")}</span><span>{t("Built for people. Guided by evidence.")}<span className="footer-dot">·</span><ShieldCheck size={13}/>{t("Decision support only")}</span></footer>
   </main>
  </div>
  {toast&&<div className="toast" role="status"><Info size={18}/>{typeof toast==='string'?t(toast):t(toast.message,toast.values)}<button aria-label={t("Dismiss notification")} onClick={()=>setToast('')}><X size={15}/></button></div>}
  {selected&&<Detail key={selected.id} item={selected} mode={mode} session={session} onClose={()=>setSelected(null)} notify={notify} onSave={item=>{setRecords(prev=>prev.map(r=>r.id===item.id?item:r));setReportRefresh(value=>value+1);setSelected(item)}}/>}
 </div>
}

function WorkspaceDialog({label, onClose, detail = false, children}) {
 const dialog = useRef(null);
 useEffect(() => { dialog.current?.showModal(); }, []);
 return <dialog ref={dialog} className="workspace-dialog" aria-label={label} onCancel={event=>{
   event.preventDefault();
   onClose();
 }}>
   <div className={detail ? 'modal-overlay detail-overlay' : 'modal-overlay'}
     onMouseDown={event=>{if(event.target === event.currentTarget) onClose();}}>
     {children}
   </div>
 </dialog>;
}

function ComplaintTable({records,onSelect}){
 const {t} = useWorkspaceLanguage();
return <div className="table-wrap"><table><thead><tr><th>{t("COMPLAINT")}</th><th>{t("CATEGORY")}</th><th>{t("LOCATION")}</th><th>{t("PRIORITY")}</th><th>{t("STATUS")}</th><th aria-label={t("View details")}/></tr></thead><tbody>{records.map(r=>{const Icon=icons[r.category]||FileText;return <tr key={r.id} onClick={()=>onSelect(r)}><td><button className="report-title" onClick={e=>{e.stopPropagation();onSelect(r)}}><span className="category-icon"><Icon size={18}/></span><span><strong>{r.title}</strong><small>{r.id.slice(0,13)} <span>·</span> {t(r.language)}{r.demo?t(" · Demo"):''}</small></span></button></td><td>{t(r.category)}</td><td><span className="location-cell"><MapPin size={13}/>{r.area}</span></td><td><Badge value={r.priority}/></td><td><Badge value={r.status}/></td><td><MoveUpRight size={16}/></td></tr>})}</tbody></table>{!records.length&&<div className="empty-state"><FileText size={30}/><h3>{t("No reports here yet")}</h3><p>{t("Submit a complaint or adjust your search to get started.")}</p></div>}</div>}
function DuplicatePage({records,allRecords,mode,onSelect}){
 const {t} = useWorkspaceLanguage();
const [pairs,setPairs]=useState([]),[busy,setBusy]=useState(false),[error,setError]=useState('');async function scan(){setBusy(true);setError('');try{if(mode==='demo'){const first=records.find(r=>r.id==='DEMO-1024'),second=records.find(r=>r.id==='DEMO-1020');setPairs(first&&second?[{first,second,note:'Illustrative pair: same area, different languages. This is a demonstration case, not a model prediction.'}]:[])}else{const results=[];for(const r of records.slice(0,40)){const candidates=await request('/admin/duplicates/'+r.id);for(const c of candidates){const candidate=allRecords.find(x=>x.id===c.id);if(candidate&&!results.some(x=>x.first.id===c.id&&x.second.id===r.id))results.push({first:r,second:candidate,note:'{method} · similarity {score} · {distance} m · {hours} hours apart',summary:c})}}setPairs(results)}}catch(e){setError(e.message)}finally{setBusy(false)}}return <><div className="trust-strip"><Copy size={25}/><div><strong>{t("Related reports are not automatically the same incident.")}</strong><p>{t("Check location, incident time and evidence. Only an administrator can confirm a link.")}</p></div><button onClick={scan} disabled={busy}>{busy?t("Checking…"):t("Find candidates")}<Search size={16}/></button></div>{error&&<p className="error">{t(error)}</p>}{!pairs.length?<div className="panel empty-state"><Copy size={34}/><h2>{t("Connect the dots, carefully.")}</h2><p>{t("Find candidate pairs to begin a human-led incident review.")}</p><button className="primary" onClick={scan} disabled={busy}>{busy?t("Scanning…"):t("Find candidate reports")}</button></div>:pairs.map((pair,i)=><article className="panel duplicate-pair" key={i}><div className="panel-title"><h2>{t("Possible shared incident")}</h2><Badge value="Review required"/></div><p className="body-copy">{t(pair.note,pair.summary?{method:t(pair.summary.method),score:pair.summary.similarity,distance:pair.summary.distance_m??t('Unknown'),hours:pair.summary.hours_apart}:undefined)}</p><div className="pair-grid">{[pair.first,pair.second].map(r=><button key={r.id} onClick={()=>onSelect(r)}><span className="subtle-label">{t(r.language)} · {r.area}</span><h3>{r.title}</h3><p>{r.text}</p><span className="text-button">{t("Review report")} <MoveUpRight size={14}/></span></button>)}</div></article>)}</>}
function Detail({item,mode,session,onClose,onSave,notify}){
 const {t,language} = useWorkspaceLanguage();
const [status,setStatus]=useState(item.status),[priority,setPriority]=useState(item.priority),[note,setNote]=useState(''),[duplicate,setDuplicate]=useState(item.duplicate_of||''),[busy,setBusy]=useState(false);const allowed=mode==='demo'||session?.role==='admin';async function save(e){e.preventDefault();setBusy(true);try{const data={status,priority,note,duplicate_of:duplicate||null};if(mode==='demo'&&duplicate){throw Error('Demo linking is disabled. Use a connected backend for validated incident links.')}const result=mode==='demo'?{...item,...data,analysis:{...item.analysis,requires_review:false,review_note:note}}:await request('/admin/complaints/'+item.id,{method:'PATCH',body:JSON.stringify(data)});onSave(result);notify(mode==='demo'?'Demo review saved in this browser':'Review saved with an audit record')}catch(e){notify(e.message)}finally{setBusy(false)}}return <WorkspaceDialog label={t("Complaint details")} onClose={onClose} detail><section className="detail-drawer"><div className="drawer-header"><span className="eyebrow">{item.demo?t("DEMONSTRATION REPORT"):t("COMPLAINT DETAILS")}</span><button className="icon-button" aria-label={t("Close details")} onClick={onClose}><X size={22}/></button></div><div className="drawer-body"><small className="muted-text">{item.id}</small><h2>{item.title}</h2><div className="detail-badges"><Badge value={item.priority}/><Badge value={item.status}/></div><p className="detail-text">{item.text}</p>
{mode === "live" && <TicketActivity admin id={item.id} language={language}/>}
<div className="detail-meta"><span><MapPin size={16}/>{item.area}</span><span><Globe size={16}/>{t(item.language)}</span><span><Clock size={16}/>{new Date(item.occurred_at).toLocaleString(language==='bn'?'bn-BD':'en-GB')}</span></div><div className="analysis-result"><h3>{t("Why this priority was suggested")}</h3>{item.analysis?.breakdown?.map(b=><div className="breakdown-row" key={b.label.startsWith('Trained severity: ')?t('Trained severity: {severity}',{severity:t(b.label.slice(18))}):t(b.label)}><span>{b.label.startsWith('Trained severity: ')?t('Trained severity: {severity}',{severity:t(b.label.slice(18))}):t(b.label)}{b.keywords?.length>0&&<small>{b.keywords.join(', ')}</small>}</span><strong>+{b.points}</strong></div>)}<p className="field-hint">{t("Priority score")} {item.score}{t("/100 · Human confirmation required")}</p><ModelEvidence analysis={item.analysis || {}}/></div>{item.analysis?.review_note&&<div className="review-note"><ShieldCheck size={18}/><div><strong>{t("Reviewer note")}</strong><p>{item.analysis.review_note}</p></div></div>}{allowed?<form onSubmit={save} className="review-form"><h3>{mode==='demo'?t("Try a demo review"):t("Administrator review")}</h3><div className="form-row"><label>{t("Status")}<select value={status} onChange={e=>setStatus(e.target.value)}>{['Submitted','Under review','In progress','Resolved'].map(x=><option key={x} value={x}>{t(x)}</option>)}</select></label><label>{t("Confirmed priority")}<select value={priority} onChange={e=>setPriority(e.target.value)}>{['Low','Medium','High','Critical'].map(x=><option key={x} value={x}>{t(x)}</option>)}</select></label></div>{mode==='live'&&<label>{t("Duplicate of (optional original report ID)")}<input value={duplicate} onChange={e=>setDuplicate(e.target.value)}/></label>}<label>{t("Review reason")}<textarea value={note} onChange={e=>setNote(e.target.value)} minLength={5} maxLength={500} rows={3} required placeholder={t("Explain your decision and any incident link.")}/></label><button className="primary full-width" disabled={busy}><ShieldCheck size={17}/>{busy?t("Saving…"):t("Confirm review")}</button></form>:<div className="login-note"><Lock size={18}/>{t("Administrator sign-in is required to review this report.")}</div>}</div></section></WorkspaceDialog>}

