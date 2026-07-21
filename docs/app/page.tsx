import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-sm font-medium text-emerald-700">
        <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
        Codex Plugin
      </div>
      <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl">
        sancheck
      </h1>
      <p className="mt-6 max-w-2xl text-lg leading-relaxed text-gray-600">
        URL safety middleware for agent workflows. Scan links before a build tool,
        script, or plugin opens them. Returns a machine-readable allow or block decision.
      </p>
      <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        <Link
          href="/docs/getting-started"
          className="rounded-full bg-emerald-700 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800"
        >
          Get Started
        </Link>
        <Link
          href="/docs"
          className="rounded-full border border-gray-200 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm transition hover:bg-gray-50"
        >
          Documentation
        </Link>
      </div>
      <div className="mt-16 grid max-w-3xl grid-cols-1 gap-6 sm:grid-cols-3">
        <FeatureCard
          title="URL Gate"
          description="Extract and validate URLs from any text or JSON payload."
        />
        <FeatureCard
          title="Prompt Injection"
          description="Detect hidden instructions in fetched page content."
        />
        <FeatureCard
          title="Middleware Contract"
          description="stdin in, JSON decision out. Exit codes for CI/CD."
        />
      </div>
    </main>
  );
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-gray-100 bg-white p-6 text-left shadow-sm">
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-gray-600">{description}</p>
    </div>
  );
}
