import React from "react";

// Format price to Vietnamese currency
const formatVND = (price) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(price);

// Score bar color: green > 70, yellow 40-70, orange < 40
const scoreColor = (score) => {
  if (score >= 70) return "bg-green-400";
  if (score >= 40) return "bg-yellow-400";
  return "bg-orange-400";
};

const ProductCard = ({ product, rank }) => {
  const [copied, setCopied] = React.useState(false);
  const [imgError, setImgError] = React.useState(false);

  const handleCopy = (e) => {
    e.preventDefault();
    navigator.clipboard.writeText(product.product_url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className="relative bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden border border-gray-100 flex flex-col group">

      {/* ── Rank badge ─────────────────────────────────────────────── */}
      <div className={`
        absolute top-2 left-2 z-10 w-7 h-7 rounded-full flex items-center justify-center
        text-xs font-bold text-white shadow-md
        ${rank === 1 ? "bg-yellow-500" : rank === 2 ? "bg-gray-400" : rank === 3 ? "bg-amber-600" : "bg-orange-500"}
      `}>
        {rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `#${rank}`}
      </div>

      {/* ── Discount badge ─────────────────────────────────────────── */}
      {product.discount_percent > 0 && (
        <div className="absolute top-2 right-2 z-10 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
          -{product.discount_percent}%
        </div>
      )}

      {/* ── Product image ───────────────────────────────────────────── */}
      <a href={product.product_url} target="_blank" rel="noopener noreferrer" className="block overflow-hidden">
        <img
          src={imgError ? "https://placehold.co/200x200?text=No+Image" : product.image_url}
          alt={product.name}
          onError={() => setImgError(true)}
          className="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-300"
        />
      </a>

      <div className="p-3 flex flex-col flex-grow">

        {/* ── Badges row ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-1 mb-1.5 flex-wrap">
          {product.is_official_shop && (
            <span className="text-[9px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded font-bold uppercase tracking-wide">
              Mall
            </span>
          )}
          {product.location && (
            <span className="text-[9px] text-gray-400 truncate">📍 {product.location}</span>
          )}
        </div>

        {/* ── Product name ────────────────────────────────────────────── */}
        <a
          href={product.product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-gray-800 line-clamp-2 hover:text-orange-500 transition-colors mb-2 leading-snug"
          title={product.name}
        >
          {product.name}
        </a>

        {/* ── Price ───────────────────────────────────────────────────── */}
        <div className="mt-auto">
          <div className="flex items-baseline gap-1.5 mb-0.5">
            <span className="text-orange-500 font-bold text-sm">
              {formatVND(product.price)}
            </span>
          </div>
          {product.original_price && product.original_price > product.price && (
            <span className="text-[10px] text-gray-400 line-through">
              {formatVND(product.original_price)}
            </span>
          )}

          {/* ── Stats row ─────────────────────────────────────────────── */}
          <div className="flex justify-between items-center text-[10px] text-gray-500 mt-2 mb-2">
            <span className="flex items-center gap-0.5">
              ⭐ <span className="font-medium">{product.rating?.toFixed(1) ?? "—"}</span>
            </span>
            <span>🛒 {product.sold >= 1000 ? `${(product.sold/1000).toFixed(1)}k` : product.sold}</span>
          </div>

          {/* ── AI Score bar ──────────────────────────────────────────── */}
          {product.score != null && (
            <div className="mb-3">
              <div className="flex justify-between text-[9px] text-gray-400 mb-0.5">
                <span>Độ liên quan</span>
                <span className="font-semibold text-gray-600">{product.score}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1">
                <div
                  className={`h-1 rounded-full transition-all ${scoreColor(product.score)}`}
                  style={{ width: `${Math.min(product.score, 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* ── Action buttons ────────────────────────────────────────── */}
          <div className="flex gap-1.5">
            <a
              href={product.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center bg-orange-500 hover:bg-orange-600 text-white text-xs py-2 rounded-lg font-semibold transition-colors"
            >
              Xem Shopee
            </a>
            <button
              onClick={handleCopy}
              title="Copy link"
              className="w-8 flex items-center justify-center border border-gray-200 hover:border-orange-300 rounded-lg text-sm transition-colors"
            >
              {copied ? "✓" : "🔗"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;