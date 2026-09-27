import Link from "next/link";
import { redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { SkillAdministration } from "@/components/skill-administration";
import { apiJson, requireUser } from "@/lib/server-api";
type Skill={id:string;name:string;description?:string|null;category?:string|null};
type Role={id:string;name:string};type Course={id:string;title:string};
type Governance={role_requirements:{role_id:string;role:string;skill_id:string;skill:string;required_proficiency:number}[];course_mappings:{course_id:string;course:string;skill_id:string;skill:string;target_proficiency:number}[]};
export default async function CapabilityFramework(){
  const user=await requireUser<{permissions?:string[]}>();
  if(!user.permissions?.includes("skills.manage"))redirect("/dashboard/skills");
  const [skills,roles,courses,governance]=await Promise.all([
    apiJson<Skill[]>("/api/v1/skills"),apiJson<Role[]>("/api/v1/admin/roles"),
    apiJson<Course[]>("/api/v1/courses"),apiJson<Governance>("/api/v1/skills/governance")
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
    <section className="data-panel"><div className="section-heading compact"><div><span className="eyebrow">Design workflow</span><h2>Define → require → align → validate</h2></div></div><p>Write observable definitions, attach required levels to system roles, map relevant courses, then review learner gaps on Skills & Capabilities. These roles are access roles from User Administration; occupational job profiles need a separate model. Course mappings describe intended learning and do not verify proficiency.</p></section>
    <SkillAdministration skills={skills??[]} roles={roles??[]} courses={courses??[]} initialGovernance={framework}/>
  </DashboardShell>;
}
