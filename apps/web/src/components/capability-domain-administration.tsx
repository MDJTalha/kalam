"use client";

import { FormEvent, useState } from "react";
import { Link2, Plus, ShieldCheck, Target } from "lucide-react";
import { Notice, SectionCard } from "./ui";

type Objective = { id:string; objective:string; priority:number; status:string };
type Capability = { id:string; name:string; code:string };
type Competency = { id:string; name:string; code:string; levels?:Array<{level:number;definition:string;behavioral_indicators?:string[]}> };
type Role = { id:string; name:string };
type Skill = { id:string; name:string };
type Level = { level:number; name:string; definition:string };

async function request(path:string, options?:RequestInit) {
  const response = await fetch("/api/lms/capability-domain"+path, options);
  const data = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(typeof data.detail==="string" ? data.detail : "The request could not be completed.");
  return data;
}

export function CapabilityDomainAdministration({
  objectives, capabilities, competencies, roles, skills, levels,
}:{
  objectives:Objective[]; capabilities:Capability[]; competencies:Competency[]; roles:Role[]; skills:Skill[]; levels:Level[];
}) {
  const [objectiveItems,setObjectiveItems]=useState(objectives);
  const [competencyItems,setCompetencyItems]=useState(competencies);
  const [objective,setObjective]=useState("");
  const [objectiveDescription,setObjectiveDescription]=useState("");
  const [category,setCategory]=useState("");
  const [priority,setPriority]=useState("3");
  const [competencyName,setCompetencyName]=useState("");
  const [competencyCode,setCompetencyCode]=useState("");
  const [competencyDefinition,setCompetencyDefinition]=useState("");
  const [competencyType,setCompetencyType]=useState("behavioral");
  const [selectedCompetencyId,setSelectedCompetencyId]=useState(competencies[0]?.id||"");
  const [competencyLevels,setCompetencyLevels]=useState<Record<number,{definition:string;behavioral_indicators:string}>>(
    Object.fromEntries([1,2,3,4,5].map(level=>{
      const existing=competencies[0]?.levels?.find(x=>x.level===level);
      return [level,{definition:existing?.definition||"",behavioral_indicators:(existing?.behavioral_indicators||[]).join(", ")}];
    }))
  );
  const [requirementCriticality,setRequirementCriticality]=useState("medium");
  const [requirementWeight,setRequirementWeight]=useState("1");
  const [objectiveId,setObjectiveId]=useState(objectives[0]?.id||"");
  const [capabilityId,setCapabilityId]=useState(capabilities[0]?.id||"");
  const [requiredLevel,setRequiredLevel]=useState("3");
  const [capabilityMapId,setCapabilityMapId]=useState(capabilities[0]?.id||"");
  const [competencyMapId,setCompetencyMapId]=useState(competencies[0]?.id||"");
  const [roleId,setRoleId]=useState(roles[0]?.id||"");
  const [targetType,setTargetType]=useState("capability");
  const [targetId,setTargetId]=useState(capabilities[0]?.id||"");
  const [busy,setBusy]=useState(false);
  const [feedback,setFeedback]=useState<{kind:"success"|"error";text:string}|null>(null);

  async function run(action:()=>Promise<void>, message:string){
    setBusy(true); setFeedback(null);
    try { await action(); setFeedback({kind:"success",text:message}); }
    catch(e){ setFeedback({kind:"error",text:e instanceof Error?e.message:"Request failed"}); }
    finally { setBusy(false); }
  }

  async function createObjective(e:FormEvent){
    e.preventDefault();
    await run(async()=>{
      const data=await request("/objectives",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
        objective:objective.trim(),description:objectiveDescription.trim()||null,priority:Number(priority),strategic_category:category.trim()||null
      })});
      setObjectiveItems(items=>[...items,data]);
      setObjectiveId(data.id); setObjective(""); setObjectiveDescription(""); setCategory("");
    },"Strategic objective created.");
  }

  async function createCompetency(e:FormEvent){
    e.preventDefault();
    await run(async()=>{
      const data=await request("/competencies",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
        code:competencyCode.trim(),name:competencyName.trim(),definition:competencyDefinition.trim(),type:competencyType
      })});
      setCompetencyItems(items=>[...items,data]);
      setCompetencyMapId(data.id);
      setSelectedCompetencyId(data.id); setCompetencyName(""); setCompetencyCode(""); setCompetencyDefinition("");
    },"Competency created. Add its five governed level definitions next.");
  }

  async function saveCompetencyLevels(e:FormEvent){
    e.preventDefault();
    await run(async()=>{
      await request("/competencies/"+selectedCompetencyId+"/levels",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(
        [1,2,3,4,5].map(level=>({level,definition:competencyLevels[level].definition.trim(),behavioral_indicators:competencyLevels[level].behavioral_indicators.split(",").map(x=>x.trim()).filter(Boolean)}))
      )});
    },"Five governed competency levels saved.");
  }

  async function mapObjective(e:FormEvent){
    e.preventDefault();
    await run(async()=>{
      await request("/objectives/"+objectiveId+"/capabilities",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({capability_id:capabilityId,required_level:Number(requiredLevel)})});
    },"Strategic objective → capability mapping saved.");
  }

  async function mapCompetency(e:FormEvent){
    e.preventDefault();
    await run(async()=>{
      await request("/capabilities/"+capabilityMapId+"/competencies",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({competency_id:competencyMapId})});
    },"Capability → competency mapping saved.");
  }

  async function saveRoleRequirement(e:FormEvent){
    e.preventDefault();
    await run(async()=>{
      await request("/roles/"+roleId+"/requirements",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target_type:targetType,target_id:targetId,required_level:Number(requiredLevel),criticality:requirementCriticality,weight:Number(requirementWeight)})});
    },"Governed role requirement saved.");
  }

  const targetItems = targetType==="capability" ? capabilities : targetType==="competency" ? competencyItems : skills;
  return <div className="console-grid">
    {feedback&&<Notice kind={feedback.kind}>{feedback.text}</Notice>}

    <SectionCard eyebrow="Strategic architecture" title="Create strategic objective">
      <form className="studio-form" onSubmit={createObjective}>
        <label>Objective<input value={objective} onChange={e=>setObjective(e.target.value)} minLength={3} maxLength={240} required placeholder="e.g. Expand digital operating capability"/></label>
        <label>Description<textarea value={objectiveDescription} onChange={e=>setObjectiveDescription(e.target.value)} rows={3} placeholder="Describe the business outcome and strategic intent."/></label>
        <div className="form-grid"><label>Strategic category<input value={category} onChange={e=>setCategory(e.target.value)} maxLength={120}/></label><label>Priority (1–5)<input type="number" min={1} max={5} value={priority} onChange={e=>setPriority(e.target.value)}/></label></div>
        <button className="button button-primary" disabled={busy}><Plus size={15}/> Create objective</button>
      </form>
    </SectionCard>

    <SectionCard eyebrow="Competency framework" title="Create competency">
      <form className="studio-form" onSubmit={createCompetency}>
        <div className="form-grid"><label>Code<input value={competencyCode} onChange={e=>setCompetencyCode(e.target.value)} maxLength={80} required placeholder="e.g. STRAT-THINK"/></label><label>Type<select value={competencyType} onChange={e=>setCompetencyType(e.target.value)}><option value="behavioral">Behavioral</option><option value="functional">Functional</option><option value="technical">Technical</option><option value="leadership">Leadership</option></select></label></div>
        <label>Name<input value={competencyName} onChange={e=>setCompetencyName(e.target.value)} maxLength={180} required/></label>
        <label>Definition<textarea value={competencyDefinition} onChange={e=>setCompetencyDefinition(e.target.value)} rows={3} minLength={10} required placeholder="Define observable capability, not a course or activity."/></label>
        <button className="button button-primary" disabled={busy}><Plus size={15}/> Create competency</button>
      </form>
    </SectionCard>

    <SectionCard eyebrow="Competency governance" title="Define all five competency levels">
      <form className="studio-form" onSubmit={saveCompetencyLevels}>
        <label>Competency<select value={selectedCompetencyId} onChange={e=>{const id=e.target.value;setSelectedCompetencyId(id);const selected=competencyItems.find(x=>x.id===id);setCompetencyLevels(Object.fromEntries([1,2,3,4,5].map(level=>{const existing=selected?.levels?.find(x=>x.level===level);return [level,{definition:existing?.definition||"",behavioral_indicators:(existing?.behavioral_indicators||[]).join(", ")}]})))}} required>{competencyItems.map(x=><option key={x.id} value={x.id}>{x.name} · {x.code}</option>)}</select></label>
        <div className="compact-list">
          {[1,2,3,4,5].map(level=><div className="compact-row" key={level}>
            <div><strong>{level} — {levels.find(x=>x.level===level)?.name || "Governed level"}</strong></div>
            <div className="studio-form">
              <label>Definition<textarea value={competencyLevels[level].definition} onChange={e=>setCompetencyLevels(v=>({...v,[level]:{...v[level],definition:e.target.value}}))} rows={2} minLength={3} required placeholder="Observable standard for this level."/></label>
              <label>Behavioral indicators<input value={competencyLevels[level].behavioral_indicators} onChange={e=>setCompetencyLevels(v=>({...v,[level]:{...v[level],behavioral_indicators:e.target.value}}))} placeholder="Indicator 1, Indicator 2"/></label>
            </div>
          </div>)}
        </div>
        <button className="button button-secondary" disabled={busy||!selectedCompetencyId}><ShieldCheck size={15}/> Save five-level framework</button>
        {!competencyItems.length&&<p>Create a competency first.</p>}
      </form>
    </SectionCard>

    <SectionCard eyebrow="Strategy alignment" title="Objective → capability">
      <form className="studio-form" onSubmit={mapObjective}>
        <label>Strategic objective<select value={objectiveId} onChange={e=>setObjectiveId(e.target.value)} required>{objectiveItems.map(x=><option key={x.id} value={x.id}>{x.objective}</option>)}</select></label>
        <label>Organizational capability<select value={capabilityId} onChange={e=>setCapabilityId(e.target.value)} required>{capabilities.map(x=><option key={x.id} value={x.id}>{x.name} · {x.code}</option>)}</select></label>
        <label>Required capability level<select value={requiredLevel} onChange={e=>setRequiredLevel(e.target.value)}>{levels.map(x=><option key={x.level} value={x.level}>{x.level} — {x.name}</option>)}</select></label>
        <button className="button button-secondary" disabled={busy||!objectiveId||!capabilityId}><Target size={15}/> Save strategic mapping</button>
        {!objectiveItems.length&&<p>Create a strategic objective first.</p>}
      </form>
    </SectionCard>

    <SectionCard eyebrow="Capability architecture" title="Capability → competency">
      <form className="studio-form" onSubmit={mapCompetency}>
        <label>Organizational capability<select value={capabilityMapId} onChange={e=>setCapabilityMapId(e.target.value)} required>{capabilities.map(x=><option key={x.id} value={x.id}>{x.name} · {x.code}</option>)}</select></label>
        <label>Competency<select value={competencyMapId} onChange={e=>setCompetencyMapId(e.target.value)} required>{competencyItems.map(x=><option key={x.id} value={x.id}>{x.name} · {x.code}</option>)}</select></label>
        <button className="button button-secondary" disabled={busy||!capabilityMapId||!competencyMapId}><Link2 size={15}/> Save competency mapping</button>
        {!competencyItems.length&&<p>Create a competency first.</p>}
      </form>
    </SectionCard>

    <SectionCard eyebrow="Role architecture" title="Governed role requirement">
      <form className="studio-form" onSubmit={saveRoleRequirement}>
        <label>Role<select value={roleId} onChange={e=>setRoleId(e.target.value)} required>{roles.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
        <div className="form-grid"><label>Requirement type<select value={targetType} onChange={e=>{const next=e.target.value;setTargetType(next);setTargetId(next==="capability"?capabilities[0]?.id||"":next==="competency"?competencyItems[0]?.id||"":skills[0]?.id||"")}}><option value="capability">Capability</option><option value="competency">Competency</option><option value="skill">Skill</option></select></label><label>Required level<select value={requiredLevel} onChange={e=>setRequiredLevel(e.target.value)}>{levels.map(x=><option key={x.level} value={x.level}>{x.level} — {x.name}</option>)}</select></label></div>
        <div className="form-grid"><label>Criticality<select value={requirementCriticality} onChange={e=>setRequirementCriticality(e.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></label><label>Weight (1–100)<input type="number" min={1} max={100} value={requirementWeight} onChange={e=>setRequirementWeight(e.target.value)}/></label></div>
        <label>Target<select value={targetId} onChange={e=>setTargetId(e.target.value)} required>{targetItems.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
        <button className="button button-secondary" disabled={busy||!roleId||!targetId}><ShieldCheck size={15}/> Save role requirement</button>
      </form>
    </SectionCard>

    <SectionCard eyebrow="Governed scale" title="One proficiency language">
      <div className="compact-list">{levels.map(x=><div className="compact-row" key={x.level}><div><strong>{x.level} — {x.name}</strong><small>{x.definition}</small></div></div>)}</div>
      <p className="section-meta">All Phase 1 capability, competency and role requirements use this tenant-governed 1–5 scale.</p>
    </SectionCard>
  </div>;
}
