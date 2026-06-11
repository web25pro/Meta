import Link from 'next/link';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900 text-panda-white">
      <div className="container mx-auto px-4 py-20 max-w-4xl">
        <Link href="/" className="text-blue-400 hover:text-blue-300 mb-8 inline-block">
          &larr; Back to the Jungle
        </Link>
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent">
          Privacy Policy
        </h1>
        <div className="space-y-6 text-blue-100">
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">1. Introduction</h2>
            <p>
              Welcome to the LPanda Meta-Jungle. We respect your privacy and are committed to protecting your personal data. This privacy policy will inform you about how we look after your personal data when you visit our platform and tell you about your privacy rights and how the law protects you.
            </p>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">2. The Data We Collect</h2>
            <p>
              We may collect, use, store and transfer different kinds of personal data about you which we have grouped together as follows:
            </p>
            <ul className="list-disc ml-6 mt-2 space-y-2">
              <li>Identity Data includes first name, last name, username or similar identifier.</li>
              <li>Contact Data includes email address and telephone numbers.</li>
              <li>Technical Data includes internet protocol (IP) address, your login data, browser type and version, time zone setting and location.</li>
            </ul>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">3. How We Use Your Data</h2>
            <p>
              We will only use your personal data when the law allows us to. Most commonly, we will use your personal data in the following circumstances:
            </p>
            <ul className="list-disc ml-6 mt-2 space-y-2">
              <li>To register you as a new user in the Jungle.</li>
              <li>To manage your tasks and bamboo rewards.</li>
              <li>To provide you with relevant announcements and schedule updates.</li>
            </ul>
          </section>
          <section>
            <h2 className="text-2xl font-semibold text-panda-white mb-4">4. Data Security</h2>
            <p>
              We have put in place appropriate security measures to prevent your personal data from being accidentally lost, used or accessed in an unauthorised way, altered or disclosed.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
