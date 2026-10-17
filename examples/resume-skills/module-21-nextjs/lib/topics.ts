import 'server-only';

const topics = [
  { slug: 'node', title: 'Node.js', summary: 'A runtime for JavaScript outside the browser.' },
  { slug: 'react', title: 'React', summary: 'Components describe UI from current inputs.' },
];

export function listTopics() { return topics.map(topic => ({ ...topic })); }
export function findTopic(slug: string) { return topics.find(topic => topic.slug === slug); }

// A synthetic environment marker verifies non-disclosure; it is not a credential.
export function serverConfigured() { return Boolean(process.env.M21_PRIVATE_MARKER); }
