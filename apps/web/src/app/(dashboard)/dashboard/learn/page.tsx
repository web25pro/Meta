'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { BookOpen, Check, Trophy } from 'lucide-react';
import {
  Card,
  Button,
  Badge,
  PPAmount,
  Modal,
  ProgressBar,
  cn,
} from '@meta-jungle/ui';

interface Course {
  id: string;
  title: string;
  blurb: string;
  lessons: number;
  pp: number;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  progress: number;
  quiz: { q: string; options: string[]; answer: number };
}

const COURSES: Course[] = [
  {
    id: '1', title: 'Web3 Foundations', blurb: 'Wallets, keys, and how blockchains work.', lessons: 6, pp: 200, level: 'Beginner', progress: 100,
    quiz: { q: 'What secures ownership of a crypto wallet?', options: ['A username', 'A private key', 'An email', 'A phone number'], answer: 1 },
  },
  {
    id: '2', title: 'Understanding Base', blurb: 'Why L2s matter and how Base scales Ethereum.', lessons: 5, pp: 250, level: 'Beginner', progress: 60,
    quiz: { q: 'Base is best described as a…', options: ['Layer 1', 'Layer 2 rollup', 'Centralized bank', 'Stablecoin'], answer: 1 },
  },
  {
    id: '3', title: 'DeFi Essentials', blurb: 'Liquidity, yield, and managing risk.', lessons: 8, pp: 400, level: 'Intermediate', progress: 0,
    quiz: { q: 'Providing liquidity exposes you to…', options: ['Nothing', 'Impermanent loss', 'Higher gas only', 'Account bans'], answer: 1 },
  },
  {
    id: '4', title: 'NFT Utility & Reputation', blurb: 'How NFTs unlock real-world value on Meta-Jungle.', lessons: 4, pp: 300, level: 'Intermediate', progress: 0,
    quiz: { q: 'A soul-bound NFT is…', options: ['Freely tradable', 'Non-transferable', 'Always free', 'A stablecoin'], answer: 1 },
  },
];

const LEVEL_TONE = { Beginner: 'success', Intermediate: 'cobalt', Advanced: 'gold' } as const;

export default function LearnPage() {
  const [active, setActive] = useState<Course | null>(null);
  const [picked, setPicked] = useState<number | null>(null);
  const [result, setResult] = useState<'idle' | 'correct' | 'wrong'>('idle');

  const open = (c: Course) => {
    setActive(c);
    setPicked(null);
    setResult('idle');
  };

  const submit = () => {
    if (picked === null || !active) return;
    const ok = picked === active.quiz.answer;
    setResult(ok ? 'correct' : 'wrong');
    if (ok) toast.success(`Quiz passed! +${active.pp} PP`);
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Learn to Earn</h1>
        <p className="mt-1 text-body text-ink-muted">
          Complete courses, pass the quiz, and earn Panda Points.
        </p>
      </div>

      <div className="grid gap-lg sm:grid-cols-2">
        {COURSES.map((c) => (
          <Card key={c.id} className="flex flex-col gap-md">
            <div className="flex items-start justify-between">
              <div className="rounded-card bg-brand-ice p-3 text-brand-cobalt">
                <BookOpen className="h-6 w-6" />
              </div>
              <Badge tone={LEVEL_TONE[c.level]}>{c.level}</Badge>
            </div>
            <div>
              <h3 className="font-display text-h2 text-ink-primary">{c.title}</h3>
              <p className="text-label text-ink-muted">{c.blurb}</p>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-label text-ink-muted">
                <span>{c.lessons} lessons</span>
                <span>{c.progress}% complete</span>
              </div>
              <ProgressBar value={c.progress} tone={c.progress === 100 ? 'gold' : 'sky'} />
            </div>
            <div className="mt-auto flex items-center justify-between">
              <PPAmount value={c.pp} size="sm" />
              <Button size="sm" onClick={() => open(c)}>
                {c.progress === 100 ? 'Take Quiz' : c.progress > 0 ? 'Continue' : 'Start'}
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Modal open={!!active} onClose={() => setActive(null)} title={active?.title}>
        {active && (
          <div className="space-y-lg">
            {result === 'correct' ? (
              <div className="space-y-md text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
                  <Trophy className="h-8 w-8 text-reward-gold" />
                </div>
                <h3 className="font-display text-h2 text-ink-primary">Quiz passed!</h3>
                <p className="text-body text-ink-muted">You earned</p>
                <PPAmount value={active.pp} size="lg" />
                <Button className="w-full" onClick={() => setActive(null)}>Done</Button>
              </div>
            ) : (
              <>
                <p className="text-body text-ink-primary">{active.quiz.q}</p>
                <div className="space-y-sm">
                  {active.quiz.options.map((opt, i) => (
                    <button
                      key={i}
                      onClick={() => { setPicked(i); setResult('idle'); }}
                      className={cn(
                        'flex w-full items-center justify-between rounded-card border px-md py-sm text-left text-body transition-colors',
                        picked === i
                          ? 'border-brand-cobalt bg-brand-ice text-ink-primary'
                          : 'border-line bg-bg-primary text-ink-primary hover:bg-bg-elevated',
                      )}
                    >
                      {opt}
                      {picked === i && <Check className="h-4 w-4 text-brand-cobalt" />}
                    </button>
                  ))}
                </div>
                {result === 'wrong' && (
                  <p className="rounded-card bg-danger/10 px-md py-sm text-label text-danger">
                    Not quite — review the lesson and try again.
                  </p>
                )}
                <Button className="w-full" onClick={submit} disabled={picked === null}>
                  Submit Answer
                </Button>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
