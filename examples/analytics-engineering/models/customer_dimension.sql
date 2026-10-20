WITH candidates AS (
 SELECT tenant_id,entity_id customer_id,source_version,
 json_extract(payload_json,'$.effective_from') valid_from,
 json_extract(payload_json,'$.plan') plan
 FROM valid_changes WHERE stream='customers'
), ranked AS (
 SELECT *,ROW_NUMBER() OVER(
 PARTITION BY tenant_id,customer_id,valid_from ORDER BY source_version DESC) rn
 FROM candidates
), periods AS (
 SELECT tenant_id,customer_id,valid_from,plan,
 LEAD(valid_from) OVER(PARTITION BY tenant_id,customer_id ORDER BY valid_from) valid_to
 FROM ranked WHERE rn=1
)
SELECT tenant_id,length(customer_id)||':'||customer_id||':'||valid_from customer_sk,
 customer_id,valid_from,valid_to,plan,0 is_unknown FROM periods
UNION ALL
SELECT DISTINCT tenant_id,'unknown','__unknown__','0001-01-01',NULL,'Unknown',1
FROM bounded_changes;
