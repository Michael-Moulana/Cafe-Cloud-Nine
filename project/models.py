from flask import current_app
from .db import mysql

def get_user_by_email(email):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM user WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    return user

def create_user(name, email, password, role="customer"):
    cursor = mysql.connection.cursor()
    query = "INSERT INTO user (name, email, password, role) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (name, email, password, role))
    mysql.connection.commit()
    cursor.close()

def update_user_details(user_id, name, email, phone, street_name, city, postcode, territory):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE user
        SET name = %s, email = %s, phone_number = %s
        WHERE userID = %s
    """, (name, email, phone, user_id))

    cur.execute("""
        SELECT addressID FROM user WHERE userID = %s
    """, (user_id,))
    result = cur.fetchone()

    if result['addressID']:  # If address exists for the user
        # Update the existing address
        cur.execute("""
            UPDATE address
            SET street_name = %s, city = %s, postcode = %s, territory = %s
            WHERE addressID = %s
        """, (street_name, city, postcode, territory, result['addressID']))
    else:  # If no address exists for the user
        # Insert a new address and link it to the user
        cur.execute("""
            INSERT INTO address (street_name, city, postcode, territory)
            VALUES (%s, %s, %s, %s)
        """, (street_name, city, postcode, territory))

        # Get the last inserted addressID and update the user table
        address_id = cur.lastrowid
        cur.execute("""
            UPDATE user
            SET addressID = %s
            WHERE userID = %s
        """, (address_id, user_id))



    mysql.connection.commit()
    cur.close()





# for admin page
def get_all_items():
    cur = mysql.connection.cursor()
    cur.execute("SELECT itemID, name, price, description, category, image FROM item")
    items = cur.fetchall()
    cur.close()
    return items

def get_item_by_id(item_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT itemID, name, price, description, category, image FROM item WHERE itemID = %s", (item_id,))
    item = cur.fetchone()
    cur.close()
    return item

def update_item_in_db(item_id, name, price, description, category, image):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE item
        SET name = %s, price = %s, description = %s, category = %s, image = %s
        WHERE itemID = %s
    """, (name, price, description, category, image, item_id))
    mysql.connection.commit()
    cur.close()

def add_item_to_db(name, price, description, category, image):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO item (name, price, description, category, image)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, price, description, category, image))
    mysql.connection.commit()
    cur.close()

def remove_item_from_db(item_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM item WHERE itemID = %s", (item_id,))
    mysql.connection.commit()
    cur.close()