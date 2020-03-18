{
    'name': 'Stock Location Limit Capacity Advance',
    'version': '12.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'erickalvino@gmail.com',
    'website': "https://github.com/OCA/stock-logistics-warehouse",
    'summary': """Add a limit by product quantity on a stock location,
                And Also Usage Quantity and Capacity Remainding
                This limit can later be used to track the capacity
                available of the location.""",
    'category': 'Warehouse',
    'development_status': 'Alfa',
    'maintainers': ['erickalvino'],
    'depends': [
        'stock','stock_location_limit_product'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_location_view.xml',
    ],
    'installable': True,
}
