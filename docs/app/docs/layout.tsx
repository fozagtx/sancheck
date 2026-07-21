import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import { pageTree } from '@/source';
import type { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <DocsLayout
      tree={pageTree}
      nav={{
        title: 'seccheck',
      }}
      links={[
        {
          text: 'Getting Started',
          url: '/docs/getting-started',
          active: 'nested-url',
        },
      ]}
    >
      {children}
    </DocsLayout>
  );
}
