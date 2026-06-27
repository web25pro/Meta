import Link from 'next/link';
import {
  ArrowRight,
  Trophy,
  Wallet,
  Target,
  ShieldCheck,
  Smartphone,
  Phone,
  Ticket,
  Gift,
  GraduationCap,
} from 'lucide-react';
import {
  Button,
  PandaMascot,
  LeaderboardRow,
  PPAmount,
} from '@meta-jungle/ui';

/**
 * Meta-Jungle landing page (Master Prompt v3.0, Chapter 4.1).
 * Navy hero with bamboo texture, white feature grid, ice-blue utility showcase,
 * leaderboard preview. White-first; bamboo gold reserved for PP only.
 */
export default function HomePage() {
  return (
    <div className="min-h-screen bg-bg-primary text-ink-primary">
      {/* ── Nav Bar (panda navy) ───────────────────────────────────────── */}
      <header className="bg-bg-dark">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-md py-md">
          <div className="flex items-center gap-sm">
            <span className="text-2xl">🐼</span>
            <span className="font-display text-xl font-bold text-ink-inverse">
              Meta-Jungle
            </span>
          </div>
          <div className="hidden items-center gap-xl text-label text-brand-ice md:flex">
            <Link href="#features" className="hover:text-ink-inverse">Features</Link>
            <Link href="#utility" className="hover:text-ink-inverse">Marketplace</Link>
            <Link href="#leaderboard" className="hover:text-ink-inverse">Leaderboard</Link>
            <Link href="/auth/register" className="hover:text-ink-inverse">Partners</Link>
          </div>
          <div className="flex items-center gap-sm">
            <Link href="/auth/login">
              <Button variant="ghost" size="sm" className="border-brand-ice/40 text-ink-inverse hover:bg-white/10">
                Sign In
              </Button>
            </Link>
            <Link href="/auth/register">
              <Button size="sm">Connect Wallet</Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Hero (navy + bamboo texture) ───────────────────────────────── */}
      <section className="relative overflow-hidden bg-bg-dark">
        <div className="bamboo-texture pointer-events-none absolute inset-0" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-2xl px-md py-3xl md:grid-cols-2">
          <div>
            <h1 className="font-display text-display-lg leading-none text-ink-inverse text-balance">
              Your actions have value here.
            </h1>
            <p className="mt-lg max-w-md text-xl text-brand-ice">
              Earn Panda Points. Unlock real-world utilities. Own your reputation.
            </p>
            <div className="mt-xl flex flex-wrap gap-md">
              <Link href="/auth/register">
                <Button variant="gradient" size="lg">
                  Start Earning <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="#leaderboard">
                <Button variant="ghost" size="lg" className="border-brand-ice/40 text-ink-inverse hover:bg-white/10">
                  View Leaderboard
                </Button>
              </Link>
            </div>
            {/* Live stats ticker */}
            <div className="mt-xl flex flex-wrap gap-sm">
              {[
                '47,291 users',
                '2.4M PP earned today',
                '138 active campaigns',
              ].map((s) => (
                <span
                  key={s}
                  className="rounded-pill bg-brand-cobalt/30 px-md py-1 text-label text-ice"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div className="flex justify-center">
            <PandaMascot size={220} />
          </div>
        </div>
      </section>

      {/* ── Features Grid (white) ──────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-6xl px-md py-3xl">
        <h2 className="text-center font-display text-h1 text-ink-primary">
          Everything you need to earn, own, and access
        </h2>
        <div className="mt-2xl grid gap-lg md:grid-cols-3">
          <FeatureCard icon={<Target />} title="Complete Quests" desc="Social, partner, learning and daily quests — earn Panda Points for verified actions." />
          <FeatureCard icon={<Wallet />} title="Panda Wallet" desc="Hold PP, LPanda and USDC. Send, receive, swap, stake — P2P trade with escrow." />
          <FeatureCard icon={<Trophy />} title="Climb the Leaderboard" desc="Global and regional rankings refreshed continuously across Africa, Asia & Europe." />
          <FeatureCard icon={<ShieldCheck />} title="Three-Score Reputation" desc="Activity, Reputation & Influence build a portable on-chain identity you protect." />
          <FeatureCard icon={<Gift />} title="Redeem Utilities" desc="Airtime, gift cards, events, education and healthcare — spend PP on real value." />
          <FeatureCard icon={<Smartphone />} title="Earn Anywhere" desc="Web today, native mobile next. Your jungle travels with you." />
        </div>
      </section>

      {/* ── Utility Showcase (ice-blue) ────────────────────────────────── */}
      <section id="utility" className="bg-bg-elevated">
        <div className="mx-auto max-w-6xl px-md py-3xl">
          <h2 className="font-display text-h1 text-ink-primary">
            Redeem your points anywhere.
          </h2>
          <div className="mt-xl flex gap-md overflow-x-auto pb-md">
            <UtilityCard icon={<Phone />} name="Airtime ₦100" from={200} />
            <UtilityCard icon={<Ticket />} name="Concert ticket" from={1000} />
            <UtilityCard icon={<Gift />} name="Amazon GC $10" from={1100} />
            <UtilityCard icon={<GraduationCap />} name="Web3 bootcamp" from={3000} />
            <UtilityCard icon={<Phone />} name="Data Bundle 1GB" from={500} />
          </div>
        </div>
      </section>

      {/* ── Leaderboard Preview (white) ────────────────────────────────── */}
      <section id="leaderboard" className="mx-auto max-w-3xl px-md py-3xl">
        <h2 className="font-display text-h1 text-ink-primary">Top of the Jungle</h2>
        <div className="mt-xl overflow-hidden rounded-card border border-line bg-bg-primary shadow-card">
          <LeaderboardRow rank={1} username="panda_king" role="Alpha OG" ppEarned={184920} rankChange={2} />
          <LeaderboardRow rank={2} username="bamboo.eth" role="OG Panda" ppEarned={151340} rankChange={-1} />
          <LeaderboardRow rank={3} username="jungle_runner" role="OG Panda" ppEarned={142180} rankChange={1} />
          <div className="relative">
            <div className="pointer-events-none select-none blur-sm">
              <LeaderboardRow rank={4} username="••••••••" ppEarned={98000} />
              <LeaderboardRow rank={5} username="••••••••" ppEarned={91000} />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <Link href="/auth/register">
                <Button>Connect wallet to see your rank</Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer (panda navy) ────────────────────────────────────────── */}
      <footer className="bg-bg-dark">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-sm px-md py-xl text-label text-brand-ice">
          <span>Earn everywhere. Spend everywhere. Own everything.</span>
          <span className="text-ink-muted">
            © {new Date().getFullYear()} Meta-Jungle Ecosystem · Powered by LPanda NFT · Built on Base
          </span>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <div className="group rounded-card border border-line bg-bg-primary p-lg shadow-card transition-all hover:border-b-4 hover:border-b-brand-cobalt hover:shadow-card-hover">
      <div className="mb-md text-brand-cobalt">{icon}</div>
      <h3 className="font-display text-h2 text-ink-primary">{title}</h3>
      <p className="mt-sm text-body text-ink-muted">{desc}</p>
    </div>
  );
}

function UtilityCard({
  icon,
  name,
  from,
}: {
  icon: React.ReactNode;
  name: string;
  from: number;
}) {
  return (
    <div className="w-44 shrink-0 rounded-card border border-line bg-bg-primary p-lg shadow-card">
      <div className="mb-md text-brand-cobalt">{icon}</div>
      <div className="text-body font-medium text-ink-primary">{name}</div>
      <div className="mt-sm text-label text-ink-muted">
        From <PPAmount value={from} size="sm" />
      </div>
    </div>
  );
}
