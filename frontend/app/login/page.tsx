"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { login, register } from "@/lib/api";
import { useStore } from "@/lib/store";

/* ------------------------------------------------------------------ */
/*  Animation variants                                                 */
/* ------------------------------------------------------------------ */

const cardVariants = {
  hidden: { opacity: 0, y: 32 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as number[] },
  },
};

const fieldVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.35, ease: "easeOut" },
  }),
};

const errorVariants = {
  hidden: { opacity: 0, height: 0 },
  visible: { opacity: 1, height: "auto", transition: { duration: 0.25 } },
  exit: { opacity: 0, height: 0, transition: { duration: 0.2 } },
};

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

function BackgroundOrb({
  style,
  delay,
}: {
  style: React.CSSProperties;
  delay: number;
}) {
  return (
    <motion.div
      className="absolute rounded-full blur-3xl pointer-events-none"
      style={style}
      animate={{ scale: [1, 1.15, 1], opacity: [0.15, 0.28, 0.15] }}
      transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay }}
    />
  );
}

function Spinner() {
  return (
    <motion.span
      className="inline-block h-4 w-4 rounded-full border-2 border-white/30 border-t-white"
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 0.75, ease: "linear" }}
      aria-hidden="true"
    />
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function LoginPage() {
  const router = useRouter();
  const setToken = useStore((s) => s.setToken);
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const slideDir = useRef<1 | -1>(1);

  const handleToggle = () => {
    slideDir.current = isRegister ? -1 : 1;
    setIsRegister((v) => !v);
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const resp = isRegister
        ? await register(email, displayName, password)
        : await login(email, password);

      setToken(resp.data.access_token);
      router.push(isRegister ? "/onboarding" : "/dashboard");
    } catch (err: unknown) {
      const axErr = err as {
        response?: { status?: number; data?: { detail?: string } };
      };
      const status = axErr?.response?.status;
      const msg = axErr?.response?.data?.detail;
      if (status === 409) {
        setError("This email is already registered. Try signing in instead.");
      } else {
        setError(msg || "Authentication failed");
      }
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-colors";

  const fields = isRegister
    ? [
        <motion.div key="name" custom={0} variants={fieldVariants} initial="hidden" animate="visible">
          <input
            type="text"
            placeholder="Display Name"
            aria-label="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className={inputClass}
            required
          />
        </motion.div>,
        <motion.div key="email-reg" custom={1} variants={fieldVariants} initial="hidden" animate="visible">
          <input
            type="email"
            placeholder="Email"
            aria-label="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
            required
          />
        </motion.div>,
        <motion.div key="pw-reg" custom={2} variants={fieldVariants} initial="hidden" animate="visible">
          <input
            type="password"
            placeholder="Password"
            aria-label="Password, minimum 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
            required
            minLength={8}
          />
        </motion.div>,
      ]
    : [
        <motion.div key="email-login" custom={0} variants={fieldVariants} initial="hidden" animate="visible">
          <input
            type="email"
            placeholder="Email"
            aria-label="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
            required
          />
        </motion.div>,
        <motion.div key="pw-login" custom={1} variants={fieldVariants} initial="hidden" animate="visible">
          <input
            type="password"
            placeholder="Password"
            aria-label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
            required
            minLength={8}
          />
        </motion.div>,
      ];

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-gray-950 overflow-hidden">
      {/* Animated background gradient orbs */}
      <BackgroundOrb
        style={{
          left: "-10%", top: "5%", width: "40vw", height: "40vw",
          background: "radial-gradient(circle, #7c3aed 0%, transparent 70%)",
          opacity: 0.2,
        }}
        delay={0}
      />
      <BackgroundOrb
        style={{
          right: "-5%", bottom: "10%", width: "35vw", height: "35vw",
          background: "radial-gradient(circle, #2563eb 0%, transparent 70%)",
          opacity: 0.15,
        }}
        delay={2}
      />
      <BackgroundOrb
        style={{
          left: "35%", bottom: "-5%", width: "25vw", height: "25vw",
          background: "radial-gradient(circle, #6d28d9 0%, transparent 70%)",
          opacity: 0.18,
        }}
        delay={4}
      />

      <motion.div
        className="relative z-10 bg-gray-900 p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-800"
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.h1
          className="text-3xl font-bold text-white mb-2"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18, duration: 0.4 }}
        >
          NexusMind
        </motion.h1>

        <AnimatePresence mode="wait">
          <motion.p
            key={isRegister ? "sub-reg" : "sub-login"}
            className="text-gray-400 mb-8"
            initial={{ opacity: 0, x: slideDir.current * 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -slideDir.current * 16 }}
            transition={{ duration: 0.22 }}
          >
            {isRegister ? "Create your account" : "Sign in to your account"}
          </motion.p>
        </AnimatePresence>

        <AnimatePresence mode="wait">
          <motion.form
            key={isRegister ? "form-register" : "form-login"}
            onSubmit={handleSubmit}
            className="space-y-4"
            initial={{ opacity: 0, x: slideDir.current * 28 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -slideDir.current * 28 }}
            transition={{ duration: 0.28, ease: "easeInOut" }}
            aria-label={isRegister ? "Create account form" : "Sign in form"}
            noValidate
          >
            {fields}

            <div aria-live="polite" aria-atomic="true">
              <AnimatePresence>
                {error && (
                  <motion.p
                    className="text-red-400 text-sm overflow-hidden"
                    role="alert"
                    variants={errorVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                  >
                    {error}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 flex items-center justify-center gap-2"
              whileTap={{ scale: 0.97 }}
              whileHover={!loading ? { scale: 1.015 } : {}}
              transition={{ type: "spring", stiffness: 380, damping: 20 }}
            >
              {loading ? (
                <>
                  <Spinner />
                  <span>{isRegister ? "Creating account..." : "Signing in..."}</span>
                </>
              ) : isRegister ? (
                "Create Account"
              ) : (
                "Sign In"
              )}
            </motion.button>
          </motion.form>
        </AnimatePresence>

        <p className="text-gray-500 text-sm mt-6 text-center">
          {isRegister ? "Already have an account?" : "Need an account?"}{" "}
          <button
            onClick={handleToggle}
            className="text-purple-400 hover:text-purple-300 hover:underline transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 rounded"
          >
            {isRegister ? "Sign In" : "Register"}
          </button>
        </p>
      </motion.div>
    </div>
  );
}
