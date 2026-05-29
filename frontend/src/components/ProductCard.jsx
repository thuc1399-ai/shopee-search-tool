import React from 'react';

const ProductCard = ({ product, rank }) => {
    return (
        <div className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white flex flex-col">
            <div className="relative">
                <span className="absolute top-0 left-0 bg-red-500 text-white px-2 py-1 rounded-br-lg font-bold z-10">
                    Top {rank}
                </span>
                <img 
                    src={product.image_url} 
                    alt={product.name} 
                    className="w-full h-48 object-cover"
                    onError={(e) => e.target.src = 'https://via.placeholder.com/200?text=No+Image'}
                />
            </div>
            <div className="p-4 flex flex-col flex-grow">
                <h3 className="font-semibold text-gray-800 line-clamp-2 mb-2 text-sm">
                    {product.name}
                </h3>
                <div className="mt-auto">
                    <p className="text-red-500 font-bold text-lg mb-2">
                        {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(product.price)}
                    </p>
                    <div className="flex justify-between items-center text-xs text-gray-500 mb-4">
                        <span>Đã bán: {product.sold}</span>
                        <span>
                            {product.rating != null ? product.rating.toFixed(1) : "N/A"}
                        </span>
                    </div>
                    <a 
                        href={product.product_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="block w-full text-center bg-orange-500 text-white py-2 rounded hover:bg-orange-600 transition-colors text-sm"
                    >
                        Xem trên Shopee
                    </a>
                </div>
            </div>
        </div>
    );
};

export default ProductCard;