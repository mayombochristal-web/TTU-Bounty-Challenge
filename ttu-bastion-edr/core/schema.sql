-- ============================================================
-- TTU BASTION EDR – Schéma de base (exécuter une seule fois)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS ttu_core;
-- Registre des applications
CREATE TABLE ttu_core.registry (
app_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
app_name TEXT UNIQUE NOT NULL,

k_factor FLOAT DEFAULT 1.0,
base_threshold FLOAT DEFAULT 5.0,
adaptive_threshold FLOAT DEFAULT 5.0,
free_scans_remaining INTEGER DEFAULT 3, -- 3 analyses gratuites
is_active BOOLEAN DEFAULT TRUE,
last_heartbeat TIMESTAMPTZ DEFAULT NOW()
);
-- Vault de dissipation
CREATE TABLE ttu_core.dissipation_vault (
id BIGSERIAL PRIMARY KEY,
app_id UUID REFERENCES ttu_core.registry(app_id) ON DELETE CASCADE,
target_table TEXT NOT NULL,
payload JSONB NOT NULL,
priority INTEGER DEFAULT 1,
ingested_at TIMESTAMPTZ DEFAULT NOW(),
processed BOOLEAN DEFAULT FALSE,
processed_at TIMESTAMPTZ
);
CREATE INDEX idx_ttu_dissipation_active ON ttu_core.dissipation_vault (app_id,
processed) WHERE processed = FALSE;
-- Mise à jour instantanée de k
CREATE OR REPLACE FUNCTION ttu_core.trigger_k_dynamics()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
v_queue_size BIGINT;
v_new_k FLOAT;
BEGIN
SELECT COUNT(*) INTO v_queue_size
FROM ttu_core.dissipation_vault
WHERE app_id = NEW.app_id AND processed = FALSE;
v_new_k := 1.0 + ( (v_queue_size::FLOAT / 100.0) ^ 2 );
UPDATE ttu_core.registry
SET k_factor = v_new_k, last_heartbeat = NOW()
WHERE app_id = NEW.app_id;
RETURN NEW;
END;
$$;
CREATE TRIGGER trg_k_flow AFTER INSERT ON ttu_core.dissipation_vault
FOR EACH ROW EXECUTE FUNCTION ttu_core.trigger_k_dynamics();
-- Battement de cœur (modulation du seuil)
CREATE OR REPLACE FUNCTION ttu_core.heartbeat_modulation()
RETURNS void LANGUAGE plpgsql AS $$
DECLARE

v_global_stress FLOAT;
v_contraction_factor FLOAT;
BEGIN
SELECT COALESCE(SUM(k_factor), 1.0) INTO v_global_stress
FROM ttu_core.registry WHERE is_active = TRUE;
v_contraction_factor := 1.0 / (1.0 + (v_global_stress / 20.0));
UPDATE ttu_core.registry
SET adaptive_threshold = GREATEST(1.5, base_threshold * v_contraction_factor),
last_heartbeat = NOW();
END;
$$;
-- Planification toutes les minutes
SELECT cron.schedule('ttu-heartbeat', '* * * * *', 'SELECT ttu_core.heartbeat_modulation();');
-- Traitement des files (appel aux fonctions spécifiques)
CREATE OR REPLACE FUNCTION ttu_core.dispatch_processing()
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
r RECORD;
BEGIN
FOR r IN SELECT app_name FROM ttu_core.registry WHERE is_active = TRUE LOOP
BEGIN
EXECUTE format('SELECT process_app_%I()', r.app_name);
EXCEPTION WHEN undefined_function THEN
RAISE WARNING 'Fonction process_app_% inexistante', r.app_name;
END;
END LOOP;
END;
$$;
SELECT cron.schedule('ttu-processing', '* * * * *', 'SELECT ttu_core.dispatch_processing();');
-- Purge automatique
CREATE OR REPLACE FUNCTION ttu_core.purge_processed_flux(p_interval INTERVAL
DEFAULT '1 hour')
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
DELETE FROM ttu_core.dissipation_vault
WHERE processed = TRUE AND processed_at < (NOW() - p_interval);
END;
$$;
SELECT cron.schedule('ttu-purge', '0 * * * *', 'SELECT ttu_core.purge_processed_flux(''1
hour'');');