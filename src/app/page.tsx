export default function Home() {
  return (
    <div className="min-h-screen bg-[var(--surface)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface-elevated)]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-[var(--primary)]"></div>
              <h1 className="text-xl font-semibold text-[var(--text)]">
                Social Media AI Panel
              </h1>
            </div>
            <nav className="flex items-center gap-6">
              <a 
                href="#" 
                className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors cursor-pointer"
              >
                Dashboard
              </a>
              <a 
                href="#" 
                className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors cursor-pointer"
              >
                Analytics
              </a>
              <a 
                href="#" 
                className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors cursor-pointer"
              >
                Content
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-[var(--text)] text-balance">
            Welcome to Your
            <span className="gradient-text"> AI-Powered</span>
            <br />
            Social Media Command Center
          </h2>
          
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--text-muted)]">
            Scrape competitor data, generate AI content, and schedule posts 
            across Twitter/X, LinkedIn, Instagram, and Bluesky — all from one dashboard.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <button className="inline-flex items-center justify-center rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-white hover:bg-[var(--primary-hover)] transition-colors cursor-pointer">
              Get Started
            </button>
            <button className="inline-flex items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)] px-6 py-3 text-sm font-medium text-[var(--text)] hover:bg-[var(--secondary)] transition-colors cursor-pointer">
              View Documentation
            </button>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="mt-20 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              title: "Intelligence Hub",
              description: "Track competitors and analyze viral content across platforms",
              color: "var(--chart-1)",
            },
            {
              title: "AI Content Generator",
              description: "Generate engaging posts and threads with AI assistance",
              color: "var(--chart-2)",
            },
            {
              title: "Smart Scheduler",
              description: "Schedule posts at optimal times for maximum engagement",
              color: "var(--chart-3)",
            },
            {
              title: "Analytics Dashboard",
              description: "Track performance metrics and growth across all platforms",
              color: "var(--chart-4)",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6 transition-all hover:-translate-y-0.5 hover:shadow-lg cursor-pointer"
              style={{ transitionDuration: "var(--duration-normal)" }}
            >
              <div
                className="mb-4 h-2 w-12 rounded-full"
                style={{ backgroundColor: feature.color }}
              />
              <h3 className="text-lg font-semibold text-[var(--text)]">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-[var(--text-muted)]">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
