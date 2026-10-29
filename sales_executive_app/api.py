import math
import base64
from datetime import timedelta
from dateutil import parser as date_parser
import frappe
from frappe.defaults import get_user_default
from frappe.utils import now_datetime, today, flt, cint, get_datetime
from frappe.utils.data import convert_utc_to_system_timezone
from frappe.utils.file_manager import save_file


def get_employee():
    emp = frappe.db.get_value(
        "Employee", {"user_id": frappe.session.user, "status": "Active"}
    )
    if not emp:
        # Fallback if Administrator is used or test user
        if frappe.session.user == "Administrator":
            first_emp = frappe.db.get_value("Employee", {"status": "Active"}, "name")
            if first_emp:
                return first_emp
        frappe.throw("No active Employee is linked to this user")
    return emp


def get_employee_info():
    emp_id = get_employee()
    emp = frappe.db.get_value(
        "Employee",
        emp_id,
        ["name", "employee_name", "department", "company", "user_id"],
        as_dict=True,
    )
    return emp or {"name": emp_id, "employee_name": emp_id}


def is_manager():
    roles = frappe.get_roles(frappe.session.user)
    return any(r in roles for r in ["System Manager", "Sales Manager", "HR Manager"])


def haversine(lat1, lon1, lat2, lon2):
    """Return the distance in meters between two GPS points."""
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def save_photo(doctype, docname, b64, filename):
    if not b64:
        return None
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    f = save_file(filename, base64.b64decode(b64), doctype, docname, is_private=0)
    return f.file_url


def save_location_log(employee, latitude, longitude, source, timestamp=None, accuracy=10, speed=0, battery=100, is_mock=0):
    timestamp = timestamp or now_datetime()
    duplicate = frappe.db.exists(
        "Location Log",
        {
            "employee": employee,
            "timestamp": timestamp,
            "latitude": flt(latitude),
            "longitude": flt(longitude),
            "source": source,
        },
    )
    if duplicate:
        return duplicate

    doc = frappe.get_doc(
        {
            "doctype": "Location Log",
            "employee": employee,
            "timestamp": timestamp,
            "latitude": flt(latitude),
            "longitude": flt(longitude),
            "accuracy": flt(accuracy),
            "speed": flt(speed),
            "battery": flt(battery),
            "is_mock": cint(is_mock),
            "source": source,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def get_attendance_checkins(employee, date):
    return frappe.get_all(
        "Employee Checkin",
        filters={"employee": employee, "time": ["between", [date, date + " 23:59:59"]]},
        fields=["log_type", "time"],
        order_by="time asc",
    )


def summarize_attendance(checkins):
    first_clock_in = None
    active_clock_in = None
    last_clock_out = None
    total_seconds = 0
    for checkin in checkins:
        if checkin.log_type == "IN":
            first_clock_in = first_clock_in or checkin.time
            active_clock_in = checkin.time
        elif checkin.log_type == "OUT":
            last_clock_out = checkin.time
            if active_clock_in:
                total_seconds += max(
                    0, (get_datetime(checkin.time) - get_datetime(active_clock_in)).total_seconds()
                )
                active_clock_in = None

    if active_clock_in:
        total_seconds += max(
            0, (get_datetime(now_datetime()) - get_datetime(active_clock_in)).total_seconds()
        )

    return {
        "first_clock_in": first_clock_in,
        "clock_in": active_clock_in or first_clock_in,
        "clock_out": None if active_clock_in else last_clock_out,
        "is_on_duty": bool(active_clock_in),
        "working_hours": round(total_seconds / 3600, 2),
    }


def attach_visit_item_details(visits):
    if not visits:
        return

    names = [visit.name for visit in visits]
    details = frappe.get_all(
        "Item Details",
        filters={"parent": ["in", names], "parenttype": "Shop Visit"},
        fields=["parent", "item", "qty", "price"],
        order_by="parent asc, idx asc",
    )
    item_codes = list({detail.item for detail in details if detail.item})
    item_names = {}
    if item_codes:
        item_names = {
            item.name: {"item_name": item.item_name, "stock_uom": item.stock_uom}
            for item in frappe.get_all(
                "Item",
                filters={"name": ["in", item_codes]},
                fields=["name", "item_name", "stock_uom"],
            )
        }
    by_visit = {}
    for detail in details:
        by_visit.setdefault(detail.parent, []).append(
            {
                "item": detail.item,
                "item_name": item_names.get(detail.item, {}).get("item_name", detail.item),
                "stock_uom": item_names.get(detail.item, {}).get("stock_uom"),
                "qty": detail.qty,
                "price": detail.price,
            }
        )
    for visit in visits:
        visit["details"] = by_visit.get(visit.name, [])


def parse_ts(ts):
    """Convert an ISO timestamp from the phone into server-timezone datetime."""
    try:
        dt = date_parser.isoparse(ts)
        if dt.tzinfo:
            dt = convert_utc_to_system_timezone(dt).replace(tzinfo=None)
        return dt
    except Exception:
        return now_datetime()


# ---------- Authentication & Info ----------

@frappe.whitelist(allow_guest=True)
def ping():
    if frappe.session.user == "Guest":
        return {
            "user": "Guest",
            "is_logged_in": False,
            "csrf_token": frappe.session.csrf_token,
        }
    emp = get_employee_info()
    return {
        "user": frappe.session.user,
        "employee": emp.get("name"),
        "employee_name": emp.get("employee_name") or emp.get("name"),
        "is_manager": is_manager(),
        "today": today(),
        "is_logged_in": True,
        "csrf_token": frappe.session.csrf_token,
    }


@frappe.whitelist()
def get_meta_options():
    groups = frappe.get_all("Customer Group", filters={"is_group": 0}, pluck="name", limit=50)
    if not groups:
        groups = frappe.get_all("Customer Group", pluck="name", limit=50)
    territories = frappe.get_all("Territory", filters={"is_group": 0}, pluck="name", limit=50)
    if not territories:
        territories = frappe.get_all("Territory", pluck="name", limit=50)
    return {
        "customer_groups": groups,
        "territories": territories,
    }


# ---------- Customers / Shops ----------

@frappe.whitelist()
def my_shops(latitude=None, longitude=None, search=None, limit=200):
    emp = get_employee()
    filters = {"disabled": 0}
    
    # Check if this employee has assigned customers
    has_assigned = frappe.db.count("Customer", {"disabled": 0, "custom_assigned_employee": emp})
    if has_assigned > 0:
        filters["custom_assigned_employee"] = emp

    if search:
        search = search.strip()
        shops = frappe.db.sql("""
            SELECT name, customer_name,
                   COALESCE(custom_shop_name, customer_name) as shop_name,
                   custom_contact_person as contact_person,
                   mobile_no, primary_address, territory, customer_group,
                   custom_shop_latitude as shop_latitude,
                   custom_shop_longitude as shop_longitude,
                   custom_geofence_radius as geofence_radius,
                   custom_assigned_employee as assigned_employee
            FROM `tabCustomer`
            WHERE disabled = 0
              AND (%(assigned)s IS NULL OR custom_assigned_employee = %(assigned)s)
              AND (customer_name LIKE %(search)s
                   OR custom_shop_name LIKE %(search)s
                   OR custom_contact_person LIKE %(search)s
                   OR name LIKE %(search)s
                   OR mobile_no LIKE %(search)s
                   OR territory LIKE %(search)s)
            ORDER BY COALESCE(custom_shop_name, customer_name) ASC
            LIMIT %(limit)s
        """, {
            "assigned": emp if has_assigned > 0 else None,
            "search": f"%{search}%",
            "limit": cint(limit) or 200,
        }, as_dict=True)
    else:
        shops = frappe.get_all(
            "Customer",
            filters=filters,
            fields=[
                "name",
                "customer_name",
                "custom_shop_name as shop_name",
                "custom_contact_person as contact_person",
                "mobile_no",
                "primary_address",
                "territory",
                "customer_group",
                "custom_shop_latitude as shop_latitude",
                "custom_shop_longitude as shop_longitude",
                "custom_geofence_radius as geofence_radius",
                "custom_assigned_employee as assigned_employee",
            ],
            limit=cint(limit) or 200,
            order_by="custom_shop_name asc, customer_name asc",
        )
        for s in shops:
            if not s.get("shop_name"):
                s["shop_name"] = s.get("customer_name")

    if latitude and longitude:
        u_lat = flt(latitude)
        u_lng = flt(longitude)
        for s in shops:
            if s.shop_latitude and s.shop_longitude:
                s["distance"] = round(
                    haversine(u_lat, u_lng, flt(s.shop_latitude), flt(s.shop_longitude))
                )
        shops.sort(key=lambda x: (x.get("distance") is None, x.get("distance", 10**9)))

    return shops


@frappe.whitelist()
def add_customer(
    customer_name,
    shop_name=None,
    contact_person=None,
    mobile_no=None,
    address=None,
    territory=None,
    customer_group=None,
    latitude=None,
    longitude=None,
    description=None,
):
    emp = get_employee()
    if not customer_name or not customer_name.strip():
        frappe.throw("Customer Name is required")

    final_customer_name = customer_name.strip()
    final_shop_name = (shop_name or customer_name).strip()

    # Fallback customer group and territory if none selected
    if not customer_group:
        customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "Commercial"
    if not territory:
        territory = frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories"

    doc = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": final_customer_name,
        "custom_shop_name": final_shop_name,
        "custom_contact_person": contact_person.strip() if contact_person else None,
        "customer_group": customer_group,
        "territory": territory,
        "mobile_no": mobile_no.strip() if mobile_no else None,
        "primary_address": address.strip() if address else None,
        "customer_details": description.strip() if description else None,
        "custom_assigned_employee": emp,
        "custom_shop_latitude": flt(latitude) if latitude else 0.0,
        "custom_shop_longitude": flt(longitude) if longitude else 0.0,
        "custom_geofence_radius": 100,
    })
    doc.flags.ignore_permissions = True
    doc.insert()

    # Also record standard Contact doctype linked to Customer
    if contact_person and contact_person.strip():
        try:
            contact = frappe.get_doc({
                "doctype": "Contact",
                "first_name": contact_person.strip(),
                "mobile_no": mobile_no.strip() if mobile_no else None,
                "is_primary_contact": 1,
                "links": [{"link_doctype": "Customer", "link_name": doc.name}],
            })
            contact.flags.ignore_permissions = True
            contact.insert()
            frappe.db.set_value("Customer", doc.name, "customer_primary_contact", contact.name)
        except Exception:
            pass

    return {
        "name": doc.name,
        "customer_name": doc.customer_name,
        "shop_name": doc.custom_shop_name,
        "contact_person": doc.custom_contact_person,
        "shop_latitude": doc.custom_shop_latitude,
        "shop_longitude": doc.custom_shop_longitude,
    }


@frappe.whitelist()
def set_shop_location(customer, latitude, longitude):
    emp = get_employee()
    assigned = frappe.db.get_value("Customer", customer, "custom_assigned_employee")
    if assigned and assigned != emp and not is_manager():
        frappe.throw("This shop is not assigned to you")
    frappe.db.set_value("Customer", customer, {
        "custom_shop_latitude": flt(latitude),
        "custom_shop_longitude": flt(longitude),
    })
    return "ok"


# ---------- Attendance & Day Tracking ----------

@frappe.whitelist()
def clock_in(latitude, longitude, selfie_b64=None):
    emp = get_employee()
    d = today()

    checkins = get_attendance_checkins(emp, d)
    if checkins and checkins[-1].log_type == "IN":
        frappe.throw("You have already clocked in today")

    doc = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": emp,
        "log_type": "IN",
        "time": now_datetime(),
        "latitude": flt(latitude),
        "longitude": flt(longitude),
    })
    doc.flags.ignore_permissions = True
    doc.insert()

    if selfie_b64:
        save_photo("Employee Checkin", doc.name, selfie_b64, "clockin_selfie.jpg")

    save_location_log(emp, latitude, longitude, "Clock In")

    return {"name": doc.name, "time": str(doc.time)}


@frappe.whitelist()
def clock_out(latitude, longitude, selfie_b64=None):
    emp = get_employee()
    d = today()

    checkins = get_attendance_checkins(emp, d)
    if not checkins or checkins[-1].log_type != "IN":
        frappe.throw("You have not clocked in today")

    # Auto checkout any active visit if forgotten
    active_visit = frappe.db.get_value(
        "Shop Visit",
        {"employee": emp, "visit_date": d, "check_out_time": ("is", "not set")},
        "name"
    )
    if active_visit:
        frappe.db.set_value("Shop Visit", active_visit, "check_out_time", now_datetime())

    doc = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": emp,
        "log_type": "OUT",
        "time": now_datetime(),
        "latitude": flt(latitude),
        "longitude": flt(longitude),
    })
    doc.flags.ignore_permissions = True
    doc.insert()

    if selfie_b64:
        save_photo("Employee Checkin", doc.name, selfie_b64, "clockout_selfie.jpg")

    save_location_log(emp, latitude, longitude, "Clock Out")
    report = build_daily_report(emp, d)
    return {"name": doc.name, "time": str(doc.time), "report": report}


# ---------- GPS tracking ----------

@frappe.whitelist()
def upload_locations(points, sharing_enabled=0):
    """points = JSON list of {lat, lng, ts, acc, speed, battery, mock}"""
    emp = get_employee()
    if not cint(sharing_enabled):
        frappe.throw("Location sharing must be enabled to upload location updates")
    checkins = get_attendance_checkins(emp, today())
    if not checkins or checkins[-1].log_type != "IN":
        frappe.throw("Location updates can only be saved while clocked in")

    points = frappe.parse_json(points)
    saved = 0
    for p in points[:500]:
        timestamp = parse_ts(p.get("ts"))
        recent_log = frappe.get_all(
            "Location Log",
            filters={
                "employee": emp,
                "timestamp": [">=", get_datetime(timestamp) - timedelta(hours=1)],
            },
            fields=["name"],
            order_by="timestamp desc",
            limit=1,
        )
        if recent_log:
            continue
        save_location_log(
            emp,
            p.get("lat"),
            p.get("lng"),
            "Background",
            timestamp=timestamp,
            accuracy=p.get("acc"),
            speed=p.get("speed"),
            battery=p.get("battery", 100),
            is_mock=p.get("mock"),
        )
        saved += 1
    return {"saved": saved, "processed": min(len(points), 500)}


# ---------- Shop Visits ----------

@frappe.whitelist()
def shop_checkin(customer, latitude, longitude, selfie_b64=None, shop_photo_b64=None,
                 is_mock=0, remarks=None):
    emp = get_employee()
    shop = frappe.db.get_value(
        "Customer", customer,
        ["custom_shop_latitude", "custom_shop_longitude", "custom_geofence_radius"],
        as_dict=True,
    )
    if not shop:
        frappe.throw("Customer not found")

    dist = None
    suspicious = cint(is_mock)
    if shop.custom_shop_latitude and shop.custom_shop_longitude:
        dist = haversine(flt(latitude), flt(longitude),
                         flt(shop.custom_shop_latitude), flt(shop.custom_shop_longitude))
        limit = shop.custom_geofence_radius or 100
        if dist > limit:
            frappe.throw(
                f"You are {round(dist)} m away from the shop. "
                f"Move within {limit} m to check in."
            )
    else:
        # Shop location is not set, flag the visit for review
        suspicious = 1

    visit = frappe.get_doc({
        "doctype": "Shop Visit",
        "employee": emp,
        "customer": customer,
        "visit_date": today(),
        "check_in_time": now_datetime(),
        "latitude": flt(latitude),
        "longitude": flt(longitude),
        "distance_from_shop": dist,
        "is_suspicious": suspicious,
        "remarks": remarks,
    })
    visit.flags.ignore_permissions = True
    visit.insert()

    save_location_log(emp, latitude, longitude, "Shop Check-in")

    updates = {}
    if selfie_b64:
        updates["selfie"] = save_photo("Shop Visit", visit.name, selfie_b64, "selfie.jpg")
    if shop_photo_b64:
        updates["shop_photo"] = save_photo("Shop Visit", visit.name, shop_photo_b64, "shop.jpg")
    if updates:
        visit.db_set(updates)

    return {
        "visit": visit.name,
        "customer": customer,
        "customer_name": frappe.db.get_value("Customer", customer, "customer_name"),
    }


@frappe.whitelist()
def shop_checkout(visit, remarks=None, order_qty=None):
    v = frappe.get_doc("Shop Visit", visit)
    if v.employee != get_employee() and not is_manager():
        frappe.throw("Not allowed")
    updates = {"check_out_time": now_datetime()}
    if remarks:
        updates["remarks"] = remarks
    if order_qty is not None and flt(order_qty) > 0:
        updates["order_qty"] = flt(order_qty)
    v.db_set(updates)
    return "ok"


# ---------- Orders & Catalog ----------

def get_selling_price_list():
    price_list = get_user_default("selling_price_list") or frappe.get_single_value(
        "Selling Settings", "selling_price_list"
    )
    return frappe.db.get_value(
        "Price List", {"name": price_list, "enabled": 1, "selling": 1}, "name"
    )


def get_selling_item_price(item_code, uom, price_list, customer=None):
    if not price_list:
        return 0

    from erpnext.stock.get_item_details import get_item_price

    price = get_item_price(
        {
            "price_list": price_list,
            "uom": uom,
            "transaction_date": today(),
            "customer": customer,
        },
        item_code,
    )
    return flt(price[0].price_list_rate) if price else 0


@frappe.whitelist()
def item_list(search="", customer=None):
    search = search.strip() if search else ""
    items = frappe.get_all(
        "Item",
        filters={
            "disabled": 0,
            "is_sales_item": 1,
            "item_group": "Finished Goods",
            "item_name": ["like", f"%{search}%"],
        },
        fields=["item_code", "item_name", "stock_uom"],
        limit=50,
        order_by="item_name asc",
    )
    price_list = get_selling_price_list()
    for item in items:
        item["price"] = get_selling_item_price(
            item.item_code, item.stock_uom, price_list, customer=customer
        )

    return items


@frappe.whitelist()
def create_order(visit, items=None, order_qty=None, remarks=None):
    """Saves order quantity and details directly on Shop Visit without creating ERPNext Sales Order."""
    v = frappe.get_doc("Shop Visit", visit)
    if v.employee != get_employee() and not is_manager():
        frappe.throw("Not allowed")

    parsed_items = frappe.parse_json(items) if items else []
    if not isinstance(parsed_items, list):
        frappe.throw("Order items must be a list")
    total_qty = flt(order_qty) if order_qty else sum(flt(i.get("qty", 0)) for i in parsed_items if flt(i.get("qty", 0)) > 0)

    updates = {"order_qty": total_qty}
    item_rows = []
    for item in parsed_items:
        item_code = item.get("item_code") or item.get("item")
        qty = flt(item.get("qty"))
        if not item_code or qty <= 0:
            continue
        available_item = frappe.db.get_value(
            "Item",
            {"name": item_code, "disabled": 0, "is_sales_item": 1, "item_group": "Finished Goods"},
            "name",
        )
        if not available_item:
            frappe.throw(f"Item {item_code} is not an available Finished Goods item")
        item_uom = frappe.db.get_value("Item", item_code, "stock_uom")
        price = get_selling_item_price(
            item_code, item_uom, get_selling_price_list(), customer=v.customer
        )
        item_rows.append({"item": item_code, "qty": qty, "price": price})

    combined_remarks = (remarks or "").strip()
    if parsed_items:
        item_desc = ", ".join([f"{i.get('item_code')} (x{i.get('qty')})" for i in parsed_items if flt(i.get("qty", 0)) > 0])
        if item_desc:
            if combined_remarks:
                combined_remarks += f" | Order: {item_desc}"
            else:
                combined_remarks = f"Order: {item_desc}"

    if combined_remarks:
        updates["remarks"] = combined_remarks

    # Note: ERPNext Sales Order creation is completely disabled as requested
    v.update(updates)
    v.set("details", item_rows)
    v.save(ignore_permissions=True)
    return {"order_qty": total_qty}


# ---------- Reports & Today Status ----------

def calc_km(emp, date):
    pts = frappe.get_all(
        "Location Log",
        filters={"employee": emp, "timestamp": ["between", [date, date + " 23:59:59"]]},
        fields=["latitude", "longitude", "accuracy", "timestamp"],
        order_by="timestamp asc",
    )
    total, prev = 0.0, None
    for p in pts:
        if p.accuracy and p.accuracy > 70:
            continue
        if prev:
            d = haversine(prev.latitude, prev.longitude, p.latitude, p.longitude)
            secs = (get_datetime(p.timestamp) - get_datetime(prev.timestamp)).total_seconds() or 1
            if d >= 20 and d / secs < 45:  # ignore jitter and teleports
                total += d
        prev = p
    return round(total / 1000, 2)


def build_daily_report(emp, date):
    visits = frappe.get_all(
        "Shop Visit",
        filters={"employee": emp, "visit_date": date},
        fields=["check_in_time", "check_out_time", "order_qty"],
        order_by="check_in_time asc",
    )
    attendance = summarize_attendance(get_attendance_checkins(emp, date))
    cin = attendance["first_clock_in"]
    cout = attendance["clock_out"]

    values = {
        "employee": emp,
        "report_date": date,
        "clock_in": cin,
        "clock_out": cout,
        "shops_visited": len(visits),
        "total_order_qty": sum(flt(v.order_qty) for v in visits),
        "km_travelled": calc_km(emp, date),
        "first_visit_time": visits[0].check_in_time if visits else None,
        "last_visit_time": visits[-1].check_in_time if visits else None,
        "working_hours": attendance["working_hours"],
    }

    name = frappe.db.exists("Daily Report", {"employee": emp, "report_date": date})
    doc = frappe.get_doc("Daily Report", name) if name else frappe.new_doc("Daily Report")
    doc.update(values)
    doc.save(ignore_permissions=True)
    return values


@frappe.whitelist()
def today_status():
    emp_info = get_employee_info()
    emp = emp_info.get("name")
    d = today()

    attendance = summarize_attendance(get_attendance_checkins(emp, d))
    cin = attendance["clock_in"]
    cout = attendance["clock_out"]

    visits = frappe.get_all(
        "Shop Visit",
        filters={"employee": emp, "visit_date": d},
        fields=[
            "name",
            "customer",
            "check_in_time",
            "check_out_time",
            "order_qty",
            "sales_order",
            "remarks",
            "distance_from_shop",
            "selfie",
            "shop_photo",
            "is_suspicious",
        ],
        order_by="check_in_time desc",
    )
    active_visit = None
    for v in visits:
        v["customer_name"] = frappe.db.get_value("Customer", v.customer, "customer_name")
        if not v.check_out_time and not active_visit:
            active_visit = v

    km = calc_km(emp, d)
    total_qty = sum(flt(v.get("order_qty", 0)) for v in visits)
    attach_visit_item_details(visits)

    return {
        "employee": emp,
        "employee_name": emp_info.get("employee_name") or emp,
        "date": d,
        "clock_in": cin,
        "clock_out": cout,
        "working_hours": attendance["working_hours"],
        "km_travelled": km,
        "shops_visited": len(visits),
        "total_order_qty": total_qty,
        "visits": visits,
        "active_visit": active_visit,
    }


@frappe.whitelist()
def get_daily_report(date=None):
    emp_info = get_employee_info()
    emp = emp_info.get("name")
    d = date or today()

    rep = build_daily_report(emp, d)
    visits = frappe.get_all(
        "Shop Visit",
        filters={"employee": emp, "visit_date": d},
        fields=[
            "name",
            "customer",
            "check_in_time",
            "check_out_time",
            "order_qty",
            "sales_order",
            "remarks",
            "distance_from_shop",
            "selfie",
            "shop_photo",
        ],
        order_by="check_in_time asc",
    )
    for v in visits:
        v["customer_name"] = frappe.db.get_value("Customer", v.customer, "customer_name")
    attach_visit_item_details(visits)

    return {
        "report": rep,
        "employee_name": emp_info.get("employee_name") or emp,
        "date": d,
        "visits": visits,
    }


@frappe.whitelist()
def get_past_reports(limit=30):
    emp = get_employee()
    return frappe.get_all(
        "Daily Report",
        filters={"employee": emp},
        fields=[
            "name",
            "report_date",
            "clock_in",
            "clock_out",
            "shops_visited",
            "total_order_qty",
            "km_travelled",
            "working_hours",
        ],
        order_by="report_date desc",
        limit=cint(limit) or 30,
    )


@frappe.whitelist()
def get_manager_dashboard():
    if not is_manager():
        frappe.throw("Access restricted to managers")

    d = today()
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "department", "user_id"],
        order_by="employee_name asc",
    )

    data = []
    for emp in employees:
        attendance = summarize_attendance(get_attendance_checkins(emp.name, d))
        cin = attendance["clock_in"]
        cout = attendance["clock_out"]

        visits = frappe.get_all(
            "Shop Visit",
            filters={"employee": emp.name, "visit_date": d},
            fields=["name", "order_qty", "check_in_time", "check_out_time"],
        )
        last_loc = frappe.get_all(
            "Location Log",
            filters={"employee": emp.name, "timestamp": ["between", [d, d + " 23:59:59"]]},
            fields=["latitude", "longitude", "timestamp", "battery"],
            order_by="timestamp desc",
            limit=1,
        )

        data.append({
            "employee": emp.name,
            "employee_name": emp.employee_name,
            "clock_in": cin,
            "clock_out": cout,
            "shops_visited": len(visits),
            "order_qty": sum(flt(v.order_qty) for v in visits),
            "last_location": last_loc[0] if last_loc else None,
        })

    return data


@frappe.whitelist()
def get_map_view_data(employee=None, date=None, territory=None):
    current_emp = get_employee()
    is_mgr = is_manager()

    target_emp = employee if (is_mgr and employee) else current_emp
    d = date or today()

    # 1. Active Salespeople for Live Map
    employees_data = []
    emp_list = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "department"],
        order_by="employee_name asc",
    )
    for emp in emp_list:
        attendance = summarize_attendance(get_attendance_checkins(emp.name, d))
        cin = attendance["clock_in"]
        cout = attendance["clock_out"]

        last_loc = frappe.get_all(
            "Location Log",
            filters={"employee": emp.name, "timestamp": ["between", [d, d + " 23:59:59"]]},
            fields=["latitude", "longitude", "timestamp", "battery", "speed", "accuracy"],
            order_by="timestamp desc",
            limit=1,
        )

        status = "Not Started"
        color = "grey"
        last_updated_time = None

        if attendance["is_on_duty"]:
            if last_loc:
                last_time = get_datetime(last_loc[0].timestamp)
                mins_ago = (get_datetime(now_datetime()) - last_time).total_seconds() / 60
                if mins_ago <= 70:
                    color = "green"
                    status = "On Duty"
                else:
                    color = "orange"
                    status = "GPS Off / Inactive"
            else:
                color = "orange"
                status = "GPS Off"
        elif cin:
            status = "Day Ended"
            color = "grey"
        else:
            status = "Not Started"
            color = "grey"

        if last_loc:
            last_updated_time = str(last_loc[0].timestamp)

        employees_data.append({
            "employee": emp.name,
            "employee_name": emp.employee_name or emp.name,
            "status": status,
            "color": color,
            "clock_in": str(cin) if cin else None,
            "clock_out": str(cout) if cout else None,
            "last_location": last_loc[0] if last_loc else None,
            "last_updated": last_updated_time,
        })

    # 2. Route Line points for selected salesperson and date
    route_points = frappe.get_all(
        "Location Log",
        filters={"employee": target_emp, "timestamp": ["between", [d, d + " 23:59:59"]]},
        fields=["latitude", "longitude", "timestamp", "speed", "battery", "accuracy"],
        order_by="timestamp asc",
    )
    for p in route_points:
        p["time"] = str(p.timestamp)[11:16]

    # 3. Visit Checkpoints for selected salesperson and date
    visits = frappe.get_all(
        "Shop Visit",
        filters={"employee": target_emp, "visit_date": d},
        fields=[
            "name",
            "customer",
            "check_in_time",
            "check_out_time",
            "latitude",
            "longitude",
            "order_qty",
            "sales_order",
            "is_suspicious",
            "distance_from_shop",
            "remarks",
        ],
        order_by="check_in_time asc",
    )
    for v in visits:
        v["customer_name"] = frappe.db.get_value("Customer", v.customer, "customer_name")
        waiting_mins = 0
        if v.check_in_time and v.check_out_time:
            waiting_mins = round((get_datetime(v.check_out_time) - get_datetime(v.check_in_time)).total_seconds() / 60)
        v["waiting_time"] = waiting_mins

    # 4. Shop Pins with Geofence Radius
    cust_filters = {"disabled": 0}
    if territory:
        cust_filters["territory"] = territory
    if not is_mgr:
        cust_filters["custom_assigned_employee"] = current_emp

    shops = frappe.get_all(
        "Customer",
        filters=cust_filters,
        fields=[
            "name",
            "customer_name",
            "custom_shop_name as shop_name",
            "custom_contact_person as contact_person",
            "custom_shop_latitude as latitude",
            "custom_shop_longitude as longitude",
            "custom_geofence_radius as geofence_radius",
            "territory",
            "customer_group",
            "custom_assigned_employee as assigned_employee",
            "mobile_no",
            "primary_address",
        ],
        limit=500,
    )
    for s in shops:
        if not s.get("shop_name"):
            s["shop_name"] = s.get("customer_name")
    valid_shops = [s for s in shops if s.latitude and s.longitude and (flt(s.latitude) != 0.0 or flt(s.longitude) != 0.0)]

    km = calc_km(target_emp, d)

    return {
        "selected_employee": target_emp,
        "selected_date": d,
        "is_manager": is_mgr,
        "salespeople": employees_data,
        "route": route_points,
        "visits": visits,
        "shops": valid_shops,
        "km_travelled": km,
    }