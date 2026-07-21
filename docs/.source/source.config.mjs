// source.config.ts
import { defineConfig } from "fumadocs-mdx/config";
var source_config_default = defineConfig({
  contentDir: "source",
  outputDir: ".source",
  mdxOptions(options) {
    return options;
  }
});
export {
  source_config_default as default
};
