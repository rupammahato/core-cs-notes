'use client';

// Fumadocs' DefaultSearchDialog renders its footer (which holds the tag filter) as a sibling of
// the portaled popup, so passing `tags` leaks a stray row onto every page. Same dialog, with the
// subject filter moved inside the popup where it belongs.
import { useState } from 'react';
import { useDocsSearch } from 'fumadocs-core/search/client';
import { fetchClient } from 'fumadocs-core/search/client/fetch';
import {
  SearchDialog,
  SearchDialogClose,
  SearchDialogContent,
  SearchDialogHeader,
  SearchDialogIcon,
  SearchDialogInput,
  SearchDialogList,
  SearchDialogOverlay,
  TagsList,
  TagsListItem,
} from 'fumadocs-ui/components/dialog/search';
import type { SharedProps } from 'fumadocs-ui/contexts/search';

const subjects = [
  { name: 'DSA', value: 'dsa' },
  { name: 'OOP', value: 'oop' },
  { name: 'OS', value: 'os' },
  { name: 'DBMS', value: 'dbms' },
  { name: 'CN', value: 'cn' },
  { name: 'Resume Skills', value: 'resume-skills' },
  { name: 'System Design', value: 'system-design' },
  { name: 'Product & Analytics', value: 'product-analytics' },
];

export default function SubjectSearchDialog(props: SharedProps) {
  const [tag, setTag] = useState<string>();
  const { search, setSearch, query } = useDocsSearch({
    client: fetchClient({ api: '/api/search', tag }),
  });

  return (
    <SearchDialog
      search={search}
      onSearchChange={setSearch}
      isLoading={query.isLoading}
      {...props}
    >
      <SearchDialogOverlay />
      <SearchDialogContent>
        <SearchDialogHeader>
          <SearchDialogIcon />
          <SearchDialogInput />
          <SearchDialogClose />
        </SearchDialogHeader>
        <SearchDialogList items={query.data !== 'empty' ? query.data : null} />
        <TagsList
          tag={tag}
          onTagChange={setTag}
          allowClear
          className="border-t bg-fd-secondary/50 p-3"
        >
          {subjects.map((subject) => (
            <TagsListItem key={subject.value} value={subject.value}>
              {subject.name}
            </TagsListItem>
          ))}
        </TagsList>
      </SearchDialogContent>
    </SearchDialog>
  );
}
