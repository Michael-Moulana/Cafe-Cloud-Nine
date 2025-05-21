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

