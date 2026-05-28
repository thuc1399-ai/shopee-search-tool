export default function ProductCard({ product, rank }) {
  const formatPrice = (p) =>
    new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(p);

  return (
    <div className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 relative">
      {/* Rank badge */}
      <div className="absolute top-2 left-2 z-10 bg-orange-500 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs font-bold shadow">
        #{rank}
      </div>

      {/* AI Score badge */}
      {product.score && (
        <div className="absolute top-2 right-2 z-10 bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full font-semibold">
           {product.score}
        </div>
      )}

      {/* Image */}
      <a href={product.product_url} target="_blank" rel="noreferrer">
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-48 object-cover hover:scale-105 transition-transform duration-300"
          onError={(e) => { e.target.src = "/placeholder.png"; }}
        />
      </a>

      <div className="p-3">
        {/* Shop badges */}
        <div className="flex gap-1 mb-1">
          {product.is_official_shop && (
            <span className="text-[10px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded font-semibold">
              Mall
            </span>
          )}
          <span className="text-[10px] text-gray-400">📍 {product.location}</span>
        </div>

        {/* Name */}
        <a href={product.product_url} target="_blank" rel="noreferrer">
          <p className="text-sm font-medium text-gray-800 line-clamp-2 hover:text-orange-500 transition-colors mb-2">
            {product.name}
          </p>
        </a>

        {/* Price */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-orange-500 font-bold text-base">
            {formatPrice(product.price)}
          </span>
          {product.discount_percent && (
            <span className="bg-red-100 text-red-500 text-xs px-1 rounded font-semibold">
              -{product.discount_percent}%
            </span>
          )}
        </div>
        {product.original_price && (
          <p className="text-xs text-gray-400 line-through">
            {formatPrice(product.original_price)}
          </p>
        )}

        {/* Stats */}
        <div className="flex justify-between text-xs text-gray-500 mt-2 pt-2 border-t border-gray-100">
          <span> {product.rating ?? "N/A"}</span>
          <span> Đã bán {product.sold.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}