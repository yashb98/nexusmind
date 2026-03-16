"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { listEvents, createEvent, joinEvent } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

interface EventItem { id: string; name: string; description: string; event_type: string; status: string; start_time: string; participant_count: number; }

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.35, ease: "easeOut" } }),
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.2, ease: "easeOut" } },
  exit: { opacity: 0, scale: 0.92, transition: { duration: 0.15 } },
};

export default function EventsPage() {
  const router = useRouter();
  const { token, _hydrated } = useStore();
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newType, setNewType] = useState("debate");
  const [newDate, setNewDate] = useState("");
  const firstFocusRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!_hydrated) return;
    if (!token) { router.replace("/login"); return; }
    loadEvents();
  }, [token, _hydrated]);

  useEffect(() => {
    if (showCreate) setTimeout(() => firstFocusRef.current?.focus(), 50);
  }, [showCreate]);

  const handleModalKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") { setShowCreate(false); return; }
    if (e.key !== "Tab" || !modalRef.current) return;
    const focusable = modalRef.current.querySelectorAll<HTMLElement>('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusable[0]; const last = focusable[focusable.length - 1];
    if (e.shiftKey ? document.activeElement === first : document.activeElement === last) { e.preventDefault(); (e.shiftKey ? last : first).focus(); }
  };

  const loadEvents = async () => {
    setLoading(true);
    try { const resp = await listEvents(); setEvents(resp.data); } catch { setEvents([]); }
    setLoading(false);
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try { await createEvent({ name: newName.trim(), description: newDesc.trim(), event_type: newType, start_time: newDate || undefined }); setShowCreate(false); setNewName(""); setNewDesc(""); setNewDate(""); loadEvents(); } catch { /* handled */ }
  };

  const handleJoin = async (id: string) => { try { await joinEvent(id); loadEvents(); } catch { /* handled */ } };

  if (!_hydrated || !token) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-950"><div className="text-gray-400">{!_hydrated ? "Loading..." : "Redirecting..."}</div></div>;
  }

  const live = events.filter((e) => e.status === "live");
  const upcoming = events.filter((e) => e.status === "upcoming" || e.status === "scheduled");
  const past = events.filter((e) => e.status === "completed" || e.status === "past");
  const formatDate = (iso: string) => { try { return new Date(iso).toLocaleString(); } catch { return iso; } };
  const statusColor = (status: string) => { switch (status) { case "live": return "bg-green-900/40 text-green-300 border-green-700/40"; case "upcoming": case "scheduled": return "bg-blue-900/40 text-blue-300 border-blue-700/40"; default: return "bg-gray-800 text-gray-400 border-gray-700"; } };

  const EventCard = ({ event, index }: { event: EventItem; index: number }) => (
    <motion.div custom={index} variants={cardVariants} initial="hidden" animate="visible" whileHover={{ y: -2, boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }} className={`rounded-xl border bg-gray-900 p-4 flex flex-col gap-2 ${event.status === "live" ? "border-green-700/60" : "border-gray-800"}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">{event.name}</h3>
        <div className="flex gap-1.5 items-center">
          {event.status === "live" && <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" /><span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" /></span>}
          <span role="status" className={`text-[10px] uppercase font-semibold rounded-full px-2 py-0.5 border ${statusColor(event.status)}`}>{event.status}</span>
          <span className="text-[10px] uppercase font-semibold rounded-full px-2 py-0.5 bg-purple-900/40 text-purple-300 border border-purple-700/40">{event.event_type}</span>
        </div>
      </div>
      <p className="text-xs text-gray-400 line-clamp-2">{event.description || "No description"}</p>
      <div className="flex items-center justify-between mt-auto pt-2">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {event.start_time && <span>{formatDate(event.start_time)}</span>}
          <span>{event.participant_count ?? 0} participants</span>
        </div>
        {event.status !== "completed" && event.status !== "past" && <button onClick={() => handleJoin(event.id)} className="rounded-lg bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-500 transition-colors">Join</button>}
      </div>
    </motion.div>
  );

  const Section = ({ title, items, highlight, startIndex }: { title: string; items: EventItem[]; highlight?: boolean; startIndex: number }) =>
    items.length > 0 ? (
      <section className="mb-10">
        <h2 className={`text-sm font-semibold mb-4 ${highlight ? "text-green-400" : "text-gray-300"}`}>{title}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{items.map((e, i) => <EventCard key={e.id} event={e} index={startIndex + i} />)}</div>
      </section>
    ) : null;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-xl font-bold">Events</h1>
          <button onClick={() => setShowCreate(true)} aria-label="Create a new event" className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 transition-colors">+ Create Event</button>
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-600 border-t-purple-400" /></div>
        ) : events.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-20">No events yet. Create one to get started.</p>
        ) : (
          <>
            <Section title="Live Now" items={live} highlight startIndex={0} />
            <Section title="Upcoming Events" items={upcoming} startIndex={live.length} />
            <Section title="Past Events" items={past} startIndex={live.length + upcoming.length} />
          </>
        )}

        <AnimatePresence>
          {showCreate && (
            <motion.div key="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={(e) => { if (e.target === e.currentTarget) setShowCreate(false); }}>
              <motion.div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="create-event-title" variants={modalVariants} initial="hidden" animate="visible" exit="exit" onKeyDown={handleModalKeyDown} className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
                <h2 id="create-event-title" className="text-lg font-semibold text-white mb-4">Create Event</h2>
                <input ref={firstFocusRef} type="text" placeholder="Event name" value={newName} onChange={(e) => setNewName(e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 mb-3" />
                <textarea placeholder="Description (optional)" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} rows={3} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 mb-3 resize-none" />
                <select value={newType} onChange={(e) => setNewType(e.target.value)} aria-label="Event type" className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-purple-500 mb-3">
                  <option value="debate">Debate</option><option value="brainstorm">Brainstorm</option><option value="workshop">Workshop</option><option value="research">Research</option>
                </select>
                <input type="datetime-local" value={newDate} onChange={(e) => setNewDate(e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-purple-500 mb-4" />
                <div className="flex gap-3 justify-end">
                  <button onClick={() => setShowCreate(false)} className="rounded-lg px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">Cancel</button>
                  <button onClick={handleCreate} disabled={!newName.trim()} className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">Create</button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
