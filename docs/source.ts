import { createMDXSource } from 'fumadocs-mdx';
import { loader } from 'fumadocs-core/framework/next';
import { docs, meta } from './.source';

export const { getPage, getPages, pageTree } = loader({
  baseUrl: '/docs',
  source: createMDXSource(docs, meta),
  i18n: false,
});

export type Page = ReturnType<typeof getPage>;

