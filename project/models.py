from flask import current_app
from .db import mysql
from datetime import datetime

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

    if result['addressID']:  
        cur.execute("""
            UPDATE address
            SET street_name = %s, city = %s, postcode = %s, territory = %s
            WHERE addressID = %s
        """, (street_name, city, postcode, territory, result['addressID']))
    else:  
        cur.execute("""
            INSERT INTO address (street_name, city, postcode, territory)
            VALUES (%s, %s, %s, %s)
        """, (street_name, city, postcode, territory))

        address_id = cur.lastrowid
        cur.execute("""
            UPDATE user
            SET addressID = %s
            WHERE userID = %s
        """, (address_id, user_id))



    mysql.connection.commit()
    cur.close()

def get_all_items():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM item")
    items = cur.fetchall()
    cur.close()
    return items

def get_carousels():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM carousel")
    carousels = cur.fetchall()
    cur.close()
    return carousels

def search_items(query='', category=''):
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM item"
    filters = []
    params = []

    if query:
        filters.append("name LIKE %s")
        params.append(f"%{query}%")
    if category:
        filters.append("category = %s")
        params.append(category)
    if filters:
        sql += " WHERE " + " AND ".join(filters)

    cur.execute(sql, params)
    results = cur.fetchall()
    cur.close()
    return results


def get_item_by_id(item_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT itemID, name, price, description, category, image FROM item WHERE itemID = %s", (item_id,))
    item = cur.fetchone()
    cur.close()
    return item

def get_user_details_by_id(user_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.name, u.email, u.phone_number,
               u.addressID
        FROM user u
        WHERE u.userID = %s
    """, (user_id,))
    user_details = cur.fetchone()
    cur.close()
    return user_details

def get_user_addresses(user_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.addressID, a.street_name, a.city, a.postcode, a.territory 
        FROM address a
        JOIN user u ON u.addressID = a.addressID 
        WHERE u.userID = %s
    """, (user_id,))
    addresses = cur.fetchall()
    cur.close()
    return addresses

def create_order(user_id, order_date, address_id, status, total, payment_method, delivery_option):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO user_order (userID, order_date, delivery_addressID, status, total_amount, 
                                payment_method, delivery_mode)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        datetime.now(),
        address_id,
        'pending',
        total,
        payment_method,
        delivery_option
    ))
    order_id = cur.lastrowid
    mysql.connection.commit()
    return order_id

def add_order_items(order_id, items):
    from .db import mysql
    cur = mysql.connection.cursor()
    for item in items:
        cur.execute("""
            INSERT INTO order_items (orderID, itemID, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (
            order_id,
            item['itemID'],
            item['quantity'],
            item['price']
        ))
    mysql.connection.commit()
    cur.close()


def get_user_orders(user_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT o.orderID, o.order_date, o.total_amount, o.status,
               i.name AS item_name, oi.quantity, oi.unit_price, oi.total_price
        FROM user_order o
        JOIN order_items oi ON o.orderID = oi.orderID
        JOIN item i ON oi.itemID = i.itemID
        WHERE o.userID = %s
        ORDER BY o.order_date DESC
    """, (user_id,))
    orders = cur.fetchall()
    cur.close()
    return orders

def get_user_profile(user_id):
    from .db import mysql
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.name, u.email, u.phone_number,
               a.street_name, a.city, a.postcode, a.territory
        FROM user u
        LEFT JOIN address a ON u.addressID = a.addressID
        WHERE u.userID = %s
    """, (user_id,))
    user = cur.fetchone()
    cur.close()
    return user

# for admin page 
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

def get_reviews():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.review_text, u.name
        FROM review r
        LEFT JOIN user u ON r.userID = u.userID
    """)
    reviews = cur.fetchall()
    cur.close()
    return reviews

def insert_inquiry(name, email, subject, message):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO inquiry (name, email, subject, message, date_submitted, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, email, subject, message, datetime.now(), 'pending'))
    mysql.connection.commit()
    cur.close()

def insert_review(user_id, review_text):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO review (userID, review_text)
        VALUES (%s, %s)
    """, (user_id, review_text))
    mysql.connection.commit()
    cur.close()

# admin - orders
def get_all_user_orders():
    query = """
        SELECT 
            o.orderID,
            o.order_date,
            o.status,
            o.total_amount,
            o.payment_method,
            o.delivery_mode,
            u.name AS user_name,
            u.email AS user_email,
            u.phone_number,
            CONCAT_WS(', ', a.street_name, a.city, a.postcode, a.territory) AS delivery_address
        FROM user_order o
        JOIN user u ON o.userID = u.userID
        LEFT JOIN address a ON o.delivery_addressID = a.addressID
        ORDER BY o.order_date DESC
    """

    cur = mysql.connection.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()

    # Format each row
    orders = []
    for row in rows:
        # Format datetime and decimal
        row['order_date'] = row['order_date'].strftime("%d %b %Y, %H:%M") if row['order_date'] else 'N/A'
        row['total_amount'] = f"${float(row['total_amount']):.2f}" if row['total_amount'] is not None else "$0.00"
        orders.append(row)

    return orders

def get_order_items(order_id):
    cur = mysql.connection.cursor()
    query = """
        SELECT 
            i.name AS item_name,
            oi.quantity,
            oi.unit_price,
            oi.total_price
        FROM order_items oi
        JOIN item i ON oi.itemID = i.itemID
        WHERE oi.orderID = %s
    """
    cur.execute(query, (order_id,))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()

    return [dict(zip(columns, row)) for row in rows]

def update_order_status(order_id, new_status):
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user_order SET status = %s WHERE orderID = %s", (new_status, order_id))
        mysql.connection.commit()
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise
    finally:
        cur.close()

        
def get_category_enum_values():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT COLUMN_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'item' AND COLUMN_NAME = 'category'
    """)
    row = cur.fetchone()
    cur.close()

    if row:
        enum_str = row['COLUMN_TYPE']  # e.g., "enum('drinks','breakfast','main course')"
        # Extract inside enum(...)
        enum_values = enum_str[6:-1]  # remove "enum(" from start and ")" from end
        # Split while preserving phrases with spaces
        values = [v.strip("'") for v in enum_values.split(",")]
        return values
    return []

def update_enum_categories(new_enum_list):
    """
    Updates the ENUM values of the 'category' column in 'item' table.
    WARNING: this alters the table structure.
    """
    enum_str = ','.join([f"'{val}'" for val in new_enum_list])
    cur = mysql.connection.cursor()
    cur.execute(f"""
        ALTER TABLE item MODIFY COLUMN category ENUM({enum_str}) NOT NULL
    """)
    mysql.connection.commit()
    cur.close()
