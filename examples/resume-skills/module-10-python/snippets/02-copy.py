from copy import deepcopy
original = {'tags': ['backend']}
shallow = original.copy()
deep = deepcopy(original)
shallow['tags'].append('python')
shallow['new'] = True
print(original)
print(deep)
print('new' in original, shallow is original)
