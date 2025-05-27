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
    card_number VARCHAR(255),
    delivery_mode ENUM('eco-delivery', 'express-delivery', 'standard-delivery') NOT NULL,
    FOREIGN KEY (userID) REFERENCES user(userID) ON DELETE CASCADE,
	FOREIGN KEY (delivery_addressID) REFERENCES address(addressID) ON DELETE SET NULL
);

CREATE TABLE item (
    itemID INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    image VARCHAR(255),  
    category ENUM('drinks', 'breakfast', 'main course') NOT NULL
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


INSERT INTO item (name, price, description, category, image) VALUES
('Avocado on Toast', 20, 'Fresh avocado served on crispy toast.','breakfast', 'img/item1.jpeg'),
('French Toast', 19, 'Classic French toast with syrup.', 'breakfast', 'img/item2.jpeg'),
('Iced Coffee', 8, 'Chilled coffee with ice.', 'drinks', 'img/item3.jpeg'),
('Peach Iced Tea', 7, 'Refreshing peach-flavored iced tea.', 'drinks', 'img/item4.jpeg'),
('Pad Thai Noodles', 27, 'Spicy Pad Thai noodles with veggies.', 'main course', 'img/item5.jpeg'),
('Satay Chicken', 18, 'Grilled chicken skewers with satay sauce.', 'main course' , 'img/item6.jpeg');

INSERT INTO carousel (carouselImg_url) VALUES
('img/carousel-item1.jpg'), 
('img/carousel-item2.jpg'),
('img/carousel-item3.jpg'),
('img/carousel-item4.jpg');

/*add users manually before review insertion->
INSERT INTO user (name, phone_number, email, role, addressID) VALUES
('Alice Smith', '0412345678', 'alice@example.com', 'customer', 1),
('Charlie Lee', '0422334455', 'charlie@example.com', 'customer', 2);
INSERT INTO address (street_name, city, postcode, territory) VALUES
('123 George St', 'Brisbane', '4000', 'QLD'),
('456 Queen St', 'Sydney', '2000', 'NSW'),

+ make admin user*/

INSERT INTO review(userID, review_text) VALUES (1, "Amazing service and the coffee is always hot. Highly recommend!"), (2, "Great food! The eco-delivery option is pretty cool");




