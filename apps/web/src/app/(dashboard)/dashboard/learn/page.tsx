'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
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
import { metajungleAPI } from '@/api/metajungle';

interface Course {
  id: string;
  title: string;
  blurb: string;
  lessons: number;
  pp: number;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  progress: number;
  quiz: { q: string; options: string[] };
}

// Quiz data is stored server-side in the Course model's quiz JSONB field.
// The list endpoint returns the quiz question/options but NOT the answer index.
// The submitQuiz endpoint handles grading server-side.

const LEVEL_TONE = { Beginner: 'success', Intermediate: 'cobalt', Advanced: 'gold' } as const;

export default function LearnPage() {
  const queryClient = useQueryClient();
  const [active, setActive] = useState<Course | null>(null);
  const [picked, setPicked] = useState<number | null>(null);
  const [result, setResult] = useState<'idle' | 'correct' | 'wrong'>('idle');

  // Live courses from the backend. Quiz is graded server-side via submitQuiz.
  const { data, isLoading } = useQuery('mjCourses', metajungleAPI.listCourses, { retry: false });
  const courses: Course[] = data
    ? data.map((c) => ({
        id: c.id,
        title: c.title,
        blurb: c.blurb,
        lessons: c.lessons,
        pp: c.pp_reward,
        level: c.level,
        progress: 0,
        quiz: c.quiz ?? { q: '', options: [] },
      }))
    : [];

  const open = (c: Course) => {
    setActive(c);
    setPicked(null);
    setResult('idle');
  };

  const submit = async () => {
    if (picked === null || !active) return;
    try {
      const res = await metajungleAPI.submitQuiz(active.id, [picked]);
      setResult(res.passed ? 'correct' : 'wrong');
      if (res.passed) {
        toast.success(res.pp_awarded > 0 ? `Quiz passed! +${res.pp_awarded} PP` : 'Quiz already completed');
        queryClient.invalidateQueries('pointsHistory');
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to submit quiz');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Learn to Earn</h1>
        <p className="mt-1 text-body text-ink-muted">
          Complete courses, pass the quiz, and earn Panda Points.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-lg sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-64 animate-pulse rounded-card bg-bg-elevated" />
          ))}
        </div>
      ) : courses.length === 0 ? (
        <div className="rounded-card border border-line bg-bg-primary p-xl text-center text-ink-muted">
          No courses available yet. Check back soon!
        </div>
      ) : (
      <div className="grid gap-lg sm:grid-cols-2">
        {courses.map((c) => (
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
              <ProgressBar value={c.progress} tone={c.progress === 100 ? 'gold' : 'jungle'} />
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
      )}

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
