import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';
import { Inter, JetBrains_Mono } from 'next/font/google';
import SubjectSearchDialog from '@/components/search-dialog';
import type { Metadata } from 'next';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jetbrains' });

export const metadata: Metadata = {
  title: { template: '%s · Core CS Notes', default: 'Core CS Notes' },
  description:
    'Core computer science, resume skills, system design, product and analytics — interview handbooks, chapter by chapter.',
  applicationName: 'Core CS Notes',
  // app/icon.svg is picked up automatically for the tab icon.
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <RootProvider
          theme={{ defaultTheme: 'dark' }}
          search={{ SearchDialog: SubjectSearchDialog }}
        >
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
