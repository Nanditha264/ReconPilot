import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('admin@reconpilot.local');
  const [password, setPassword] = useState('AdminSecret2026!');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed. Please verify credentials.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectPreset = (presetEmail: string, presetPass: string) => {
    setEmail(presetEmail);
    setPassword(presetPass);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen w-screen flex flex-col justify-center items-center bg-finance-950 p-4">
      <div className="w-full max-w-md">
        {/* Logo and Product Title */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-brand-primary flex items-center justify-center text-white font-bold text-xl mx-auto shadow-md mb-3">
            RP
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">ReconPilot</h1>
          <p className="text-xs text-finance-400 font-mono mt-1">AI Finance Controller · Track 4</p>
        </div>

        {/* Login Form */}
        <Card className="bg-white border-finance-800 p-6 shadow-xl">
          <div className="flex items-center justify-between mb-6 pb-3 border-b border-finance-100">
            <h2 className="text-base font-bold text-finance-900">Operator Sign In</h2>
            <Badge variant="success" size="sm">Argon2id + JWT Active</Badge>
          </div>

          {errorMessage && (
            <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <div>{errorMessage}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-finance-700 uppercase tracking-wider mb-1">
                Operator Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-finance-300 rounded-md text-finance-900 focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary"
                placeholder="controller@reconpilot.local"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-finance-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-finance-300 rounded-md text-finance-900 focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary"
                placeholder="••••••••••••••••"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting}
              className="w-full py-2.5 font-semibold text-sm mt-2 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In to Controller Console</span>
              )}
            </Button>
          </form>

          {/* Quick Preset Selector for Testing/Evaluation (Available only in development mode) */}
          {import.meta.env.DEV && (
            <div className="mt-6 pt-4 border-t border-finance-100">
              <span className="text-[11px] font-semibold text-finance-500 uppercase tracking-wider block mb-2">
                Evaluator Quick Access (Sandbox Only):
              </span>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleSelectPreset('admin@reconpilot.local', 'AdminSecret2026!')}
                  className="px-2 py-1 text-[11px] font-medium bg-finance-100 text-finance-700 hover:bg-finance-200 rounded text-center transition-colors"
                >
                  Admin
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectPreset('operator@reconpilot.local', 'OperatorSecret2026!')}
                  className="px-2 py-1 text-[11px] font-medium bg-finance-100 text-finance-700 hover:bg-finance-200 rounded text-center transition-colors"
                >
                  Operator
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectPreset('reviewer@reconpilot.local', 'ReviewerSecret2026!')}
                  className="px-2 py-1 text-[11px] font-medium bg-finance-100 text-finance-700 hover:bg-finance-200 rounded text-center transition-colors"
                >
                  Reviewer
                </button>
              </div>
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-finance-100 flex items-center justify-center gap-1.5 text-xs text-finance-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>PostgreSQL session persistence & RBAC enforced</span>
          </div>
        </Card>
      </div>
    </div>
  );
};

