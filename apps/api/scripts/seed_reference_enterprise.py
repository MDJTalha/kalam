from __future__ import annotations

import asyncio
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, insert, select

from app.core.security import hash_password
from app.core.role_catalog import TENANT_ROLE_PERMISSIONS
from app.db.models import (
    Assessment, AssessmentAttempt, Certificate, ComplianceAssignment,
    ComplianceRequirement, ComplianceRequirementVersion, Course, CourseCategory,
    CourseModule, CourseSkill, Enrollment, LiveSession, AttendanceRecord,
    Lesson, OrgUnit, Permission, Question, Role, RolePermission,
    RoleSkillRequirement, Skill, Tenant, User, UserRole, UserSkill,
    DevelopmentPlan, DevelopmentMilestone, AuditLog,
)
from app.db.session import SessionLocal

TENANT_NAME = "Nexa Beverage & Water International"
TENANT_SLUG = "nexa-beverage-water-international"
EMAIL_DOMAIN = "nbwi.global"
ADMIN_EMAIL = "admin@nbwi.global"
ADMIN_PASSWORD = os.getenv("ENTERPRISE_ADMIN_PASSWORD", "ChangeMe!2026#NBWI")
NOW = datetime.now(timezone.utc)

REGIONS = {
    "Asia": [
        ("Pakistan", "PK", 624), ("India", "IN", 672), ("United Arab Emirates", "AE", 240),
        ("Saudi Arabia", "SA", 240), ("Indonesia", "ID", 288), ("Philippines", "PH", 240),
        ("Japan", "JP", 192), ("Singapore", "SG", 144), ("Bangladesh", "BD", 48),
    ],
    "Europe": [
        ("United Kingdom", "GB", 336), ("Germany", "DE", 288), ("France", "FR", 240),
        ("Italy", "IT", 211), ("Spain", "ES", 173), ("Poland", "PL", 192),
        ("Netherlands", "NL", 144), ("Turkey", "TR", 144), ("Sweden", "SE", 96),
    ],
    "North America": [("United States", "US", 864), ("Canada", "CA", 288), ("Mexico", "MX", 384)],
    "South America": [("Brazil", "BR", 672), ("Argentina", "AR", 192), ("Chile", "CL", 144), ("Colombia", "CO", 144), ("Peru", "PE", 96)],
    "Africa": [("South Africa", "ZA", 336), ("Nigeria", "NG", 288), ("Egypt", "EG", 240), ("Kenya", "KE", 192), ("Morocco", "MA", 173), ("Ghana", "GH", 115), ("Tanzania", "TZ", 96)],
    "Oceania": [("Australia", "AU", 624), ("New Zealand", "NZ", 144), ("Fiji", "FJ", 48), ("Papua New Guinea", "PG", 48)],
    "Antarctica": [],
}

GLOBAL_HEADCOUNT = 400
FIRST_NAMES = [
    "Aarav","Aisha","Amelia","Andreas","Anika","Arjun","Ava","Benjamin","Camila","Carlos","Chloe","Daniel","David","Elena","Elias","Emma","Ethan","Fatima","Felix","Grace","Hana","Hassan","Henry","Isabella","Jamal","James","Javier","Jonas","Joseph","Kaito","Karim","Khalid","Liam","Lucas","Maya","Meera","Michael","Mila","Mohammed","Nadia","Noah","Nora","Omar","Olivia","Priya","Rafael","Reem","Samuel","Sara","Sofia","Sophie","Tariq","Thomas","Victor","Yara","Yusuf","Zain","Zara"
]
LAST_NAMES = [
    "Adams","Ahmed","Alvarez","Anderson","Baker","Bennett","Berg","Brown","Campbell","Carter","Chen","Chowdhury","Collins","Costa","Das","Davies","Davis","Dawson","Diaz","Dubois","Evans","Fernandez","Fischer","Garcia","Ghosh","Gomez","Gonzalez","Gupta","Hansen","Hassan","Hoffmann","Hughes","Ibrahim","Ito","Jackson","Jansen","Jensen","Johnson","Jones","Khan","Kim","Kumar","Lee","Lewis","Lopez","Martin","Martinez","Mason","Matsumoto","Mendes","Miller","Mitchell","Mohamed","Morris","Murphy","Nakamura","Nelson","Nguyen","Nielsen","Novak","Okafor","Olsen","Ortiz","Patel","Pereira","Peterson","Pham","Phillips","Popov","Rahman","Reed","Rossi","Roy","Sanchez","Santos","Schmidt","Schneider","Scott","Shah","Singh","Smith","Soto","Stewart","Suzuki","Taylor","Thompson","Torres","Turner","Walker","Wang","Watanabe","Watson","Weber","Williams","Wilson","Wong","Wood","Wright","Yamada","Young","Zhang"
]

async def batch_insert(session, model, rows, size=750):
    for start in range(0, len(rows), size):
        if rows[start:start + size]:
            await session.execute(insert(model), rows[start:start + size])

def distribute(total, weights):
    raw = [total * weight for weight in weights]
    values = [int(value) for value in raw]
    for index in sorted(range(len(raw)), key=lambda i: raw[i] - values[i], reverse=True)[: total - sum(values)]:
        values[index] += 1
    return values

async def get_permissions(session):
    definitions = {
        "tenant.read":"View tenant","tenant.manage":"Manage tenant","users.read":"View users",
        "users.manage":"Manage users","courses.read":"View courses","courses.manage":"Manage courses",
        "learning.access":"Access learning","assessments.manage":"Manage assessments",
        "certificates.manage":"Manage certificates","compliance.manage":"Manage compliance",
        "skills.manage":"Manage skills","capabilities.read":"View capability framework","capabilities.manage":"Manage capability framework","development.manage":"Manage development plans",
        "reports.read":"View reports","reports.manage":"Manage saved reports and schedules",
        "audit.read":"View audit logs","files.read":"View governed files","files.manage":"Manage file controls",
        "integrations.manage":"Manage integrations","ai.manage":"Manage governed AI",
    }
    existing = {item.key: item for item in (await session.execute(select(Permission))).scalars().all()}
    for key, description in definitions.items():
        if key not in existing:
            item = Permission(id=uuid4(), key=key, description=description)
            session.add(item)
            existing[key] = item
    await session.flush()
    return existing

async def purge_reference_tenants(session):
    await session.execute(delete(Tenant).where(Tenant.slug.in_([
        "demo-corporation", "isolation-corporation", TENANT_SLUG
    ])))
    await session.commit()

async def seed():
    async with SessionLocal() as session:
        await purge_reference_tenants(session)
        tenant_id = uuid4()
        session.add(Tenant(
            id=tenant_id, name=TENANT_NAME, slug=TENANT_SLUG, status="active",
            settings={
                "industry":"Food & Beverage","hq":"Global Corporate Centre",
                "product_lines":["Cold Drinks","Mineral Water"],
                "operating_continents":["Asia","Europe","North America","South America","Africa","Oceania","Antarctica"],
                "antarctica_coverage":"Partner and distributor network; no permanent employee base",
                "dataset_class":"enterprise_reference_dataset",
                "headcount":10000,
            },
        ))
        permissions = await get_permissions(session)

        role_permissions = {
            name: list(keys) for name, keys in TENANT_ROLE_PERMISSIONS.items()
        }
        # Keep this legacy label only in the reference dataset for compatibility
        # with its sample-user assignments; production tenants use L&D Administrator.
        role_permissions["HR/L&D Admin"] = list(TENANT_ROLE_PERMISSIONS["L&D Administrator"])
        roles = {}
        for name, keys in role_permissions.items():
            role = Role(
                id=uuid4(), tenant_id=tenant_id, name=name,
                description=f"{name} access role",
                role_kind="legacy" if name == "HR/L&D Admin" else "predefined",
            )
            session.add(role); roles[name] = role
        await session.flush()
        role_links = []
        for role_name, keys in role_permissions.items():
            for key in keys:
                role_links.append({"role_id":roles[role_name].id,"permission_id":permissions[key].id})
        await batch_insert(session, RolePermission, role_links)
        await session.commit()

        org_rows = []
        unit_ids = {}
        def add_unit(key, name, parent_key, unit_type, code):
            unit_id = uuid4(); unit_ids[key] = unit_id
            org_rows.append({"id":unit_id,"tenant_id":tenant_id,"parent_id":unit_ids.get(parent_key),"name":name,"unit_type":unit_type,"code":code})
            return unit_id

        add_unit("global","Global Group","", "group","NBWI-GLOBAL")
        global_units = [
            ("exec","Global Executive Office","executive",10),("strategy","Corporate Strategy & Transformation","function",30),
            ("finance","Global Finance","function",40),("people","People & Culture","function",45),
            ("legal","Legal, Risk & Compliance","function",25),("tech","Technology & Digital","function",49),
            ("supply","Global Supply Chain & Procurement","function",50),("quality","Global Quality & Food Safety","function",45),
            ("esg","Sustainability & ESG","function",20),("cold_global","Cold Drinks Global Business","product",40),
            ("water_global","Mineral Water Global Business","product",40),
        ]
        for key,name,typ,_ in global_units: add_unit(key,name,"global",typ,key.upper())
        region_heads = {}
        for region in REGIONS:
            add_unit(f"region:{region}", f"{region} Region", "global", "region", region[:3].upper())
        country_units = {}
        for region, countries in REGIONS.items():
            for country, code, _headcount in countries:
                ckey=f"country:{code}"
                add_unit(ckey,country,"region:"+region,"country",code)
                country_units[code] = {}
                for subkey, label in [
                    ("lead","Country Leadership"),("cold_mfg","Cold Drinks Manufacturing & Operations"),
                    ("cold_com","Cold Drinks Commercial"),("water_mfg","Mineral Water Manufacturing & Operations"),
                    ("water_com","Mineral Water Commercial"),("supply","Supply Chain & Distribution"),
                    ("quality","Quality, EHS & Regulatory"),("enable","People, Finance & IT"),
                ]:
                    country_units[code][subkey]=add_unit(
                        f"{code}:{subkey}", label, ckey,
                        "leadership" if subkey=="lead" else "business" if subkey.startswith(("cold","water")) else "function",
                        f"{code}-{subkey.upper()}",
                    )
        await batch_insert(session, OrgUnit, org_rows)
        await session.commit()

        user_rows=[]; user_role_rows=[]; user_by_unit={}; employee_ids=[]
        manager_by_unit={}; admin_user_id=None; regional_presidents={}
        employee_password_hash=hash_password(secrets.token_urlsafe(32))
        admin_password_hash=hash_password(ADMIN_PASSWORD)

        def create_person(first,last,title,unit_id,manager_id,region=None,country=None,access=None,password_hash=None):
            nonlocal admin_user_id
            employee_number=f"NBWI-{len(employee_ids)+1:06d}"
            email=ADMIN_EMAIL if title=="Group Chief Executive Officer" else f"{employee_number.lower()}@{EMAIL_DOMAIN}"
            uid=uuid4(); employee_ids.append(uid)
            user_rows.append({
                "id":uid,"tenant_id":tenant_id,"email":email,"password_hash":password_hash or employee_password_hash,
                "first_name":first,"last_name":last,"employee_number":employee_number,"job_title":title,
                "org_unit_id":unit_id,"manager_id":manager_id,"is_active":True,
            })
            role_names={"Learner / Employee"}
            if access: role_names.update(access)
            if any(token in title for token in ["Manager","Head","Director","President","Supervisor","Lead","Chief"]):
                role_names.add("Manager")
            for role_name in role_names:
                user_role_rows.append({"user_id":uid,"role_id":roles[role_name].id})
            if title=="Group Chief Executive Officer":
                admin_user_id=uid
            return uid

        first_index=0
        # Global executive and functional teams
        ceo=create_person("Amelia","Taylor","Group Chief Executive Officer",unit_ids["exec"],None,access={"Tenant Administrator","Global Executive"},password_hash=admin_password_hash)
        for region in REGIONS:
            rid=add_unit if False else unit_ids[f"region:{region}"]
            first=FIRST_NAMES[(first_index+3)%len(FIRST_NAMES)]; last=LAST_NAMES[(first_index+7)%len(LAST_NAMES)]; first_index+=1
            regional_presidents[region]=create_person(first,last,f"Regional President, {region}",rid,ceo,region,access={"Regional Executive"})
        def add_country_team(region, country, code, headcount):
            nonlocal first_index
            gm=create_person(FIRST_NAMES[(first_index+9)%len(FIRST_NAMES)],LAST_NAMES[(first_index+13)%len(LAST_NAMES)],f"Country General Manager, {country}",country_units[code]["lead"],regional_presidents[region],region,country)
            first_index+=1
            profiles={
                "cold_mfg":("Cold Drinks Plant Manager","Production Shift Supervisor",["Process Engineer","Production Technician","Production Operator","Packaging Line Operator"]),
                "cold_com":("Cold Drinks Commercial Manager","Regional Sales Supervisor",["Key Account Manager","Sales Representative","Brand Executive","Merchandiser"]),
                "water_mfg":("Mineral Water Plant Manager","Production Shift Supervisor",["Process Engineer","Production Technician","Water Treatment Operator","Packaging Line Operator"]),
                "water_com":("Mineral Water Commercial Manager","Regional Sales Supervisor",["Key Account Manager","Sales Representative","Water Brand Executive","Merchandiser"]),
                "supply":("Supply Chain & Distribution Manager","Warehouse & Logistics Supervisor",["Supply Planner","Logistics Coordinator","Warehouse Associate","Distribution Driver"]),
                "quality":("Quality, EHS & Regulatory Manager","Quality Shift Supervisor",["Food Safety Specialist","Laboratory Analyst","EHS Specialist","Quality Assurance Specialist"]),
                "enable":("Country HR, Finance & IT Manager","People Operations Supervisor",["HR Business Partner","Finance Analyst","IT Support Specialist","Payroll Specialist"]),
            }
            subkeys=["cold_mfg","cold_com","water_mfg","water_com","supply","quality","enable"]
            counts=distribute(headcount-1,[0.31,0.14,0.22,0.10,0.08,0.07,0.08])
            for subkey,count in zip(subkeys,counts):
                if count<=0: continue
                unit=country_units[code][subkey]; manager_title,supervisor_title,staff_titles=profiles[subkey]
                access={"Quality & Compliance"} if subkey=="quality" else {"HR Business Partner"} if subkey=="enable" else None
                unit_manager=create_person(FIRST_NAMES[first_index%len(FIRST_NAMES)],LAST_NAMES[(first_index+17)%len(LAST_NAMES)],manager_title,unit,gm,region,country,access); first_index+=1
                remaining=count-1
                supervisors=[]
                if remaining>=12:
                    supervisor_count=max(1,remaining//25)
                    for s in range(supervisor_count):
                        supervisor=create_person(FIRST_NAMES[(first_index+s)%len(FIRST_NAMES)],LAST_NAMES[(first_index+s*3+19)%len(LAST_NAMES)],supervisor_title,unit,unit_manager,region,country,access); supervisors.append(supervisor); first_index+=1
                    remaining-=supervisor_count
                for n in range(remaining):
                    title=staff_titles[n%len(staff_titles)]
                    access_role={"Instructor"} if "Learning" in title else {"HR Business Partner"} if title=="HR Business Partner" else {"Quality & Compliance"} if ("Food Safety" in title or "Laboratory" in title or "EHS" in title or "Quality Assurance" in title) else None
                    parent=supervisors[n%len(supervisors)] if supervisors else unit_manager
                    create_person(FIRST_NAMES[(first_index+n)%len(FIRST_NAMES)],LAST_NAMES[(first_index+n*5+23)%len(LAST_NAMES)],title,unit,parent,region,country,access_role); first_index+=1

        global_profile_titles = {
            "exec":["Group Chief Operating Officer","Chief Commercial Officer","Chief Manufacturing Officer","Chief Information Officer","Chief Revenue Officer","Group Legal Counsel","Executive Strategy Partner","Executive Operations Partner","Executive Business Partner"],
            "strategy":["Chief Strategy Officer","Transformation Director","Transformation Manager","Business Transformation Analyst"],
            "finance":["Global Finance Director","Finance Manager","FP&A Manager","Finance Analyst"],
            "people":["Chief People Officer","Global HR Director","HR Business Partner","Learning & Development Manager","Training Facilitator","People Operations Specialist"],
            "legal":["General Counsel","Risk & Compliance Director","Compliance Manager","Internal Auditor","Compliance Specialist"],
            "tech":["Chief Technology Officer","Digital Transformation Director","Enterprise Applications Manager","Data Engineer","IT Support Specialist"],
            "supply":["Chief Supply Chain Officer","Procurement Director","Supply Planning Manager","Logistics Manager","Procurement Specialist"],
            "quality":["Global Quality Director","Food Safety Director","Quality Systems Manager","Food Safety Specialist","Laboratory Analyst"],
            "esg":["Sustainability Director","ESG Manager","Water Stewardship Manager","Sustainability Analyst"],
            "cold_global":["Global Cold Drinks President","Cold Drinks Commercial Director","Cold Drinks Category Manager","Cold Drinks Supply Planner"],
            "water_global":["Global Mineral Water President","Water Business Director","Water Category Manager","Water Supply Planner"],
        }
        global_managers={}
        for key, titles in global_profile_titles.items():
            count=next(item[3] for item in global_units if item[0]==key)
            if key=="exec":
                manager=ceo
                start_index=1
            else:
                manager=create_person(FIRST_NAMES[first_index%len(FIRST_NAMES)],LAST_NAMES[(first_index+11)%len(LAST_NAMES)],titles[0],unit_ids[key],ceo,access={"HR/L&D Admin"} if key=="people" else {"Quality & Compliance"} if key=="quality" else None)
                first_index+=1; start_index=1
            manager_by_unit[key]=manager; global_managers[key]=manager
            for n in range(start_index,count):
                title=titles[n%len(titles)]
                first=FIRST_NAMES[(first_index+n)%len(FIRST_NAMES)]; last=LAST_NAMES[(first_index+n*3+5)%len(LAST_NAMES)]
                access={"Auditor"} if "Auditor" in title else {"HR/L&D Admin"} if "Learning" in title or "Training" in title else {"HR Business Partner"} if "HR" in title else {"Instructor"} if "Facilitator" in title else {"Quality & Compliance"} if ("Quality" in title or "Food Safety" in title or "Compliance" in title) else None
                create_person(first,last,title,unit_ids[key],manager,access=access); first_index+=1

        for region, countries in REGIONS.items():
            for country, code, headcount in countries:
                add_country_team(region,country,code,headcount)
        await batch_insert(session, User, user_rows)
        await batch_insert(session, UserRole, user_role_rows)
        await session.commit()

        # Re-read users so all downstream records use persisted IDs.
        users=list((await session.execute(select(User).where(User.tenant_id==tenant_id).order_by(User.employee_number))).scalars().all())
        # Skills
        skill_defs = [
            ("Food Safety & HACCP","Quality"),("GMP & Sanitation","Quality"),("Beverage Quality Control","Quality"),
            ("Water Quality & Source Protection","Quality"),("CIP & Hygiene Systems","Operations"),("Process Control","Operations"),
            ("Production Planning","Operations"),("Packaging Operations","Operations"),("Maintenance Planning","Engineering"),
            ("EHS Management","Risk"),("Incident Investigation","Risk"),("Supply Planning","Supply Chain"),
            ("Inventory Management","Supply Chain"),("Warehouse Operations","Supply Chain"),("Logistics Management","Supply Chain"),
            ("Procurement","Commercial"),("Strategic Sourcing","Commercial"),("Route-to-Market","Commercial"),
            ("Key Account Management","Commercial"),("Brand Management","Commercial"),("Revenue Management","Commercial"),
            ("Digital Marketing","Commercial"),("Financial Controls","Finance"),("FP&A","Finance"),
            ("People Management","People"),("Performance Management","People"),("Learning Facilitation","People"),
            ("Business Acumen","Leadership"),("Strategic Thinking","Leadership"),("Change Leadership","Leadership"),
            ("Data Literacy","Digital"),("Cybersecurity Awareness","Digital"),("Data Analysis","Digital"),
            ("Regulatory Compliance","Risk"),("Internal Audit","Risk"),("Sustainability","ESG"),
            ("Water Stewardship","ESG"),("Project Management","Leadership"),("Customer Experience","Commercial"),
        ]
        skill_rows=[{"id":uuid4(),"tenant_id":tenant_id,"name":name,"description":f"{name} capability for the global F&B operating model","category":cat} for name,cat in skill_defs]
        await batch_insert(session, Skill, skill_rows); await session.commit()
        skills={row["name"]:row["id"] for row in skill_rows}

        role_skill_map={
            "Global Executive":["Business Acumen","Strategic Thinking","Change Leadership","Data Literacy"],
            "Regional Executive":["Business Acumen","Strategic Thinking","People Management","Financial Controls"],
            "HR/L&D Admin":["People Management","Learning Facilitation","Performance Management","Data Literacy"],
            "HR Business Partner":["People Management","Performance Management","Learning Facilitation","Data Literacy"],
            "Manager":["People Management","Performance Management","Business Acumen","EHS Management"],
            "Instructor":["Learning Facilitation","Data Literacy","Customer Experience"],
            "Quality & Compliance":["Food Safety & HACCP","Regulatory Compliance","Internal Audit","EHS Management"],
            "Auditor":["Internal Audit","Regulatory Compliance","Data Analysis"],
        }
        rs_rows=[]
        for role_name,names in role_skill_map.items():
            for name in names:
                rs_rows.append({"role_id":roles[role_name].id,"skill_id":skills[name],"required_proficiency":4 if role_name in {"Global Executive","Regional Executive"} else 3})
        await batch_insert(session, RoleSkillRequirement, rs_rows); await session.commit()

        # Course catalogue
        category_names=["Food Safety","Product & Quality","Manufacturing","Supply Chain","Commercial","People & Leadership","Risk & Compliance","Digital & Data","Sustainability"]
        cat_rows=[{"id":uuid4(),"tenant_id":tenant_id,"name":name,"description":f"{name} learning portfolio"} for name in category_names]
        await batch_insert(session, CourseCategory, cat_rows); await session.commit()
        cats={x["name"]:x["id"] for x in cat_rows}
        course_defs=[
            ("F&B Food Safety Fundamentals","Food Safety"),("HACCP: Hazard Analysis & Critical Control Points","Food Safety"),
            ("GMP for Beverage Manufacturing","Food Safety"),("Personal Hygiene & Food Handler Safety","Food Safety"),
            ("Allergen & Cross-Contact Control","Food Safety"),("Cold Drinks Production Excellence","Manufacturing"),
            ("Mineral Water Production Excellence","Manufacturing"),("CIP & Sanitation Systems","Manufacturing"),
            ("Packaging Line Changeover","Manufacturing"),("Preventive Maintenance & Reliability","Manufacturing"),
            ("Beverage Quality Control","Product & Quality"),("Water Quality & Source Protection","Product & Quality"),
            ("Laboratory Practices & Sample Integrity","Product & Quality"),("EHS Fundamentals","Risk & Compliance"),
            ("Incident Investigation & Root Cause","Risk & Compliance"),("Emergency Response & Crisis Management","Risk & Compliance"),
            ("Code of Conduct & Responsible Business","Risk & Compliance"),("Anti-Bribery & Third-Party Integrity","Risk & Compliance"),
            ("Cybersecurity for the Modern Workforce","Digital & Data"),("Data Protection & Privacy","Digital & Data"),
            ("Sales Excellence & Route-to-Market","Commercial"),("Key Account Management","Commercial"),
            ("Brand & Category Management","Commercial"),("Supply Chain Planning","Supply Chain"),
            ("Warehouse & Inventory Excellence","Supply Chain"),("Procurement & Strategic Sourcing","Supply Chain"),
            ("People Manager Foundations","People & Leadership"),("Performance Management","People & Leadership"),
            ("Learning Facilitation Skills","People & Leadership"),("Strategic Leadership","People & Leadership"),
            ("Sustainability & ESG Essentials","Sustainability"),("Water Stewardship & Resource Efficiency","Sustainability"),
        ]
        course_rows=[]; course_skill_rows=[]
        skill_course_pairs={
            0:["Food Safety & HACCP"],1:["Food Safety & HACCP"],2:["GMP & Sanitation"],3:["Food Safety & HACCP"],
            5:["Process Control","Packaging Operations"],6:["Process Control","Water Quality & Source Protection"],
            7:["CIP & Hygiene Systems"],10:["Beverage Quality Control"],11:["Water Quality & Source Protection"],
            13:["EHS Management"],14:["Incident Investigation"],17:["Regulatory Compliance"],18:["Regulatory Compliance"],
            19:["Cybersecurity Awareness"],20:["Data Literacy"],21:["Route-to-Market"],22:["Key Account Management"],
            23:["Supply Planning"],24:["Warehouse Operations","Inventory Management"],25:["Procurement","Strategic Sourcing"],
            26:["People Management"],27:["Performance Management"],28:["Learning Facilitation"],29:["Strategic Thinking"],
            30:["Sustainability"],31:["Water Stewardship"],
        }
        for idx,(title,cat) in enumerate(course_defs):
            cid=uuid4(); course_rows.append({"id":cid,"tenant_id":tenant_id,"title":title,"slug":f"nbwi-{idx+1:02d}-{title.lower().replace(' ','-').replace('&','and')[:70]}","description":f"Enterprise learning for {title.lower()} across Nexa Beverage & Water International.","status":"published","estimated_minutes":45+(idx%4)*15,"category_id":cats[cat],"owner_id":admin_user_id,"visibility":"tenant","enrollment_policy":"open","capacity":None,"audience_org_units":[],"tags":[cat,"global","F&B"],"prerequisites":[],"is_mandatory_default":cat in {"Food Safety","Risk & Compliance"},"record_metadata":{"product_lines":["Cold Drinks","Mineral Water"]}})
            for sname in skill_course_pairs.get(idx,["Business Acumen"]):
                course_skill_rows.append({"course_id":cid,"skill_id":skills[sname],"target_proficiency":3})
        await batch_insert(session, Course, course_rows)
        await batch_insert(session, CourseSkill, course_skill_rows); await session.commit()
        courses=course_rows

        module_rows=[]; lesson_rows=[]; assessment_rows=[]; question_rows=[]
        for idx,course in enumerate(courses):
            for pos,module_title in enumerate(["Core Standard","Applied Practice"],1):
                mid=uuid4(); module_rows.append({"id":mid,"course_id":course["id"],"title":module_title,"description":f"{module_title} for {course['title']}","position":pos})
                for lpos,lesson_title in enumerate(["Principles","Workplace application"],1):
                    body = (f"{course['title']} establishes the enterprise standard, required controls, evidence expectations, and practical actions employees apply in daily work." if lesson_title == "Principles" else f"Apply the {course['title']} standard to a workplace scenario: identify the control point, follow the approved procedure, record evidence, and escalate non-conformance through the local process.")
                    lesson_rows.append({"id":uuid4(),"module_id":mid,"title":f"{lesson_title}: {course['title']}","content_type":"rich_text","content":{"body":body},"position":lpos})
            if idx % 2 == 0:
                aid=uuid4(); assessment_rows.append({"id":aid,"tenant_id":tenant_id,"course_id":course["id"],"title":f"{course['title']} Knowledge Check","passing_score":70,"max_attempts":2,"time_limit_minutes":20})
                question_rows.append({"id":uuid4(),"assessment_id":aid,"question_type":"single_choice","prompt":f"Which practice best supports {course['title']}?","options":["Controlled documented practice","Unverified shortcut","Unapproved exception"],"answer_key":{"correct":"Controlled documented practice"},"points":1,"position":1})
        await batch_insert(session, CourseModule, module_rows); await batch_insert(session, Lesson, lesson_rows)
        await batch_insert(session, Assessment, assessment_rows); await batch_insert(session, Question, question_rows)
        await session.commit()

        # Learning activity: every employee receives four structured learning records.
        enrollment_rows=[]; completed_course_by_user={}
        for i,user in enumerate(users):
            base=[courses[(i*3)%len(courses)],courses[(i*3+5)%len(courses)],courses[(i*3+11)%len(courses)],courses[(i*3+17)%len(courses)]]
            for j,course in enumerate(base):
                created=NOW-timedelta(days=(i*7+j*11)%45)
                status_bucket=(i*7+j*13)%100
                status="completed" if status_bucket<58 else "in_progress" if status_bucket<80 else "enrolled"
                due=NOW-timedelta(days=((i+j)%12)+1) if status!="completed" and (i+j)%9==0 else NOW+timedelta(days=15+((i+j)*3)%75)
                completed_at=None
                if status=="completed":
                    completed_at=created+timedelta(days=2+((i+j)%12))
                    if completed_at>NOW: completed_at=NOW-timedelta(hours=(i+j)%24)
                    completed_course_by_user.setdefault(user.id,course["id"])
                enrollment_rows.append({"id":uuid4(),"tenant_id":tenant_id,"course_id":course["id"],"user_id":user.id,"status":status,"due_at":due,"completed_at":completed_at,"source":"enterprise_provisioning","created_at":created,"updated_at":created})
        await batch_insert(session, Enrollment, enrollment_rows); await session.commit()

        # Persisted skill evidence; proficiencies intentionally vary by role and employee.
        user_skill_rows=[]
        skill_list=list(skills)
        for i,user in enumerate(users):
            choices=[]
            title=(user.job_title or "").lower()
            if any(x in title for x in ["quality","food safety","compliance","audit"]): choices += ["Food Safety & HACCP","Regulatory Compliance","Beverage Quality Control","Internal Audit"]
            elif any(x in title for x in ["production","plant","operator","maintenance"]): choices += ["GMP & Sanitation","Process Control","Packaging Operations","Maintenance Planning"]
            elif any(x in title for x in ["supply","warehouse","logistics","procurement"]): choices += ["Supply Planning","Inventory Management","Warehouse Operations","Logistics Management"]
            elif any(x in title for x in ["sales","commercial","account","brand","marketing"]): choices += ["Route-to-Market","Key Account Management","Brand Management","Customer Experience"]
            elif any(x in title for x in ["people","hr","learning","training"]): choices += ["People Management","Performance Management","Learning Facilitation","Data Literacy"]
            else: choices += ["Business Acumen","Data Literacy","Cybersecurity Awareness","Customer Experience"]
            choices += [skill_list[(i*5)%len(skill_list)],skill_list[(i*7+3)%len(skill_list)]]
            seen=set()
            for name in choices:
                if name in seen: continue
                seen.add(name)
                proficiency=2+((i+len(name))%4)
                user_skill_rows.append({"id":uuid4(),"user_id":user.id,"skill_id":skills[name],"proficiency":proficiency,"evidence_source":"enterprise_learning_record"})
        await batch_insert(session, UserSkill, user_skill_rows); await session.commit()

        # Compliance obligations across food safety, EHS, conduct and digital control.
        requirement_defs=[
            ("Food Safety & HACCP Annual Recertification","Annual food safety capability assurance",365,30,0),
            ("EHS Annual Certification","Annual environment, health and safety assurance",365,30,13),
            ("Code of Conduct Annual Certification","Annual responsible business certification",365,30,16),
            ("Cybersecurity Annual Awareness","Annual security awareness certification",365,30,18),
        ]
        req_rows=[]; req_version_rows=[]
        for name,desc,recurrence,due_days,course_idx in requirement_defs:
            rid=uuid4(); req_rows.append({"id":rid,"tenant_id":tenant_id,"name":name,"description":desc,"recurrence_days":recurrence,"due_days":due_days,"active":True,"rules":{"enterprise_scope":"global"},"version":1})
            req_version_rows.append({"requirement_id":rid,"version":1,"tenant_id":tenant_id,"snapshot":{"name":name,"description":desc,"recurrence_days":recurrence,"due_days":due_days},"changed_by":admin_user_id})
        await batch_insert(session, ComplianceRequirement, req_rows); await batch_insert(session, ComplianceRequirementVersion, req_version_rows); await session.commit()
        compliance_rows=[]
        for i,user in enumerate(users):
            for j,req in enumerate(req_rows):
                bucket=(i*11+j*17)%100
                status="completed" if bucket<84 else "assigned" if bucket<94 else "in_progress"
                due=NOW-timedelta(days=5+((i+j)%45)) if status!="completed" and (i+j)%4==0 else NOW+timedelta(days=20+((i+j)*2)%120)
                compliance_rows.append({"id":uuid4(),"tenant_id":tenant_id,"requirement_id":req["id"],"requirement_version":1,"user_id":user.id,"course_id":courses[requirement_defs[j][4]]["id"],"due_at":due,"status":status,"created_at":NOW-timedelta(days=(i*3+j)%90),"updated_at":NOW})
        await batch_insert(session, ComplianceAssignment, compliance_rows); await session.commit()

        # Certificates for completed learning evidence; one current credential per employee.
        cert_rows=[]
        for i,(uid,cid) in enumerate(completed_course_by_user.items()):
            cert_rows.append({"id":uuid4(),"tenant_id":tenant_id,"user_id":uid,"course_id":cid,"verification_code":f"NBWI-{i+1:08d}-{secrets.token_hex(5).upper()}","issued_at":NOW-timedelta(days=(i%90)),"expires_at":NOW+timedelta(days=275),"record_metadata":{"credential_type":"course_completion","issuer":"NBWI Learning Academy"}})
        await batch_insert(session, Certificate, cert_rows); await session.commit()

        # Development plans for managers and leadership roles.
        manager_users=[u for u in users if any(token in (u.job_title or "") for token in ["Manager","Director","President","Chief","Head","Lead"])]
        plan_rows=[]; milestone_rows=[]
        for i,user in enumerate(manager_users):
            if i%2: continue
            pid=uuid4(); plan_rows.append({"id":pid,"tenant_id":tenant_id,"user_id":user.id,"title":f"2026 Leadership Development Plan - {user.job_title}","status":"active","goals":[{"goal":"Strengthen business leadership","target":"leadership_capability"},{"goal":"Improve data-led decisions","target":"data_literacy"}]})
            milestone_rows.append({"id":uuid4(),"tenant_id":tenant_id,"plan_id":pid,"title":"Leadership capability milestone","description":"Complete targeted leadership development and evidence application.","due_at":NOW+timedelta(days=120),"status":"planned","completed_at":None,"owner_id":user.id})
        await batch_insert(session, DevelopmentPlan, plan_rows); await batch_insert(session, DevelopmentMilestone, milestone_rows); await session.commit()

        # Assessments and attempts for completed learning.
        assessment_by_course={row["course_id"]:row["id"] for row in assessment_rows}
        attempt_rows=[]
        for i,user in enumerate(users):
            if i%3==0:
                for course_id in list(assessment_by_course)[:4]:
                    if completed_course_by_user.get(user.id)==course_id:
                        score=70+((i*7)%31)
                        attempt_rows.append({"id":uuid4(),"assessment_id":assessment_by_course[course_id],"user_id":user.id,"attempt_number":1,"answers":{"result":"completed"},"score":score,"passed":score>=70,"feedback":"Assessment completed against the published enterprise learning standard.","graded_by":admin_user_id,"grade_override":False,"started_at":NOW-timedelta(days=(i%60)+5,hours=2),"submitted_at":NOW-timedelta(days=(i%60)+5,hours=1)})
        await batch_insert(session, AssessmentAttempt, attempt_rows); await session.commit()

        # Live delivery footprint across global regions.
        instructors=[u for u in users if "Facilitator" in (u.job_title or "") or "Instructor" in (u.job_title or "")]
        instructors=instructors[:80] or [users[0]]
        session_rows=[]; attendance_rows=[]
        for idx in range(90):
            instructor=instructors[idx%len(instructors)]
            course=courses[idx%len(courses)]
            ended=idx<70
            starts=NOW-timedelta(days=idx+1,hours=2) if ended else NOW+timedelta(days=idx-69,hours=3)
            ends=starts+timedelta(hours=2)
            sid=uuid4()
            session_rows.append({"id":sid,"tenant_id":tenant_id,"course_id":course["id"],"instructor_id":instructor.id,"title":f"{course['title']} - Live Cohort {idx+1:03d}","starts_at":starts,"ends_at":ends,"location":f"{['Dubai','London','Singapore','Toronto','Johannesburg','Sydney'][idx%6]} Learning Centre","status":"completed" if ended else "scheduled"})
            if ended:
                for k in range(30):
                    learner=users[(idx*97+k*13)%len(users)]
                    mark=(idx+k)%10
                    status="present" if mark<7 else "late" if mark==7 else "absent"
                    attendance_rows.append({"id":uuid4(),"live_session_id":sid,"user_id":learner.id,"status":status,"marked_at":ends+timedelta(minutes=20)})
        await batch_insert(session, LiveSession, session_rows); await batch_insert(session, AttendanceRecord, attendance_rows); await session.commit()

        audit_rows=[]
        for i,action in enumerate(["enterprise.organization.provisioned","enterprise.learning.catalog.published","enterprise.compliance.baseline.created","enterprise.capability.baseline.created","enterprise.live_delivery.baseline.created"]):
            audit_rows.append({"id":uuid4(),"tenant_id":tenant_id,"actor_id":admin_user_id,"action":action,"entity_type":"enterprise_dataset","entity_id":str(tenant_id),"summary":action.replace("."," ").title(),"record_metadata":{"provisioning":"enterprise_reference_dataset"}})
        await batch_insert(session, AuditLog, audit_rows)
        await session.commit()

        print(f"ENTERPRISE_SEED_COMPLETE tenant={TENANT_SLUG} users={len(users)} courses={len(courses)} org_units={len(org_rows)}")
        print(f"ADMIN_EMAIL={ADMIN_EMAIL}")
        print(f"ADMIN_PASSWORD={ADMIN_PASSWORD}")
        print("NOTE: Employee identities are synthetic reference records; no dashboard KPI is hardcoded.")

if __name__ == "__main__":
    asyncio.run(seed())
