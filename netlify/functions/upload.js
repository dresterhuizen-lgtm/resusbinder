const OWNER='dresterhuizen-lgtm', REPO='resusbinder', BRANCH='main';
const headers={ 'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff' };
const respond=(statusCode,obj)=>({statusCode,headers,body:JSON.stringify(obj)});
const gh=async(path,token,method='GET',body)=>{const r=await fetch('https://api.github.com/repos/'+OWNER+'/'+REPO+'/'+path,{method,headers:{Authorization:'Bearer '+token,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const json=await r.json().catch(()=>({}));if(!r.ok)throw Error('GitHub '+r.status+': '+(json.message||'Request failed'));return json};
exports.handler=async(event)=>{
 if(event.httpMethod!=='POST')return respond(405,{error:'POST required'});
 const key=process.env.RESUS_UPLOAD_KEY,token=process.env.RESUS_GITHUB_TOKEN;
 if(!key||!token)return respond(503,{error:'Upload service not configured. Set RESUS_UPLOAD_KEY and RESUS_GITHUB_TOKEN in Netlify environment variables.'});
 const provided=(event.headers.authorization||event.headers.Authorization||'').replace(/^Bearer\s+/i,'');
 const crypto=require('crypto');
 const a=Buffer.from(provided),b=Buffer.from(key);
 if(!a.length||a.length!==b.length||!crypto.timingSafeEqual(a,b))return respond(401,{error:'Invalid upload key'});
 try{
 const data=JSON.parse(event.body||'{}'),title=String(data.title||'').trim(),category=String(data.category||'Studies'),base64=String(data.base64||''),mime=String(data.mime||'');
 if(!title||title.length>180||!['Studies','Resus Binder','CCR'].includes(category))return respond(400,{error:'Valid title and category required'});
 if(!['application/pdf','image/png','image/jpeg'].includes(mime))return respond(400,{error:'PDF, PNG or JPEG only'});
 if(!/^[A-Za-z0-9+/]+={0,2}$/.test(base64))return respond(400,{error:'Invalid file encoding'});
 const buffer=Buffer.from(base64,'base64'),max=5*1024*1024;
 if(!buffer.length||buffer.length>max)return respond(413,{error:'File must be 1 byte to 5 MB'});
 const ext=mime==='application/pdf'?'pdf':mime==='image/png'?'png':'jpg';
 const sig=ext==='pdf'?buffer.subarray(0,5).toString()==='%PDF-':ext==='png'?buffer.subarray(0,8).equals(Buffer.from('89504e470d0a1a0a','hex')):buffer[0]===255&&buffer[1]===216;
 if(!sig)return respond(400,{error:'File signature does not match selected type'});
 const slug=title.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,72)||'document';
 const suffix=crypto.randomBytes(4).toString('hex'),filename=slug+'-'+suffix+'.'+ext,path='assets/'+filename;
 const manifestPath='uploads.json';
 let manifest=[],sha;
 try{const old=await gh('contents/'+manifestPath+'?ref='+BRANCH,token);sha=old.sha;manifest=JSON.parse(Buffer.from(old.content.replace(/\s/g,''),'base64').toString('utf8'));if(!Array.isArray(manifest))throw Error('Invalid uploads manifest')}catch(e){if(!String(e.message).includes('GitHub 404'))throw e}
 // Commit binary first; do not expose GitHub credentials to the browser.
 await gh('contents/'+path,token,'PUT',{message:'Upload '+title,content:base64,branch:BRANCH});
 const item={id:'upload-'+suffix,title,pdf:ext==='pdf'?filename:undefined,file:ext!=='pdf'?filename:undefined,thumb:'',categories:[category==='Studies'?'Other':category],tags:[category],studies:category==='Studies',binder:category==='Resus Binder',ccr:category==='CCR',high_yield:false,width:600,height:800,recent_rank:0,uploaded_at:new Date().toISOString()};
 manifest.unshift(item);
 await gh('contents/'+manifestPath,token,'PUT',{message:'Index uploaded document '+title,content:Buffer.from(JSON.stringify(manifest,null,2)+'\n').toString('base64'),branch:BRANCH,...(sha?{sha}:{})});
 return respond(200,{ok:true,title,path,category,sha256:crypto.createHash('sha256').update(buffer).digest('hex')});
 }catch(e){return respond(500,{error:String(e.message||e)})}
};