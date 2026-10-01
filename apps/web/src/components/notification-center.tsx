"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Bell, CheckCheck, ChevronRight, Filter, Search, ShieldAlert } from "lucide-react";

export type NotificationItem={
  id:string;type:string;category:string;priority:string;action_href?:string|null;title:string;body:string;email_sent_at?:string|null;read_at?:string|null;created_at:string;
};

const labels:Record<string,string>={learning:"Learning",compliance:"Compliance",assessment:"Assessments",credentials:"Credentials",support:"Support",security:"Security",approvals:"Approvals",system:"System"};

export function NotificationCenter({initialItems,timezone="UTC"}:{initialItems:NotificationItem[];timezone?:string}){
  const [items,setItems]=useState(initialItems);
  const [query,setQuery]=useState("");
  const [category,setCategory]=useState("all");
  const [readState,setReadState]=useState("all");
  const [busy,setBusy]=useState(false);

  const categories=useMemo(()=>Array.from(new Set(items.map(item=>item.category))).sort(),[items]);
  const filtered=useMemo(()=>items.filter(item=>{
    const text=(item.title+" "+item.body+" "+item.type+" "+item.category).toLowerCase();
    const queryMatch=!query.trim()||text.includes(query.trim().toLowerCase());
    const categoryMatch=category==="all"||item.category===category;
    const readMatch=readState==="all"||(readState==="unread"&&!item.read_at)||(readState==="read"&&Boolean(item.read_at));
    return queryMatch&&categoryMatch&&readMatch;
  }),[items,query,category,readState]);

  const unread=items.filter(item=>!item.read_at).length;
  const important=items.filter(item=>["high","critical"].includes(item.priority)&&!item.read_at).length;

  async function markRead(id:string){
    const response=await fetch("/api/lms/notifications/"+id+"/read",{method:"POST"});
    if(response.ok)setItems(current=>current.map(item=>item.id===id?{...item,read_at:new Date().toISOString()}:item));
  }
  async function markAll(){
    setBusy(true);
    try{
      const response=await fetch("/api/lms/notifications/read-all",{method:"POST"});
      if(response.ok){const now=new Date().toISOString();setItems(current=>current.map(item=>({...item,read_at:item.read_at||now})))}
    }finally{setBusy(false)}
  }

  return <div className="notification-center">
    <section className="notification-overview">
      <article><Bell size={18}/><span>Unread</span><strong>{unread}</strong><small>Notifications requiring review</small></article>
      <article><ShieldAlert size={18}/><span>High priority</span><strong>{important}</strong><small>Unread high/critical notifications</small></article>
      <article><CheckCheck size={18}/><span>Total</span><strong>{items.length}</strong><small>Recent notifications loaded</small></article>
      <div className="notification-overview-action"><button className="button notification-bulk-action" type="button" onClick={()=>void markAll()} disabled={busy||unread===0}><CheckCheck size={14}/>{busy?"Updating…":"Mark all as read"}</button><Link className="notification-preferences-link" href="/dashboard/settings#notifications">Notification preferences <ChevronRight size={13}/></Link></div>
    </section>

    <section className="notification-toolbar">
      <label><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search notifications"/></label>
      <label><Filter size={14}/><select value={category} onChange={e=>setCategory(e.target.value)}><option value="all">All categories</option>{categories.map(item=><option key={item} value={item}>{labels[item]||item}</option>)}</select></label>
      <label><Filter size={14}/><select value={readState} onChange={e=>setReadState(e.target.value)}><option value="all">All states</option><option value="unread">Unread</option><option value="read">Read</option></select></label>
    </section>

    <section className="notification-list">
      {filtered.length===0?<div className="empty-state"><Bell size={24}/><h2>No notifications match these filters</h2><p>Adjust search or filters to review other notifications.</p></div>:filtered.map(item=><article className={"notification-card "+(!item.read_at?"unread ":"")+"priority-"+item.priority} key={item.id}>
        <div className="notification-card-main">
          <div className="notification-card-top"><span className="notification-category">{labels[item.category]||item.category}</span><span className={"notification-priority "+item.priority}>{item.priority}</span>{!item.read_at&&<span className="notification-new">New</span>}</div>
          <h2>{item.title}</h2><p>{item.body}</p>
          <small>{new Date(item.created_at).toLocaleString(undefined,{timeZone:timezone})}{item.email_sent_at?" · Email sent":""}</small>
        </div>
        <div className="notification-card-actions">
          {item.action_href&&<Link className="button button-secondary" href={item.action_href}>Open <ChevronRight size={14}/></Link>}
          {!item.read_at&&<button className="button button-secondary" type="button" onClick={()=>void markRead(item.id)}>Mark read</button>}
        </div>
      </article>)}
    </section>
  </div>;
}
