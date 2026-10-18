import json
def known(values):
    present=[value for value in values if value is not None]
    return sum(present) if present else None
values=[0,None,200]
missing=sum(value is None for value in values)
print(json.dumps({'known_cents':known(values),'missing':missing,
                  'complete':None if missing else known(values),
                  'all_missing_known':known([None,None])}))
