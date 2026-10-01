"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, CircleAlert, FlaskConical, Save, ShieldCheck, WifiOff } from "lucide-react";

type Integration={id:string;provider:string;status:string;config:Record<string,unknown>;last_checked_at?:string|null;last_check_status?:string|null;last_check_message?:string|null};
type Field={key:string;label:string;type:"text"|"url"|"number"|"password-env"|"boolean";help?:string;placeholder?:string};

const labels:Record<string,string>={hris:"HRIS",oidc:"OpenID Connect",saml:"SAML 2.0",email:"Email",calendar:"Calendar",lti:"LTI",xapi:"xAPI",scorm:"SCORM",cmi5:"cmi5"};

function fields(provider:string):Field[]{
  if(provider==="oidc"||provider==="lti")return[
    {key:"issuer",label:"Issuer",type:"url",help:"Use the identity provider issuer URL.",placeholder:"https://id.example.com/"},
    {key:"discovery_url",label:"Discovery URL",type:"url",help:"Optional when the issuer exposes standard discovery.",placeholder:"https://id.example.com/.well-known/openid-configuration"},
    {key:"client_id",label:"Client ID",type:"text",placeholder:"kalam-enterprise"},
    {key:"client_secret_env",label:"Client secret environment variable",type:"password-env",help:"Store the secret in deployment configuration, never in Kalam.",placeholder:"KALAM_OIDC_CLIENT_SECRET"},
    {key:"login_enabled",label:"Enable enterprise sign-in",type:"boolean",help:"Enables the provider as a sign-in path after the connection check passes."},
  ];
  if(provider==="saml")return[
    {key:"metadata_url",label:"Metadata URL",type:"url",placeholder:"https://id.example.com/metadata.xml"},
    {key:"entity_id",label:"Service provider entity ID",type:"text",placeholder:"https://kalam.example.com/saml"},
    {key:"login_enabled",label:"Enable enterprise sign-in",type:"boolean"},
  ];
  if(provider==="email")return[
    {key:"host",label:"SMTP host",type:"text",placeholder:"smtp.example.com"},
    {key:"port",label:"SMTP port",type:"number",placeholder:"587"},
    {key:"username",label:"SMTP username",type:"text",placeholder:"noreply@example.com"},
    {key:"password_env",label:"SMTP password environment variable",type:"password-env",placeholder:"KALAM_SMTP_PASSWORD"},
    {key:"starttls",label:"Use STARTTLS",type:"boolean"},
    {key:"ssl",label:"Use implicit TLS",type:"boolean"},
  ];
  if(provider==="xapi")return[
    {key:"endpoint",label:"xAPI endpoint",type:"url",placeholder:"https://lrs.example.com/xapi/"},
    {key:"username",label:"xAPI username",type:"text"},
    {key:"password_env",label:"xAPI password environment variable",type:"password-env",placeholder:"KALAM_XAPI_PASSWORD"},
    {key:"token_env",label:"Bearer token environment variable",type:"password-env",placeholder:"KALAM_XAPI_TOKEN"},
  ];
  if(provider==="scorm"||provider==="cmi5")return[
    {key:"manifest_url",label:provider==="scorm"?"SCORM manifest URL":"cmi5 course structure URL",type:"url",placeholder:"https://content.example.com/manifest.xml"},
  ];
  return[
    {key:"health_url",label:"Health endpoint",type:"url",help:"Kalam performs a bounded HTTPS health check before marking the provider connected.",placeholder:"https://service.example.com/health"},
    {key:"token_env",label:"Bearer token environment variable",type:"password-env",placeholder:"KALAM_INTEGRATION_TOKEN"},
    {key:"timeout_seconds",label:"Connection timeout (seconds)",type:"number",placeholder:"10"},
  ];
}

export function IntegrationConsole({ initialRows }: { initialRows: Integration[] }) {
  const [rows,setRows]=useState(initialRows);
  const [provider,setProvider]=useState(initialRows[0]?.provider || "hris");
  const [config,setConfig]=useState<Record<string,unknown>>(initialRows.find(x=>x.provider===provider)?.config || {});
  const [status,setStatus]=useState(initialRows.find(x=>x.provider===provider)?.status || "configured");
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const [testResult,setTestResult]=useState<{ok?:boolean;message?:string;latency_ms?:number}|null>(null);

  const selected=rows.find(x=>x.provider===provider);
  const providerFields=useMemo(()=>fields(provider),[provider]);

  function selectProvider(value:string){
    const row=rows.find(x=>x.provider===value);
    setProvider(value); setConfig(row?.config || {}); setStatus(row?.status || "configured"); setTestResult(null); setMessage(""); setError("");
  }

  function setValue(key:string,value:string|boolean|number){setConfig(current=>({...current,[key]:value}));setMessage("");setError("");setTestResult(null);}

  async function request<T>(url:string,init:RequestInit={}){
    const response=await fetch(url,{...init,headers:{"Content-Type":"application/json",...(init.headers||{})}});
    const data=await response.json().catch(()=>({} as T));
    if(!response.ok)throw new Error(typeof data==="object"&&data&&"detail" in data?String((data as {detail?:unknown}).detail):"The integration action could not be completed.");
    return data as T;
  }

  async function save(){
    setBusy(true);setMessage("");setError("");setTestResult(null);
    try{
      const data=await request<Integration>("/api/lms/integrations/"+provider,{method:"PUT",body:JSON.stringify({provider,status,config})});
      setRows(current=>[...current.filter(item=>item.provider!==provider),data]);setMessage("Configuration saved. Run a connection test before treating it as healthy.");
    }catch(e){setError(e instanceof Error?e.message:"Unable to save integration.");}finally{setBusy(false);}
  }

  async function test(){
    setBusy(true);setMessage("");setError("");setTestResult(null);
    try{
      const data=await request<{ok:boolean;message:string;latency_ms:number}>("/api/lms/integrations/"+provider+"/test",{method:"POST"});
      setTestResult(data);setMessage("Connection verified. Registry evidence has been updated.");
      setRows(current=>current.map(item=>item.provider===provider?{...item,status:"connected",last_check_status:"passed",last_check_message:data.message}:item));
    }catch(e){setError(e instanceof Error?e.message:"Connection test failed.");setTestResult({ok:false,message:e instanceof Error?e.message:"Connection test failed."});}
    finally{setBusy(false);}
  }

  return <div className="integration-console">
    <div className="integration-console-toolbar">
      <div><span className="eyebrow">Controlled configuration</span><h3>Provider connection</h3><p>Configure only the fields required by the selected integration. Secrets remain deployment-managed through environment references.</p></div>
      <div className="integration-console-status">{selected?.last_check_status==="passed"?<><CheckCircle2 size={15}/> Verified</>:selected?.last_check_status==="failed"?<><CircleAlert size={15}/> Needs attention</>:<><WifiOff size={15}/> Not tested</>}</div>
    </div>
    <div className="integration-console-grid">
      <div className="integration-provider-list" role="listbox" aria-label="Integration provider">
        {Object.keys(labels).map(key=>{const row=rows.find(item=>item.provider===key);return <button type="button" className={provider===key?"integration-provider selected":"integration-provider"} key={key} onClick={()=>selectProvider(key)}><span><strong>{labels[key]}</strong><small>{row?.last_check_status==="passed"?"Connection verified":row?.status||"Not configured"}</small></span>{row?.last_check_status==="passed"?<CheckCircle2 size={15}/>:<ShieldCheck size={15}/>}</button>})}
      </div>
      <div className="integration-form-panel">
        <div className="integration-form-heading"><div><span className="eyebrow">{labels[provider]}</span><h4>{provider==="email"?"Transactional delivery":provider==="hris"?"Workforce data":"Enterprise integration"}</h4></div><select value={status} onChange={e=>setStatus(e.target.value)} aria-label="Connection state"><option value="configured">Configured</option><option value="disabled">Disabled</option></select></div>
        <div className="form-grid integration-fields">
          {providerFields.map(field=>field.type==="boolean"?<label className="integration-toggle" key={field.key}><input type="checkbox" checked={Boolean(config[field.key])} onChange={e=>setValue(field.key,e.target.checked)}/><span><strong>{field.label}</strong>{field.help?<small>{field.help}</small>:null}</span></label>:<label className="form-field" key={field.key}><span>{field.label}</span><input type={field.type==="url"?"url":"text"} inputMode={field.type==="number"?"numeric":undefined} value={String(config[field.key]??"")} placeholder={field.placeholder} onChange={e=>setValue(field.key,field.type==="number"?Number(e.target.value):e.target.value)}/>{field.help?<small>{field.help}</small>:null}</label>)}
        </div>
        {error?<div className="form-error" role="alert">{error}</div>:null}
        {message?<div className="form-success" role="status"><CheckCircle2 size={14}/>{message}</div>:null}
        {testResult?<div className={testResult.ok?"integration-test-result passed":"integration-test-result failed"}><FlaskConical size={15}/><div><strong>{testResult.ok?"Connection test passed":"Connection test failed"}</strong><p>{testResult.message}{testResult.latency_ms!=null?" · "+testResult.latency_ms+" ms":""}</p></div></div>:null}
        <div className="form-actions integration-actions"><button className="button button-secondary" type="button" onClick={()=>void save()} disabled={busy}><Save size={15}/> Save configuration</button><button className="button button-primary" type="button" onClick={()=>void test()} disabled={busy||!selected}><FlaskConical size={15}/> Test connection</button></div>
      </div>
    </div>
  </div>;
}
