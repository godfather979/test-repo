"use client";

interface StockProps {
  stock: {
    symbol: string;
    name: string;
    price: number;
    change: string;
  };
}

export default function StockCard({ stock }: StockProps) {
  return (
    <div className="bg-[#161b22] border border-gray-700 p-5 rounded-2xl shadow-lg hover:scale-[1.03] transition-all cursor-pointer">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-semibold">{stock.symbol}</h2>
        <span className={`text-sm ${stock.change.startsWith("-") ? "text-red-400" : "text-green-400"}`}>
          {stock.change}
        </span>
      </div>

      <p className="text-gray-300 text-sm mb-3">{stock.name}</p>
      <p className="text-2xl font-bold mb-4">₹{stock.price}</p>

      {/* Sparkline Placeholder */}
      <div className="h-10 bg-gray-800 rounded-lg mb-4 animate-pulse"></div>

      <button className="w-full py-2 rounded-lg bg-green-600 hover:bg-green-700 transition-all">
        Add to Watchlist ⭐
      </button>
    </div>
  );
}
