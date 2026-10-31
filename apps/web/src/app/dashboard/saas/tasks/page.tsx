import Link from "next/link";
import { AlertTriangle, CheckCircle2, ClipboardCheck, Clock3 } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { SaaSCrmNav } from "@/components/saas-crm-nav";
import { TaskCreateForm, TaskQuickActions } from "@/components/saas-crm-forms";
import { DataTable, EmptyState, MetricCard, SectionCard, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Task={id:string;account_id?:string|null;account_name?:string|null;subscription_id?:string|null;owner_user_id?:string|null;task_type:string;title:string;description?:string|null;status:string;priority:string;due_at?:string|null;completed_at?:string|null;source_key?:string|null;created_at:string};
type TaskPage={items:Task[];total:number;offset:number;limit:number;counts:{open:number;overdue:number;due_soon:number;completed:number}};
type TeamMember={id:string;name:string;is_active:boolean};

export default async function SaaSTasksPage({searchParams}:{searchParams:Promise<{status?:string;type?:string;page?:string}>}){
  const params=await searchParams;
  const query=new URLSearchParams();
  if(params.status)query.set("status",params.status);
  if(params.type)query.set("task_type",params.type);
  const requestedPage=Number(params.page||1);
  const page=Number.isSafeInteger(requestedPage)&&requestedPage>0?Math.min(requestedPage,100000):1;
  const listQuery=new URLSearchParams(query);
  listQuery.set("limit","25");
  listQuery.set("offset",String((page-1)*25));
  await requireUser();
  const [result,team]=await Promise.all([
    apiJsonResult<TaskPage>("/api/v1/saas/crm/page/tasks?"+listQuery.toString()),
    apiJsonResult<TeamMember[]>("/api/v1/saas/crm/team"),
  ]);
  if(!result.ok||!team.ok)return <DashboardShell title="Tasks" eyebrow="SaaS CRM"><section className="data-panel" role="alert"><h2>Task data unavailable</h2><p>${!result.ok ? `HTTP ${result.status}: ${result.error || "Task queue unavailable."}` : `HTTP ${team.status}: ${team.error || "CRM team unavailable."}`}</p></section></DashboardShell>;
  const taskPage=result.data!;
  const teamMembers=team.data ?? [];

  const tasks=result.items;
  const {open,overdue,due_soon:dueSoon,completed}=result.counts;
  const pageCount=Math.max(1,Math.ceil(result.total/result.limit));
  const pageHref=(target:number)=>{const search=new URLSearchParams();if(params.status)search.set("status",params.status);if(params.type)search.set("type",params.type);search.set("page",String(target));return "/dashboard/saas/tasks?"+search.toString();};

  return <DashboardShell title="Tasks" eyebrow="SaaS CRM" breadcrumbs={[{label:"SaaS Operations",href:"/dashboard/saas"},{label:"Tasks"}]}>
    <SaaSCrmNav/>
    <div className="stat-grid saas-spaced-section">
      <MetricCard label="Open" value={open} detail="Commercial follow-up work" icon={ClipboardCheck}/>
      <MetricCard label="Due in 7 days" value={dueSoon} detail="Immediate follow-up window" icon={Clock3}/>
      <MetricCard label="Overdue" value={overdue} detail="Past due and incomplete" icon={AlertTriangle}/>
      <MetricCard label="Completed" value={completed} detail="Closed tasks in current view" icon={CheckCircle2}/>
    </div>

    <SectionCard eyebrow="Task queue" title="Commercial work" meta={taskPage.total+" tasks"}>
      <form method="get" className="toolbar-row">
        <label>Status<select name="status" defaultValue={params.status||""}><option value="">All statuses</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="completed">Completed</option></select></label>
        <label>Type<select name="type" defaultValue={params.type||""}><option value="">All task types</option><option value="renewal">Renewal</option><option value="follow_up">Follow-up</option><option value="trial">Trial</option><option value="proposal">Proposal</option><option value="contract">Contract</option><option value="billing">Billing</option><option value="customer_success">Customer success</option></select></label>
        <button className="button button-primary" type="submit">Apply filters</button>
        <Link className="button button-secondary" href="/dashboard/saas/tasks">Clear</Link>
      </form>
      <DataTable caption="Commercial task queue"
        columns={["Task","Account","Type","Priority","Due","Status","Update"]}
        empty={<EmptyState title="No CRM tasks match these filters" description="Create a follow-up task or generate renewal milestones from the Renewals workspace."/>}
        rows={tasks.map(task=>[
          <span key="a"><strong>{task.title}</strong>{task.description&&<small>{task.description}</small>}</span>,
          task.account_id?<Link key="b" className="text-link" href={"/dashboard/saas/clients/"+task.account_id}>{task.account_name||"Account"}</Link>:<span key="b">—</span>,
          <span key="c">{task.task_type.replaceAll("_"," ")}</span>,
          <StatusBadge key="d" status={task.priority}/>,
          <span key="e">{task.due_at?new Date(task.due_at).toLocaleDateString():"—"}</span>,
          <StatusBadge key="f" status={task.status}/>,
          <TaskQuickActions key="g" id={task.id} status={task.status}/>
        ])}
      />
      <nav className="toolbar-row saas-spaced-pagination" aria-label="Task pages">
        {page>1?<Link className="button button-secondary" href={pageHref(page-1)}>Previous</Link>:null}
        <span>Page {page} of {pageCount} · {result.total} tasks</span>
        {page<pageCount?<Link className="button button-secondary" href={pageHref(page+1)}>Next</Link>:null}
      </nav>
    </SectionCard>

    <SectionCard eyebrow="New follow-up" title="Create task"><TaskCreateForm team={team}/></SectionCard>
  </DashboardShell>;
}
