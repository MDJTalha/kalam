import Link from "next/link";
import { redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { SkillAdministration } from "@/components/skill-administration";
import { CapabilityDomainAdministration } from "@/components/capability-domain-administration";
import { apiJson, requireUser } from "@/lib/server-api";
type Skill={id:string;name:string;description?:string|null;category?:string|null};
type Role={id:string;name:string};type Course={id:string;title:string};
type Capability={id:string;name:string;code:string};
type Objective={id:string;objective:string;priority:number;status:string};
type Competency={id:string;name:string;code:string;definition:string;type:string;status:string;levels?:Array<{level:number;definition:string;behavioral_indicators?:string[]}>};
type Level={level:number;name:string;definition:string};
type Person={id:string;first_name:string;last_name:string;email:string;is_active:boolean};
type Governance={role_requirements:{role_id:string;role:string;skill_id:string;skill:string;required_proficiency:number}[];course_mappings:{course_id:string;course:string;skill_id:string;skill:string;target_proficiency:number}[]};
export default async function CapabilityFramework(){
  const user=await requireUser<{permissions?:string[]}>();
  const canDomain = !!user.permissions?.some(permission => ["skills.manage","capabilities.manage","strategic_objectives.manage","competencies.manage","role_requirements.manage"].includes(permission));
  if(!canDomain)redirect("/dashboard/skills");
  const [skills,roles,courses,governance,people,objectives,capabilities,competencies,levels]=await Promise.all([
    apiJson<Skill[]>("/api/v1/skills"),apiJson<Role[]>("/api/v1/organization/roles"),
    apiJson<Course[]>("/api/v1/courses"),apiJson<Governance>("/api/v1/skills/governance"),apiJson<Person[]>("/api/v1/people"),
    apiJson<Objective[]>("/api/v1/capability-domain/objectives"),apiJson<Capability[]>("/api/v1/capabilities"),
    apiJson<Competency[]>("/api/v1/capability-domain/competencies"),apiJson<Level[]>("/api/v1/capability-domain/proficiency-levels")
  ]);
  const framework=governance??{role_requirements:[],course_mappings:[]};
  const coveredRoles=new Set(framework.role_requirements.map(item=>item.role_id)).size;
  const alignedSkills=new Set(framework.course_mappings.map(item=>item.skill_id)).size;
  return <DashboardShell title="Capability Framework" eyebrow="Capability governance" breadcrumbs={[{label:"Skills & Capabilities",href:"/dashboard/skills"},{label:"Capability Framework"}]}>
    <section className="skills-command-hero"><div><span className="eyebrow">Framework design</span><h2>Define capabilities and align learning to system roles.</h2><p>Maintain clear skill definitions, set proficiency requirements for existing system roles, and align courses to the capabilities they support.</p><div className="skills-command-actions"><Link className="button button-secondary" href="/dashboard/skills">View my capability profile</Link></div></div><div className="skills-command-aside"><span>Framework coverage</span><strong>{coveredRoles}/{roles?.length??0}</strong><small>system roles with skill requirements</small></div></section>
    <section className="stat-grid skills-stat-grid" aria-label="Framework coverage">
      <div className="stat-card"><span>Defined skills</span><strong>{skills?.length??0}</strong><small>Tenant taxonomy</small></div>
      <div className="stat-card"><span>Role requirements</span><strong>{framework.role_requirements.length}</strong><small>Across {coveredRoles} roles</small></div>
      <div className="stat-card"><span>Course mappings</span><strong>{framework.course_mappings.length}</strong><small>Across {alignedSkills} skills</small></div>
      <div className="stat-card"><span>Unmapped roles</span><strong>{Math.max(0,(roles?.length??0)-coveredRoles)}</strong><small>System roles without requirements</small></div>
    </section>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Phase 1 architecture</span><h2>Strategy → capability → competency → role requirement</h2></div></div><p>Phase 1 adds the canonical capability domain around the existing skills foundation. Strategic objectives define business intent; capabilities express organizational capacity; competencies describe observable human capability; role requirements govern what each role must demonstrate. Learning mappings remain supporting evidence, not capability achievement.</p></section>
    <CapabilityDomainAdministration objectives={objectives??[]} capabilities={capabilities??[]} competencies={competencies??[]} roles={roles??[]} skills={skills??[]} levels={levels??[]}/>
    <SkillAdministration skills={skills??[]} roles={roles??[]} courses={courses??[]} people={(people??[]).filter(person=>person.is_active)} initialGovernance={framework}/>
  </DashboardShell>;
}
