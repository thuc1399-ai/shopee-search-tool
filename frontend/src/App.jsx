import { useState } from "react";
import { searchProducts } from "./api/search";
import ProductCard from "./components/ProductCard";

export default function App() {
  const [keyword, setKeyword] = useState("");
  const [useAI, setUseAI] = useState(true);
  const [sortBy, setSortBy] = useState("relevancy");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!keyword.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchProducts({ keyword, useAI, sortBy });
      setResult(data);
    } catch (e) {
      setError("Không thể tải kết quả. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white">
      {/* Header */}
      <header className="bg-orange-500 text-white py-4 px-6 shadow-lg">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <img src="https://cf.shopee.vn/file/sg-11134004-7rd4g-m7kkfm9j6nme07_tn" className="h-8" alt="shopee" />
          <h1 className="text-xl font-bold">Shopee Search Tool</h1>
          <span className="ml-auto text-xs bg-orange-400 px-2 py-1 rounded-full">
             AI-Powered
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Search box */}
        <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <div className="flex gap-3 mb-4">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Tìm kiếm sản phẩm trên Shopee..."
              className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-xl font-semibold transition-colors disabled:opacity-50"
            >
              {loading ? "⏳ Đang tìm..." : "🔍 Tìm kiếm"}
            </button>
          </div>

          {/* Options */}
          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useAI}
                onChange={(e) => setUseAI(e.target.checked)}
                className="accent-orange-500"
              />
               AI tối ưu keyword
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-orange-400"
            >
              <option value="relevancy">Liên quan nhất</option>
              <option value="sales">Bán chạy nhất</option>
              <option value="price">Giá thấp nhất</option>
            </select>
          </div>
        </div>

        {/* AI info bar */}
        {result?.keyword_enhanced && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-2 mb-4 text-sm text-blue-700">
             AI đã tối ưu keyword: <strong>"{result.keyword_original}"</strong> →{" "}
            <strong>"{result.keyword_enhanced}"</strong>
            <span className="ml-2 text-gray-400">({result.search_time_ms}ms)</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 text-red-600 rounded-xl px-4 py-3 mb-4 text-sm">
             {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <>
            <p className="text-sm text-gray-500 mb-4">
              Tìm thấy <strong>{result.total_found}</strong> sản phẩm
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {result.products.map((p, i) => (
                <ProductCard key={p.item_id} product={p} rank={i + 1} />
              ))}
            </div>
          </>
        )}

        {/* Empty state */}
        {!result && !loading && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">🛍️</p>
            <p>Nhập từ khóa để tìm kiếm sản phẩm trên Shopee</p>
          </div>
        )}
      </main>
    </div>
  );
}