-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: 127.0.0.1    Database: farmafactura
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit_log`
--

DROP TABLE IF EXISTS `audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `audit_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` datetime DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `operation` varchar(100) DEFAULT NULL,
  `module` varchar(100) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `status` varchar(20) DEFAULT 'OK',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=120 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_log`
--

LOCK TABLES `audit_log` WRITE;
/*!40000 ALTER TABLE `audit_log` DISABLE KEYS */;
INSERT INTO `audit_log` VALUES (1,'2026-06-17 17:55:58','admin','LOGIN','auth','Usuario: admin','OK'),(2,'2026-06-17 18:10:56','admin','LOGIN','auth','Usuario: admin','OK'),(3,'2026-06-17 20:29:17','admin','LOGIN','auth','Usuario: admin','OK'),(4,'2026-06-21 09:26:21','sistema','LOGIN','auth','Usuario: admin1','FALLIDO'),(5,'2026-06-21 09:26:27','admin','LOGIN','auth','Usuario: admin','OK'),(6,'2026-06-21 13:46:47','admin','LOGIN','auth','Usuario: admin','OK'),(7,'2026-06-21 13:56:05','admin','LOGIN','auth','Usuario: admin','OK'),(8,'2026-06-21 13:57:27','admin','LOGIN','auth','Usuario: admin','OK'),(9,'2026-06-21 14:02:24','admin','LOGIN','auth','Usuario: admin','OK'),(10,'2026-06-21 14:03:54','admin','LOGIN','auth','Usuario: admin','OK'),(11,'2026-06-21 14:20:38','admin','LOGIN','auth','Usuario: admin','OK'),(12,'2026-06-21 17:56:43','admin','LOGIN','auth','Usuario: admin','OK'),(13,'2026-06-23 12:44:45','admin','LOGIN','auth','Usuario: admin','OK'),(14,'2026-06-23 12:46:14','admin','LOGIN','auth','Usuario: admin','OK'),(15,'2026-06-23 14:03:55','admin','LOGIN','auth','Usuario: admin','OK'),(16,'2026-06-23 14:36:13','caja1','LOGIN','auth','Usuario: caja1','OK'),(17,'2026-06-23 14:38:20','sistema','LOGIN','auth','Usuario: admin','FALLIDO'),(18,'2026-06-23 14:38:24','admin','LOGIN','auth','Usuario: admin','OK'),(19,'2026-06-23 20:47:44','admin','LOGIN','auth','Usuario: admin','OK'),(20,'2026-06-23 20:51:19','admin','LOGIN','auth','Usuario: admin','OK'),(21,'2026-06-23 21:15:28','admin','LOGIN','auth','Usuario: admin','OK'),(22,'2026-06-23 21:18:57','admin','LOGIN','auth','Usuario: admin','OK'),(23,'2026-06-23 21:22:51','admin','LOGIN','auth','Usuario: admin','OK'),(24,'2026-06-23 21:47:15','admin','LOGIN','auth','Usuario: admin','OK'),(25,'2026-06-23 22:00:19','admin','LOGIN','auth','Usuario: admin','OK'),(26,'2026-06-23 22:18:14','admin','LOGIN','auth','Usuario: admin','OK'),(27,'2026-06-23 23:01:37','admin','LOGIN','auth','Usuario: admin','OK'),(28,'2026-06-24 19:06:23','sistema','LOGIN','auth','Usuario: admin','FALLIDO'),(29,'2026-06-24 19:06:41','admin','LOGIN','auth','Usuario: admin','OK'),(30,'2026-06-24 20:43:37','admin','PRODUCTO_AGREGADO','inventario','#1 \'paracetamol\' | Stock:20 | Precio:$10.0','OK'),(31,'2026-06-24 22:49:50','sistema','LOGIN','auth','Usuario: admin123','FALLIDO'),(32,'2026-06-24 22:49:58','admin','LOGIN','auth','Usuario: admin','OK'),(33,'2026-06-24 22:51:23','admin','LOTE_REGISTRADO','lotes','Producto #1 \'paracetamol\' | Lote: LOT-20260624-0001 | Qty: 123','OK'),(34,'2026-06-25 12:16:36','admin','LOGIN','auth','Usuario: admin','OK'),(35,'2026-06-25 12:22:29','admin','PRODUCTO_AGREGADO','inventario','#2 \'winazorb\' | Stock:12312 | Precio:$20.0','OK'),(36,'2026-06-25 12:25:48','admin','LOTE_REGISTRADO','lotes','Producto #2 \'winazorb\' | Lote: LOT-20260625-0001 | Qty: 123','OK'),(37,'2026-06-25 12:46:21','admin','LOGIN','auth','Usuario: admin','OK'),(38,'2026-06-25 12:51:51','admin','LOGIN','auth','Usuario: admin','OK'),(39,'2026-06-25 12:54:56','admin','LOGIN','auth','Usuario: admin','OK'),(40,'2026-06-25 13:01:28','admin','LOGIN','auth','Usuario: admin','OK'),(41,'2026-06-25 13:09:39','admin','LOGIN','auth','Usuario: admin','OK'),(42,'2026-06-26 00:16:33','admin','LOGIN','auth','Usuario: admin','OK'),(43,'2026-06-26 00:19:36','admin','LOGIN','auth','Usuario: admin','OK'),(44,'2026-06-26 00:20:22','admin','PRODUCTO_AGREGADO','inventario','#3 \'asdasd\' | Stock:123 | Precio:$123.0','OK'),(45,'2026-06-29 13:13:09','admin','LOGIN','auth','Usuario: admin','OK'),(46,'2026-06-29 13:17:07','admin','LOGIN','auth','Usuario: admin','OK'),(47,'2026-06-29 13:18:49','admin','LOGIN','auth','Usuario: admin','OK'),(48,'2026-06-29 20:20:51','admin','LOGIN','auth','Usuario: admin','OK'),(49,'2026-06-30 23:27:15','sistema','LOGIN','auth','Usuario: admin','FALLIDO'),(50,'2026-06-30 23:27:20','admin','LOGIN','auth','Usuario: admin','OK'),(51,'2026-06-30 23:48:11','admin','LOGIN','auth','Usuario: admin','OK'),(52,'2026-07-01 00:54:42','admin','LOGIN','auth','Usuario: admin','OK'),(53,'2026-07-01 01:14:43','admin','LOGIN','auth','Usuario: admin','OK'),(54,'2026-07-01 01:18:27','admin','LOGIN','auth','Usuario: admin','OK'),(55,'2026-07-01 12:06:26','sistema','LOGIN','auth','Usuario: admin','FALLIDO'),(56,'2026-07-01 12:06:33','admin','LOGIN','auth','Usuario: admin','OK'),(57,'2026-07-01 12:07:32','admin','LOGIN','auth','Usuario: admin','OK'),(58,'2026-07-01 12:11:14','admin','LOTE_EDITADO','lotes','Lote #1 \'LOT-20260624-0001\' | Qty: 123→123 | Estado: activo','OK'),(59,'2026-07-01 12:11:14','admin','LOTE_EDITADO','lotes','Lote #1 \'LOT-20260624-0001\' | Qty: 123→123 | Estado: activo','OK'),(60,'2026-07-01 12:11:57','admin','LOTE_EDITADO','lotes','Lote #1 \'LOT-20260624-0001\' | Qty: 123→123 | Estado: activo','OK'),(61,'2026-07-01 12:13:04','admin','LOGIN','auth','Usuario: admin','OK'),(62,'2026-07-01 12:20:46','admin','LOGIN','auth','Usuario: admin','OK'),(63,'2026-07-01 12:53:52','admin','LOGIN','auth','Usuario: admin','OK'),(64,'2026-07-01 12:54:44','admin','LOGIN','auth','Usuario: admin','OK'),(65,'2026-07-01 12:58:51','admin','LOGIN','auth','Usuario: admin','OK'),(66,'2026-07-01 13:14:12','admin','LOGIN','auth','Usuario: admin','OK'),(67,'2026-07-01 13:15:23','admin','LOGIN','auth','Usuario: admin','OK'),(68,'2026-07-01 13:17:56','admin','PRODUCTO_AGREGADO','inventario','#5 \'paracetamol\' | Stock:123 | Precio:$10.0','OK'),(69,'2026-07-01 13:18:06','admin','PRODUCTO_AGREGADO','inventario','#6 \'paracetamol\' | Stock:123 | Precio:$10.0','OK'),(70,'2026-07-01 13:26:47','admin','LOGIN','auth','Usuario: admin','OK'),(71,'2026-07-01 13:29:31','admin','VENTA','facturacion','Factura #000002 | Cliente: Darwin | Total: $283.20 | Pago: Efectivo | Items: 1','OK'),(72,'2026-07-01 13:30:37','admin','VENTA','facturacion','Factura #000003 | Cliente: Darwin | Total: $283.20 | Pago: Efectivo | Items: 1','OK'),(73,'2026-07-01 13:42:32','admin','LOGIN','auth','Usuario: admin','OK'),(74,'2026-07-01 13:45:36','admin','LOGIN','auth','Usuario: admin','OK'),(75,'2026-07-01 13:51:54','admin','VENTA','facturacion','Factura #000004 | Cliente: Darwin | Total: $47.20 | Pago: Efectivo | Items: 1','OK'),(76,'2026-07-01 14:24:37','admin','LOGIN','auth','Usuario: admin','OK'),(77,'2026-07-01 14:28:27','admin','PRODUCTO_AGREGADO','inventario','#8 \'azetaminofen\' | Stock:50 | Precio:$15.0','OK'),(78,'2026-07-01 14:31:49','admin','PRECIO_CAMBIADO','inventario','Producto #6 \'azetaminofen\' | Precio: $15.00 → $10.00','OK'),(79,'2026-07-01 14:46:30','admin','PRODUCTO_AGREGADO','inventario','#11 \'acetaminofen\' | Stock:200 | Precio:$15.0','OK'),(80,'2026-07-01 14:56:00','admin','LOTE_REGISTRADO','lotes','Producto #7 \'acetaminofen\' | Lote: 200-321 | Qty: 10000','OK'),(81,'2026-07-01 15:00:19','admin','LOTE_EDITADO','lotes','Lote #9 \'200-321\' | Qty: 10000→10000 | Estado: activo','OK'),(82,'2026-07-01 15:04:03','admin','PRODUCTO_AGREGADO','inventario','#13 \'aceyainofen\' | Stock:10000 | Precio:$15.0','OK'),(83,'2026-07-01 15:07:02','admin','LOTE_REGISTRADO','lotes','Producto #8 \'aceyainofen\' | Lote: 213-332 | Qty: 300','OK'),(84,'2026-07-01 15:10:00','admin','VENTA','facturacion','Factura #000005 | Cliente: Darwin | Total: $169.92 | Pago: Efectivo | Items: 1','OK'),(85,'2026-07-01 17:30:25','admin','LOGIN','auth','Usuario: admin','OK'),(86,'2026-07-01 17:49:36','admin','LOGIN','auth','Usuario: admin','OK'),(87,'2026-07-01 17:52:53','admin','PRODUCTO_AGREGADO','inventario','#15 \'paracetamol\' | Stock:1000 | Precio:$20.0','OK'),(88,'2026-07-01 17:55:09','admin','LOTE_REGISTRADO','lotes','Producto #9 \'paracetamol\' | Lote: 123-1232 | Qty: 100000','OK'),(89,'2026-07-01 17:55:32','admin','LOTE_RETIRADO','lotes','Lote #11 \'123-1232\' | 100000 uds','OK'),(90,'2026-07-01 17:55:37','admin','LOTE_RETIRADO','lotes','Lote #11 \'123-1232\' | 0 uds','OK'),(91,'2026-07-01 19:39:18','admin','LOTE_REGISTRADO','lotes','Producto #9 \'paracetamol\' | Lote: 123-12412 | Qty: 500000','OK'),(92,'2026-07-01 19:42:08','admin','LOTE_REGISTRADO','lotes','Producto #9 \'paracetamol\' | Lote: 231-12345123 | Qty: 100','OK'),(93,'2026-07-01 19:46:06','admin','PRODUCTO_AGREGADO','inventario','#18 \'azetaminofen\' | Stock:1000 | Precio:$10.0','OK'),(94,'2026-07-01 19:55:57','admin','LOGIN','auth','Usuario: admin','OK'),(95,'2026-07-01 20:03:07','admin','LOGIN','auth','Usuario: admin','OK'),(96,'2026-07-01 20:06:25','admin','LOTE_REGISTRADO','lotes','Producto #10 \'azetaminofen\' | Lote: 2312-1234 | Qty: 1000','OK'),(97,'2026-07-01 20:07:25','admin','VENTA','facturacion','Factura #000006 | Cliente: Darwin | Total: $590.00 | Pago: Efectivo | Items: 1','OK'),(98,'2026-07-01 20:21:21','admin','LOGIN','auth','Usuario: admin','OK'),(99,'2026-07-01 20:34:59','admin','LOGIN','auth','Usuario: admin','OK'),(100,'2026-07-01 21:02:37','admin','PRODUCTO_AGREGADO','inventario','#22 \'paracetamol\' | Stock:1000 | Precio:$5.0','OK'),(101,'2026-07-01 21:09:34','admin','LOTE_REGISTRADO','lotes','Producto #11 \'paracetamol\' | Lote: 2313 | Qty: 10000','OK'),(102,'2026-07-06 16:08:54','admin','LOGIN','auth','Usuario: admin','OK'),(103,'2026-07-06 16:17:42','admin','LOGIN','auth','Usuario: admin','OK'),(104,'2026-07-06 23:22:06','admin','LOGIN','auth','Usuario: admin','OK'),(105,'2026-07-06 23:25:27','admin','LOGIN','auth','Usuario: admin','OK'),(106,'2026-07-06 23:26:29','admin','LOTE_EDITADO','lotes','Lote #15 \'2312-1234\' | Qty: 950→950 | Estado: activo','OK'),(107,'2026-07-06 23:29:09','admin','LOGIN','auth','Usuario: admin','OK'),(108,'2026-07-06 23:43:42','admin','LOGIN','auth','Usuario: admin','OK'),(109,'2026-07-06 23:44:21','sistema','LOGIN','auth','Usuario: admin','FALLIDO'),(110,'2026-07-06 23:44:29','admin','LOGIN','auth','Usuario: admin','OK'),(111,'2026-07-06 23:47:30','admin','LOGIN','auth','Usuario: admin','OK'),(112,'2026-07-08 17:46:19','admin','LOGIN','auth','Usuario: admin','OK'),(113,'2026-07-08 18:35:47','admin','LOGIN','auth','Usuario: admin','OK'),(114,'2026-07-09 18:14:44','admin','LOGIN','auth','Usuario: admin','OK'),(115,'2026-07-09 18:20:03','admin','PRODUCTO_AGREGADO','inventario','#24 \'Medicamnrto de prueba\' | Stock:123 | Precio:$235.28','OK'),(116,'2026-07-09 18:22:19','admin','PRODUCTO_AGREGADO','inventario','#25 \'Medicamnrto de prueba\' | Stock:123 | Precio:$235.28','OK'),(117,'2026-07-09 18:22:51','admin','PRECIO_CAMBIADO','inventario','Producto #12 \'Medicamnrto de prueba\' | Precio: $235.28 → $235.28','OK'),(118,'2026-07-09 18:38:50','admin','PRECIO_CAMBIADO','inventario','Producto #12 \'Medicamento de prueba\' | Precio: $235.28 → $235.28','OK'),(119,'2026-07-09 19:01:25','admin','VENTA','facturacion','Factura #000007 | Cliente: reterytr | Total: $1,180.00 | Pago: Efectivo | Items: 1','OK');
/*!40000 ALTER TABLE `audit_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customers` (
  `id` varchar(50) NOT NULL,
  `name` varchar(200) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `address` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_customers_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES ('0000002','gfhjgfjhj','hgkjhgk','hgkhgk'),('1','Darwin','1233','calle b'),('78','kkkkk','kkk','kkk'),('ewrert','reterytr','tryutyu','trutru');
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_adjustments`
--

DROP TABLE IF EXISTS `inventory_adjustments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventory_adjustments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lot_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `type` enum('entrada','salida','ajuste') NOT NULL,
  `quantity` int(11) NOT NULL,
  `reason` varchar(200) DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_adjustments_product` (`product_id`),
  KEY `idx_adjustments_lot` (`lot_id`),
  CONSTRAINT `inventory_adjustments_ibfk_1` FOREIGN KEY (`lot_id`) REFERENCES `lots` (`id`) ON DELETE CASCADE,
  CONSTRAINT `inventory_adjustments_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_adjustments`
--

LOCK TABLES `inventory_adjustments` WRITE;
/*!40000 ALTER TABLE `inventory_adjustments` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventory_adjustments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice_items`
--

DROP TABLE IF EXISTS `invoice_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `invoice_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `invoice_id` int(11) DEFAULT NULL,
  `product_id` int(11) DEFAULT NULL,
  `product_name` varchar(200) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `idx_items_invoice` (`invoice_id`),
  KEY `idx_items_product` (`product_name`),
  CONSTRAINT `invoice_items_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`) ON DELETE CASCADE,
  CONSTRAINT `invoice_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice_items`
--

LOCK TABLES `invoice_items` WRITE;
/*!40000 ALTER TABLE `invoice_items` DISABLE KEYS */;
INSERT INTO `invoice_items` VALUES (2,2,NULL,'winazorb',12,20.00,283.20),(3,3,NULL,'winazorb',12,20.00,283.20),(4,4,NULL,'winazorb',2,20.00,47.20),(5,5,NULL,'aceyainofen',12,12.00,169.92),(6,6,10,'azetaminofen',5,100.00,590.00),(7,7,12,'Medicamento de prueba',1,1000.00,1180.00);
/*!40000 ALTER TABLE `invoice_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoices`
--

DROP TABLE IF EXISTS `invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `invoices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(200) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `purchase_date` datetime NOT NULL,
  `employee` varchar(100) DEFAULT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_invoices_date` (`purchase_date`),
  KEY `idx_invoices_customer` (`customer_name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoices`
--

LOCK TABLES `invoices` WRITE;
/*!40000 ALTER TABLE `invoices` DISABLE KEYS */;
INSERT INTO `invoices` VALUES (1,'Darwin',1195.56,'2026-05-11 00:00:00','admin',NULL),(2,'Darwin',283.20,'2026-07-01 13:28:19','admin','Efectivo'),(3,'Darwin',283.20,'2026-07-01 13:28:19','admin','Efectivo'),(4,'Darwin',47.20,'2026-07-01 13:50:42','admin','Efectivo'),(5,'Darwin',169.92,'2026-07-01 15:08:00','admin','Efectivo'),(6,'Darwin',590.00,'2026-07-01 20:06:44','admin','Efectivo'),(7,'reterytr',1180.00,'2026-07-09 18:54:20','admin','Efectivo');
/*!40000 ALTER TABLE `invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lot_movements`
--

DROP TABLE IF EXISTS `lot_movements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lot_movements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lot_id` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `quantity` int(11) NOT NULL,
  `reason` text DEFAULT NULL,
  `invoice_id` int(11) DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `invoice_id` (`invoice_id`),
  KEY `idx_movements_lot` (`lot_id`),
  CONSTRAINT `lot_movements_ibfk_1` FOREIGN KEY (`lot_id`) REFERENCES `lots` (`id`) ON DELETE CASCADE,
  CONSTRAINT `lot_movements_ibfk_2` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lot_movements`
--

LOCK TABLES `lot_movements` WRITE;
/*!40000 ALTER TABLE `lot_movements` DISABLE KEYS */;
INSERT INTO `lot_movements` VALUES (23,15,'entrada',1000,'Recepción de mercancía',NULL,'admin','2026-07-01 20:06:25'),(24,15,'salida',-50,'Venta',6,'admin','2026-07-01 20:07:23'),(25,16,'entrada',10000,'Recepción de mercancía',NULL,'admin','2026-07-01 21:09:34');
/*!40000 ALTER TABLE `lot_movements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lots`
--

DROP TABLE IF EXISTS `lots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lots` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `lot_number` varchar(100) NOT NULL,
  `quantity_received` int(11) DEFAULT 0,
  `quantity_available` int(11) DEFAULT 0,
  `cost` decimal(10,2) DEFAULT 0.00,
  `expiry_date` date DEFAULT NULL,
  `received_date` date DEFAULT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `status` varchar(20) DEFAULT 'activo',
  PRIMARY KEY (`id`),
  KEY `supplier_id` (`supplier_id`),
  KEY `idx_lots_product` (`product_id`),
  KEY `idx_lots_expiry` (`expiry_date`),
  KEY `idx_lots_status` (`status`),
  KEY `idx_lots_fefo` (`product_id`,`expiry_date`,`status`),
  CONSTRAINT `lots_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `lots_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lots`
--

LOCK TABLES `lots` WRITE;
/*!40000 ALTER TABLE `lots` DISABLE KEYS */;
INSERT INTO `lots` VALUES (15,10,'2312-1234',1000,950,0.30,'2026-07-31','2026-07-01',NULL,'','activo'),(16,11,'2313',10000,10000,0.30,NULL,'2026-07-01',NULL,'','activo');
/*!40000 ALTER TABLE `lots` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`farmausr`@`localhost`*/ /*!50003 TRIGGER trg_lots_after_insert
            AFTER INSERT ON lots
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET
                    stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = NEW.product_id
                          AND status = 'activo'
                    ),
                    expiry_date = (
                        SELECT MIN(expiry_date)
                        FROM lots
                        WHERE product_id = NEW.product_id
                          AND status = 'activo'
                          AND quantity_available > 0
                    )
                WHERE id = NEW.product_id;
            END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`farmausr`@`localhost`*/ /*!50003 TRIGGER trg_lots_after_update
            AFTER UPDATE ON lots
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET
                    stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = NEW.product_id
                          AND status = 'activo'
                    ),
                    expiry_date = (
                        SELECT MIN(expiry_date)
                        FROM lots
                        WHERE product_id = NEW.product_id
                          AND status = 'activo'
                          AND quantity_available > 0
                    )
                WHERE id = NEW.product_id;
            END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`farmausr`@`localhost`*/ /*!50003 TRIGGER trg_lots_after_delete
            AFTER DELETE ON lots
            FOR EACH ROW
            BEGIN
                UPDATE products
                SET
                    stock = (
                        SELECT COALESCE(SUM(quantity_available), 0)
                        FROM lots
                        WHERE product_id = OLD.product_id
                          AND status = 'activo'
                    ),
                    expiry_date = (
                        SELECT MIN(expiry_date)
                        FROM lots
                        WHERE product_id = OLD.product_id
                          AND status = 'activo'
                          AND quantity_available > 0
                    )
                WHERE id = OLD.product_id;
            END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_units`
--

DROP TABLE IF EXISTS `product_units`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_units` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `unit_name` varchar(50) NOT NULL,
  `factor` int(11) NOT NULL DEFAULT 1,
  `price` decimal(10,2) DEFAULT NULL,
  `is_base` tinyint(1) DEFAULT 0,
  `is_default` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_pu_product` (`product_id`),
  KEY `idx_punits_product` (`product_id`),
  CONSTRAINT `product_units_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_units`
--

LOCK TABLES `product_units` WRITE;
/*!40000 ALTER TABLE `product_units` DISABLE KEYS */;
INSERT INTO `product_units` VALUES (18,10,'Unidad',1,NULL,1,1),(21,10,'blitzer',10,100.00,0,0),(22,11,'Unidad',1,NULL,1,1),(23,11,'blister',10,50.00,0,0),(24,12,'Unidad',1,NULL,1,0),(25,13,'Unidad',1,NULL,1,1),(26,12,'Blister',10,345.00,0,0),(27,12,'caja',30,1000.00,0,1);
/*!40000 ALTER TABLE `product_units` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `products` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) DEFAULT NULL,
  `active_ingredient` varchar(200) DEFAULT NULL,
  `presentation` varchar(100) DEFAULT NULL,
  `laboratory` varchar(200) DEFAULT NULL,
  `category` varchar(100) DEFAULT 'General',
  `stock` int(11) DEFAULT 0,
  `min_stock` int(11) DEFAULT 10,
  `price` decimal(10,2) DEFAULT 0.00,
  `cost` decimal(10,2) DEFAULT 0.00,
  `expiry_date` date DEFAULT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `supplier_id` (`supplier_id`),
  KEY `idx_products_name` (`name`),
  KEY `idx_products_category` (`category`),
  KEY `idx_products_stock` (`stock`),
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (10,'azetaminofen','dolor de cabeza','Tabletas','','Antibióticos',950,100,10.00,0.30,'2026-07-31',NULL),(11,'paracetamol','analgesico','Tabletas','farmax','Analgésicos',20000,100,5.00,0.30,NULL,NULL),(12,'Medicamento de prueba','tnt','Tabletas','Canary','Cardiovascular',0,10,235.28,0.00,NULL,NULL),(13,'Medicamnrto de prueba','tnt','Tabletas','Canary','Cardiovascular',123,10,235.28,0.00,NULL,1);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_suppliers_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
INSERT INTO `suppliers` VALUES (1,'Laboratorios HECL','77777yyy77777','jhfhffh','una cualquiera','ninguna'),(2,'Laboratorios HECL','77777yyy77777','jhfhffh','una cualquiera','ninguna');
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) DEFAULT 'employee',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','Administrador'),(2,'caja1','f88fa5ec367813bccb28321b56d55e05e1a2572d44c1f2c11354708309e5da9c','employee');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `v_stock_real`
--

DROP TABLE IF EXISTS `v_stock_real`;
/*!50001 DROP VIEW IF EXISTS `v_stock_real`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `v_stock_real` AS SELECT
 1 AS `product_id`,
  1 AS `name`,
  1 AS `category`,
  1 AS `price`,
  1 AS `min_stock`,
  1 AS `stock_total`,
  1 AS `proxima_vencimiento`,
  1 AS `lotes_activos` */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `v_stock_real`
--

/*!50001 DROP VIEW IF EXISTS `v_stock_real`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`farmausr`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_stock_real` AS select `p`.`id` AS `product_id`,`p`.`name` AS `name`,`p`.`category` AS `category`,`p`.`price` AS `price`,`p`.`min_stock` AS `min_stock`,coalesce(sum(`l`.`quantity_available`),0) AS `stock_total`,min(`l`.`expiry_date`) AS `proxima_vencimiento`,count(`l`.`id`) AS `lotes_activos` from (`products` `p` left join `lots` `l` on(`l`.`product_id` = `p`.`id` and `l`.`status` = 'activo' and `l`.`quantity_available` > 0)) group by `p`.`id`,`p`.`name`,`p`.`category`,`p`.`price`,`p`.`min_stock` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-09 19:08:08
