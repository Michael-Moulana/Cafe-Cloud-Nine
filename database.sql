-- Database creation
CREATE DATABASE a2_db;

use a2_db;

SET SQL_SAFE_UPDATES = 0;

CREATE TABLE address (
    addressID INT AUTO_INCREMENT PRIMARY KEY,
    street_name VARCHAR(255),
    city VARCHAR(100),
    postcode VARCHAR(20),
    territory VARCHAR(100)
);

CREATE TABLE user (
    userID INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255),
    phone_number VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    role ENUM('admin', 'customer') NOT NULL DEFAULT 'customer',
    addressID INT,
    FOREIGN KEY (addressID) REFERENCES address(addressID)
);

CREATE TABLE user_order (
    orderID INT AUTO_INCREMENT PRIMARY KEY,
    userID INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivery_addressID INT,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(10, 2),
    payment_method ENUM('cash', 'card', 'apple_pay') NOT NULL,
    delivery_mode ENUM('eco-delivery', 'express-delivery', 'standard-delivery') NOT NULL,
    FOREIGN KEY (userID) REFERENCES user(userID) ON DELETE CASCADE,
	FOREIGN KEY (delivery_addressID) REFERENCES address(addressID) ON DELETE SET NULL
);

CREATE TABLE category (
    categoryID INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL
)ENGINE=InnoDB;

CREATE TABLE item (
    itemID INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    image VARCHAR(255),  
    categoryID INT,
    FOREIGN KEY (categoryID) REFERENCES category(categoryID) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE order_items (
    order_itemID INT AUTO_INCREMENT PRIMARY KEY,
    orderID INT NOT NULL,
    itemID INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    FOREIGN KEY (orderID) REFERENCES user_order(orderID) ON DELETE CASCADE,
    FOREIGN KEY (itemID) REFERENCES item(itemID) ON DELETE CASCADE
);

CREATE TABLE inquiry (
    inquiryID INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'resolved', 'ignored') DEFAULT 'pending',
    response TEXT DEFAULT NULL
) ENGINE=InnoDB;

CREATE TABLE review(
    reviewID INT AUTO_INCREMENT PRIMARY KEY,
    userID INT NOT NULL,
    review_text TEXT NOT NULL,
    FOREIGN KEY (userID) REFERENCES user(userID) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE carousel (
    carouselImgID INT auto_increment primary key,
    carouselImg_url TEXT
) ENGINE=InnoDB;

-- Triggers 
DELIMITER $$

CREATE TRIGGER update_total_amount_after_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE user_order
    SET total_amount = (
        SELECT SUM(total_price)
        FROM order_items
        WHERE orderID = NEW.orderID
    )
    WHERE orderID = NEW.orderID;
END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER update_total_amount_after_update
AFTER UPDATE ON order_items
FOR EACH ROW
BEGIN
    UPDATE user_order
    SET total_amount = (
        SELECT SUM(total_price)
        FROM order_items
        WHERE orderID = NEW.orderID
    )
    WHERE orderID = NEW.orderID;
END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER update_total_amount_after_delete
AFTER DELETE ON order_items
FOR EACH ROW
BEGIN
    UPDATE user_order
    SET total_amount = (
        SELECT SUM(total_price)
        FROM order_items
        WHERE orderID = OLD.orderID
    )
    WHERE orderID = OLD.orderID;
END $$

DELIMITER ;

-- Sample data

INSERT INTO category (category_name) VALUES ('breakfast'), ('main course'), ('drinks'), ('dessert');

INSERT INTO item (name, price, description, categoryID, image) VALUES
('Avocado on Toast', 20, 'Fresh avocado served on crispy toast.', 1, 'img/item1.jpeg'),
('French Toast', 19, 'Classic French toast with syrup.', 1, 'img/item2.jpeg'),
('Iced Coffee', 8, 'Chilled coffee with ice.', 3, 'img/item3.jpeg'),
('Peach Iced Tea', 7, 'Refreshing peach-flavored iced tea.', 3, 'img/item4.jpeg'),
('Pad Thai Noodles', 27, 'Spicy Pad Thai noodles with veggies.', 2, 'img/item5.jpeg'),
('Satay Chicken', 18, 'Grilled chicken skewers with satay sauce.', 2 , 'img/item6.jpeg'),
('Chicken Burger', 24, 'Grilled chicken patty with lettuce, tomato, and mayo in a toasted bun.', 2, 'img/item7.jpeg'),
('Chocolate Brownie', 10, 'Rich and fudgy chocolate brownie.', 4, 'img/item8.jpeg'), 
('Matcha Cheesecake', 13, 'Creamy cheesecake with a matcha twist.', 4, 'img/item9.jpeg');

INSERT INTO carousel (carouselImg_url) VALUES
('img/carousel-item1.jpg'), 
('img/carousel-item2.jpg'),
('img/carousel-item3.jpg'),
('img/carousel-item4.jpg');

INSERT into address(street_name, city, postcode, territory) VALUES 
('123 Queen St', 'Brisbane', '1234', 'QLD'),
('123 George St', 'Brisbane', '5678', 'QLD'),
('123 Queen St', 'Sydney', '9876', 'NSW'); 

INSERT INTO user (name, password, phone_number, email, role, addressID) VALUES
('Alice Smith', 'scrypt:32768:8:1$HZIFscB9KSrseSKv$2a0f3a394dc73d47ea9c8e51bf8892ca2b8c670237c8a7d7fc8eb65714eb2be8b6edea71292502a66ab23a0e7ab33d3ca5735b80ae531f3cdb231a46ef5f2e5f', '0412233445', 'alice@example.com', 'customer', 1),
('Charlie Lee', 'scrypt:32768:8:1$w0lgzSAydOFhvWzC$ad4d06bd06a61c85f550d05ac89a9466b5bdb21e09f74a5e7c144ae204ed1b9e9de2114e5dec13bca533b3d3c3c9e81faa785a4e8fabcd1e8da4afc9df3f14db', '0412345678', 'charlie@example.com', 'customer', 2),
('John Mathews', 'scrypt:32768:8:1$MqHfGY1ZxZG3EO5T$1ba7efa65307e488467bc1e3b6eabe2990477761f26ec66919215df71bc258ced2f20c544a7bf1f0e3716f89305e644f51a231ee7a1d8b9fb3ae94e350645d5d', '0498765432', 'john@example.com', 'customer', 3);
INSERT INTO user (name, password, email, role) VALUES ('Admin', 'scrypt:32768:8:1$wi5jjgtbyaWZChwy$352204aa2dc1bcfe33cb475f1071f658090c5190344a7198436f8fdf7b9e283fb325d57422353dfdfa1c026ec6c5fcac53b08f43c215455a19abcee8c6528f07', 'admin@example.com', 'admin');

INSERT INTO review(userID, review_text) VALUES (1, "Amazing service and the coffee is always hot. Highly recommend!"), (2, "Great food! The eco-delivery option is pretty cool");

INSERT INTO user_order(userID, order_date, delivery_addressID, status, total_amount, payment_method, delivery_mode) VALUES
(1, '2025-05-31 19:48:19', 1, 'pending', 27.00, 'card', 'standard-delivery'),
(1, '2025-05-31 19:48:43', 1, 'pending', 34.00, 'apple_pay', 'express-delivery'),
(2, '2025-05-31 19:50:04', 2, 'pending', 45.00, 'cash', 'eco-delivery'),
(3, '2025-05-31 19:51:57', 3, 'pending', 39.00, 'cash', 'standard-delivery');

INSERT INTO order_items(orderID, itemID, quantity, unit_price) VALUES
(1, 2, 1, 19.00),
(1, 3, 1, 8.00),
(2, 1, 1, 20.00),
(2, 4, 2, 7.00),
(3, 5, 1, 27.00),
(3, 6, 1, 18.00),
(4, 3, 2, 8.00),
(4, 8, 1, 10.00),
(4, 9, 1, 13.00);
