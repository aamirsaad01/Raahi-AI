-- =============================================================================
-- Raahi AI — PostgreSQL baseline schema
-- =============================================================================
-- Apply from this directory so relative includes resolve:
--   psql -U postgres -d raahi_ai -f db_init.sql
-- Or from repo root:
--   psql -U postgres -d raahi_ai -f database/postgresql/db_init.sql
--
-- Files under schema/ are ordered by dependency (users → itineraries → …).
-- =============================================================================

\set ON_ERROR_STOP on

\echo '>> 00_functions'
\ir schema/00_functions.sql
\echo '>> 01_users'
\ir schema/01_users.sql
\echo '>> 02_location_mapping'
\ir schema/02_location_mapping.sql
\echo '>> 03_itineraries'
\ir schema/03_itineraries.sql
\echo '>> 04_checklist'
\ir schema/04_checklist.sql
\echo '>> 05_hazard_reports'
\ir schema/05_hazard_reports.sql
\echo '>> 06_points_of_interest'
\ir schema/06_points_of_interest.sql
\echo '>> 07_travel_corridors'
\ir schema/07_travel_corridors.sql
\echo '>> 08_ndma'
\ir schema/08_ndma.sql
\echo '>> 09_chat'
\ir schema/09_chat.sql
\echo '>> 10_emergency_safe_points'
\ir schema/10_emergency_safe_points.sql

\echo '>> Done. Raahi AI schema is up to date.'
