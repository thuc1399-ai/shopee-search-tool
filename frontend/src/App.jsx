import { useState, useEffect, useRef, useCallback } from "react";
import { searchProducts } from "./api/search";
import ProductCard from "./components/ProductCard";

const SkeletonCard = () => (
  <div className="animate-pulse border rounded-xl overflow-hidden bg-white shadow-sm">
    <div className="h-48 bg-gray-200" />
    <div className="p-4 space-y-3">
      <div className="h-3 bg-gray-200 rounded w-full" />
      <div className="h-3 bg-gray-200 rounded w-4/5" />
      <div className="h-5 bg-orange-100 rounded w-2/5 mt-2" />
      <div className="h-3 bg-gray-100 rounded w-3/5" />
    </div>
  </div>
);

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

const API_BASE = "/api/v1";

export default function App() {
  const [keyword, setKeyword] = useState("");
  const [useAI, setUseAI] = useState(true);
  const [sortBy, setSortBy] = useState("relevancy");
  const [limit, setLimit] = useState(10);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const [searchHistory, setSearchHistory] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem("search_history") || "[]"); }
    catch { return []; }
  });
  
  const inputRef = useRef(null);
  const suggestRef = useRef(null);
  const debouncedKw = useDebounce(keyword, 250);

  useEffect(() => {
    if (!debouncedKw.trim() || debouncedKw.length < 2) {
      setSuggestions([]);
      return;
    }
    
    const controller = new AbortController();
    
    fetch(`${API_BASE}/suggest?q=${encodeURIComponent(debouncedKw)}&limit=6`, {
      signal: controller.signal
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => setSuggestions(d?.suggestions || []))
      .catch(err => {
        if (err.name !== 'AbortError') setSuggestions([]);
      });
      
    return () => controller.abort();
  }, [debouncedKw]);

  useEffect(() => {
    const handler = (e) => {
      if (suggestRef.current && !suggestRef.current.contains(e.target)) {
        setShowSuggest(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSearch = useCallback(async (kw = keyword, currentLimit = limit) => {
    const q = kw.trim();
    if (!q) return;
    
    setShowSuggest(false);
    setLoading(true);
    setError(null);
    
    try {
      const data = await searchProducts({ keyword: q, useAI, sortBy, limit: currentLimit });
      setResult(data);
      setSearchHistory(prev => {
        const next = [q, ...prev.filter(h => h !== q)].slice(0, 8);
        sessionStorage.setItem("search_history", JSON.stringify(next));
        return next;
      });
    } catch (e) {
      setError(e?.message || "Không thể tải kết quả. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, [keyword, useAI, sortBy, limit]);

  const handleSuggestClick = (s) => {
    setKeyword(s);
    setLimit(10);
    setShowSuggest(false);
    handleSearch(s, 10);
  };
  
  const loadMore = () => {
    const newLimit = limit + 10;
    setLimit(newLimit);
    handleSearch(keyword, newLimit);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white">
      <header className="bg-orange-500 text-white py-4 px-6 shadow-lg">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <img
            src="https://cf.shopee.vn/file/sg-11134004-7rd4g-m7kkfm9j6nme07_tn"
            className="h-8" alt="shopee"
            onError={e => e.target.style.display = "none"}
          />
          <h1 className="text-xl font-bold">Shopee Search Tool</h1>
          <span className="ml-auto text-xs bg-orange-400 px-2 py-1 rounded-full font-semibold">
            ✨ AI-Powered
          </span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <div className="relative flex gap-3 mb-4" ref={suggestRef}>
            <div className="relative flex-1">
              <input
                ref={inputRef}
                type="text"
                value={keyword}
                onChange={e => { setKeyword(e.target.value); setShowSuggest(true); }}
                onKeyDown={e => {
                  if (e.key === "Enter") { setLimit(10); handleSearch(keyword, 10); }
                  if (e.key === "Escape") setShowSuggest(false);
                }}
                onFocus={() => setShowSuggest(true)}
                placeholder="Tìm kiếm sản phẩm trên Shopee..."
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
              />

              {showSuggest && (suggestions.length > 0 || searchHistory.length > 0) && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
                  {suggestions.length > 0 && (
                    <>
                      <p className="text-[10px] text-gray-400 px-3 pt-2 pb-1 uppercase tracking-wide">
                        Gợi ý
                      </p>
                      {suggestions.map((s, i) => (
                        <button
                          key={i}
                          onMouseDown={() => handleSuggestClick(s)}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-orange-50 flex items-center gap-2 transition-colors"
                        >
                          <span className="text-orange-400">🔍</span>
                          <span className="line-clamp-1">{s}</span>
                        </button>
                      ))}
                    </>
                  )}
                  {searchHistory.length > 0 && !keyword.trim() && (
                    <>
                      <p className="text-[10px] text-gray-400 px-3 pt-2 pb-1 uppercase tracking-wide border-t border-gray-100">
                        Lịch sử tìm kiếm
                      </p>
                      {searchHistory.map((h, i) => (
                        <button
                          key={i}
                          onMouseDown={() => handleSuggestClick(h)}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2 transition-colors"
                        >
                          <span className="text-gray-400">🕓</span>
                          <span>{h}</span>
                        </button>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={() => { setLimit(10); handleSearch(keyword, 10); }}
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600 active:scale-95 text-white px-6 py-3 rounded-xl font-semibold transition-all disabled:opacity-50 whitespace-nowrap"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="3" strokeDasharray="32" strokeDashoffset="12"/>
                  </svg>
                  Đang tìm...
                </span>
              ) : "🔍 Tìm kiếm"}
            </button>
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-gray-600 items-center">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={useAI}
                onChange={e => setUseAI(e.target.checked)}
                className="accent-orange-500 w-4 h-4"
              />
              <span className="font-medium">✨ AI tối ưu keyword</span>
            </label>

            <div className="flex items-center gap-2 ml-auto">
              <span className="text-gray-400 text-xs">Sắp xếp:</span>
              <select
                value={sortBy}
                onChange={e => {
                  setSortBy(e.target.value);
                  setLimit(10);
                }}
                className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-orange-400 bg-white"
              >
                <option value="relevancy">Liên quan nhất</option>
                <option value="sold">Bán chạy nhất</option>
                <option value="price">Giá thấp nhất</option>
              </select>
            </div>
          </div>
        </div>

        {result?.keyword_enhanced && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-2.5 mb-4 flex items-center gap-2 text-sm text-blue-700">
            <span className="text-base">✨</span>
            <span>
              AI tối ưu: <strong>"{result.keyword_original}"</strong>
              {" → "}
              <strong>"{result.keyword_enhanced}"</strong>
            </span>
            <span className="ml-auto text-xs text-gray-400 whitespace-nowrap">
              {result.search_time_ms}ms
            </span>
          </div>
        )}

        {result && !loading && (
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              Hiển thị <strong className="text-gray-800">{result.products?.length || 0}</strong> sản phẩm
              {!result.keyword_enhanced && (
                <span className="text-gray-400"> · {result.search_time_ms}ms</span>
              )}
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl px-4 py-3 mb-4 text-sm flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {loading && limit === 10 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Array.from({ length: 10 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : result?.products?.length > 0 ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {result.products.map((p, i) => (
                <ProductCard key={`${p.item_id}-${i}`} product={p} rank={i + 1} />
              ))}
            </div>
            
            {result.products.length >= limit && (
              <div className="mt-8 text-center">
                 <button 
                    onClick={loadMore}
                    disabled={loading}
                    className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-6 py-2.5 rounded-full text-sm font-medium transition-colors"
                 >
                    {loading ? "Đang tải..." : "Xem thêm sản phẩm"}
                 </button>
              </div>
            )}
          </>
        ) : result && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-3">😕</p>
            <p className="font-medium text-gray-500">Không tìm thấy sản phẩm nào</p>
            <p className="text-sm mt-1">Thử từ khóa khác hoặc bật chế độ AI tối ưu</p>
          </div>
        )}

        {!result && !loading && (
          <div className="text-center py-20 text-gray-400">
            <p className="text-5xl mb-4">🛍️</p>
            <p className="text-base font-medium text-gray-500 mb-2">
              Nhập từ khóa để tìm kiếm sản phẩm
            </p>
            <p className="text-xs text-gray-400">Hỗ trợ tìm kiếm tiếng Việt và tiếng Anh</p>

            <div className="flex flex-wrap justify-center gap-2 mt-6">
              {["tai nghe", "điện thoại samsung", "laptop gaming", "đồng hồ thông minh"].map(q => (
                <button
                  key={q}
                  onClick={() => { setKeyword(q); setLimit(10); handleSearch(q, 10); }}
                  className="text-xs bg-orange-50 hover:bg-orange-100 text-orange-600 border border-orange-200 px-3 py-1.5 rounded-full transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}