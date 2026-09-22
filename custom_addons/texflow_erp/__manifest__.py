{
    'name': 'TexFlow ERP',
    'version': '19.0.1.0.0',
    'summary': 'Textile and Garment Manufacturing & Distribution ERP',
    'description': """
TexFlow ERP
===========

A custom ERP solution for textile and garment manufacturing businesses.

Main business areas:
- Manufacturing
- Inventory
- Purchase
- Sales
- Warehouse
- Quality Control
- Maintenance
- Distribution
""",
    'category': 'Manufacturing',
    'author': 'Farzana Islam',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
    ],
'data': [
    'security/ir.model.access.csv',
    'data/production_order_sequence.xml',
    'data/production_stage_data.xml',
    'views/production_stage_views.xml',
    'views/production_order_search_views.xml',
    'views/production_order_report_views.xml',
    'views/production_order_views.xml',
    'views/production_order_menu.xml',
],
    'demo': [],
    'installable': True,
    'application': True,
}
