-- Elapsed UTC windows anchored to each user's first visible signup.
-- Product funnel requires the same operation ID at start and success.
WITH visible AS (
  SELECT e.* FROM events e JOIN users u ON u.id=e.subject
  WHERE u.internal=0 AND e.occurred<:event_cutoff AND e.received<=:knowledge_cutoff
), anchors AS (
  SELECT subject, MIN(occurred) AS signup
  FROM visible WHERE name='signup_completed' GROUP BY subject
)
SELECT a.subject, a.signup,
  a.signup + 86400 <= :event_cutoff AS activation_mature,
  EXISTS (
    SELECT 1 FROM visible s WHERE s.subject=a.subject AND s.name='generation_started'
      AND s.occurred>=a.signup AND s.occurred<a.signup+86400
  ) AS started,
  EXISTS (
    SELECT 1 FROM visible s JOIN visible c ON c.subject=s.subject AND c.operation=s.operation
    WHERE s.subject=a.subject AND s.name='generation_started' AND c.name='generation_succeeded'
      AND s.occurred>=a.signup AND c.occurred>=s.occurred AND c.occurred<a.signup+86400
  ) AS completed,
  a.signup + (:retention_day + 1)*86400 <= :event_cutoff AS retention_mature,
  EXISTS (
    SELECT 1 FROM visible r WHERE r.subject=a.subject AND r.name='generation_succeeded'
      AND r.occurred>=a.signup+:retention_day*86400
      AND r.occurred<a.signup+(:retention_day+1)*86400
  ) AS retained
FROM anchors a ORDER BY a.subject;
