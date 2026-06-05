-- ---------------------------------------------------------------------------
-- Esquema PostgreSQL + PostGIS para "Ruteo Bogotá"
--
-- Este script crea la extensión PostGIS y la tabla de ubicaciones guardadas.
-- La aplicación también puede crear las tablas automáticamente vía SQLAlchemy
-- (init_db), pero se incluye este archivo para despliegues con Docker o setup
-- manual de la base de datos.
-- ---------------------------------------------------------------------------

-- Habilitar la extensión espacial PostGIS.
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla de ubicaciones personalizadas dentro de Bogotá.
CREATE TABLE IF NOT EXISTS locations (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    description VARCHAR(500) NOT NULL DEFAULT '',
    lat         DOUBLE PRECISION NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    category    VARCHAR(60) NOT NULL DEFAULT 'general',
    -- Punto geográfico (lon, lat) en SRID 4326 para consultas espaciales.
    geom        GEOMETRY(Point, 4326)
);

-- Índice por categoría para filtrados frecuentes.
CREATE INDEX IF NOT EXISTS idx_locations_category ON locations (category);

-- Índice espacial GiST para consultas de cercanía/intersección.
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST (geom);

-- Trigger para mantener 'geom' sincronizado con lat/lon en inserciones/updates.
CREATE OR REPLACE FUNCTION sync_location_geom() RETURNS TRIGGER AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lon, NEW.lat), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_location_geom ON locations;
CREATE TRIGGER trg_sync_location_geom
    BEFORE INSERT OR UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION sync_location_geom();

-- Datos de ejemplo: ubicaciones representativas de Bogotá.
INSERT INTO locations (name, description, lat, lon, category) VALUES
    ('Universidad Distrital - Sede Tecnológica', 'Facultad Tecnológica', 4.5765, -74.1188, 'universidad'),
    ('Plaza de Bolívar', 'Centro histórico de Bogotá', 4.5981, -74.0758, 'punto_interes'),
    ('Centro Comercial Andino', 'Zona Rosa', 4.6669, -74.0531, 'centro_comercial'),
    ('Hospital San Ignacio', 'Pontificia Universidad Javeriana', 4.6286, -74.0644, 'hospital'),
    ('Estación TransMilenio Calle 100', 'Autopista Norte', 4.6860, -74.0556, 'estacion_transmilenio')
ON CONFLICT DO NOTHING;
