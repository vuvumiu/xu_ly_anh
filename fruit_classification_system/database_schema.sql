-- SQL schema for fruit classification system
-- Compatible with MySQL/MariaDB on XAMPP

-- Create database (adjust charset/collation if needed)
CREATE DATABASE IF NOT EXISTS fruit_classification
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE fruit_classification;

-- Products (e.g., tomato, watermelon)
CREATE TABLE IF NOT EXISTS products (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL,
  description VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_products_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Image captures or sessions
CREATE TABLE IF NOT EXISTS captures (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  product_id INT UNSIGNED NOT NULL,
  source VARCHAR(128) NULL COMMENT 'camera id, file path, etc',
  image_path VARCHAR(255) NULL,
  captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_captures_product_id (product_id),
  CONSTRAINT fk_captures_product
    FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Classification results
CREATE TABLE IF NOT EXISTS classifications (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  capture_id BIGINT UNSIGNED NOT NULL,
  product_id INT UNSIGNED NOT NULL,
  size_label VARCHAR(16) NULL,
  ripeness_label VARCHAR(16) NULL,
  defect_detected TINYINT(1) NOT NULL DEFAULT 0,
  defect_area_ratio DECIMAL(6,4) NULL,
  color_ratio_red DECIMAL(6,4) NULL,
  color_ratio_green DECIMAL(6,4) NULL,
  a_star_value DECIMAL(6,2) NULL,
  b_star_value DECIMAL(6,2) NULL,
  confidence DECIMAL(6,4) NULL,
  extra JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_classifications_capture_id (capture_id),
  KEY idx_classifications_product_id (product_id),
  CONSTRAINT fk_classifications_capture
    FOREIGN KEY (capture_id) REFERENCES captures(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_classifications_product
    FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed default product from config (optional, can be inserted from app)
-- INSERT IGNORE INTO products(name, description) VALUES ('tomato', 'Default tomato product');



