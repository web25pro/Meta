import Link from 'next/link';

export default function SupportPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900 text-panda-white">
      <div className="container mx-auto px-4 py-20 max-w-4xl text-center">
        <Link href="/" className="text-blue-400 hover:text-blue-300 mb-8 inline-block">
          &larr; Back to the Jungle
        </Link>
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent">
          Jungle Support
        </h1>
        <div className="bg-blue-800 bg-opacity-60 backdrop-blur border border-blue-600 rounded-2xl p-12 shadow-2xl">
          <p className="text-xl text-blue-100 mb-8">
            Having trouble in the Meta-Jungle? Our elder pandas are here to help.
          </p>
          <div className="space-y-4">
            <p className="text-blue-200">
              For account issues, bamboo reward discrepancies, or technical glitches:
            </p>
            <a 
              href="mailto:support@lpanda.com" 
              className="text-2xl font-bold text-blue-300 hover:text-blue-200 block transition-colors"
            >
              support@lpanda.com
            </a>
          </div>
          <div className="mt-12 pt-12 border-t border-blue-700">
            <p className="text-blue-300 text-sm">
              Please include your username and a detailed description of your quest issues.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
