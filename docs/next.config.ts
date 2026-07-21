import { createMDX } from 'fumadocs-mdx/next';
import type { NextConfig } from 'next';

const withMDX = createMDX();

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: 'export',
  basePath: '/sancheck',
  images: {
    unoptimized: true,
  },
};

export default withMDX(nextConfig);
