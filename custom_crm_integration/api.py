import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def create_quotation_for_company(deal_name, company):
    """
    Creates an ERPNext Quotation from a Frappe CRM Deal,
    forcing the specified Company.
    """
    # 1. Permission and Validation Checks
    if not frappe.db.exists("Company", company):
        frappe.throw(f"ERPNext Company {company} does not exist or access is denied.")

    try:
        # Fetch the CRM Deal document
        deal = frappe.get_doc("Deal", deal_name)

        if not deal.organization and not deal.customer:
            frappe.throw("Deal must be linked to an Organization or Customer.")

        # Determine the target customer or lead based on the Deal
        if deal.customer:
            quotation_to = "Customer"
            customer_or_lead = deal.customer
        else: # Use Organization as Lead if no Customer exists yet
            quotation_to = "Lead"
            customer_or_lead = deal.organization

        # 2. Create the Quotation document
        quotation = frappe.new_doc("Quotation")

        # --- Core Data Mapping ---
        quotation.company = company  # CRITICAL: Sets the specific ERPNext company
        quotation.quotation_to = quotation_to

        if quotation_to == "Customer":
            quotation.customer = customer_or_lead
        else:
            quotation.party_name = customer_or_lead  # Use party_name for Leads/Organizations

        quotation.crm_deal = deal_name
        quotation.title = f"Quotation for Deal: {deal.title} ({company})"
        quotation.transaction_date = nowdate()

        # Set Validity Date (e.g., 30 days)
        quotation.valid_till = frappe.utils.add_days(nowdate(), 30)

        # 3. Handle Items (Simplified)
        # NOTE: This requires custom logic based on how you track products in the CRM Deal.
        # For a simple test, you can manually add one item:
        # if deal.get('products'):
        #     for item in deal.products:
        #         quotation.append('items', {
        #             'item_code': item.item_code,
        #             'qty': item.qty,
        #             'rate': item.rate
        #         })

        # 4. Insert the Quotation
        quotation.insert(ignore_permissions=True)
        frappe.db.commit()

        return quotation.name

    except Exception as e:
        frappe.log_error(title="Multi-Company Quotation Error", message=frappe.get_traceback())
        frappe.throw(f"Failed to create Quotation: {str(e)}")