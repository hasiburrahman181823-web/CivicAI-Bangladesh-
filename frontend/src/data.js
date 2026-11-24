import {ruleAnalysis} from './api/client';
const now=new Date();
const examples=[
 ['DEMO-1024','Water supply interrupted near the school','No water for three days near the school in Mirpur 10. Families are unable to access drinking water.','Mirpur 10','Water','High','Under review','English',23.8069,90.3687],
 ['DEMO-1023','Exposed electrical wire on the footpath','An exposed wire is hanging over the footpath near a school. Please inspect before anyone is injured.','Dhanmondi 27','Electricity','Critical','In progress','English',23.7515,90.3718],
 ['DEMO-1022','রাস্তার মাঝখানে বড় গর্ত','মোহাম্মদপুরের রাস্তায় বড় গর্ত হয়েছে। কয়েক দিন ধরে যানবাহন চলাচলে সমস্যা হচ্ছে।','Mohammadpur','Road','Medium','Submitted','Bangla',23.766,90.358],
 ['DEMO-1021','Drain blocked beside the market','Garbage has blocked the drain beside the market for several days. Water is collecting on the pavement.','Uttara Sector 7','Waste','Medium','In progress','English',23.868,90.400],
 ['DEMO-1020','Mirpur e pani nai','Mirpur 10 er school er pashe tin din dhore pani nai. Pani supply thik kora dorkar.','Mirpur 10','Water','High','Under review','Banglish',23.8072,90.3689],
 ['DEMO-1019','Streetlight restored near the crossing','The streetlight near the crossing was not working. A reviewer has marked this demonstration case resolved.','Gulshan 2','Electricity','Low','Resolved','English',23.794,90.414],
];
export const demoRecords=examples.map((x,i)=>({id:x[0],title:x[1],text:x[2],area:x[3],category:x[4],priority:x[5],status:x[6],language:x[7],latitude:x[8],longitude:x[9],created_at:new Date(now-i*3600000).toISOString(),occurred_at:new Date(now-i*3600000-7200000).toISOString(),analysis:ruleAnalysis(x[2]),demo:true}));
