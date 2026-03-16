"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useStore } from "@/lib/store";
import { listGroups, discoverGroups, createGroup, joinGroup } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

interface Group { id: string; name: string; description: string; group_type: string; member_count: number; is_member?: boolean; }

const cardVariants = {
  hidden: { opacity: 0, scale: 0.94, y: 16 },
  visible: (i: number) => ({ opacity: 1, scale: 1, y: 0, transition: { delay: i * 0.06, duration: 0.35, ease: "easeOut" } }),
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.2, ease: "easeOut" } },
  exit: { opacity: 0, scale: 0.92, transition: { duration: 0.15 } },
};

export default function GroupsPage() {
  const router = useRouter();
  const { token, _hydrated } = useStore();
  const [myGroups, setMyGroups] = useState<Group[]>([]);
  const [discovered, setDiscovered] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newType, setNewType] = useState("open");
  const firstFocusRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!_hydrated) return;
    if (!token) { router.replace("/login"); return; }
    loadGroups();
  }, [token, _hydrated]);

  useEffect(() => {
    if (showCreate) setTimeout(() => firstFocusRef.current?.focus(), 50);
  }, [showCreate]);

  const handleModalKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") { setShowCreate(false); return; }
    if (e.key !== "Tab" || !modalRef.current) return;
    const focusable = modalRef.current.querySelectorAll<HTMLElement>('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey ? document.activeElement === first : document.activeElement === last) {
      e.preventDefault();
      (e.shiftKey ? last : first).focus();
    }
  };

  const loadGroups = async () => {
    setLoading(true);
    try {
      const [mine, disc] = await Promise.all([listGroups().catch(() => ({ data: [] })), discoverGroups().catch(() => ({ data: [] }))]);
      setMyGroups(mine.data);
      setDiscovered(disc.data);
    } catch { /* handled */ }
    setLoading(false);
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await createGroup({ name: newName.trim(), description: newDesc.trim(), group_type: newType });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
      loadGroups();
    } catch { /* handled */ }
  };

  const handleJoin = async (id: string) => {
    try { await joinGroup(id); loadGroups(); } catch { /* handled */ }
  };

  if (!_hydrated || !token) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-950"><div className="text-gray-400">{!_hydrated ? "Loading..." : "Redirecting..."}</div></div>;
  }

  const GroupCard = ({ group, showJoin, index }: { group: Group; showJoin?: boolean; index: number }) => (
    <motion.div custom={index} variants={cardVariants} initial="hidden" animate="visible" whileHover={{ y: -2, boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }} className="rounded-xl border border-gray-800 bg-gray-900 p-4 flex flex-col gap-2 cursor-default">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">{group.name}</h3>
        <span className="text-[10px] uppercase font-semibold rounded-full px-2 py-0.5 bg-purple-900/40 text-purple-300 border border-purple-700/40">{group.group_type}</span>
      </div>
      <p className="text-xs text-gray-400 line-clamp-2">{group.description || "No description"}</p>
      <div className="flex items-center justify-between mt-auto pt-2">
        <span className="text-xs text-gray-500">{group.member_count ?? 0} members</span>
        {showJoin && <button onClick={() => handleJoin(group.id)} className="rounded-lg bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-500 transition-colors">Join</button>}
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-xl font-bold">Groups</h1>
          <button onClick={() => setShowCreate(true)} aria-label="Create a new group" className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 transition-colors">+ Create Group</button>
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-600 border-t-purple-400" /></div>
        ) : (
          <>
            <section className="mb-10">
              <h2 className="text-sm font-semibold text-gray-300 mb-4">My Groups</h2>
              {myGroups.length === 0 ? <p className="text-sm text-gray-500">No groups yet. Create one or discover public groups.</p> : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{myGroups.map((g, i) => <GroupCard key={g.id} group={g} index={i} />)}</div>
              )}
            </section>
            <section>
              <h2 className="text-sm font-semibold text-gray-300 mb-4">Discover Groups</h2>
              {discovered.length === 0 ? <p className="text-sm text-gray-500">No groups to discover right now.</p> : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{discovered.map((g, i) => <GroupCard key={g.id} group={g} showJoin index={i} />)}</div>
              )}
            </section>
          </>
        )}

        <AnimatePresence>
          {showCreate && (
            <motion.div key="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={(e) => { if (e.target === e.currentTarget) setShowCreate(false); }}>
              <motion.div ref={modalRef} role="dialog" aria-modal="true" aria-labelledby="create-group-title" variants={modalVariants} initial="hidden" animate="visible" exit="exit" onKeyDown={handleModalKeyDown} className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
                <h2 id="create-group-title" className="text-lg font-semibold text-white mb-4">Create Group</h2>
                <input ref={firstFocusRef} type="text" placeholder="Group name" value={newName} onChange={(e) => setNewName(e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 mb-3" />
                <textarea placeholder="Description (optional)" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} rows={3} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-purple-500 mb-3 resize-none" />
                <select value={newType} onChange={(e) => setNewType(e.target.value)} aria-label="Group type" className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-sm text-white outline-none focus:border-purple-500 mb-4">
                  <option value="open">Open</option>
                  <option value="closed">Closed</option>
                  <option value="secret">Secret</option>
                </select>
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
