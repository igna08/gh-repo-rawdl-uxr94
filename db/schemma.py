import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ------------------------------------------------------------
# 1) Cargar la variable de entorno DATABASE_URL desde .env
# ------------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("ERROR: la variable DATABASE_URL no está definida. "
                       "Revisa tu archivo .env.")

print(f"[INFO] Usando DATABASE_URL = {DATABASE_URL}")

# ------------------------------------------------------------
# 2) Todo el esquema SQL que quieres ejecutar en PostgreSQL
#    (incluye extensiones, función update_timestamp, triggers,
#     tablas y índices)
# ------------------------------------------------------------
schema_sql = """
-- Enable UUID generation and other extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 0. Trigger to auto-update updated_at on row modifications
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. Roles definition
CREATE TABLE IF NOT EXISTS roles (
    id         SMALLINT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE
);

-- 2. Users
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    status          TEXT NOT NULL CHECK(status IN ('pending','active','suspended')) DEFAULT 'pending',
    consent_granted_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMPTZ
);
CREATE TRIGGER trg_users_update_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 3. Tenants (Schools)
CREATE TABLE IF NOT EXISTS schools (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    address         TEXT NOT NULL,
    description     TEXT,
    logo_url        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMPTZ
);
CREATE TRIGGER trg_schools_update_timestamp
    BEFORE UPDATE ON schools
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 4. User roles (multitenant)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id         SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id, school_id)
);

-- 5. Invitations
CREATE TABLE IF NOT EXISTS invitations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL,
    role_id         SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    token           UUID NOT NULL DEFAULT gen_random_uuid(),
    expires_at      TIMESTAMPTZ NOT NULL,
    used_at         TIMESTAMPTZ,
    sent_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_invitation_dates CHECK (expires_at > created_at)
);
CREATE TRIGGER trg_invitations_update_timestamp
    BEFORE UPDATE ON invitations
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 6. Email Verification Tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           UUID NOT NULL DEFAULT gen_random_uuid(),
    expires_at      TIMESTAMPTZ NOT NULL,
    used_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_email_verif_dates CHECK (expires_at > created_at)
);

-- 7. Password Reset Requests
CREATE TABLE IF NOT EXISTS password_reset_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           UUID NOT NULL DEFAULT gen_random_uuid(),
    expires_at      TIMESTAMPTZ NOT NULL,
    used_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_password_reset_dates CHECK (expires_at > created_at)
);

-- 8. Permissions (optional, fine-grained ACL)
CREATE TABLE IF NOT EXISTS permissions (
    role_id         SMALLINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    resource        TEXT NOT NULL,
    action          TEXT NOT NULL,
    PRIMARY KEY (role_id, resource, action)
);

-- 9. Classrooms
CREATE TABLE IF NOT EXISTS classrooms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    capacity        INTEGER,
    responsible     TEXT,
    image_url       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMPTZ,
    UNIQUE (school_id, code)
);
CREATE TRIGGER trg_classrooms_update_timestamp
    BEFORE UPDATE ON classrooms
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 10. Asset categories
CREATE TABLE IF NOT EXISTS asset_categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER trg_asset_categories_update_timestamp
    BEFORE UPDATE ON asset_categories
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 11. Asset templates
CREATE TABLE IF NOT EXISTS asset_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id     UUID NOT NULL REFERENCES asset_categories(id) ON DELETE RESTRICT,
    name            TEXT NOT NULL,
    description     TEXT,
    default_image_url TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER trg_asset_templates_update_timestamp
    BEFORE UPDATE ON asset_templates
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 12. Assets
CREATE TABLE IF NOT EXISTS assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID NOT NULL REFERENCES asset_templates(id) ON DELETE RESTRICT,
    classroom_id    UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    serial_number   TEXT UNIQUE,
    status          TEXT NOT NULL CHECK(status IN ('operational','decommissioned')) DEFAULT 'operational',
    purchase_date   DATE,
    value_estimate  DECIMAL(12,2) CHECK (value_estimate >= 0),
    image_url       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMPTZ
);
CREATE TRIGGER trg_assets_update_timestamp
    BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 13. Asset events / audit log
CREATE TABLE IF NOT EXISTS asset_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id        UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL,
    description     TEXT,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 14. QR Codes
CREATE TABLE IF NOT EXISTS qr_codes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id        UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE UNIQUE,
    qr_url          TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 15. Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id        UUID REFERENCES assets(id) ON DELETE SET NULL,
    reported_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    description     TEXT NOT NULL,
    photo_url       TEXT,
    status          TEXT NOT NULL CHECK(status IN ('open','resolved')) DEFAULT 'open',
    reported_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 16. Subscription plans
CREATE TABLE IF NOT EXISTS plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,
    price_monthly   DECIMAL(10,2) NOT NULL CHECK (price_monthly >= 0),
    max_schools     INTEGER CHECK (max_schools >= 0),
    max_assets      INTEGER CHECK (max_assets >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER trg_plans_update_timestamp
    BEFORE UPDATE ON plans
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 17. Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    plan_id         UUID NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    status          TEXT NOT NULL CHECK(status IN ('active','past_due','cancelled','expired')) DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_subscription_dates CHECK (end_date >= start_date)
);
CREATE TRIGGER trg_subscriptions_update_timestamp
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 18. Payments
CREATE TABLE IF NOT EXISTS payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    amount          DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    gateway_id      TEXT NOT NULL,
    status          TEXT NOT NULL CHECK(status IN ('pending','succeeded','failed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TRIGGER trg_payments_update_timestamp
    BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Índices
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_assets_serial ON assets(serial_number);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
"""

# ------------------------------------------------------------
# 3) Función que aplica el esquema completo
# ------------------------------------------------------------
def create_schema():
    # Crear el engine de SQLAlchemy
    engine = create_engine(DATABASE_URL, echo=False)

    print("[INFO] Conectando a la base de datos...")
    with engine.connect() as conn:
        # Si tu driver necesita autocommit para DDL, descomenta la siguiente línea:
        # conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        print("[INFO] Iniciando transacción para aplicar el esquema...")
        # Envolvemos en BEGIN/COMMIT para evitar errores de DDL parcialmente aplicadas
        conn.execute(text("BEGIN;"))
        conn.execute(text(schema_sql))
        conn.execute(text("COMMIT;"))
        print("[SUCCESS] El esquema se ha aplicado correctamente.")

if __name__ == "__main__":
    try:
        create_schema()
    except Exception as e:
        print(f"[ERROR] Ocurrió un problema al aplicar el esquema:\n{e}")
        raise