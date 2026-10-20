// Copies the handbook .md files into content/docs/<subject>/<group>/ with frontmatter.
// Source notes are never modified. Runs before `dev` and `build`.
// Group folders drive the collapsible sidebar; lib/source.ts strips them from the URL.
import { readdirSync, readFileSync, writeFileSync, rmSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { icons } from 'lucide-react'; // the icon registry the fumadocs plugin resolves against

// Add a subject here the same way: index = the roadmap file's slug, groups cover every other chapter.
const SUBJECTS = [
  {
    slug: 'dsa',
    title: 'DSA',
    dir: '../DSA Notes',
    description: 'Data Structures & Algorithms in C++',
    icon: 'Binary',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Foundations', icon: 'Blocks', pages: ['cpp-stl', 'complexity', 'bit-manipulation'] },
      { slug: 'linear', title: 'Linear Structures', icon: 'List', pages: ['arrays-strings', 'hashing', 'linked-lists', 'stacks-queues'] },
      { slug: 'recursion-sorting', title: 'Recursion & Sorting', icon: 'Repeat', pages: ['recursion', 'searching-sorting', 'backtracking'] },
      { slug: 'trees-heaps', title: 'Trees & Heaps', icon: 'Network', pages: ['trees', 'heaps', 'trie'] },
      { slug: 'algorithms', title: 'Algorithms', icon: 'Workflow', pages: ['greedy-intervals', 'graphs', 'dynamic-programming'] },
    ],
  },
  {
    slug: 'oop',
    title: 'OOP',
    dir: '../OOP Notes',
    description: 'Object-oriented programming and low-level design in C++',
    icon: 'Boxes',
    index: 'master-roadmap',
    groups: [
      { slug: 'core', title: 'Core OOP', icon: 'Box', pages: ['classes-objects', 'constructors-destructors-copying', 'encapsulation-abstraction', 'inheritance', 'polymorphism'] },
      { slug: 'modelling', title: 'Modelling', icon: 'Share2', pages: ['relationships-uml', 'modern-cpp-object-model'] },
      { slug: 'design', title: 'Design', icon: 'Compass', pages: ['solid-principles', 'design-patterns'] },
      { slug: 'lld', title: 'Low-Level Design', icon: 'BuildingComplex', pages: ['lld-method-parking-lru-splitwise', 'lld-snake-elevator-bookmyshow'] },
      { slug: 'revision', title: 'Revision', icon: 'ListChecks', pages: ['consolidation'] },
    ],
  },
  {
    slug: 'os',
    title: 'OS',
    dir: '../OS Notes',
    description: 'Processes, scheduling, memory, concurrency and file systems',
    icon: 'Cpu',
    index: 'master-roadmap',
    groups: [
      { slug: 'processes', title: 'Foundations & Processes', icon: 'Activity', pages: ['os-fundamentals', 'processes', 'threads', 'cpu-scheduling'] },
      { slug: 'concurrency', title: 'Concurrency', icon: 'GitMerge', pages: ['synchronization', 'deadlocks'] },
      { slug: 'memory', title: 'Memory', icon: 'MemoryStick', pages: ['memory-management', 'virtual-memory'] },
      { slug: 'storage-io', title: 'Storage & I/O', icon: 'HardDrive', pages: ['storage-file-systems', 'ipc-io'] },
      { slug: 'revision', title: 'Revision', icon: 'ListChecks', pages: ['putting-it-together', 'consolidation'] },
    ],
  },
  {
    slug: 'dbms',
    title: 'DBMS',
    dir: '../DBMS Notes',
    description: 'Relational design, SQL, indexing and transactions',
    icon: 'Database',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Foundations', icon: 'Layers', pages: ['dbms-fundamentals', 'relational-model-keys'] },
      { slug: 'design', title: 'Design & Normalization', icon: 'Share2', pages: ['er-model-schema-design', 'normalization'] },
      { slug: 'sql', title: 'SQL', icon: 'Terminal', pages: ['sql-querying', 'sql-joins-subqueries-windows', 'sql-ddl-views-programmability'] },
      { slug: 'internals', title: 'Internals', icon: 'Gauge', pages: ['indexing-storage'] },
      { slug: 'transactions', title: 'Transactions', icon: 'ArrowLeftRight', pages: ['transactions-concurrency', 'recovery-relational-algebra'] },
      { slug: 'scaling', title: 'Scaling & Revision', icon: 'Network', pages: ['nosql-scaling', 'consolidation'] },
    ],
  },
  {
    slug: 'cn',
    title: 'CN',
    dir: '../CN Notes',
    description: 'Layering, TCP/IP, routing, DNS, HTTP and TLS',
    icon: 'Router',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Foundations', icon: 'Layers', pages: ['fundamentals-layering', 'framing-errors'] },
      { slug: 'link-network', title: 'Link & Network', icon: 'Network', pages: ['medium-access-lan', 'ip-addressing-subnetting', 'routing'] },
      { slug: 'transport', title: 'Transport', icon: 'ArrowLeftRight', pages: ['udp-tcp-connections', 'tcp-reliability-congestion'] },
      { slug: 'application', title: 'Application', icon: 'Globe', pages: ['dns', 'http-web'] },
      { slug: 'security', title: 'Security', icon: 'ShieldCheck', pages: ['network-security'] },
      { slug: 'end-to-end', title: 'End to End & Revision', icon: 'ListChecks', pages: ['url-walkthrough', 'consolidation'] },
    ],
  },
  {
    slug: 'resume-skills',
    title: 'Resume Skills',
    dir: '../Resume Skills Notes',
    description: 'Backend, frameworks, cloud and AI skills for interviews',
    icon: 'Layers',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Backend Foundations', icon: 'Blocks', pages: ['how-backend-works', 'javascript-fundamentals', 'asynchronous-javascript', 'typescript-fundamentals', 'nodejs'] },
      { slug: 'backend-apis', title: 'Backend APIs', icon: 'Server', pages: ['express-backend-structure', 'rest-apis-http', 'authentication-sessions-jwt-oauth', 'api-security-authorization-multi-tenancy', 'webhooks-payments-reliable-integrations'] },
      { slug: 'python-backend', title: 'Python Backend', icon: 'Code', pages: ['python-fundamentals', 'flask-fastapi-python-request-handling', 'django-django-rest-framework'] },
      { slug: 'databases', title: 'Databases', icon: 'Database', pages: ['postgresql-backend', 'mongodb-backend', 'neo4j-graph-backed-applications'] },
      { slug: 'data-pipelines', title: 'Caching and Background Work', icon: 'Workflow', pages: ['caching-background-jobs-data-ingestion'] },
      { slug: 'deployment', title: 'Deployment and Operations', icon: 'Boxes', pages: ['docker-fundamentals', 'linux-deployment-nginx-pm2', 'aws-gcp-fundamentals', 'git-ci-cd-testing-observability-performance'] },
      { slug: 'frontend', title: 'Frontend Fundamentals', icon: 'Code', pages: ['react-fundamentals', 'nextjs-api-routes-tailwind'] },
      { slug: 'ai-systems', title: 'AI Systems', icon: 'Brain', pages: ['llm-ai-api-fundamentals', 'rag-document-ingestion', 'embeddings-pinecone-pgvector', 'langchain-langgraph-llamaindex'] },
      { slug: 'system-design', title: 'System Design', icon: 'Workflow', pages: ['system-design-load-balancer'] },
      { slug: 'resume-projects', title: 'Resume Projects', icon: 'ListChecks', pages: ['resume-project-experience-deep-dives'] },
      { slug: 'revision', title: 'Revision', icon: 'ListChecks', pages: ['consolidation-interview-drills'] },
    ],
  },
  {
    slug: 'system-design',
    title: 'System Design',
    dir: '../System Design Notes',
    description: 'Architecture foundations and worked system designs for backend interviews',
    icon: 'Network',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Foundations', icon: 'Blocks', pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling', 'reliable-workflows-concurrency', 'secure-observable-operations'] },
      { slug: 'worked-systems', title: 'Worked Systems', icon: 'Wrench', pages: ['url-shortener', 'rate-limiter', 'notifications-webhooks', 'file-upload-processing', 'booking-reservations', 'chat-messaging', 'social-feed-photo-sharing', 'job-scheduler-workers', 'checkout-payments-credit-ledger', 'search-autocomplete', 'load-balancer-distributed-cache', 'multi-tenant-saas', 'multi-tenant-rag', 'analytics-event-pipeline'] },
      { slug: 'revision', title: 'Revision', icon: 'ListChecks', pages: ['consolidation'] },
    ],
  },
  {
    slug: 'product-analytics',
    title: 'Product & Analytics',
    dir: '../Product Analytics Notes',
    description: 'Product decisions, requirements, economics and analytics for interviews',
    icon: 'Compass',
    index: 'master-roadmap',
    groups: [
      { slug: 'product-foundations', title: 'Product Foundations', icon: 'Lightbulb', pages: ['product-thinking-requirements-design'] },
      { slug: 'economics', title: 'Pricing & Economics', icon: 'Coins', pages: ['pricing-unit-economics'] },
      { slug: 'analytics', title: 'Analytics & Experiments', icon: 'ChartLine', pages: ['product-analytics-experiments'] },
      { slug: 'analysis', title: 'Python & Excel', icon: 'Table', pages: ['python-excel-analysis'] },
      { slug: 'marketing', title: 'Marketing & Visualization', icon: 'ChartColumn', pages: ['marketing-measurement-data-visualization'] },
      { slug: 'revision', title: 'Revision & Resume Drills', icon: 'ListChecks', pages: ['consolidation-resume-drills'] },
    ],
  },
  {
    slug: 'sql-interview',
    title: 'SQL Interview Lab',
    dir: '../SQL Interview Notes',
    description: 'Business SQL problems, verified answers and interview practice',
    icon: 'Database',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Dataset & Method', icon: 'Blocks', pages: ['dataset-and-solving-method'] },
      { slug: 'problems', title: 'Worked Problems', icon: 'Terminal', pages: ['joins-grain-and-null-semantics', 'windows-and-time-series', 'funnels-cohorts-and-retention', 'reconciliation-and-query-plans'] },
      { slug: 'revision', title: 'Revision & Mocks', icon: 'ListChecks', pages: ['consolidation-and-mocks'] },
    ],
  },
  {
    slug: 'probability-statistics',
    title: 'Probability & Statistics',
    dir: '../Probability Statistics Notes',
    description: 'Probability foundations, statistical inference and interview practice',
    icon: 'ChartLine',
    index: 'master-roadmap',
    groups: [
      { slug: 'probability', title: 'Probability Foundations', icon: 'Binary', pages: ['probability-and-counting', 'conditional-probability-and-bayes', 'random-variables-and-distributions'] },
      { slug: 'statistics', title: 'Statistical Foundations', icon: 'ChartColumn', pages: ['descriptive-statistics-and-sampling', 'estimation-and-confidence-intervals'] },
      { slug: 'inference', title: 'Tests & Models', icon: 'Workflow', pages: ['hypothesis-tests-and-experiments', 'correlation-and-regression'] },
      { slug: 'revision', title: 'Revision & Mocks', icon: 'ListChecks', pages: ['consolidation-and-mocks'] },
    ],
  },
  {
    slug: 'product-casebook',
    title: 'Product Casebook',
    dir: '../Product Casebook Notes',
    description: 'Worked product and analytics cases with evidence, trade-offs and decisions',
    icon: 'Compass',
    index: 'master-roadmap',
    groups: [
      { slug: 'method', title: 'Method & Evidence', icon: 'Blocks', pages: ['case-method-and-evidence'] },
      { slug: 'product', title: 'Product & Growth', icon: 'Lightbulb', pages: ['product-sense-and-prioritization', 'growth-activation-and-retention', 'pricing-and-business-models'] },
      { slug: 'analysis', title: 'Analysis & Operations', icon: 'Workflow', pages: ['metrics-and-root-cause-analysis', 'marketplaces-and-operations', 'experiments-ai-and-launch-decisions'] },
      { slug: 'revision', title: 'Revision & Mocks', icon: 'ListChecks', pages: ['consolidation-and-mocks'] },
    ],
  },
  {
    slug: 'analytics-engineering',
    title: 'Analytics Engineering',
    dir: '../Analytics Engineering Notes',
    description: 'Warehouse modeling, CDC, transformations, trusted metrics and operations',
    icon: 'Database',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Warehouse Foundations', icon: 'Blocks', pages: ['warehouse-foundations-and-dataset', 'dimensional-modeling-and-history', 'ingestion-cdc-and-canonical-state'] },
      { slug: 'transformation', title: 'Transformations & Refreshes', icon: 'Workflow', pages: ['transformations-and-dbt-workflows', 'incremental-refreshes-and-backfills'] },
      { slug: 'operations', title: 'Quality, Metrics & Operations', icon: 'Gauge', pages: ['quality-observability-and-publication', 'semantic-metrics-and-consumption', 'production-architecture-and-performance'] },
      { slug: 'revision', title: 'Revision & Mocks', icon: 'ListChecks', pages: ['consolidation-and-mocks'] },
    ],
  },
  {
    slug: 'machine-coding',
    title: 'Machine Coding',
    dir: '../Machine Coding Notes',
    description: 'Runnable C++17 systems, state invariants, edge cases and interview practice',
    icon: 'Code',
    index: 'master-roadmap',
    groups: [
      { slug: 'foundations', title: 'Method & State', icon: 'Blocks', pages: ['solving-method-and-test-harness', 'transactional-key-value-store', 'sliding-window-rate-limiter'] },
      { slug: 'coordination', title: 'Callbacks & Scheduling', icon: 'Workflow', pages: ['event-bus-and-callback-lifecycle', 'virtual-time-task-scheduler'] },
      { slug: 'applications', title: 'Worked Applications', icon: 'Terminal', pages: ['vending-machine-and-exact-change', 'meeting-room-booking', 'in-memory-document-search', 'feature-flag-evaluator'] },
      { slug: 'revision', title: 'Revision & Mocks', icon: 'ListChecks', pages: ['consolidation-and-mocks'] },
    ],
  },
];

// A bad icon name is only a build-time warning, so fail here instead.
for (const s of SUBJECTS)
  for (const { icon } of [s, ...s.groups])
    if (!(icon in icons)) throw new Error(`unknown lucide icon "${icon}"`);

const partNo = (f) => Number(f.match(/part-(\d+)/)?.[1] ?? 0);
const yaml = (s) => JSON.stringify(s); // JSON strings are valid YAML scalars

/** Pull the title/description out of a note's leading `# ` lines and strip them from the body. */
function parseNote(path) {
  const lines = readFileSync(path, 'utf8').replace(/\r\n/g, '\n').split('\n');

  // Leading "# " lines form the title: "Handbook — Part 11" + "Phase 9: Trees", or one line "... — Part 1: Master Roadmap".
  let i = 0;
  const h1s = [];
  while (i < lines.length && (lines[i].startsWith('# ') || lines[i].trim() === '')) {
    if (lines[i].startsWith('# ')) h1s.push(lines[i].slice(2).trim());
    i++;
  }
  const last = h1s.at(-1) ?? '';
  const title = h1s.length > 1 ? last : last.replace(/^.*Part \d+:\s*/, '');

  // The first line after the title, if bold/italic, becomes the description.
  let description = '';
  if (/^(\*\*.*\*\*|\*.*\*)$/.test(lines[i]?.trim() ?? '')) {
    description = lines[i].trim().replace(/^\*+|\*+$/g, '');
    i++;
  }

  const body = lines.slice(i).join('\n').replace(/^\s*---\s*\n/, ''); // drop leading horizontal rule
  return { title, description, body };
}

const write = (path, { title, description, part }, body) =>
  writeFileSync(path, `---\ntitle: ${yaml(title)}\ndescription: ${yaml(description)}\npart: ${part}\n---\n\n${body}`);

for (const subject of SUBJECTS) {
  const out = join('content/docs', subject.slug);
  rmSync(out, { recursive: true, force: true });
  mkdirSync(out, { recursive: true });

  const files = readdirSync(subject.dir).filter((f) => f.endsWith('.md'));
  const bySlug = new Map();
  for (const file of files) {
    const slug = file.replace(/\.md$/, '').replace(/^.*?part-\d+-/, '').replace(/^(phase|module)-\d+[ab]?-/, '');
    bySlug.set(slug, { file, part: partNo(file) });
  }

  // The roadmap becomes the subject's landing page at /docs/<subject>.
  const index = bySlug.get(subject.index);
  if (!index) throw new Error(`${subject.slug}: no index chapter "${subject.index}"`);
  const indexNote = parseNote(join(subject.dir, index.file));
  write(join(out, 'index.md'), { ...indexNote, part: index.part }, indexNote.body);
  bySlug.delete(subject.index);

  for (const group of subject.groups) {
    const dir = join(out, group.slug);
    mkdirSync(dir, { recursive: true });
    for (const slug of group.pages) {
      const entry = bySlug.get(slug);
      if (!entry) throw new Error(`${subject.slug}: group "${group.slug}" lists unknown chapter "${slug}"`);
      const note = parseNote(join(subject.dir, entry.file));
      write(join(dir, `${slug}.md`), { ...note, part: entry.part }, note.body);
      bySlug.delete(slug);
    }
    writeFileSync(
      join(dir, 'meta.json'),
      JSON.stringify({ title: group.title, icon: group.icon, pages: group.pages }, null, 2),
    );
  }

  // Loud failure beats a chapter silently vanishing from the sidebar.
  if (bySlug.size) throw new Error(`${subject.slug}: chapters in no group: ${[...bySlug.keys()].join(', ')}`);

  writeFileSync(
    join(out, 'meta.json'),
    JSON.stringify(
      {
        title: subject.title,
        description: subject.description,
        icon: subject.icon,
        root: true,
        pages: ['index', ...subject.groups.map((g) => g.slug)],
      },
      null,
      2,
    ),
  );
  console.log(`synced ${subject.slug}: ${subject.groups.length} groups, ${files.length} chapters`);
}
