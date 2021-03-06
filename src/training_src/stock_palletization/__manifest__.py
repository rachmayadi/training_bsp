{
    "name": "Stock Palletization",
    "summary": "Split the number of items to several package/pallet]",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "http://gitlab.binasanprima.com",
    "author": "erickalvino@gmail.com",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ['stock','multi_step_wizard','stock_location_limit_product', 'stock_location_limit_product_advance'],
    "data": ['views/stock_move_views.xml','views/pallet_wizard_views.xml', 'views/location_capacity_views.xml'],
    "demo": [],
}
