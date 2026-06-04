import Link from 'next/link';
import { ArrowRight, Leaf, Target, Users, TrendingUp, Flame, Crown } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900">
      {/* Jungle background decorations */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
        <div className="absolute top-10 left-5 text-9xl opacity-5">🌿</div>
        <div className="absolute bottom-10 right-5 text-9xl opacity-5">🎋</div>
        <div className="absolute top-1/3 right-10 text-8xl opacity-5">🐼</div>
      </div>

      {/* Header */}
      <header className="container mx-auto px-4 py-6 border-b border-blue-700 relative z-10">
        <nav className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-400 rounded-full flex items-center justify-center font-bold text-jungle-900 shadow-lg shadow-blue-400/50">
              🐼
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent">LPanda</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              href="/login"
              className="text-blue-200 hover:text-panda-white transition-colors font-medium"
            >
              Login
            </Link>
            <Link
              href="/auth/register"
              className="bg-blue-600 text-panda-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-lg shadow-blue-600/50"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          <div className="text-6xl mb-6 filter drop-shadow-lg animate-bounce">🌿</div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Welcome to the
            <span className="bg-gradient-to-r from-blue-400 via-blue-300 to-panda-white bg-clip-text text-transparent"> Jungle Realm</span>
          </h1>
          <p className="text-xl text-blue-100 mb-8">
            Join our panda community in the jungle. Complete tasks, earn bamboo rewards, and climb to legendary status.
          </p>
          <div className="flex items-center justify-center space-x-4 flex-wrap">
            <Link
              href="/auth/register"
              className="bg-gradient-to-r from-blue-600 to-blue-500 text-panda-white px-8 py-4 rounded-lg hover:from-blue-700 hover:to-blue-600 transition-all flex items-center space-x-2 text-lg font-semibold shadow-lg shadow-blue-600/50"
            >
              <span>Start Your Quest</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/login"
              className="border-2 border-blue-400 text-blue-300 px-8 py-4 rounded-lg hover:bg-blue-400 hover:text-jungle-900 transition-all text-lg font-semibold"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mt-20">
          <FeatureCard
            icon={<Leaf className="h-8 w-8 text-blue-400" />}
            title="Complete Quests"
            description="Take on jungle challenges and earn bamboo rewards"
          />
          <FeatureCard
            icon={<Flame className="h-8 w-8 text-blue-300" />}
            title="Build Your Streak"
            description="Daily activities to grow your power in the jungle"
          />
          <FeatureCard
            icon={<TrendingUp className="h-8 w-8 text-blue-400" />}
            title="Climb the Ranks"
            description="Rise from novice to legendary jungle warrior"
          />
          <FeatureCard
            icon={<Crown className="h-8 w-8 text-blue-300" />}
            title="Unlock Treasures"
            description="Discover hidden rewards and exclusive perks"
          />
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-8 mt-20 text-center">
          <StatCard number="10K+" label="Jungle Warriors" />
          <StatCard number="50K+" label="Quests Completed" />
          <StatCard number="1M+" label="Bamboo Earned" />
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-20 border-t border-blue-700 relative z-10">
        <div className="text-center text-blue-100">
          <p>&copy; 2024 LPanda Platform - Where Pandas Thrive in the Jungle. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-gradient-to-br from-blue-800 to-jungle-800 bg-opacity-60 backdrop-blur border border-blue-600 rounded-lg p-8 text-center hover:bg-opacity-80 transition-all hover:shadow-lg hover:shadow-blue-500/20">
      <div className="flex justify-center mb-4">{icon}</div>
      <h3 className="text-lg font-bold text-panda-white mb-2">{title}</h3>
      <p className="text-blue-100">{description}</p>
    </div>
  );
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="bg-gradient-to-br from-blue-700 to-jungle-800 bg-opacity-60 backdrop-blur border border-blue-600 rounded-lg p-8 hover:shadow-lg hover:shadow-blue-500/20 transition-all">
      <div className="text-3xl font-bold text-blue-300 mb-2">{number}</div>
      <div className="text-blue-100 font-medium">{label}</div>
    </div>
  );
}
