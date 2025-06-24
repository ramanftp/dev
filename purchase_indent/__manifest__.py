{
    'name': 'Purchase Indent',
    'version': '1.1',
    'summary': 'End-to-end purchase indent workflow with approval system',
    'description': """
        Complete purchase indent workflow with multi-level approvals,
        budget controls, and audit tracking.
    """,
    'author': 'Raman Marikanti',
    'website': 'https://www.ftprotech.com',
    'category': 'Operations/Project',
    'depends': ['project', 'purchase','account','hr','mail'],
    'data': [
        'security/procurement_security.xml',
        'security/ir.model.access.csv',
        'data/procurement_sequence.xml',
        # 'data/mail_template_data.xml',
        'views/purchase_indent_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',

}