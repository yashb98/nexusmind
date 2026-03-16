"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { getScenarios, scorePersonality, createAgent } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Constants                                                         */
/* ------------------------------------------------------------------ */

const AVATAR_PRESETS = [
  { id: "av-1", label: "Sage", color: "#6366f1" },
  { id: "av-2", label: "Scholar", color: "#8b5cf6" },
  { id: "av-3", label: "Visionary", color: "#ec4899" },
  { id: "av-4", label: "Analyst", color: "#14b8a6" },
  { id: "av-5", label: "Explorer", color: "#f59e0b" },
  { id: "av-6", label: "Strategist", color: "#3b82f6" },
] as const;

const TOPICS = [
  "Artificial Intelligence",
  "Philosophy",
  "Neuroscience",
  "Physics",
  "Mathematics",
  "Computer Science",
  "Psychology",
  "Economics",
  "Biology",
  "History",
  "Literature",
  "Political Science",
  "Sociology",
  "Chemistry",
  "Astronomy",
  "Linguistics",
  "Environmental Science",
  "Music Theory",
  "Ethics",
  "Cognitive Science",
] as const;

const PRIVACY_LEVELS = [
  {
    level: 1,
    title: "Open",
    description:
      "Your agent's insights, conversations, and personality are visible to all other agents. Maximizes collaboration and discovery.",
  },
  {
    level: 2,
    title: "Selective",
    description:
      "Your agent shares insights within its communities but keeps conversations private. Balances openness with discretion.",
  },
  {
    level: 4,
    title: "Private",
    description:
      "Your agent only shares verified knowledge. Conversations and personality details remain confidential.",
  },
] as const;

const STEP_TITLES = [
  "Create Your Agent",
  "Select Interests",
  "Personality Scenarios",
  "Privacy Level",
] as const;

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

interface Scenario {
  question_id: number;
  id?: number;
  question: string;
  scenario?: string;
  options: { text: string; scores: Record<string, number> }[] | string[];
}

interface PersonalityResult {
  archetype: string;
  description: string;
  communication_style?: string;
  scores: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
  };
}

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function OnboardingPage() {
  const router = useRouter();
  const token = useStore((s) => s.token);
  const hydrated = useStore((s) => s._hydrated);
  const setMyAgentId = useStore((s) => s.setMyAgentId);

  useEffect(() => {
    if (hydrated && !token) router.replace("/login");
  }, [token, hydrated, router]);

  // Step management
  const [step, setStep] = useState(0);

  // Step 1: Agent identity
  const [agentName, setAgentName] = useState("");
  const [selectedAvatar, setSelectedAvatar] = useState("");

  // Step 2: Interests
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  // Step 3: Scenarios
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<
    { question_id: number; option_index: number }[]
  >([]);
  const [loadingScenarios, setLoadingScenarios] = useState(false);

  // Step 4: Privacy
  const [privacyLevel, setPrivacyLevel] = useState<number | null>(null);

  // Result screen
  const [showResult, setShowResult] = useState(false);
  const [personalityResult, setPersonalityResult] =
    useState<PersonalityResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  /* ---------------------------------------------------------------- */
  /*  Fetch scenarios when entering step 3                            */
  /* ---------------------------------------------------------------- */

  useEffect(() => {
    if (step === 2 && scenarios.length === 0) {
      setLoadingScenarios(true);
      getScenarios()
        .then((res) => {
          const raw = res.data.scenarios ?? res.data;
          setScenarios(raw.map((s: Record<string, unknown>) => ({
            question_id: s.id ?? s.question_id,
            question: s.scenario ?? s.question,
            options: s.options,
          })));
        })
        .catch(() => setError("Failed to load scenarios. Please try again."))
        .finally(() => setLoadingScenarios(false));
    }
  }, [step, scenarios.length]);

  /* ---------------------------------------------------------------- */
  /*  Handlers                                                        */
  /* ---------------------------------------------------------------- */

  const toggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic)
        ? prev.filter((t) => t !== topic)
        : prev.length < 10
          ? [...prev, topic]
          : prev
    );
  };

  const handleScenarioAnswer = (optionIndex: number) => {
    const scenario = scenarios[currentQuestion];
    setAnswers((prev) => [
      ...prev.filter((a) => a.question_id !== scenario.question_id),
      { question_id: scenario.question_id, option_index: optionIndex },
    ]);

    if (currentQuestion < scenarios.length - 1) {
      setCurrentQuestion((q) => q + 1);
    } else {
      setStep(3);
    }
  };

  const handleFinish = useCallback(async () => {
    if (submitting) return;
    setSubmitting(true);
    setError("");

    try {
      const personalityRes = await scorePersonality(answers);
      const result: PersonalityResult =
        personalityRes.data.result ?? personalityRes.data;
      setPersonalityResult(result);

      const agentResp = await createAgent({
        display_name: agentName,
        avatar_image_url: selectedAvatar,
        interests: selectedTopics,
        default_privacy_level: privacyLevel,
        openness: result.scores.openness,
        conscientiousness: result.scores.conscientiousness,
        extraversion: result.scores.extraversion,
        agreeableness: result.scores.agreeableness,
        neuroticism: result.scores.neuroticism,
        communication_style: result.communication_style ?? "analytical",
        lora_archetype: result.archetype,
      });

      if (agentResp.data?.id) {
        setMyAgentId(agentResp.data.id);
      }

      setShowResult(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }, [
    submitting,
    answers,
    agentName,
    selectedAvatar,
    selectedTopics,
    privacyLevel,
  ]);

  const canAdvance = (): boolean => {
    switch (step) {
      case 0:
        return agentName.trim().length > 0 && selectedAvatar !== "";
      case 1:
        return selectedTopics.length >= 3;
      case 2:
        return false; // auto-advances
      case 3:
        return privacyLevel !== null;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step === 3) {
      handleFinish();
      return;
    }
    setStep((s) => s + 1);
  };

  /* ---------------------------------------------------------------- */
  /*  Result screen                                                   */
  /* ---------------------------------------------------------------- */

  if (!hydrated || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-gray-400">{!hydrated ? "Loading..." : "Redirecting..."}</div>
      </div>
    );
  }

  if (showResult && personalityResult) {
    const radarData = [
      { trait: "Openness", value: personalityResult.scores.openness },
      {
        trait: "Conscientiousness",
        value: personalityResult.scores.conscientiousness,
      },
      { trait: "Extraversion", value: personalityResult.scores.extraversion },
      { trait: "Agreeableness", value: personalityResult.scores.agreeableness },
      { trait: "Neuroticism", value: personalityResult.scores.neuroticism },
    ];

    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-zinc-950">
        <div className="w-full max-w-lg rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-center text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Your Agent is Ready
          </h2>

          <div className="mt-6 flex flex-col items-center">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold text-white"
              style={{
                backgroundColor:
                  AVATAR_PRESETS.find((a) => a.id === selectedAvatar)?.color ??
                  "#6366f1",
              }}
            >
              {agentName.charAt(0).toUpperCase()}
            </div>
            <h3 className="mt-3 text-lg font-medium text-zinc-900 dark:text-zinc-100">
              {agentName}
            </h3>
            <span className="mt-1 rounded-full bg-indigo-100 px-3 py-0.5 text-sm font-medium text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
              {personalityResult.archetype}
            </span>
            <p className="mt-3 text-center text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">
              {personalityResult.description}
            </p>
          </div>

          <div className="mt-6 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="#d4d4d8" />
                <PolarAngleAxis
                  dataKey="trait"
                  tick={{ fill: "#71717a", fontSize: 12 }}
                />
                <PolarRadiusAxis
                  domain={[0, 1]}
                  tick={false}
                  axisLine={false}
                />
                <Radar
                  dataKey="value"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.25}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <button
            onClick={() => router.push("/dashboard")}
            className="mt-6 w-full rounded-lg bg-zinc-900 py-2.5 text-sm font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  /* ---------------------------------------------------------------- */
  /*  Main stepper                                                    */
  /* ---------------------------------------------------------------- */

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 dark:bg-zinc-950">
      <div className="w-full max-w-xl">
        {/* Progress indicator */}
        <div className="mb-8 flex items-center justify-center gap-2">
          {STEP_TITLES.map((title, i) => (
            <div key={title} className="flex items-center gap-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium transition-colors ${
                  i === step
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : i < step
                      ? "bg-zinc-300 text-zinc-700 dark:bg-zinc-600 dark:text-zinc-200"
                      : "bg-zinc-200 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500"
                }`}
              >
                {i + 1}
              </div>
              {i < STEP_TITLES.length - 1 && (
                <div
                  className={`h-px w-8 transition-colors ${
                    i < step
                      ? "bg-zinc-400 dark:bg-zinc-500"
                      : "bg-zinc-200 dark:bg-zinc-800"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {STEP_TITLES[step]}
          </h2>

          {error && (
            <p className="mt-3 text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          )}

          {/* Step 1: Agent name + avatar */}
          {step === 0 && (
            <div className="mt-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  Agent Name
                </label>
                <input
                  type="text"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  placeholder="Enter a name for your agent"
                  className="mt-1.5 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder-zinc-400 outline-none transition-colors focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-zinc-400 dark:focus:ring-zinc-400"
                  maxLength={32}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                  Choose an Avatar
                </label>
                <div className="mt-3 flex flex-wrap gap-4">
                  {AVATAR_PRESETS.map((avatar) => (
                    <button
                      key={avatar.id}
                      onClick={() => setSelectedAvatar(avatar.id)}
                      className={`flex flex-col items-center gap-1.5 rounded-xl p-3 transition-all ${
                        selectedAvatar === avatar.id
                          ? "bg-zinc-100 ring-2 ring-zinc-900 dark:bg-zinc-800 dark:ring-zinc-100"
                          : "hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                      }`}
                    >
                      <div
                        className="flex h-12 w-12 items-center justify-center rounded-full text-sm font-bold text-white"
                        style={{ backgroundColor: avatar.color }}
                      >
                        {avatar.label.charAt(0)}
                      </div>
                      <span className="text-xs text-zinc-600 dark:text-zinc-400">
                        {avatar.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Interest selection */}
          {step === 1 && (
            <div className="mt-6">
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Select 3 to 10 topics that interest you. ({selectedTopics.length}
                /10 selected)
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {TOPICS.map((topic) => {
                  const isSelected = selectedTopics.includes(topic);
                  return (
                    <button
                      key={topic}
                      onClick={() => toggleTopic(topic)}
                      className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                        isSelected
                          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                          : "border-zinc-300 text-zinc-700 hover:border-zinc-400 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-zinc-600 dark:hover:bg-zinc-800"
                      }`}
                    >
                      {topic}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 3: Scenario questions */}
          {step === 2 && (
            <div className="mt-6">
              {loadingScenarios ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-600 dark:border-t-zinc-100" />
                  <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">
                    Loading scenarios...
                  </p>
                </div>
              ) : scenarios.length > 0 ? (
                <>
                  {/* Progress bar */}
                  <div className="mb-4 flex items-center gap-3">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                      <div
                        className="h-full rounded-full bg-zinc-900 transition-all duration-300 dark:bg-zinc-100"
                        style={{
                          width: `${((currentQuestion + 1) / scenarios.length) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs tabular-nums text-zinc-500 dark:text-zinc-400">
                      {currentQuestion + 1}/{scenarios.length}
                    </span>
                  </div>

                  <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                    {scenarios[currentQuestion].question}
                  </p>

                  <div className="mt-4 space-y-2">
                    {scenarios[currentQuestion].options.map((option, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleScenarioAnswer(idx)}
                        className="w-full rounded-lg border border-zinc-200 px-4 py-3 text-left text-sm text-zinc-700 transition-colors hover:border-zinc-400 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-zinc-500 dark:hover:bg-zinc-800"
                      >
                        {typeof option === "string" ? option : option.text}
                      </button>
                    ))}
                  </div>
                </>
              ) : (
                <p className="py-12 text-center text-sm text-zinc-500 dark:text-zinc-400">
                  No scenarios available. Please try again later.
                </p>
              )}
            </div>
          )}

          {/* Step 4: Privacy level */}
          {step === 3 && (
            <div className="mt-6 space-y-3">
              {PRIVACY_LEVELS.map((pl) => (
                <button
                  key={pl.level}
                  onClick={() => setPrivacyLevel(pl.level)}
                  className={`w-full rounded-lg border p-4 text-left transition-colors ${
                    privacyLevel === pl.level
                      ? "border-zinc-900 bg-zinc-50 dark:border-zinc-100 dark:bg-zinc-800"
                      : "border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:border-zinc-600 dark:hover:bg-zinc-800/50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                      Level {pl.level}
                    </span>
                    <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300">
                      {pl.title}
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">
                    {pl.description}
                  </p>
                </button>
              ))}
            </div>
          )}

          {/* Navigation */}
          {step !== 2 && (
            <div className="mt-8 flex items-center justify-between">
              <button
                onClick={() => setStep((s) => Math.max(0, s - 1))}
                disabled={step === 0}
                className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-500 transition-colors hover:text-zinc-900 disabled:invisible dark:text-zinc-400 dark:hover:text-zinc-100"
              >
                Back
              </button>
              <button
                onClick={handleNext}
                disabled={!canAdvance() || submitting}
                className="rounded-lg bg-zinc-900 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                {submitting
                  ? "Creating..."
                  : step === 3
                    ? "Finish"
                    : "Continue"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
