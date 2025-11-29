"use client";

import { useWatchlistStore } from "../../store/watchlistStore";
import StockCard from "../components/StockCard";
import NewsFeed from "../components/NewsFeed";

export default function Watchlist() {
  const watchlist = useWatchlistStore((state) => state.watchlist);

  return (
    <div className="flex min-h-screen bg-[#f8fafc] stock-doodle-bg">
      <main className="flex-1 px-12 py-10">
        <h1 className="text-4xl font-extrabold mb-6">Watchlist</h1>

        {watchlist.length === 0 ? (
          <p className="text-gray-600 text-lg">No stocks yet. Go to Dashboard and click +</p>
        ) : (
          <div className="grid grid-cols-2 gap-8 max-w-5xl">
            {watchlist.map((stock, i) => (
              <StockCard key={i} stock={stock} />
            ))}
          </div>
        )}
      </main>

      <NewsFeed />
    </div>
  );
}
