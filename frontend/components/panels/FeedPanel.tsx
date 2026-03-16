"use client";

import { useEffect, useState } from "react";
import { getFeed, getUnreadCount, markFeedRead } from "@/lib/api";

interface FeedItem {
  id: string;
  item_type: string;
  title: string;
  summary: string;
  created_at: string;
  is_read: boolean;
  metadata?: Record<string, unknown>;
}

const typeIcon = (type: string): string => {
  switch (type) {
    case "conversation": return "💬";
    case "insight": return "💡";
    case "verification": return "✅";
    case "group": return "👥";
    case "event": return "📅";
    case "connection": return "🔗";
    case "evolution": return "🧬";
    default: return "📌";
  }
};

export default function FeedPanel() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeed();
  }, []);

  const loadFeed = async () => {
    setLoading(true);
    try {
      const [feedResp, unreadResp] = await Promise.all([
        getFeed(50).catch(() => ({ data: [] })),
        getUnreadCount().catch(() => ({ data: { count: 0 } })),
      ]);
      setItems(feedResp.data);
      setUnread(unreadResp.data?.count ?? 0);
    } catch { /* handled */ }
    setLoading(false);
  };

  const handleMarkRead = async (id: string) => {
    try {
      await markFeedRead(id);
      setItems((prev) => prev.map((i) => (i.id === id ? { ...i, is_read: true } : i)));
      setUnread((prev) => Math.max(0, prev - 1));
    } catch { /* handled */ }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-600 border-t-purple-400" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-sm text-gray-500">No activity yet. Start conversations to see your feed.</p>
      </div>
    );
  }

  return (
    <div>
      {unread > 0 && (
        <div className="mb-3 flex items-center gap-2">
          <span className="inline-flex items-center justify-center rounded-full bg-purple-600 px-2 py-0.5 text-[10px] font-bold text-white">
            {unread}
          </span>
          <span className="text-xs text-gray-400">unread items</span>
        </div>
      )}
      <div className="space-y-2">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => !item.is_read && handleMarkRead(item.id)}
            className={`w-full text-left rounded-lg border p-3 transition-colors ${
              item.is_read
                ? "border-gray-800 bg-gray-900/50"
                : "border-purple-800/40 bg-gray-900 hover:bg-gray-800"
            }`}
          >
            <div className="flex items-start gap-2.5">
              <span className="text-base mt-0.5">{typeIcon(item.item_type)}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-medium text-white truncate">{item.title}</h4>
                  <span className="text-[10px] text-gray-500 shrink-0">
                    {item.created_at ? new Date(item.created_at).toLocaleDateString() : ""}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{item.summary}</p>
              </div>
              {!item.is_read && (
                <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-purple-500" />
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
