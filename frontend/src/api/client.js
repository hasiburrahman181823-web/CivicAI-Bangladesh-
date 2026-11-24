export const API = import.meta.env.VITE_API_URL || '';
export async function request(path, options={}) {
  const response = await fetch(API + '/api' + path, {
    ...options, credentials:'include',
    headers:{...(options.body instanceof FormData ? {} : {'Content-Type':'application/json'}), ...options.headers}
  });
  let result;
  try { result = await response.json(); }
  catch { throw Object.assign(new Error('The server could not complete this request.'), {status: response.status}); }
  if (!response.ok) {
    const detail = typeof result?.detail === 'string' ? result.detail : 'Please check all required fields and the incident time.';
    throw Object.assign(new Error(detail), {status: response.status});
  }
  return result;
}

export async function downloadCSV(path) {
  const response = await fetch(API + '/api' + path, {credentials: 'include'});
  if (!response.ok) {
    const result = await response.json();
    throw new Error(result.detail || 'The CSV export could not be completed.');
  }
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = 'civicai-complaints.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function ruleAnalysis(text) {
  const lower=text.toLowerCase();
  const groups={Water:['water','পানি','pani','pipe','পাইপ'],Electricity:['electric','বিদ্যুৎ','current','wire'],Road:['road','রাস্তা','rasta','pothole','গর্ত'],Waste:['waste','garbage','বর্জ্য','ময়লা','moyla','drain'],Health:['hospital','হাসপাতাল','স্বাস্থ্য','clinic'],Gas:['gas','গ্যাস'],Safety:['crime','fire','আগুন','চুরি','accident']};
  const ranked=Object.entries(groups).map(([category,words])=>({category,words:words.filter(w=>lower.includes(w))})).sort((a,b)=>b.words.length-a.words.length);
  const breakdown=[{label:'Base review score',points:20,keywords:[]}];
  for(const [label,words,points] of [['Immediate safety cue',['fire','আগুন','exposed wire','gas leak','গ্যাস লিক','injured'],45],['Essential service disruption',['no water','পানি নেই','pani nai','power outage','বিদ্যুৎ নেই'],20],['Sensitive facility mentioned',['school','hospital','স্কুল','হাসপাতাল'],10],['Extended disruption mentioned',['days','দিন','din dhore','week'],10]]){
    const keywords=words.filter(w=>lower.includes(w)); if(keywords.length)breakdown.push({label,points,keywords});
  }
  const score=Math.min(100,breakdown.reduce((s,x)=>s+x.points,0));
  return {category:ranked[0].words.length?ranked[0].category:'Other',keywords:ranked[0].words,score,priority:score>=75?'Critical':score>=55?'High':score>=35?'Medium':'Low',breakdown,confidence:null,requires_review:true,duplicates:[],method:'Transparent keyword and policy rules; not a trained model'};
}
