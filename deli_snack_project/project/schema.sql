-- =========================================================
-- Deli Snack - Esquema de base de datos (PostgreSQL)
-- Ejecuta este script completo una sola vez para crear
-- las tablas y datos de prueba que usa app.py
-- =========================================================

DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS pinatas CASCADE;
DROP TABLE IF EXISTS dulces CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- -----------------------------------------------------
-- Usuarios (login)
-- -----------------------------------------------------
CREATE TABLE usuarios (
    id_usuario     SERIAL PRIMARY KEY,
    nombre         VARCHAR(120) NOT NULL,
    correo         VARCHAR(150) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    rol            VARCHAR(20) NOT NULL DEFAULT 'cliente'  -- 'admin' o 'cliente'
);

-- -----------------------------------------------------
-- Dulces (inventario)
-- -----------------------------------------------------
CREATE TABLE dulces (
    id_dulce   SERIAL PRIMARY KEY,
    nombre     VARCHAR(120) NOT NULL,
    gramaje    VARCHAR(50),
    precio     NUMERIC(10,2) NOT NULL,
    categoria  VARCHAR(60),
    stock      INTEGER NOT NULL DEFAULT 0,
    activo     BOOLEAN NOT NULL DEFAULT TRUE
);

-- -----------------------------------------------------
-- Pinatas (bases disponibles)
-- -----------------------------------------------------
CREATE TABLE pinatas (
    id_pinata    SERIAL PRIMARY KEY,
    forma        VARCHAR(80) NOT NULL,
    tamano       VARCHAR(50),
    precio_base  NUMERIC(10,2) NOT NULL
);

-- -----------------------------------------------------
-- Pedidos
-- -----------------------------------------------------
CREATE TABLE pedidos (
    id_pedido     SERIAL PRIMARY KEY,
    id_usuario    INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    total         NUMERIC(10,2) NOT NULL DEFAULT 0,
    estado        VARCHAR(30) NOT NULL DEFAULT 'pendiente',
   fecha_hora TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =========================================================
-- Datos de prueba
-- =========================================================

-- Usuario administrador -> correo: admin@delisnack.com / password: admin123
-- Usuario cliente        -> correo: cliente@delisnack.com / password: cliente123
INSERT INTO usuarios (nombre, correo, password_hash, rol) VALUES
('Administrador', 'admin@delisnack.com', 'scrypt:32768:8:1$nzc2UcVPn1a7VadC$695209091c1193080c26c9c9471a246e3835d4dbea994d3082fa48ccd3db9342432c7f3389e6bcc02c976067765232ddeb963388f9bfbfbf6a507e80ff8aa980', 'admin'),
('Cliente Demo', 'cliente@delisnack.com', 'scrypt:32768:8:1$we0YSrlmWNoIiVsG$8d05d5f54b0b29090cfce12a990aa00ef88a3521588e2d517f7ca705f36241f0eec000e9992c82c94951421865b7c4b3e185483735114f1805e2c533dd189aa5', 'cliente');

INSERT INTO dulces (nombre, gramaje, precio, categoria, stock, activo) VALUES
('Paleta Payaso', '25g', 4.50, 'Paletas', 200, TRUE),
('Chicles Bomba', '10g', 2.00, 'Chicles', 300, TRUE),
('Cacahuate Japones', '50g', 8.00, 'Botana', 150, TRUE),
('Rielitos', '30g', 3.50, 'Chocolate', 180, TRUE),
('Duvalin', '20g', 6.00, 'Cremas', 120, TRUE),
('Pulparindo', '20g', 5.50, 'Enchilados', 160, TRUE);

INSERT INTO pinatas (forma, tamano, precio_base) VALUES
('Estrella', 'Chica', 80.00),
('Estrella', 'Grande', 150.00),
('Payaso', 'Mediana', 120.00),
('Unicornio', 'Grande', 180.00);
