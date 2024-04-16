# 1st Party Libraries
import sys

# 3rd Party Libraries
import json
import importlib
import subprocess
import numpy as np
import pandas as pd
from pymongo import MongoClient

def products_db(selection: int):
    """
    Description:
    ------------
    - Function in charge of auto installing Python packages for a successful functioning of the program overall.
    - Access to Mongo to create a Database based on the information contained in the .json dictionary.

    Parameters:
    -----------
    - Selection: Type int, no default valuem used to get the ID of a product in this case.

    Returns:
    --------
    - Dictionary with the information about the product.
    """
    # Installing PyMongo in case it is not installed
    if importlib.util.find_spec("pymongo") == None:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymongo'])
    
    # Connecting to MongoDB
    client = MongoClient('mongodb://localhost:27017/') 

    # Checking if the Products MongoDB exists
    if 'list_products' in client.list_database_names() and 'products' in client['list_products'].list_collection_names():
        pass

    # Defining DB and Collections names
    db = client['list_products']
    collection = db['products']

    # Loading JSON file for DB creation
    with open('assets/products.json') as file:
        data = json.load(file)

    # Insert the data into the collection
    collection.insert_many([data])

    # Query for documents where the id of the product is 1
    result = collection.find_one({"products.id": selection})

    # Extract product information
    if result:
        product = next(item for item in result['products'] if item['id'] == selection)

    # Closing Connection
    client.close()

    # Providing the info regarding to the expected item
    return product

@staticmethod
def desired_product():
    """
    Description:
    ------------
    - Function in charge of displaying a menu in which the user is capable of selecting the items and amount of drinks to order
    - Information then is stored in DataFrames for its manipulation.

    Parameters:
    -----------
    - None: Static method.

    Returns:
    --------
    - No returns, prints bill.
    """

    # Loading JSON file for DB creation
    with open('assets/products.json') as file:
        data = json.load(file)

    # Initializing Empty lists for information storage
    quantity = []
    products = []

    # Variable is in charge of storing the data contained in the .json dictionary
    variable = ''
    
    # The dictionary saved in assets will be re-utilized for priting the options available for the user
    variable = ''.join([str(elements['id']) + '-> '  + elements['name'] + '\n    Descripción: ' + elements['description'] + '\n    Precio: ' + str("${:,.2f}".format(elements['price'])) + '\n' for elements in data['products']])
    
    # The user is required to enter the id of the drink
    option = input(f"""Bienvenido al menú de bebidas\n\nEntre las siguientes opciones:\n\n{variable}\nIngrese la bebida a seleccionar: """)
    
    # The user is required to enter the amount of drinks
    amount = input("\nIngrese la cantidad de bebidas: ")
    
    # The dictionary retrieved from the products_db function is saved afterwards in a empty list
    products.append(products_db(int(option)))
    
    # The dictionary is saved into a DataFrame for data manipulation
    df = pd.DataFrame(products)

    # The amount is saved in 
    quantity.append(int(amount))

    # In case if the user would like to order something else
    new_option = input("¿Desea incluir alguna otra bebida? Ingrese aquí (Si/No)")
    
    # A while loop is habilitated for selecting as many options and quantities as preferred, the loop is exited as soon as 'No' is entered
    while new_option == 'Si' or new_option == 'si':
        # Input with the options indicated earlier is presented again
        new_option = input(f"""Entre las siguientes opciones:\n\n{variable}\nIngrese la bebida a seleccionar: """)
        # Dictionary from products_db is re-utilized for storing new rows in the DataFrame
        products.append(products_db(int(new_option)))
        # Once again amount of drinks is shown up
        amount = input("\nIngrese la cantidad de bebidas: ")
        # Quantity is appended in the empty list
        quantity.append(int(amount))
        # Input for exiting while loop or to either continuing ordering other drinks
        new_option = input("¿Desea incluir alguna otra bebida? Ingrese aquí (Si/No)")
    
    # Setting DataFrame for Data Manipulation
    df = pd.DataFrame(products)
    
    # Incorporating new column called quantity
    df['quantity'] = quantity

    # Resorting columns order
    df = df[['id', 'name', 'description', 'quantity', 'price']]
    
    # Grouping by product name and price for further calculations to perform
    df_new = df.groupby(['name', 'price'])['quantity'].sum().reset_index()

    # Renaming headers to set up bill
    df_new = df_new.rename({"name": "Producto", "price": "Precio Unidad", "quantity": "Cantidad"}, axis = 1)

    # Calculating subtotal
    df_new['Subtotal'] = df_new['Precio Unidad'] * df_new['Cantidad']

    # Adding all elements from the Subtotal column
    subtotal = df_new['Subtotal'].sum()

    # Calculating IVA
    iva = float(subtotal) * (19 / 100)

    # Calculating total
    total = float(subtotal) + float(iva)

    # Formatting as currencies
    subtotal = "${:,.2f}".format(subtotal)
    iva = "${:,.2f}".format(iva)
    total = "${:,.2f}".format(total)
    df_new['Precio Unidad'] = df_new['Precio Unidad'].apply(lambda x: "${:,.2f}".format((x)))
    df_new['Subtotal'] = df_new['Subtotal'].apply(lambda x: "${:,.2f}".format((x)))

    total_values = pd.DataFrame([subtotal, iva, total], columns = None, index = ['Subtotal', 'IVA', 'Total'])
    # Presenting how the bill will look like
    print(f"""
*****************************************************
*********************Bebidas SAS*********************
******************NIT: 999.999.000-1*****************
*******************Orden de Compra*******************
{df_new.to_string(index = False)}

*****************************************************
{total_values.to_string(columns = None, header = False)}""")
    
    # Input to identify if the user agrees with the result
    final_option = input("¿Desea proceder con el pago? (Si/No): ")

    # Showing as an example that the payment went through
    if final_option == 'Si' or final_option == 'si':
        print("\n\nPago exitoso, feliz dia.")
    
    # Cancelling process
    else:
        print("\n\nLo sentimos, proceso cancelado.")