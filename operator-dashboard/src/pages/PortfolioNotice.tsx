import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, AlertTriangle, CheckCircle, Code, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui';

export default function PortfolioNotice() {
  const [countdown, setCountdown] = useState(5);
  const navigate = useNavigate();

  useEffect(() => {
    // Show portfolio notice on every login (5 second countdown)
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          navigate('/dashboard', { replace: true });
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [navigate]);

  const handleSkip = () => {
    navigate('/dashboard', { replace: true });
  };

  return (
    <div onClick={handleSkip} className="min-h-screen flex items-center justify-center bg-gradient-to-br from-neutral-50 via-blue-50 to-purple-50 dark:from-neutral-950 dark:via-blue-950 dark:to-purple-950 p-4 cursor-pointer">
      <div className="max-w-3xl w-full space-y-8 p-8 md:p-12 bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-neutral-200 dark:border-neutral-700">

        {/* Header with Icon */}
        <div className="text-center">
          <div className="mx-auto h-20 w-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 text-white flex items-center justify-center mb-6 shadow-lg">
            <Rocket className="h-10 w-10" />
          </div>

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 mb-4">
            <Code className="h-4 w-4 text-amber-700 dark:text-amber-400" />
            <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">
              Portfolio Project - In Development
            </span>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-neutral-100 mb-3">
            30-Day Content Jumpstart
          </h1>
          <p className="text-xl text-neutral-600 dark:text-neutral-400">
            AI-Powered Content Generation Platform
          </p>
        </div>

        {/* Description */}
        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <p className="text-center text-neutral-700 dark:text-neutral-300 leading-relaxed">
            This is a demonstration project showcasing AI-driven content creation capabilities
            using Claude 3.5 Sonnet, async generation, and multi-platform support.
          </p>
        </div>

        {/* Status Grid */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Implemented Features */}
          <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-5">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                  Fully Functional
                </h3>
                <ul className="text-sm text-green-800 dark:text-green-200 space-y-1">
                  <li>• Content generation engine</li>
                  <li>• Template system (15 types)</li>
                  <li>• Quality validation</li>
                  <li>• Client & project management</li>
                  <li>• Research tools integration</li>
                </ul>
              </div>
            </div>
          </div>

          {/* In Development */}
          <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-amber-900 dark:text-amber-100 mb-2">
                  In Development
                </h3>
                <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-1">
                  <li>• Some analytics features</li>
                  <li>• User management UI</li>
                  <li>• Export compatibility</li>
                  <li>• Integration configurations</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Tech Stack Badge */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 pt-6">
          <p className="text-xs text-center text-neutral-500 dark:text-neutral-400 mb-4">
            Built with React • TypeScript • Tailwind • Python • FastAPI • Claude AI
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <div className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400">
            <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {countdown}
              </span>
            </div>
            <span className="text-sm">
              Redirecting to dashboard in {countdown} second{countdown !== 1 ? 's' : ''}...
            </span>
            <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-3 flex items-center justify-center gap-2">
              <span className="animate-pulse">✨</span>
              <span>Click anywhere to continue immediately</span>
              <span className="animate-pulse">✨</span>
            </p>
          </div>

          <Button
            onClick={handleSkip}
            variant="primary"
            className="group"
          >
            Skip to Dashboard
            <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>

        {/* Footer Note */}
        <div className="text-center pt-4">
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            This notice appears once per session to set expectations about feature completeness
          </p>
        </div>
      </div>
    </div>
  );
}
