import frappe

no_cache = 1
sitemap = 0

def get_context(context):
    context.csrf_token = frappe.session.csrf_token
    context.user = frappe.session.user
    return context