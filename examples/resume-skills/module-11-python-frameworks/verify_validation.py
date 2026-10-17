from datetime import datetime
from pydantic import BaseModel, ConfigDict, ValidationError
from checks import Checks, equal, require
from domain import QuoteIn, ProductOut

checks = Checks('validation')
class Loose(BaseModel):
    quantity: int

def rejected(body):
    try:
        QuoteIn.model_validate(body)
    except ValidationError:
        return
    raise AssertionError('unexpectedly accepted: ' + repr(body))

checks.check('default integer parsing can coerce a numeric string',
             lambda: equal(Loose.model_validate({'quantity':'2'}).quantity, 2))
def boundaries():
    for value in (1, 100):
        equal(QuoteIn.model_validate({'product_id':'basic','quantity':value}).quantity, value)
checks.check('strict valid integer boundaries accepted', boundaries)
checks.check('strict integer rejects numeric string', lambda: rejected({'product_id':'basic','quantity':'2'}))
checks.check('strict integer rejects bool', lambda: rejected({'product_id':'basic','quantity':True}))
checks.check('strict integer rejects integral float', lambda: rejected({'product_id':'basic','quantity':2.0}))
checks.check('extra fields forbidden', lambda: rejected({'product_id':'basic','quantity':2,'tenant_id':'beta'}))
def invalid_values():
    for value in (0, 101, None): rejected({'product_id':'basic','quantity':value})
    rejected({'product_id':'basic'})
    rejected({'product_id':'','quantity':2})
checks.check('required fields and value bounds enforced', invalid_values)
checks.check('model_construct deliberately bypasses validation',
             lambda: equal(QuoteIn.model_construct(product_id='basic', quantity=0).quantity, 0))
class Stamp(BaseModel):
    model_config = ConfigDict(strict=True)
    when: datetime
def strict_json():
    stamp = Stamp.model_validate_json('{"when":"2026-10-14T06:30:00Z"}')
    require(isinstance(stamp.when, datetime))
    try:
        Stamp.model_validate({'when':'2026-10-14T06:30:00Z'})
    except ValidationError:
        return
    raise AssertionError('strict Python-input datetime string accepted')
checks.check('strict JSON datetime rules differ from strict Python-object input', strict_json)
checks.check('output model can select public fields while ignoring extras',
             lambda: equal(ProductOut.model_validate({'product_id':'basic','amount_paise':12500,
                            'currency':'INR','internal_cost_paise':7000}).model_dump(),
                           {'product_id':'basic','amount_paise':12500,'currency':'INR'}))
checks.save()
