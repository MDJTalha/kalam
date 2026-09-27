import Link from "next/link";
import { redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { DashboardShell } from "@/components/dashboard-shell";
import { CourseAuthoring } from "@/components/course-authoring";
import { requireUser } from "@/lib/server-api";

export default async function NewCoursePage(){const user=await requireUser<{permissions?:string[]}>();if(!user.permissions?.includes("courses.manage"))redirect("/dashboard/catalog");return <DashboardShell title="Create course" eyebrow="Learning administration"><Link href="/dashboard/catalog" className="text-link"><ArrowLeft size={14}/> Back to catalog</Link><CourseAuthoring mode="create"/></DashboardShell>;}
