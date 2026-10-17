const original = { profile: { role: 'reader' } };
const copy = { ...original };
copy.profile.role = 'admin';
console.log(JSON.stringify({ originalRole: original.profile.role, sameNestedObject: original.profile === copy.profile }));
