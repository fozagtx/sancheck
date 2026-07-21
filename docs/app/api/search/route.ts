import { createFromSource } from 'fumadocs-core/search';
import { getPages } from '@/source';

export const { staticGET: GET } = createFromSource(getPages());

