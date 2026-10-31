import Link from "next/link";
import { redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { SkillAdministration } from "@/components/skill-administration";
import { CapabilityDomainAdministration } from "@/components/capability-domain-administration";
import { StateMessage } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";
type Skill={id:string;name:string;description?:string|null;category?:string|null};
type SkillPage={items:Skill[];total:number};
type Role={id:string;name:string};type Course={id:string;title:string};type CoursePage={items:Course[];total:number};
type Capability={id:string;name:string;code:string};type CapabilityPage={items:Capability[];total:number};
type Objective={id:string;objective:string;priority:number;status:string};type ObjectivePage={items:Objective[];total:number};
type Competency={id:string;name:string;code:string;definition:string;type:string;status:string;levels?:Array<{level:number;definition:string;behavioral_indicators?:string[]}>};
type Level={level:number;name:string;definition:string};
type Person={id:string;first_name:string;last_name:string;email:string;is_active:boolean};
type PeoplePage={items:Person[];total:number};
type CompetencyPage={items:Competency[];total:number};
type Governance={role_requirements:{role_id:string;role:string;skill_id:string;skill:string;required_proficiency:number}[];course_mappings:{course_id:string;course:string;skill_id:string;skill:string;target_proficiency:number}[]};
export default async function CapabilityFramework(){
  const user=await requireUser<{permissions?:string[]}>();
  const canDomain = !!user.permissions?.some(permission => ["skills.manage","capabilities.manage","strategic_objectives.manage","competencies.manage","role_requirements.manage"].includes(permission));
  if(!canDomain)redirect("/dashboard/skills");
  const results=await Promise.all([
    apiJsonResult<SkillPage>("/api/v1/skills/page?page=1&page_size=100"),apiJsonResult<Role[]>("/api/v1/organization/roles"),
    apiJsonResult<CoursePage>("/api/v1/courses/page?page=1&page_size=100&manage=true"),apiJsonResult<Governance>("/api/v1/skills/governance"),apiJsonResult<PeoplePage>("/api/v1/people/page?page=1&page_size=20&status=active"),
    apiJsonResult<ObjectivePage>("/api/v1/capability-domain/objectives/page?page=1&page_size=100"),apiJsonResult<CapabilityPage>("/api/v1/capabilities/page?page=1&page_size=100"),
    apiJsonResult<CompetencyPage>("/api/v1/capability-domain/competencies/page?page=1&page_size=100"),apiJsonResult<Level[]>("/api/v1/capability-domain/proficiency-levels")
  ]);
  const failed=results.flatMap((result,index)=>result.ok?[]:[`Dataset ${index+1}: HTTP ${result.status} — ${result.error||"request failed"}`]);
  if(failed.length)return <DashboardShell title="Capability Framework" eyebrow="Capability governance"><StateMessage tone="danger" title="Framework data is incomplete">{failed.join(" · ")} Refresh after the affected service or permission is available; governance controls are withheld to avoid treating failures as empty data.</StateMessage></DashboardShell>;
  const [skillsResult,rolesResult,coursesResult,governanceResult,peopleResult,objectivesResult,capabilitiesResult,competenciesResult,levelsResult]=results;
  const skillPage=skillsResult.data!,roles=rolesResult.data!,coursePage=coursesResult.data!,governance=governanceResult.data!,peoplePage=peopleResult.data!,objectivePage=objectivesResult.data!,capabilityPage=capabilitiesResult.data!,competencyPage=competenciesResult.data!,levels=levelsResult.data!;
  if(objectivePage.total>objectivePage.items.length)return <DashboardShell title="Capability Framework" eyebrow="Capability governance"><StateMessage tone="danger" title="Strategic objective catalog exceeds the loaded limit">The objective catalog has more than 100 records. Searchable, paginated objective selection is required before this screen can safely manage the complete catalog.</StateMessage></DashboardShell>;
  if(capabilityPage.total>capabilityPage.items.length)return <DashboardShell title="Capability Framework" eyebrow="Capability governance"><StateMessage tone="danger" title="Capability catalog exceeds the loaded limit">The capability catalog has more than 100 records. Searchable, paginated capability selection is required before this screen can safely manage the complete catalog.</StateMessage></DashboardShell>;
  const objectives=objectivePage.items;
  const capabilities=capabilityPage.items;
  if(coursePage.total>coursePage.items.length)return <DashboardShell title="Capability Framework" eyebrow="Capability governance"><StateMessage tone="danger" title="Course catalog exceeds the mapping editor limit">The course catalog has more than 100 records. Narrowable course selection is required before this page can safely offer course-to-skill mappings.</StateMessage></DashboardShell>;
  const courses=coursePage.items;
  if(competencyPage.total>competencyPage.items.length)return <DashboardShell title="Capability Framework" eyebrow="Capability governance"><StateMessage tone="danger" title="Competency catalog exceeds the loaded limit">The framework contains more than 100 competencies. Searchable, paginated editing is needed before this screen can safely manage the complete catalog.</StateMessage></DashboardShell>;
  const competencies=competencyPage.items;
  const framework=governance??{role_requirements:[],course_mappings:[]};
  const coveredRoles=new Set(framework.role_requirements.map(item=>item.role_id)).size;
  const alignedSkills=new Set(framework.course_mappings.map(item=>item.skill_id)).size;
  return <DashboardShell title="Capability Framework" eyebrow="Capability governance" breadcrumbs={[{label:"Skills & Capabilities",href:"/dashboard/skills"},{label:"Capability Framework"}]}>
    <section className="skills-command-hero"><div><span className="eyebrow">Framework design</span><h2>Define capabilities and align learning to system roles.</h2><p>Maintain clear skill definitions, set proficiency requirements for existing system roles, and align courses to the capabilities they support.</p><div className="skills-command-actions"><Link className="button button-secondary" href="/dashboard/skills">View my capability profile</Link></div></div><div className="skills-command-aside"><span>Framework coverage</span><strong>{coveredRoles}/{roles?.length??0}</strong><small>system roles with skill requirements</small></div></section>
    <section className="stat-grid skills-stat-grid" aria-label="Framework coverage">
      <div className="stat-card"><span>Defined skills</span><strong>{skillPage.items?.length??0}</strong><small>Tenant taxonomy</small></div>
      <div className="stat-card"><span>Role requirements</span><strong>{framework.role_requirements.length}</strong><small>Across {coveredRoles} roles</small></div>
      <div className="stat-card"><span>Course mappings</span><strong>{framework.course_mappings.length}</strong><small>Across {alignedSkills} skills</small></div>
      <div className="stat-card"><span>Unmapped roles</span><strong>{Math.max(0,(roles?.length??0)-coveredRoles)}</strong><small>System roles without requirements</small></div>
    </section>
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Phase 1 architecture</span><h2>Strategy → capability → competency → role requirement</h2></div></div><p>Phase 1 adds the canonical capability domain around the existing skills foundation. Strategic objectives define business intent; capabilities express organizational capacity; competencies describe observable human capability; role requirements govern what each role must demonstrate. Learning mappings remain supporting evidence, not capability achievement.</p></section>
    <CapabilityDomainAdministration objectives={objectives??[]} capabilities={capabilities??[]} competencies={competencies??[]} roles={roles??[]} skills={skillPage.items??[]} levels={levels??[]}/>
    <SkillAdministration skills={skillPage.items??[]} roles={roles??[]} courses={courses??[]} people={peoplePage?.items??[]} initialGovernance={framework}/>
  </DashboardShell>;
}
