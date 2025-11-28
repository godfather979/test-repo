export default function Navbar() {
  return (
    <nav className="w-full h-16 flex items-center justify-between px-10 bg-[#0f141a] border-b border-gray-700 sticky top-0 z-50">
      <h1 className="text-2xl font-bold tracking-wide text-green-400">
        Khabri Stocks
      </h1>

      <div className="flex gap-8 text-lg">
        <button className="hover:text-green-400 transition">Home</button>
        <button className="hover:text-green-400 transition">Watchlist</button>
        <button className="hover:text-green-400 transition">Compare</button>
      </div>
    </nav>
  );
}
