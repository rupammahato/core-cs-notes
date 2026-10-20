WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY tenant_id,entity_id ORDER BY source_version DESC) rn
 FROM valid_changes WHERE stream='orders'
), current_orders AS (
 SELECT tenant_id,entity_id order_id,source_version,
 json_extract(payload_json,'$.customer_id') customer_id,
 json_extract(payload_json,'$.order_day') order_day,
 json_extract(payload_json,'$.billed_cents') billed_cents,
 json_extract(payload_json,'$.status') status
 FROM ranked WHERE rn=1 AND json_extract(payload_json,'$.op')='U'
)
SELECT o.tenant_id,o.order_id,o.customer_id,COALESCE(d.customer_sk,'unknown') customer_sk,
 o.order_day,o.billed_cents,o.status,o.source_version
FROM current_orders o LEFT JOIN next_dim d
 ON d.tenant_id=o.tenant_id AND d.customer_id=o.customer_id AND d.is_unknown=0
 AND d.valid_from<=o.order_day AND (d.valid_to IS NULL OR o.order_day<d.valid_to);
