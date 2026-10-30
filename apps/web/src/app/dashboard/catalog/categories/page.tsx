import { DashboardShell } from "@/components/dashboard-shell";
import { ApiActionButton } from "@/components/api-action-button";
import { ResourceForm } from "@/components/resource-form";
import { EmptyState, Section, StateMessage, StatusBadge } from "@/components/ui";
import { apiJsonResult, requireUser } from "@/lib/server-api";

type Category={id:string;name:string;description?:string|null;active:boolean};

export default async function CategoriesPage(){
  const user=await requireUser<{permissions?:string[]}>();
  const result = await apiJsonResult<Category[]>("/api/v1/courses/categories?manage=true");
  const canManage=user.permissions?.includes("courses.manage")??false;
  return <DashboardShell title="Catalog categories" eyebrow="Learning taxonomy">
    {canManage?<Section eyebrow="Taxonomy" title="Create category"><ResourceForm title="Add catalog category" endpoint="/api/lms/courses/categories" fields={[
      {name:"name",label:"Category name",required:true},
      {name:"description",label:"Description",type:"textarea"},
    ]}/></Section>:null}
    <Section eyebrow="Catalog structure" title="Categories">
      {!result.ok || !result.data
        ? <StateMessage tone="danger" title={result.status === 403 ? "Category access restricted" : result.status === 0 || result.status >= 500 ? "Category service unavailable" : "Categories could not be loaded"}>{result.error || `The category request failed with HTTP ${result.status}.`} The service response was not treated as an empty catalog.</StateMessage>
        : result.data.length
          ? <div className="compact-list">{result.data.map(x=><div className="compact-row" key={x.id}><div><strong>{x.name}</strong><small>{x.description||"No description"}</small></div><div className="button-row"><StatusBadge status={x.active?"active":"inactive"}/>{canManage?<ApiActionButton endpoint={"/api/lms/courses/categories/"+encodeURIComponent(x.id)} method="PATCH" body={{active:!x.active}} label={x.active?"Deactivate":"Activate"}/>:null}</div></div>)}</div>
          : <EmptyState title="No categories" description="Create a governed taxonomy for the course catalog."/>}
    </Section>
  </DashboardShell>;
}
