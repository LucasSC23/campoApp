-- Idempotencia para POST /ventas.
-- Seguro para datos históricos: las ventas existentes quedan con NULL.

ALTER TABLE public.ventas
ADD COLUMN IF NOT EXISTS operacion_id uuid;

ALTER TABLE public.ventas
ADD COLUMN IF NOT EXISTS operacion_hash text;

CREATE UNIQUE INDEX IF NOT EXISTS ventas_operacion_id_uidx
ON public.ventas (operacion_id)
WHERE operacion_id IS NOT NULL;
