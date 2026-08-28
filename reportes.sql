-- =============================================================
-- CAMPO BURGER - VISTAS DE REPORTES
-- =============================================================

CREATE OR REPLACE VIEW resumen_sesiones_caja AS
SELECT
    s.id AS sesion_id,
    s.fecha_apertura,
    s.fecha_cierre,
    s.estado,
    s.monto_inicial,

    COUNT(v.id) FILTER (
        WHERE v.estado = 'COMPLETADA'
    ) AS ventas_completadas,

    COUNT(v.id) FILTER (
        WHERE v.estado = 'ANULADA'
    ) AS ventas_anuladas,

    COALESCE(SUM(v.monto_total) FILTER (
        WHERE v.estado = 'COMPLETADA'
          AND v.metodo_pago = 'Efectivo'
    ), 0) AS efectivo,

    COALESCE(SUM(v.monto_total) FILTER (
        WHERE v.estado = 'COMPLETADA'
          AND v.metodo_pago = 'POS / Tarjeta'
    ), 0) AS pos,

    COALESCE(SUM(v.monto_total) FILTER (
        WHERE v.estado = 'COMPLETADA'
          AND v.metodo_pago = 'Transferencia'
    ), 0) AS transferencia,

    COALESCE(SUM(v.monto_total) FILTER (
        WHERE v.estado = 'COMPLETADA'
    ), 0) AS total_ventas,

    s.monto_inicial + COALESCE(SUM(v.monto_total) FILTER (
        WHERE v.estado = 'COMPLETADA'
          AND v.metodo_pago = 'Efectivo'
    ), 0) AS efectivo_esperado

FROM sesiones_caja s
LEFT JOIN ventas v ON v.sesion_id = s.id
GROUP BY s.id;


CREATE OR REPLACE VIEW resumen_mensual_ventas AS
SELECT
    DATE_TRUNC('month', fecha_hora)::date AS mes,
    COUNT(*) AS cantidad_ventas,

    COALESCE(SUM(monto_total) FILTER (
        WHERE metodo_pago = 'Efectivo'
    ), 0) AS efectivo,

    COALESCE(SUM(monto_total) FILTER (
        WHERE metodo_pago = 'POS / Tarjeta'
    ), 0) AS pos,

    COALESCE(SUM(monto_total) FILTER (
        WHERE metodo_pago = 'Transferencia'
    ), 0) AS transferencia,

    COALESCE(SUM(monto_total), 0) AS total

FROM ventas
WHERE estado = 'COMPLETADA'
GROUP BY DATE_TRUNC('month', fecha_hora);


-- Ejemplos:
-- SELECT * FROM resumen_sesiones_caja ORDER BY sesion_id DESC;
-- SELECT * FROM resumen_mensual_ventas ORDER BY mes DESC;

-- Revisión del posible duplicado detectado en Papas Fritas:
-- SELECT id, nombre, precio, categoria, subcategoria
-- FROM productos
-- WHERE categoria = 'Papas Fritas'
-- ORDER BY nombre;
