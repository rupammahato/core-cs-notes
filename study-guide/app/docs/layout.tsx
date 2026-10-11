import { source } from '@/lib/source';
import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import { baseOptions } from '@/lib/layout.shared';

export default function Layout({ children }: LayoutProps<'/docs'>) {
  return (
    // Subject switcher (DSA / OOP / OS) is the dropdown at the top of the sidebar.
    // tabMode="top" renders the tabs but blanks the page body on this layout — don't.
    <DocsLayout tree={source.getPageTree()} {...baseOptions()}>
      {children}
    </DocsLayout>
  );
}
