# contacts/views/__init__.py
from .auth      import admin_login_view, admin_logout_view
from .public    import landing_view, thank_you_view, category_change_request_view
from .contacts  import (contact_list_view, contact_add_view, contact_edit_view,
                        contact_delete_view, contact_detail_api,
                        category_add_view, category_toggle_view, category_delete_view)
from .exports   import export_csv_view, export_vcf_view
from .dashboard import (
    catrequest_apply_view, catrequest_reject_view,sk_dashboard_view, campaign_create_view, campaign_update_view,
                        campaign_delete_view,
    campaign_contacts_api,
    campaign_contact_status_api,
    campaign_increment_contacted, post_create_view, post_toggle_view,
                        post_delete_view, account_link_save_view, template_save_view, settings_toggle_education_view)
from .google    import google_oauth_start, google_oauth_callback, google_disconnect, google_sync
from .bulk      import (bulk_compose_view, bulk_history_view, bulk_send_api,
                        bulk_preview_api, bulk_status_api, service_request_view, service_request_thanks_view)
from .legal     import privacy_view, about_view, rules_view, delete_data_view
from .permissions import require_group




