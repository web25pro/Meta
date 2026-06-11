import Link from 'next/link';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900 text-panda-white">
      <div className="container mx-auto px-4 py-20 max-w-4xl">
        <Link href="/" className="text-blue-400 hover:text-blue-300 mb-8 inline-block">
          &larr; Back to the Jungle
        </Link>
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent">
          Terms of Service
        </h1>
        <div className="space-y-6 text-blue-100">
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing and using the LPanda Meta-Jungle Platform, you agree to be bound by these Terms of Service and all applicable laws and regulations.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">2. Use License</h2>
            <p>
              Permission is granted to temporarily use the platform for personal, non-commercial transitory viewing and participation in the Jungle ecosystem.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">3. Jungle Conduct</h2>
            <p>
              Users are expected to behave appropriately within the community. Any attempt to exploit the task system or manipulate bamboo rewards will result in immediate banishment from the Jungle.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">4. Disclaimer</h2>
            <p>
              The materials on the LPanda platform are provided on an 'as is' basis. LPanda makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
