import import_fixture
from import_fixture import label, items
import import_fixture as again
import_fixture.label = 'changed'
import_fixture.items.append('row')
print(again is import_fixture, label, again.label, items)
