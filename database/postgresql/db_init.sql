-- ===============================================
-- Raahi AI - Database Initialization Script
-- Database: raahi_ai
-- Author: Muhammad Taha
-- Created: Iteration 1
-- ===============================================

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ITINERARIES TABLE
CREATE TABLE IF NOT EXISTS itineraries (
    itinerary_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    title VARCHAR(150),
    destination VARCHAR(100),
    days INT,
    budget INT,
    season VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CHECKLIST TABLE
CREATE TABLE IF NOT EXISTS checklist (
    checklist_id SERIAL PRIMARY KEY,
    itinerary_id INT REFERENCES itineraries(itinerary_id),
    location VARCHAR(100),
    month VARCHAR(50),
    items TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
