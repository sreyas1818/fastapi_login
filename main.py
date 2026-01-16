from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from database import engine, SessionLocal
import models
from starlette.middleware.sessions import SessionMiddleware
from models import Base


app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key"
)


templates = Jinja2Templates(directory="templates")


# -------------------------------------------------
# ROOT / LANDING PAGE
# -------------------------------------------------
@app.get("/")
@app.get("/login")
def landing_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -------------------------------------------------
# USER LOGIN
# -------------------------------------------------
@app.get("/user/login")
def user_login_page(request: Request):
    return templates.TemplateResponse("user_login.html", {"request": request})


@app.post("/user/login")
def user_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.password == password
    ).first()
    db.close()

    if not user:
        return templates.TemplateResponse(
            "user_login.html",
            {"request": request, "error": "Invalid email or password"}
        )

    # Successful login → donor registration
    request.session["user_logged_in"] = True
    return RedirectResponse("/home", status_code=302)


@app.get("/user/dashboard")
def user_dashboard(request: Request):

    # 🔐 User must be logged in
    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    db = SessionLocal()

    # For now: show all requests
    # (Later you can filter per user)
    requests_data = db.query(models.BloodRequest).all()

    db.close()

    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "requests": requests_data
        }
    )



# -------------------------------------------------
# USER REGISTER (ACCOUNT CREATION ONLY)
# -------------------------------------------------
@app.get("/user/register")
def user_register_page(request: Request):
    return templates.TemplateResponse("user_register.html", {"request": request})


@app.post("/user/register")
def user_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()

    try:
        user = models.User(email=email, password=password)
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        db.close()
        return templates.TemplateResponse(
            "user_register.html",
            {"request": request, "error": "Email already exists"}
        )

    db.close()
    return RedirectResponse("/user/login", status_code=302)




# -------------------------------------------------
# DONOR REGISTRATION (AFTER LOGIN)
# -------------------------------------------------
@app.get("/donor/register")
def donor_register_page(request: Request):

    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    response = templates.TemplateResponse(
        "register.html",
        {"request": request}
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response



@app.post("/donor/register")
def donor_register(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    gender: str = Form(...),
    blood_group: str = Form(...),
    age: int = Form(...),
    city: str = Form(...)
):
    if age < 18:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Donor must be at least 18"}
        )

    db = SessionLocal()
    donor = models.Donor(
        name=name,
        phone=phone,
        gender=gender,
        blood_group=blood_group,
        age=age,
        city=city,
        availability=True
    )
    db.add(donor)
    db.commit()
    db.close()

    return templates.TemplateResponse(
        "success.html",
        {"request": request, "message": "Blood donor registered successfully"}
    )
    
    
    
    
    
    
# -------------------------------------------------
# BLOOD REQUEST (AFTER LOGIN)
# -------------------------------------------------
@app.get("/blood/request")
def blood_request_page(request: Request):

    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    response = templates.TemplateResponse(
        "blood_request.html",
        {"request": request}
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.post("/blood/request")
def submit_blood_request(
    request: Request,
    patient_name: str = Form(...),
    blood_group: str = Form(...),
    units: int = Form(...),
    hospital: str = Form(...),
    city: str = Form(...),
    contact: str = Form(...),
    notes: str = Form(None)
):
    db = SessionLocal()

    blood_request = models.BloodRequest(
        patient_name=patient_name,
        blood_group=blood_group,
        units=units,
        hospital=hospital,
        city=city,
        contact=contact,
        notes=notes,
        status="Pending"  
    )

    db.add(blood_request)
    db.commit()
    db.close()

    return templates.TemplateResponse(
        "success.html",
        {"request": request, "message": "Blood request submitted successfully"}
    )
@app.get("/search-donors")
def search_donors(
    request: Request,
    blood_group: str = "",
    city: str = ""
):
    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    db = SessionLocal()
    query = db.query(models.Donor).filter(models.Donor.availability == True)

    if blood_group:
        query = query.filter(models.Donor.blood_group == blood_group)

    if city:
        query = query.filter(models.Donor.city.ilike(f"%{city}%"))

    donors = query.all()
    db.close()

    return templates.TemplateResponse(
        "search_donors.html",
        {"request": request, "donors": donors}
    )






# -------------------------------------------------
# ADMIN LOGIN
# -------------------------------------------------
@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    admin = db.query(models.Admin).filter(
        models.Admin.username == username,
        models.Admin.password == password
    ).first()
    db.close()

    if not admin:
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Invalid admin credentials"}
        )

    # ✅ SAVE LOGIN STATE IN SESSION
    request.session["admin_logged_in"] = True
    return RedirectResponse("/admin/dashboard", status_code=302)





# -------------------------------------------------
# ADMIN DASHBOARD (PROTECTED)
# -------------------------------------------------
@app.get("/admin/dashboard")
def admin_dashboard(request: Request):

    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    donors = db.query(models.Donor).all()
    db.close()

    response = templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "donors": donors}
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response





# -------------------------------------------------
# ADMIN – VIEW BLOOD REQUESTS
# -------------------------------------------------
@app.get("/admin/requests")
def admin_requests(request: Request):

    # 🔒 Protect route
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    requests_data = db.query(models.BloodRequest).all()
    db.close()


    response = templates.TemplateResponse(
        "admin_requests.html",
        {
            "request": request,
            "requests": requests_data
        }
    )
    # Prevent back navigation after logout
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.get("/admin/request/edit/{request_id}")
def edit_blood_request(request_id: int, request: Request):

    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    req = db.query(models.BloodRequest).filter(
        models.BloodRequest.id == request_id
    ).first()
    db.close()

    return templates.TemplateResponse(
        "edit_request.html",
        {"request": request, "request_data": req}
    )

@app.post("/admin/request/update/{request_id}")
def update_blood_request(
    request_id: int,
    request: Request,
    patient_name: str = Form(...),
    units: int = Form(...),
    hospital: str = Form(...),
    city: str = Form(...),
    contact: str = Form(...),
    notes: str = Form(None)
):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    req = db.query(models.BloodRequest).filter(
        models.BloodRequest.id == request_id
    ).first()

    req.patient_name = patient_name
    req.units = units
    req.hospital = hospital
    req.city = city
    req.contact = contact
    req.notes = notes

    db.commit()
    db.close()

    return RedirectResponse("/admin/requests", status_code=302)

@app.get("/admin/request/delete/{request_id}")
def delete_blood_request(request_id: int, request: Request):

    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    req = db.query(models.BloodRequest).filter(
        models.BloodRequest.id == request_id
    ).first()

    if req:
        db.delete(req)
        db.commit()

    db.close()
    return RedirectResponse("/admin/requests", status_code=302)





# -------------------------------------------------
# ADMIN LOGOUT
# -------------------------------------------------
@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)




# -------------------------------------------------
# EDIT DONOR
# -------------------------------------------------
@app.get("/edit/{donor_id}")
def edit_donor(donor_id: int, request: Request):

    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    donor = db.query(models.Donor).filter(models.Donor.id == donor_id).first()
    db.close()

    response = templates.TemplateResponse(
        "edit_donor.html",
        {"request": request, "donor": donor}
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.post("/update/{donor_id}")
def update_donor(
    donor_id: int,
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    city: str = Form(...)
):
    db = SessionLocal()
    donor = db.query(models.Donor).filter(models.Donor.id == donor_id).first()

    donor.name = name
    donor.phone = phone
    donor.city = city
    db.commit()

    donors = db.query(models.Donor).all()
    db.close()

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "donors": donors}
    )





# -------------------------------------------------
# DELETE DONOR (PROTECTED)
# -------------------------------------------------
@app.get("/delete/{donor_id}")
def delete_donor(donor_id: int, request: Request):

    # 🔒 BLOCK IF NOT ADMIN
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    donor = db.query(models.Donor).filter(models.Donor.id == donor_id).first()

    if donor:
        db.delete(donor)
        db.commit()

    donors = db.query(models.Donor).all()
    db.close()

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "donors": donors}
    )
@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.get("/home")
def home_page(request: Request):

    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    response = templates.TemplateResponse(
        "home.html",
        {"request": request}
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.get("/user/logout")
def user_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.get("/support")
def support_page(request: Request):

    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    return templates.TemplateResponse(
        "support.html",
        {"request": request}
    )
    
@app.post("/admin/request/status/{request_id}")
def update_request_status(
    request_id: int,
    request: Request,
    status: str = Form(...)
):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    req = db.query(models.BloodRequest).filter(
        models.BloodRequest.id == request_id
    ).first()

    req.status = status
    db.commit()
    db.close()

    return RedirectResponse("/admin/requests", status_code=302)

@app.post("/admin/request/assign/{request_id}")
def assign_donor(
    request_id: int,
    request: Request,
    donor_id: int = Form(...)
):
    if not request.session.get("admin_logged_in"):
        return RedirectResponse("/admin/login", status_code=302)

    db = SessionLocal()
    req = db.query(models.BloodRequest).filter(
        models.BloodRequest.id == request_id
    ).first()

    req.assigned_donor_id = donor_id
    req.status = "Approved"
    db.commit()
    db.close()

    return RedirectResponse("/admin/requests", status_code=302)


@app.get("/user/requests")
def user_requests(request: Request):
    if not request.session.get("user_logged_in"):
        return RedirectResponse("/user/login", status_code=302)

    db = SessionLocal()
    requests_data = db.query(models.BloodRequest).all()
    db.close()

    return templates.TemplateResponse(
        "user_requests.html",
        {"request": request, "requests": requests_data}
    )
