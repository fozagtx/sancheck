import { defineConfig } from 'fumadocs-mdx/config';

export default defineConfig({
  contentDir: 'source',
  outputDir: '.source',
  mdxOptions(options) {
    return options;
  },
});
