import { getPage, getPages } from '@/source';
import { DocsPage, DocsBody, DocsDescription, DocsTitle } from 'fumadocs-ui/page';
import { notFound } from 'next/navigation';
import defaultMdxComponents from 'fumadocs-ui/mdx';

export default async function Page(props: { params: Promise<{ slug?: string[] }> }) {
  const params = await props.params;
  const page = getPage(params.slug);

  if (!page) notFound();

  const MDX = page.data.exports.default;

  return (
    <DocsPage toc={page.data.toc} full={page.data.full}>
      <DocsTitle>{page.data.title}</DocsTitle>
      <DocsDescription>{page.data.description}</DocsDescription>
      <DocsBody>
        <MDX components={defaultMdxComponents} />
      </DocsBody>
    </DocsPage>
  );
}

export async function generateStaticParams() {
  return getPages().map((page) => ({
    slug: page.slugs,
  }));
}

export function generateMetadata(props: { params: Promise<{ slug?: string[] }> }) {
  return props.params.then(async (params) => {
    const page = getPage(params.slug);
    if (!page) return {};
    return {
      title: page.data.title,
      description: page.data.description,
    };
  });
}
