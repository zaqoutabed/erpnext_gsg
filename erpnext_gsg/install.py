def after_install():
    from erpnext_gsg.utils import create_taxs_account_head

    create_taxs_account_head()
